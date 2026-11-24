#!/usr/bin/env python3
"""Read-only Step 0 APK Recon Scanner (stdlib only, zero business hardcoding).
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Usage:
    python -B recon_apk.py <path/to/game.apk> <out_dir>
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import re
import struct
import sys
import zipfile
from pathlib import Path


PACKER_SIGNATURES = {
    b"TPShell": "Tencent/TP Shell",
    b"libtprt.so": "Tencent/TP Shell",
    b"StubApp": "360 Jiagu",
    b"libjiagu": "360 Jiagu",
    b"Bangcle": "Bangcle/SecNeo",
    b"SecNeo": "Bangcle/SecNeo",
    b"libDexHelper": "Bangcle/SecNeo",
    b"ijiami": "iJiami",
    b"libexec.so": "iJiami",
    b"com.pairip": "Google PairIP",
    b"libpairipcore": "Google PairIP",
    b"libbaiduprotect": "Baidu Protect",
}

SDK_SIGNATURES = [
    b"FastApplication",
    b"QuickSDK",
    b"quicksdk",
    b"sygamehelper",
    b"shadowhook",
    b"libpine",
    b"secsdk",
    b"x7sy",
    b"smwl",
    b"thinkingdata",
    b"bugly",
    b"appsflyer",
]


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def classify_magic(head: bytes) -> str:
    if not head:
        return "empty"
    if head.startswith(b"\x02\x00\x00\x00TT"):
        return "Tabtoy_v4_Config"
    if head.startswith(b"UF\x00\x01"):
        return "CustomContainer(UF_00_01)"
    if head.startswith(b"UF\x00\x02"):
        return "CustomContainer(UF_00_02)"
    if head.startswith(b"\x00\x00\x00\x00\x00\x00\x00UnityFS"):
        return "ZeroPrefixedUnityFS(offset=7)"
    if head.startswith(b"UnityFS"):
        second = head.find(b"UnityFS", 7, 64)
        if second > 0:
            return f"DoublePrefixedUnityFS(offset={second})"
        return "UnityFS"
    if head.startswith(b"UnityWeb") or head.startswith(b"UnityRaw"):
        return "UnityLegacyBundle"
    idx = head.find(b"UnityFS", 1, 64)
    if idx > 0:
        return f"PrefixedUnityFS(offset={idx})"
    if head.startswith(b"\xaf\x1b\xb1\xfa"):
        return "IL2CPP_global-metadata(standard)"
    if head.startswith(b"\x1bLua"):
        ver = head[4] if len(head) > 4 else 0
        fmt = head[5] if len(head) > 5 else 0
        return f"LuaBytecode(v=0x{ver:02x},fmt=0x{fmt:02x})"
    if head.startswith(b"\x1bLJ"):
        return "LuaJITBytecode"
    if head.startswith(b"PK\x03\x04"):
        return "ZIP"
    if head.startswith(b"\x1f\x8b"):
        return "GZIP"
    if head.startswith((b"\x78\x9c", b"\x78\xda", b"\x78\x01")):
        return "ZLIB"
    if head.startswith(b"\x7fELF"):
        return "ELF"
    if head.startswith(b"dex\n"):
        return "DEX"
    if head.startswith(b"\x89PNG"):
        return "PNG"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if head.startswith(b"RIFF"):
        return "RIFF/WAV/WEBP"
    if head.startswith(b"OggS"):
        return "OGG"
    if head.startswith(b"FSB5"):
        return "FSB5_FMOD"
    if head.startswith(b"BKHD"):
        return "WWISE_BNK"
    if head.startswith(b"SQLite format 3"):
        return "SQLite3"
    if head.startswith(b"MZ"):
        return "PE/DLL"
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "MP4"
    sample = head[:256]
    try:
        txt = sample.decode("utf-8")
        printable = sum(1 for ch in txt if ch.isprintable() or ch in "\r\n\t")
        if printable / max(len(txt), 1) >= 0.92:
            s = txt.lstrip()
            if s.startswith(("{", "[")):
                return "Text/JSON"
            if s.startswith("<"):
                return "Text/XML"
            return "Text/Plain"
    except UnicodeDecodeError:
        pass
    return f"Binary(head={head[:12].hex()})"


def detect_unity_version(zf: zipfile.ZipFile, names: set[str]) -> str | None:
    for cand in (
        "assets/bin/Data/globalgamemanagers",
        "assets/bin/Data/data.unity3d",
        "assets/bin/Data/mainData",
    ):
        if cand in names:
            with zf.open(cand) as f:
                buf = f.read(4096)
            m = re.search(rb"(?:20\d\d|6000|5)\.\d+\.\d+[a-z]\d+", buf)
            if m:
                return m.group(0).decode("ascii", "ignore")
    return None


def detect_engine(all_names: set[str], so_names: set[str], apk_size: int) -> list[str]:
    hints: list[str] = []
    if "libunity.so" in so_names:
        if "libil2cpp.so" in so_names:
            hints.append("Unity-IL2CPP")
        elif any(n.startswith("assets/bin/Data/Managed/") and n.endswith(".dll") for n in all_names):
            hints.append("Unity-Mono")
        else:
            hints.append("Unity")
    if any(s in so_names for s in ("libxlua.so", "libtolua.so", "libslua.so", "liblua.so")):
        hints.append("Lua-Runtime-SO")
    if "libcocos2djs.so" in so_names or any(n.endswith(".jsc") for n in all_names):
        hints.append("Cocos-JS")
    if "libcocos2dlua.so" in so_names:
        hints.append("Cocos2d-Lua")
    if any("laya" in s.lower() or "conch" in s.lower() for s in so_names):
        hints.append("LayaAir-Native")
    if any("libUE4.so" == s or "libUnreal.so" == s for s in so_names):
        hints.append("Unreal")
    if apk_size < 15 * 1024 * 1024 and not hints:
        hints.append("Likely-MicroClient-Or-WebView-Shell")
    return hints or ["Unknown"]


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -B recon_apk.py <game.apk> <out_dir>", file=sys.stderr)
        sys.exit(2)

    apk_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    size = apk_path.stat().st_size
    h = hashlib.sha256()
    with apk_path.open("rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            h.update(chunk)
    sha256 = h.hexdigest()

    dir2 = collections.defaultdict(lambda: [0, 0])
    dir3 = collections.defaultdict(lambda: [0, 0])
    exts = collections.defaultdict(lambda: [0, 0])
    abis: dict[str, list[dict]] = collections.defaultdict(list)
    so_names: set[str] = set()
    dex_files = []
    magic_by_group: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    samples: dict[str, dict] = {}
    unityfs_prefix_counts: collections.Counter = collections.Counter()
    packers_found: dict[str, list[str]] = collections.defaultdict(list)
    sdks_found: set[str] = set()
    manifest_candidates: list[dict] = []
    audio_compression = collections.Counter()

    with zipfile.ZipFile(apk_path, "r") as zf:
        infos = zf.infolist()
        all_names = {i.filename for i in infos}
        total_uncomp = 0
        total_comp = 0

        for info in infos:
            if info.is_dir():
                continue
            name = info.filename
            sz = info.file_size
            total_uncomp += sz
            total_comp += info.compress_size

            parts = name.split("/")
            t1 = parts[0] if len(parts) > 1 else "(root)"
            t2 = "/".join(parts[:2]) if len(parts) > 2 else t1
            t3 = "/".join(parts[:3]) if len(parts) > 3 else t2
            dir2[t2][0] += 1
            dir2[t2][1] += sz
            dir3[t3][0] += 1
            dir3[t3][1] += sz

            ext = Path(name).suffix.lower() or "(noext)"
            exts[ext][0] += 1
            exts[ext][1] += sz

            if ext in (".ogg", ".mp3", ".wav", ".m4a", ".fsb", ".bnk"):
                audio_compression["STORED" if info.compress_type == zipfile.ZIP_STORED else "DEFLATED"] += 1

            if name.startswith("lib/") and len(parts) >= 3:
                so = parts[-1]
                so_names.add(so)
                abis[parts[1]].append({"name": so, "size": sz})
                for sig, pname in PACKER_SIGNATURES.items():
                    if sig.decode("ascii", "ignore").lower() in so.lower():
                        packers_found[pname].append(name)

            if name.endswith(".dex") and "/" not in name:
                dex_files.append({"name": name, "size": sz})
                data = zf.read(info)
                for sig, pname in PACKER_SIGNATURES.items():
                    if sig in data:
                        packers_found[pname].append(name)
                for sig in SDK_SIGNATURES:
                    if sig in data:
                        sdks_found.add(sig.decode("ascii", "ignore"))

            if name.startswith("assets/"):
                grp = f"{t2}|{ext}"
                if magic_by_group[grp].total() < 30 or ext in (".unity3d", ".ab", ".bundle", ".jsc", ".lua", ".luac", ".dll"):
                    with zf.open(info) as f:
                        head = f.read(128)
                    mc = classify_magic(head)
                    if magic_by_group[grp].total() < 30:
                        magic_by_group[grp][mc] += 1
                    if "UnityFS" in mc:
                        unityfs_prefix_counts[mc] += 1
                    if grp not in samples:
                        with zf.open(info) as f:
                            chunk64 = f.read(65536)
                        samples[grp] = {
                            "sample_path": name,
                            "size": sz,
                            "magic": mc,
                            "head_hex": head[:32].hex(),
                            "entropy_64k": round(shannon_entropy(chunk64), 3),
                        }

                if re.search(r"(manifest|listsetting|filelist|file_list|reslist|assetdatabase|version\.json|project\.manifest)", name, re.I) and not name.endswith(".unity3d.manifest"):
                    manifest_candidates.append({"path": name, "size": sz})

        # Check global-metadata.dat
        meta_info = None
        meta_cand = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
        if meta_cand in all_names:
            zi = zf.getinfo(meta_cand)
            with zf.open(zi) as f:
                buf = f.read(65536)
            std = buf[:4] == b"\xaf\x1b\xb1\xfa"
            meta_info = {
                "path": meta_cand,
                "size": zi.file_size,
                "standard_magic": std,
                "metadata_version": struct.unpack_from("<I", buf, 4)[0] if std and len(buf) >= 8 else None,
                "magic_hex": buf[:16].hex(),
                "entropy_64k": round(shannon_entropy(buf), 3),
            }
            if std:
                full_meta = zf.read(zi)
                meta_info["hybridclr_hint"] = b"LoadMetadataForAOTAssembly" in full_meta or b"HybridCLR" in full_meta

        unity_ver = detect_unity_version(zf, all_names)
        engines = detect_engine(all_names, so_names, size)
        if meta_info and meta_info.get("hybridclr_hint"):
            engines.append("HybridCLR-Detected")

        # Auto-diff Unity master manifest if present
        manifest_diffs = []
        for mc in manifest_candidates:
            p = mc["path"]
            if p.endswith(".manifest") and mc["size"] < 50 * 1024 * 1024:
                txt = zf.read(p).decode("utf-8", "replace")
                listed = re.findall(r"^\s*Name:\s*(.+?)\s*$", txt, re.M)
                if listed:
                    parent = str(Path(p).parent).replace("\\", "/")
                    present = sum(1 for item in listed if f"{parent}/{item}" in all_names)
                    manifest_diffs.append({
                        "manifest": p,
                        "listed": len(listed),
                        "present": present,
                        "missing": len(listed) - present,
                    })

    zip32_warning = len(infos) > 55000 or total_uncomp > int(3.5 * 1024**3)
    report = {
        "apk_path": str(apk_path),
        "apk_size_bytes": size,
        "apk_sha256": sha256,
        "total_entries": len(infos),
        "total_uncompressed_bytes": total_uncomp,
        "zip32_pressure_warning": zip32_warning,
        "engines_detected": engines,
        "unity_version": unity_ver,
        "abis": sorted(abis.keys()),
        "only_32bit_warning": ("armeabi-v7a" in abis and "arm64-v8a" not in abis),
        "native_libs_by_abi": {k: sorted(v, key=lambda x: x["name"]) for k, v in sorted(abis.items())},
        "dex_files": sorted(dex_files, key=lambda x: x["name"]),
        "packers_detected": {k: sorted(set(v)) for k, v in packers_found.items()},
        "sdk_clues": sorted(sdks_found),
        "global_metadata": meta_info,
        "unityfs_prefix_census": dict(unityfs_prefix_counts),
        "audio_compression": dict(audio_compression),
        "manifest_candidates": manifest_candidates[:50],
        "manifest_diffs": manifest_diffs,
        "dir2_top": {k: {"count": v[0], "bytes": v[1]} for k, v in sorted(dir2.items(), key=lambda kv: -kv[1][1])[:30]},
        "dir3_top": {k: {"count": v[0], "bytes": v[1]} for k, v in sorted(dir3.items(), key=lambda kv: -kv[1][1])[:40]},
        "extensions_top": {k: {"count": v[0], "bytes": v[1]} for k, v in sorted(exts.items(), key=lambda kv: -kv[1][1])[:30]},
        "asset_magic_groups": {k: {"counts": dict(v), "sample": samples.get(k)} for k, v in sorted(magic_by_group.items())},
    }

    out_json = out_dir / "apk-inventory-summary.json"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"APK: {apk_path.name} ({size/1024/1024:.1f} MiB, {len(infos):,} entries) SHA256={sha256[:16]}...")
    if zip32_warning:
        print("  [WARNING] Approaching/exceeding ZIP32 limits (65535 entries or 4 GiB): consider external expansion or single ZIP_STORED self-extract!")
    print(f"Engines: {engines} | Unity: {unity_ver} | ABIs: {report['abis']} | 32-bit-only: {report['only_32bit_warning']}")
    print(f"Packers: {report['packers_detected'] or 'NONE'} | SDK clues: {report['sdk_clues']}")
    print(f"global-metadata: {meta_info}")
    print(f"UnityFS census: {dict(unityfs_prefix_counts)}")
    print(f"Audio zip mode: {dict(audio_compression)}")
    if manifest_diffs:
        print(f"Manifest diffs: {manifest_diffs}")
    print(f"Saved full inventory to: {out_json}")


if __name__ == "__main__":
    main()
