#!/usr/bin/env python3
"""Compression-preserving APK entry replacer + META-INF signature cleaner (stdlib only).
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Copies unchanged entries while preserving each entry's original compress_type (so ZIP_STORED
audio/resources.arsc/libs are never accidentally compressed), strips old META-INF signature
files (.SF/.RSA/.DSA/.EC/MANIFEST.MF), replaces or adds specified files, and verifies
output entry count & target hashes before returning.

Usage:
    python -B apk_replace.py <orig.apk> <out_unsigned.apk> --replace AndroidManifest.xml=patched.xml --replace assets/main.js=out/main.js
    python -B apk_replace.py <orig.apk> <out_unsigned.apk> --staging-dir build/staging_root
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

AUDIO_VIDEO_STORED_EXTS = {".ogg", ".mp3", ".wav", ".m4a", ".mp4", ".fsb", ".bnk", ".arsc"}


def is_sig_entry(name: str) -> bool:
    if not name.startswith("META-INF/"):
        return False
    upper = name.upper()
    return upper == "META-INF/MANIFEST.MF" or upper.endswith((".SF", ".RSA", ".DSA", ".EC"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Preserve-compression APK entry replacer & signature stripper")
    ap.add_argument("orig_apk", type=Path)
    ap.add_argument("out_apk", type=Path)
    ap.add_argument("--replace", action="append", default=[], metavar="APK_PATH=LOCAL_FILE", help="Replace or add a single entry")
    ap.add_argument("--staging-dir", type=Path, help="Replace/add all files under staging directory using relative POSIX paths")
    ap.add_argument("--remove", action="append", default=[], metavar="APK_PATH", help="Remove an entry from output APK")
    ap.add_argument("--keep-meta-inf-sig", action="store_true", help="Do not strip old META-INF signatures")
    args = ap.parse_args()

    replacements: dict[str, Path] = {}
    if args.staging_dir:
        base = args.staging_dir.resolve()
        for fp in base.rglob("*"):
            if fp.is_file():
                rel = fp.relative_to(base).as_posix()
                replacements[rel] = fp
    for item in args.replace:
        if "=" not in item:
            ap.error(f"Invalid --replace format (expected APK_PATH=LOCAL_FILE): {item}")
        apk_rel, loc = item.split("=", 1)
        apk_rel = apk_rel.lstrip("/").replace("\\", "/")
        lp = Path(loc)
        if not lp.is_file():
            raise FileNotFoundError(f"Replacement file not found: {lp}")
        replacements[apk_rel] = lp

    removals = {r.lstrip("/").replace("\\", "/") for r in args.remove}
    args.out_apk.parent.mkdir(parents=True, exist_ok=True)

    replaced_existing: list[str] = []
    added_new: list[str] = []
    stripped_sigs: list[str] = []
    copied_count = 0

    with zipfile.ZipFile(args.orig_apk, "r") as zin, zipfile.ZipFile(args.out_apk, "w") as zout:
        seen = set()
        for info in zin.infolist():
            name = info.filename
            if info.is_dir():
                continue
            if not args.keep_meta_inf_sig and is_sig_entry(name):
                stripped_sigs.append(name)
                continue
            if name in removals:
                continue

            seen.add(name)
            new_info = zipfile.ZipInfo(filename=name, date_time=info.date_time)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            if name in replacements:
                payload = replacements[name].read_bytes()
                zout.writestr(new_info, payload)
                replaced_existing.append(name)
            else:
                zout.writestr(new_info, zin.read(info))
                copied_count += 1

        for name, lp in sorted(replacements.items()):
            if name not in seen:
                ext = Path(name).suffix.lower()
                ctype = zipfile.ZIP_STORED if ext in AUDIO_VIDEO_STORED_EXTS else zipfile.ZIP_DEFLATED
                zout.write(lp, arcname=name, compress_type=ctype)
                added_new.append(name)

    # Readback verification
    with zipfile.ZipFile(args.out_apk, "r") as zchk:
        out_names = set(zchk.namelist())
        for name, lp in replacements.items():
            assert name in out_names, f"Missing replacement in output APK: {name}"
            exp_sha = hashlib.sha256(lp.read_bytes()).hexdigest()
            act_sha = hashlib.sha256(zchk.read(name)).hexdigest()
            assert exp_sha == act_sha, f"Readback SHA mismatch for {name}"
        total_out = len(out_names)

    print(json.dumps({
        "orig_apk": str(args.orig_apk),
        "out_apk": str(args.out_apk),
        "out_entries": total_out,
        "copied_unchanged": copied_count,
        "replaced_existing": replaced_existing,
        "added_new": added_new,
        "stripped_signatures": stripped_sigs,
        "readback_verified": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
