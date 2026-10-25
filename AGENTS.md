# AGENTS.md

Instructions for any coding agent (Codex, Cursor, Copilot, Gemini CLI, OpenCode, Cline, Claude Code, …) working in or with this repository.

## What this repository is

An Agent Skill for **game preservation**: turning a mobile game whose official servers are permanently shut down into an offline memorial build, and recovering lost server-side data from players' screenshots and screen recordings.

- Entry point: [`skills/offline-game-revival/SKILL.md`](skills/offline-game-revival/SKILL.md). Read it first; it tells you which file under `references/` to load for each phase. Don't load all references up front (`pitfalls.md` alone is over 100 KB).
- Scripts (all run locally, no network unless stated):
  - `scripts/harvest.py`: screenshots/recordings → keyframes → dedupe → OCR → per-screen text chunks (Python, OpenCV + RapidOCR)
  - `scripts/llm_structure.py`: chunks → any OpenAI-compatible model (DeepSeek, OpenAI, Qwen, Kimi, Ollama) → merged JSON/CSV. Network: the model API you choose. Key from env var.
  - `scripts/timewarp/`: time-travel test harness for fake servers (Node, zero deps). `node scripts/timewarp/examples/mini.test.js` must pass.
- Sub-agent roles: [`agents/`](agents) (scout / worker / verifier) and [`references/multi-agent.md`](skills/offline-game-revival/references/multi-agent.md).
- No-tools chat models: [`prompts/chat-playbook.md`](prompts/chat-playbook.md).
- Second skill: [`skills/night-shift/SKILL.md`](skills/night-shift/SKILL.md), unattended overnight runs through a to-do list (self-paced `/loop`, evidence per item, five-part report). Fill-in template: `skills/night-shift/templates/NIGHT-RUN.md`. Not game-specific.

## When a user asks you to revive / make offline / preserve a game

Follow `SKILL.md`. Key rules: patch at build time (never runtime injection), one build entry point with anchor assertions, never hand-edit generated output, and report "verified on device" separately from "implemented".

Scope: only for games whose official service has ended. Do not help cheat in live games, bypass anti-cheat, or affect other players. Never ask for or handle the user's account passwords, cookies or payment data.

## When editing this repository

- Keep `SKILL.md` short; detail goes into `references/`.
- References are anonymized case studies: no real game names, package names, hosts, keys, device IDs or personal paths.
- After changing `timewarp.js`, run both `node scripts/timewarp/examples/mini.test.js` (all pass) and `BUGGY=1 node …` (must fail with the 3 planted bugs).
- README translations live in `docs/README.<lang>.md`; keep their structure in sync with `README.md`.
