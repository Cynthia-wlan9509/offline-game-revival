#!/usr/bin/env python3
"""clone_chart.py — keep this repo's clone history and draw it as an SVG (stdlib only).
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

GitHub only keeps 14 days of clone traffic, so a daily workflow calls this to merge the latest
14 days into a CSV and redraw the chart.

  python clone_chart.py <data_dir>                  # fetch (needs TRAFFIC_TOKEN + GITHUB_REPOSITORY), merge, draw
  python clone_chart.py <data_dir> --json f.json    # merge a saved API response instead of fetching
  python clone_chart.py <data_dir> --draw-only

data_dir gets clones.csv (date,count,uniques) and clones.svg. An optional baseline.json
({"date": "YYYY-MM-DD", "count": N, "uniques": M}) adds a 14-day total recorded before daily tracking began.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path


def fetch(repo: str, token: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/traffic/clones?per=day",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "clone-chart"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load(csv_path: Path) -> dict[str, tuple[int, int]]:
    rows: dict[str, tuple[int, int]] = {}
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rows[r["date"]] = (int(r["count"]), int(r["uniques"]))
    return rows


def merge(rows: dict[str, tuple[int, int]], api: dict) -> int:
    n = 0
    for c in api.get("clones", []):
        day = c["timestamp"][:10]
        new = (int(c["count"]), int(c["uniques"]))
        old = rows.get(day)
        # A day already recorded only ever grows (today's numbers are partial); never shrink history.
        if old is None or new[0] >= old[0]:
            if old != new:
                n += 1
            rows[day] = new
    return n


def save(csv_path: Path, rows: dict[str, tuple[int, int]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("date,count,uniques\n")
        for d in sorted(rows):
            f.write(f"{d},{rows[d][0]},{rows[d][1]}\n")


def nice_max(v: float) -> float:
    if v <= 0:
        return 1
    mag = 10 ** (len(str(int(v))) - 1)
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * mag:
            return m * mag
    return 10 * mag


def draw(rows: dict[str, tuple[int, int]], repo: str, base: dict | None = None) -> str:
    W, H, L, R, T, B = 800, 400, 64, 64, 64, 48
    days = sorted(rows)
    if not days:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"></svg>'
    start, end = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
    base_n, gap = 0, False
    if base and base["date"] < days[0]:
        base_n = int(base["count"])
        gap = (start - dt.date.fromisoformat(base["date"])).days > 1
        start = dt.date.fromisoformat(base["date"])
    span = max((end - start).days, 1)
    cum, total = [], base_n
    for d in days:
        total += rows[d][0]
        cum.append(total)
    daily_max = nice_max(max(rows[d][0] for d in days))
    cum_max = nice_max(total)
    pw, ph = W - L - R, H - T - B

    def x(d: str) -> float:
        return L + pw * (dt.date.fromisoformat(d) - start).days / span

    green, soft, ink, grid, mute = "#3f8f6b", "#cfe8da", "#2f3d36", "#e6efe9", "#7c8f85"
    bw = max(2.0, min(14.0, pw / (span + 1) * 0.7))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
         f'<rect width="{W}" height="{H}" rx="10" fill="#fbfdfb"/>',
         f'<text x="{L}" y="34" font-size="18" font-weight="600" fill="{ink}">Clone history</text>',
         f'<text x="{W - R}" y="34" font-size="13" text-anchor="end" fill="{mute}">{repo}</text>']
    for i in range(6):
        gy = T + ph * i / 5
        o.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{W - R}" y2="{gy:.1f}" stroke="{grid}"/>')
        o.append(f'<text x="{L - 8}" y="{gy + 4:.1f}" font-size="11" text-anchor="end" fill="{mute}">{daily_max * (5 - i) / 5:g}</text>')
        o.append(f'<text x="{W - R + 8}" y="{gy + 4:.1f}" font-size="11" fill="{green}">{cum_max * (5 - i) / 5:g}</text>')
    for d in days:
        h = ph * rows[d][0] / daily_max
        o.append(f'<rect x="{x(d) - bw / 2:.1f}" y="{T + ph - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1.5" fill="{soft}"/>')
    def y(c: int) -> float:
        return T + ph - ph * c / cum_max

    if base_n:
        bx = x(base["date"])
        o.append(f'<circle cx="{bx:.1f}" cy="{y(base_n):.1f}" r="4" fill="{green}"/>')
        o.append(f'<text x="{bx + 8:.1f}" y="{y(base_n) - 8:.1f}" font-size="11" fill="{green}">{base_n} clones in the 14 days to {base["date"][5:]}</text>')
        dash = ' stroke-dasharray="5 5"' if gap else ""
        o.append(f'<line x1="{bx:.1f}" y1="{y(base_n):.1f}" x2="{x(days[0]):.1f}" y2="{y(cum[0]):.1f}" stroke="{green}" stroke-width="2"{dash}/>')
        if gap:
            mid = (bx + x(days[0])) / 2
            o.append(f'<text x="{mid:.1f}" y="{T + ph - 8:.1f}" font-size="10" text-anchor="middle" fill="{mute}">days not recorded</text>')
    pts = " ".join(f"{x(d):.1f},{y(c):.1f}" for d, c in zip(days, cum))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{green}" stroke-width="2.5" stroke-linejoin="round"/>')
    ticks = 6
    for i in range(ticks + 1):
        d = start + dt.timedelta(days=round(span * i / ticks))
        tx = L + pw * (d - start).days / span
        o.append(f'<text x="{tx:.1f}" y="{H - B + 20}" font-size="11" text-anchor="middle" fill="{mute}">{d:%b %d}</text>')
    o.append(f'<rect x="{L}" y="{H - 18}" width="10" height="10" rx="2" fill="{soft}"/>'
             f'<text x="{L + 15}" y="{H - 9}" font-size="11" fill="{mute}">clones per day (left)</text>'
             f'<rect x="{L + 160}" y="{H - 14}" width="14" height="3" fill="{green}"/>'
             f'<text x="{L + 180}" y="{H - 9}" font-size="11" fill="{mute}">total clones (right): {"≥ " if gap else ""}{total}</text>'
             f'<text x="{W - R}" y="{H - 9}" font-size="11" text-anchor="end" fill="{mute}">since {start:%Y-%m-%d} · updated {end:%Y-%m-%d}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    repo = os.environ.get("GITHUB_REPOSITORY", "Cynthia-wlan9509/offline-game-revival")
    rows = load(out / "clones.csv")
    bp = out / "baseline.json"
    base = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else None
    if "--draw-only" not in sys.argv:
        if "--json" in sys.argv:
            api = json.loads(Path(sys.argv[sys.argv.index("--json") + 1]).read_text(encoding="utf-8"))
        else:
            token = os.environ.get("TRAFFIC_TOKEN", "")
            if not token:
                print("TRAFFIC_TOKEN is not set; skipping (see .github/workflows/clone-stats.yml).")
                return 0
            api = fetch(repo, token)
        print(f"merged {merge(rows, api)} changed days")
        save(out / "clones.csv", rows)
    (out / "clones.svg").write_text(draw(rows, repo, base), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
