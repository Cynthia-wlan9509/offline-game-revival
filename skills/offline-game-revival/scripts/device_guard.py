#!/usr/bin/env python3
"""Single-project device lock & safe ADB wrapper (stdlib only).
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Prevents cross-project emulator interference by locking every project to ONE serial
in 交接/设备锁.json, blocking dangerous commands (svc wifi disable, kill-server),
checking ABI compatibility, and safely staging non-ASCII/Chinese paths via /data/local/tmp.

Examples:
    python -B device_guard.py --init-lock 交接/设备锁.json --serial emulator-5558 --adb <path-to-adb.exe> --package com.example.game
    python -B device_guard.py --check 交接/设备锁.json
    python -B device_guard.py --check-abi 交接/设备锁.json
    python -B device_guard.py --push-safe 交接/设备锁.json local.bin /data/user/0/com.example.game/files/save.json --chmod 600 --chown-pkg
    python -B device_guard.py --clean-tmp 交接/设备锁.json
    python -B device_guard.py --exec 交接/设备锁.json -- shell getprop ro.build.version.release
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

FORBIDDEN_PATTERNS = [
    re.compile(r"svc\s+wifi\s+disable", re.I),
    re.compile(r"\bkill-server\b", re.I),
    re.compile(r"\bquitall\b", re.I),
]

ALLOWED_LAUNCHERS = (
    "com.android.launcher",
    "com.android.launcher3",
    "com.cyanogenmod.trebuchet",
    "com.mumu.launcher",
    "com.ldmnq.launcher",
)


def run_adb(adb_path: str, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [adb_path, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def load_lock(lock_path: Path) -> dict:
    if not lock_path.exists():
        raise FileNotFoundError(f"Device lock not found: {lock_path}")
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    for k in ("serial", "adb", "package"):
        if not data.get(k):
            raise ValueError(f"Device lock missing required key '{k}': {lock_path}")
    return data


def get_online_devices(adb_path: str) -> dict[str, str]:
    cp = run_adb(adb_path, ["devices"])
    devs: dict[str, str] = {}
    for ln in cp.stdout.splitlines()[1:]:
        parts = ln.strip().split()
        if len(parts) >= 2:
            devs[parts[0]] = parts[1]
    return devs


def get_foreground_pkg(adb_path: str, serial: str) -> str | None:
    cp = run_adb(adb_path, ["-s", serial, "shell", "dumpsys", "window", "windows"])
    for pat in (r"mCurrentFocus=Window\{[^\}]*\s([A-Za-z0-9_.]+)/", r"mFocusedApp=.*?\s([A-Za-z0-9_.]+)/"):
        m = re.search(pat, cp.stdout)
        if m:
            return m.group(1)
    cp2 = run_adb(adb_path, ["-s", serial, "shell", "dumpsys", "activity", "activities"])
    m2 = re.search(r"topResumedActivity=.*?\s([A-Za-z0-9_.]+)/", cp2.stdout)
    return m2.group(1) if m2 else None


def cmd_init_lock(args: argparse.Namespace) -> int:
    lock_path = Path(args.init_lock)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "serial": args.serial,
        "adb": args.adb,
        "package": args.package,
        "instance_name": args.instance or "",
        "locked_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "reason": args.reason or "Single locked test instance for this project",
    }
    lock_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"action": "init_lock", "lock_file": str(lock_path), "data": data}, ensure_ascii=False, indent=2))
    return 0


def cmd_check(lock_path: Path, require_game_fg: bool) -> int:
    lock = load_lock(lock_path)
    devs = get_online_devices(lock["adb"])
    state = devs.get(lock["serial"], "missing")
    fg = get_foreground_pkg(lock["adb"], lock["serial"]) if state == "device" else None

    pkg = lock["package"]
    if state != "device":
        safe = False
        reason = f"Locked device {lock['serial']} state is '{state}', not 'device'."
    elif fg == pkg:
        safe = True
        reason = "Target game is in foreground."
    elif not require_game_fg and (fg is None or any(fg.startswith(l) for l in ALLOWED_LAUNCHERS)):
        safe = True
        reason = f"Device idle on launcher ({fg})."
    else:
        safe = False
        reason = f"Foreground app is '{fg}', NOT locked target '{pkg}' — STOP immediately, do not hijack!"

    out = {
        "serial": lock["serial"],
        "state": state,
        "target_package": pkg,
        "foreground_package": fg,
        "safe_to_operate": safe,
        "reason": reason,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if safe else 3


def cmd_check_abi(lock_path: Path) -> int:
    lock = load_lock(lock_path)
    cp = run_adb(lock["adb"], ["-s", lock["serial"], "shell", "getprop", "ro.product.cpu.abilist"])
    abilist = [x.strip() for x in cp.stdout.strip().split(",") if x.strip()]
    out = {
        "serial": lock["serial"],
        "abilist": abilist,
        "supports_32bit_arm": "armeabi-v7a" in abilist,
        "supports_64bit_arm": "arm64-v8a" in abilist,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return cp.returncode


def cmd_push_safe(lock_path: Path, local_file: Path, remote_path: str, chmod_mode: str | None, chown_pkg: bool) -> int:
    """Push file safely even with non-ASCII local/remote paths by staging via /data/local/tmp/<guid>.bin."""
    lock = load_lock(lock_path)
    if not local_file.is_file():
        raise FileNotFoundError(f"Local file not found: {local_file}")
    tmp_remote = f"/data/local/tmp/stage_{uuid.uuid4().hex[:12]}.bin"
    try:
        cp1 = run_adb(lock["adb"], ["-s", lock["serial"], "push", str(local_file), tmp_remote], timeout=180)
        if cp1.returncode != 0:
            raise RuntimeError(f"adb push failed: {cp1.stderr or cp1.stdout}")

        remote_parent = remote_path.rsplit("/", 1)[0] if "/" in remote_path else "."
        shell_parts = [f"mkdir -p '{remote_parent}'", f"cp '{tmp_remote}' '{remote_path}'"]
        if chown_pkg:
            pkg = lock["package"]
            shell_parts.append(
                f"OWNER=$(stat -c %u:%g '/data/user/0/{pkg}' 2>/dev/null || stat -c %u:%g '/data/data/{pkg}' 2>/dev/null); "
                f"[ -n \"$OWNER\" ] && chown $OWNER '{remote_path}'"
            )
        if chmod_mode:
            shell_parts.append(f"chmod {chmod_mode} '{remote_path}'")
        cp2 = run_adb(lock["adb"], ["-s", lock["serial"], "shell", " && ".join(shell_parts)])
        if cp2.returncode != 0:
            raise RuntimeError(f"remote install step failed: {cp2.stderr or cp2.stdout}")
    finally:
        run_adb(lock["adb"], ["-s", lock["serial"], "shell", f"rm -f '{tmp_remote}'"])

    print(json.dumps({
        "action": "push_safe",
        "serial": lock["serial"],
        "local": str(local_file),
        "remote": remote_path,
        "chown_pkg": chown_pkg,
        "chmod": chmod_mode,
        "passed": True,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_clean_tmp(lock_path: Path) -> int:
    lock = load_lock(lock_path)
    cp = run_adb(
        lock["adb"],
        ["-s", lock["serial"], "shell", "rm -f /data/local/tmp/*.apk /data/local/tmp/*.tar /data/local/tmp/*.idsig /data/local/tmp/stage_*.bin"],
    )
    print(json.dumps({
        "action": "clean_tmp",
        "serial": lock["serial"],
        "returncode": cp.returncode,
        "stderr": cp.stderr.strip(),
    }, ensure_ascii=False, indent=2))
    return cp.returncode


def cmd_exec(lock_path: Path, raw_args: list[str]) -> int:
    lock = load_lock(lock_path)
    if raw_args and raw_args[0] == "--":
        raw_args = raw_args[1:]
    joined = " ".join(raw_args)
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(joined):
            print(f"BLOCKED by device_guard: forbidden command pattern '{pat.pattern}'", file=sys.stderr)
            return 4
    if "-s" in raw_args:
        idx = raw_args.index("-s")
        if idx + 1 >= len(raw_args) or raw_args[idx + 1] != lock["serial"]:
            print(f"BLOCKED by device_guard: serial mismatch (locked={lock['serial']})", file=sys.stderr)
            return 4
        final_args = raw_args
    else:
        final_args = ["-s", lock["serial"], *raw_args]
    cp = run_adb(lock["adb"], final_args, timeout=120)
    if cp.stdout:
        sys.stdout.write(cp.stdout)
    if cp.stderr:
        sys.stderr.write(cp.stderr)
    return cp.returncode


def main() -> None:
    ap = argparse.ArgumentParser(description="Single-project ADB device lock guard")
    ap.add_argument("--init-lock", help="Create/overwrite lock JSON path")
    ap.add_argument("--serial", help="Device serial for --init-lock")
    ap.add_argument("--adb", default="adb", help="adb executable path for --init-lock")
    ap.add_argument("--package", help="Target game package name for --init-lock")
    ap.add_argument("--instance", help="Optional emulator instance name")
    ap.add_argument("--reason", help="Optional lock reason")
    ap.add_argument("--check", type=Path, help="Verify locked device online & foreground safety")
    ap.add_argument("--require-game-fg", action="store_true", help="Fail check unless target game itself is foreground")
    ap.add_argument("--check-abi", type=Path, help="Query ro.product.cpu.abilist on locked device")
    ap.add_argument("--push-safe", nargs=3, metavar=("LOCK", "LOCAL", "REMOTE"), help="ASCII-staged safe push + optional chown/chmod")
    ap.add_argument("--chmod", help="Permission mode for --push-safe (e.g. 600)")
    ap.add_argument("--chown-pkg", action="store_true", help="Restore app UID:GID ownership after --push-safe")
    ap.add_argument("--clean-tmp", type=Path, help="Delete /data/local/tmp/*.apk, *.tar, stage_*.bin on locked device")
    ap.add_argument("--exec", dest="exec_lock", type=Path, help="Run adb args strictly against locked serial")
    args, remainder = ap.parse_known_args()

    if args.init_lock:
        if not args.serial or not args.package:
            ap.error("--init-lock requires --serial and --package")
        sys.exit(cmd_init_lock(args))
    if args.check:
        sys.exit(cmd_check(args.check, args.require_game_fg))
    if args.check_abi:
        sys.exit(cmd_check_abi(args.check_abi))
    if args.push_safe:
        lk, loc, rem = args.push_safe
        sys.exit(cmd_push_safe(Path(lk), Path(loc), rem, args.chmod, args.chown_pkg))
    if args.clean_tmp:
        sys.exit(cmd_clean_tmp(args.clean_tmp))
    if args.exec_lock:
        sys.exit(cmd_exec(args.exec_lock, remainder))
    ap.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
