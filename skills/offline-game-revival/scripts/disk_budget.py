#!/usr/bin/env python3
"""Disk budget fuse checker and junction-safe artifact cleaner (stdlib only).
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Examples:
    python -B disk_budget.py --workspace <workspace> --max-ws-gb 20 --min-free-gb 30 --check
    python -B disk_budget.py --post-sign <workspace>/dist
    python -B disk_budget.py --prune-evidence <workspace>/evidence --max-evidence-mb 1024 --drop-large-bin
    python -B disk_budget.py --keep-latest-apks <workspace>/build --keep 2
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import sys
from pathlib import Path

LARGE_BIN_EXTS = {".apk", ".tar", ".unity3d", ".bin", ".dll", ".pdb", ".so", ".zip", ".tgz", ".7z"}
EVIDENCE_ROLL_EXTS = {".png", ".jpg", ".jpeg", ".log", ".txt"}


def is_reparse_or_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    if os.name == "nt":
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
            if attrs != -1 and (attrs & 0x0400):  # FILE_ATTRIBUTE_REPARSE_POINT (junction/symlink)
                return True
        except Exception:
            pass
    return False


def safe_unlink(p: Path) -> bool:
    if not p.exists() and not p.is_symlink():
        return False
    if is_reparse_or_link(p):
        raise RuntimeError(f"Refusing to delete link/junction: {p}")
    if p.is_dir():
        for root, dirs, _ in os.walk(p):
            for d in dirs:
                dp = Path(root) / d
                if is_reparse_or_link(dp):
                    raise RuntimeError(f"Refusing to recurse into link/junction: {dp}")
        shutil.rmtree(p)
    else:
        p.unlink()
    return True


def dir_size_bytes(root: Path) -> int:
    total = 0
    if not root.exists():
        return 0
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not is_reparse_or_link(Path(r) / d)]
        for fn in files:
            fp = Path(r) / fn
            try:
                if not is_reparse_or_link(fp):
                    total += fp.stat().st_size
            except OSError:
                pass
    return total


def check_budget(ws: Path, min_free_gb: float, max_ws_gb: float, max_evidence_mb: float, max_bin_mb: float) -> int:
    usage = shutil.disk_usage(ws)
    free_gb = usage.free / (1024**3)
    ws_gb = dir_size_bytes(ws) / (1024**3)

    violations = []
    if free_gb < min_free_gb:
        violations.append(f"Drive free {free_gb:.2f} GiB < {min_free_gb:.2f} GiB")
    if ws_gb > max_ws_gb:
        violations.append(f"Workspace {ws_gb:.2f} GiB > {max_ws_gb:.2f} GiB")

    ev_dirs = [ws / "evidence", ws / "work" / "evidence"]
    ev_report = {}
    for ev in ev_dirs:
        if not ev.exists():
            continue
        roll_bytes = 0
        large_bins = []
        for r, dirs, files in os.walk(ev):
            dirs[:] = [d for d in dirs if not is_reparse_or_link(Path(r) / d)]
            for fn in files:
                fp = Path(r) / fn
                try:
                    sz = fp.stat().st_size
                except OSError:
                    continue
                ext = fp.suffix.lower()
                if ext in EVIDENCE_ROLL_EXTS:
                    roll_bytes += sz
                if ext in LARGE_BIN_EXTS and sz > max_bin_mb * 1024 * 1024:
                    large_bins.append({"path": str(fp), "mb": round(sz / 1024 / 1024, 2)})
        ev_mb = roll_bytes / (1024**2)
        ev_report[str(ev)] = {"png_log_mb": round(ev_mb, 2), "large_bins_over_limit": large_bins}
        if ev_mb > max_evidence_mb:
            violations.append(f"Evidence logs/images {ev_mb:.1f} MiB > {max_evidence_mb:.0f} MiB ({ev})")
        if large_bins:
            violations.append(f"Evidence has {len(large_bins)} binary files > {max_bin_mb:.0f} MiB ({ev})")

    result = {
        "workspace": str(ws),
        "drive_free_gib": round(free_gb, 2),
        "workspace_gib": round(ws_gb, 3),
        "limits": {"min_free_gib": min_free_gb, "max_ws_gib": max_ws_gb, "max_evidence_mib": max_evidence_mb},
        "evidence": ev_report,
        "passed": len(violations) == 0,
        "violations": violations,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 2


def post_sign_clean(target_dir: Path) -> int:
    removed = []
    for p in target_dir.rglob("*"):
        if not p.is_file():
            continue
        nl = p.name.lower()
        if nl.endswith(".idsig") or (nl.endswith(".apk") and any(k in nl for k in ("unsigned", "aligned", "unaligned"))):
            if safe_unlink(p):
                removed.append(str(p))
    print(json.dumps({"action": "post_sign_clean", "dir": str(target_dir), "removed": removed}, ensure_ascii=False, indent=2))
    return 0


def keep_latest_apks(build_dir: Path, keep: int) -> int:
    apks = [p for p in build_dir.rglob("*.apk") if p.is_file() and not is_reparse_or_link(p)]
    apks.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    removed = []
    for old in apks[keep:]:
        if safe_unlink(old):
            removed.append(str(old))
    print(json.dumps({
        "action": "keep_latest_apks",
        "kept": [str(p) for p in apks[:keep]],
        "removed": removed,
    }, ensure_ascii=False, indent=2))
    return 0


def prune_evidence(ev_dir: Path, max_mb: float, max_bin_mb: float, drop_large_bin: bool) -> int:
    removed = []
    if not ev_dir.exists():
        print(json.dumps({"action": "prune_evidence", "dir": str(ev_dir), "removed": []}))
        return 0
    roll_files = []
    for r, dirs, files in os.walk(ev_dir):
        dirs[:] = [d for d in dirs if not is_reparse_or_link(Path(r) / d)]
        for fn in files:
            fp = Path(r) / fn
            try:
                st = fp.stat()
            except OSError:
                continue
            ext = fp.suffix.lower()
            if drop_large_bin and ext in LARGE_BIN_EXTS and st.st_size > max_bin_mb * 1024 * 1024:
                if safe_unlink(fp):
                    removed.append({"path": str(fp), "reason": "large_bin", "mb": round(st.st_size / 1024 / 1024, 2)})
            elif ext in EVIDENCE_ROLL_EXTS:
                roll_files.append((st.st_mtime, st.st_size, fp))

    roll_files.sort(key=lambda x: x[0])  # oldest first
    total = sum(x[1] for x in roll_files)
    limit = int(max_mb * 1024 * 1024)
    for _, sz, fp in roll_files:
        if total <= limit:
            break
        if safe_unlink(fp):
            total -= sz
            removed.append({"path": str(fp), "reason": "roll_cap", "mb": round(sz / 1024 / 1024, 2)})

    print(json.dumps({
        "action": "prune_evidence",
        "remaining_roll_mib": round(total / 1024 / 1024, 2),
        "removed_count": len(removed),
        "removed": removed[:50],
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Disk budget fuse checker & safe cleaner")
    ap.add_argument("--workspace", type=Path, default=Path.cwd())
    ap.add_argument("--min-free-gb", type=float, default=30.0)
    ap.add_argument("--max-ws-gb", type=float, default=20.0)
    ap.add_argument("--max-evidence-mb", type=float, default=1024.0)
    ap.add_argument("--max-bin-mb", type=float, default=20.0)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--post-sign", type=Path, help="Remove unsigned/aligned/*.idsig under directory")
    ap.add_argument("--keep-latest-apks", type=Path, help="Keep only latest N .apk files under build dir")
    ap.add_argument("--keep", type=int, default=2)
    ap.add_argument("--prune-evidence", type=Path, help="Roll evidence logs/pngs under cap")
    ap.add_argument("--drop-large-bin", action="store_true")
    args = ap.parse_args()

    rc = 0
    if args.post_sign:
        rc = max(rc, post_sign_clean(args.post_sign))
    if args.keep_latest_apks:
        rc = max(rc, keep_latest_apks(args.keep_latest_apks, args.keep))
    if args.prune_evidence:
        rc = max(rc, prune_evidence(args.prune_evidence, args.max_evidence_mb, args.max_bin_mb, args.drop_large_bin))
    if args.check or not (args.post_sign or args.keep_latest_apks or args.prune_evidence):
        rc = max(rc, check_budget(args.workspace, args.min_free_gb, args.max_ws_gb, args.max_evidence_mb, args.max_bin_mb))
    sys.exit(rc)


if __name__ == "__main__":
    main()
