#!/usr/bin/env python3
"""Universal QA Log Oracle: aggregates logcat and local server logs into a ranked bug report.
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Usage:
    python -B qa_oracle.py --logcat evidence/logcat.txt --server-log evidence/replay.log --out evidence/oracle.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

LOGCAT_RULES: list[tuple[str, re.Pattern]] = [
    ("FATAL_CRASH", re.compile(r"(FATAL EXCEPTION|SIGSEGV|SIGABRT|tombstone|Process .* has died)", re.I)),
    ("ANR", re.compile(r"(ANR in |Application Not Responding)", re.I)),
    ("UNITY_EXCEPTION", re.compile(r"(NullReferenceException|MissingReferenceException|IndexOutOfRangeException|KeyNotFoundException|InvalidOperationException|FormatException|read code error|CRC Mismatch)", re.I)),
    ("LUA_ERROR", re.compile(r"(LUA_ERROR|LUA ERROR|attempt to index|attempt to call|stack traceback:)", re.I)),
    ("JS_ERROR", re.compile(r"(Uncaught TypeError|ReferenceError|Cannot read propert|JS:.*Error)", re.I)),
    ("ASSET_ERROR", re.compile(r"(Unable to open archive file|Failed to decompress|AssetBundle .* failed|file not found)", re.I)),
]

SERVER_RULES: list[tuple[str, re.Pattern]] = [
    ("UNSUPPORTED_PROTO", re.compile(r"(unsupported (?:local )?protocol|unhandled (?:opcode|route|cmd)|unknown (?:opcode|route|cmd))[:\s]+([A-Za-z0-9_./-]+)", re.I)),
    ("REJECTED_PROTO", re.compile(r"(?:rejected|deny|denied).*?(?:proto|opcode|cmd|route)?[:\s]*([A-Za-z0-9_./-]*)", re.I)),
    ("EMPTY_REPLY", re.compile(r"(synthesized empty reply|no replay data|empty response).*?([A-Za-z0-9_./-]*)", re.I)),
    ("SERVER_TRACEBACK", re.compile(r"(Traceback \(most recent call last\)|gateway conn error|sqlite3\.\w+Error|Unhandled exception)", re.I)),
]

PROTO_EXTRACT = re.compile(r"(?:protocol|opcode|cmd|route|op)\s*[:=#]?\s*([A-Za-z0-9_./-]{2,64})", re.I)


def scan_file(path: Path, rules: list[tuple[str, re.Pattern]], source: str, findings: dict, proto_hits: collections.Counter) -> int:
    if not path or not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        for cat, pat in rules:
            m = pat.search(line)
            if m:
                bucket = findings[cat]
                bucket["count"] += 1
                if len(bucket["samples"]) < 15:
                    bucket["samples"].append({"source": source, "line": lineno, "text": line[:240]})
                pm = PROTO_EXTRACT.search(line)
                if pm:
                    proto_hits[f"{cat}:{pm.group(1)}"] += 1
                elif m.lastindex and m.lastindex >= 2 and m.group(2):
                    proto_hits[f"{cat}:{m.group(2)}"] += 1
                break
    return len(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Aggregate logcat and server logs into structured QA oracle report")
    ap.add_argument("--logcat", type=Path, help="Path to captured logcat text file")
    ap.add_argument("--server-log", type=Path, help="Path to local offline server log file")
    ap.add_argument("--out", type=Path, help="Optional output JSON report path")
    args = ap.parse_args()

    if not args.logcat and not args.server_log:
        ap.error("Provide at least one of --logcat or --server-log")

    findings: dict[str, dict] = collections.defaultdict(lambda: {"count": 0, "samples": []})
    proto_hits: collections.Counter = collections.Counter()

    logcat_lines = scan_file(args.logcat, LOGCAT_RULES, "logcat", findings, proto_hits) if args.logcat else 0
    server_lines = scan_file(args.server_log, SERVER_RULES, "server", findings, proto_hits) if args.server_log else 0

    total_issues = sum(v["count"] for v in findings.values())
    report = {
        "passed": total_issues == 0,
        "issues_total": total_issues,
        "scanned_lines": {"logcat": logcat_lines, "server": server_lines},
        "by_category": {k: v["count"] for k, v in sorted(findings.items(), key=lambda kv: -kv[1]["count"])},
        "top_protocol_issues": [{"key": k, "count": c} for k, c in proto_hits.most_common(30)],
        "details": dict(findings),
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "passed": report["passed"],
        "issues_total": total_issues,
        "scanned_lines": report["scanned_lines"],
        "by_category": report["by_category"],
        "top_protocol_issues": report["top_protocol_issues"][:15],
    }, ensure_ascii=False, indent=2))
    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()
