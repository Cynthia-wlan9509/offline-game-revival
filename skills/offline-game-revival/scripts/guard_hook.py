#!/usr/bin/env python3
"""guard_hook.py — PreToolUse hook that stops an agent from knocking over shared emulators / adb.
Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival

Several projects often share one PC: several emulators, one adb server, one LDPlayer service.
One careless command from one agent breaks everyone else's session. This hook blocks:
  - `svc wifi disable`            (LDPlayer's adb runs over wlan0, the device drops offline at once)
  - `ldconsole quitall`           (closes every emulator, including other projects')
  - `adb kill-server`             (cuts every other project's adb session)
  - taskkill / Stop-Process on Ld9BoxSVC, Ld9BoxHeadless, dnplayer, MuMuPlayer, NemuPlayer, adb.exe
and asks for confirmation when a device-changing adb command has no `-s <serial>`.

Opt-in. Nothing happens until you register it. Claude Code, in the project's `.claude/settings.json`:

    {"hooks": {"PreToolUse": [{"matcher": "Bash|PowerShell",
      "hooks": [{"type": "command", "command": "python -I <skill>/scripts/guard_hook.py"}]}]}}

Also reads the payload shape `{"toolCall": {"args": {"CommandLine": ...}}}` used by some other agents,
and answers them with `{"decision": "allow|deny|ask", "reason": ...}`.
For Claude Code it prints nothing when the command is fine, so normal permission prompts still apply.
Any parse error fails open: a broken hook must never lock up normal work.
"""
from __future__ import annotations

import json
import re
import sys

READ_ONLY = re.compile(r"^(Select-String|rg|grep|Get-Content|type|cat|echo|Write-Output|git\s+(log|diff|show|status))\b", re.I)
DENY = [
    (re.compile(r"\bsvc\s+wifi\s+disable\b", re.I),
     'never run "svc wifi disable" on an emulator: LDPlayer\'s adb runs over wlan0 and the device drops offline. '
     "Cut the network with an iptables rule for the game's UID (remove it afterwards), or remove the INTERNET permission."),
    (re.compile(r"\bldconsole(?:\.exe)?\s+quitall\b", re.I),
     '"ldconsole quitall" closes every emulator on this PC, including other projects\'. Stop only the instance in the device lock file.'),
    (re.compile(r"\badb(?:\.exe)?\s+kill-server\b", re.I),
     '"adb kill-server" cuts the adb sessions of every other project on this PC.'),
    (re.compile(r"(taskkill|Stop-Process)\b[^\r\n]*(Ld9BoxSVC|Ld9BoxHeadless|dnplayer|MuMuPlayer|NemuPlayer|adb\.exe)", re.I),
     "killing shared emulator services or adb takes down other running projects. Ask the user first."),
]
ADB_CALL = re.compile(r"""(?:^|[;&|\r\n\s])(?:"[^"]*adb(?:\.exe)?"|(?:[A-Za-z]:\\[^\s"]*|[^\s"]*[\\/])?adb(?:\.exe)?)\s+([^\r\n;&|]+)""", re.I)
ADB_HARMLESS = re.compile(r"^(devices|version|help|start-server|connect|disconnect)\b", re.I)


def decide(cmd: str) -> tuple[str, str]:
    if READ_ONLY.match(cmd.strip()):
        return "allow", ""
    for pat, why in DENY:
        if pat.search(cmd):
            return "deny", "guard_hook: " + why
    for m in ADB_CALL.finditer(cmd):
        rest = m.group(1).strip()
        if ADB_HARMLESS.match(rest):
            continue
        if not re.search(r"(^|\s)-s\s+\S+", rest):
            return "ask", 'guard_hook: this adb command has no "-s <serial>". Check it targets the device in the project lock file.'
    return "allow", ""


def main() -> None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    except Exception:
        return
    tool_input = payload.get("tool_input")
    other = payload.get("toolCall")
    if isinstance(tool_input, dict):
        cmd = str(tool_input.get("command") or "")
        verdict, reason = decide(cmd) if cmd else ("allow", "")
        if verdict != "allow":
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": verdict,
                "permissionDecisionReason": reason,
            }}))
        return
    if isinstance(other, dict):
        cmd = str(((other.get("args") or {}).get("CommandLine")) or "")
        verdict, reason = decide(cmd) if cmd else ("allow", "")
        out = {"decision": verdict}
        if reason:
            out["reason"] = reason
        print(json.dumps(out))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
