#!/usr/bin/env python3
"""Zero-apktool binary AndroidManifest.xml INTERNET permission stripper (stdlib only).
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Replaces UTF-16LE "android.permission.INTERNET" in-place with equal-length
"android.permission.NO_NET__" (and optionally UTF-8 if AXML uses UTF-8 string pool),
preserving exact AXML string pool offsets and file length with strict assertion checks.

Usage:
    python -B strip_internet_axml.py <in_manifest.xml> <out_manifest.xml>
    python -B strip_internet_axml.py --from-apk <orig.apk> <out_manifest.xml>
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

SRC_STR = "android.permission.INTERNET"
DST_STR = "android.permission.NO_NET__"
assert len(SRC_STR) == len(DST_STR)


def strip_internet(data: bytes) -> tuple[bytes, dict]:
    if not data.startswith(b"\x03\x00\x08\x00"):
        raise ValueError(f"Not a binary AXML file (magic={data[:4].hex()})")

    src_u16 = SRC_STR.encode("utf-16le")
    dst_u16 = DST_STR.encode("utf-16le")
    src_u8 = SRC_STR.encode("utf-8")
    dst_u8 = DST_STR.encode("utf-8")

    cnt_u16 = data.count(src_u16)
    cnt_u8 = data.count(src_u8)
    if cnt_u16 + cnt_u8 == 0:
        raise RuntimeError("Target permission string 'android.permission.INTERNET' not found in AXML (anchor assertion failed)")

    patched = data.replace(src_u16, dst_u16).replace(src_u8, dst_u8)
    assert len(patched) == len(data), "Byte length changed unexpectedly"
    assert patched.count(src_u16) == 0 and patched.count(src_u8) == 0, "Residual INTERNET permission found after patch"

    return patched, {
        "original_bytes": len(data),
        "patched_bytes": len(patched),
        "replaced_utf16le": cnt_u16,
        "replaced_utf8": cnt_u8,
        "replacement": DST_STR,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="In-place equal-length INTERNET permission stripper for binary AXML")
    ap.add_argument("--from-apk", type=Path, help="Read AndroidManifest.xml directly from an APK")
    ap.add_argument("paths", nargs="+", type=Path, help="<in_manifest> <out_manifest> OR <out_manifest> when --from-apk is used")
    args = ap.parse_args()

    if args.from_apk:
        if len(args.paths) != 1:
            ap.error("With --from-apk, provide exactly one <out_manifest> path")
        with zipfile.ZipFile(args.from_apk, "r") as zf:
            raw = zf.read("AndroidManifest.xml")
        out_path = args.paths[0]
    else:
        if len(args.paths) != 2:
            ap.error("Provide <in_manifest> <out_manifest>")
        raw = args.paths[0].read_bytes()
        out_path = args.paths[1]

    patched, stats = strip_internet(raw)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(patched)
    stats["output"] = str(out_path)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
