<div align="center">

# 🎮 Offline Game Revival

### An AI agent skill that brings shut-down mobile games back to life — fully offline, on a real phone.

**When the servers die, the game shouldn't.**

[English](README.md) · [简体中文](docs/README.zh-CN.md) · [繁體中文](docs/README.zh-TW.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Español](docs/README.es.md) · [Português](docs/README.pt-BR.md) · [Français](docs/README.fr.md) · [Deutsch](docs/README.de.md) · [Русский](docs/README.ru.md) · [Tiếng Việt](docs/README.vi.md) · [Bahasa Indonesia](docs/README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

Every year, hundreds of mobile games shut down. The APK still sits on players' phones — but without the server it can't log in, can't load a save, can't do anything. Years of stories, characters and memories become unreachable.

**Offline Game Revival** is a battle-tested playbook packaged as an [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Point your coding agent (Claude Code and other agents that read `SKILL.md`) at a dead game's APK, and it knows how to turn it into a **standalone memorial edition**: install the APK, play the whole game, no network, no root, no PC, no runtime injection.

## ✨ What's inside

| | |
|---|---|
| 🔍 **Recon** | Unpack the APK, find the real logic layer (Lua / JS / C# transpiled), identify encryption and resource-integrity checks. |
| 🧩 **Anchor-asserted patching** | One build entry point. Every code replacement asserts its anchor — if the upstream package changes, the build *fails loudly* instead of shipping a silently broken patch. |
| 🖥️ **Local fake server** | Intercept the HTTP/JSON layer and answer hundreds of endpoints from a local save. A methodology for mapping every endpoint's caller and what it reads, then generating safe defaults. |
| 📦 **Repack & re-sign** | Recompute engine cache checksums, rebuild resource tables, zipalign, sign. Includes a reverse-engineered cache-checksum algorithm and loader patches for LayaAir native. |
| ✅ **On-device acceptance** | "The screen opens" ≠ "it works". State must actually change and survive a cold restart. Tutorial-driven testing: follow the game's own guide steps with real taps. |
| 🎞️ **Data rescue from screenshots & recordings** *(new)* | Server-side numbers (shop prices, gacha rates, rewards, card stats) die with the server. `scripts/harvest.py` turns **tens of GB of player screenshots and screen recordings** into a few hundred KB of categorized text — keyframes → near-duplicate removal → local OCR → per-screen grouping — **fully offline, zero tokens**, ready for any cheap text LLM to structure. |
| 📚 **Failure ledger** | 80 KB of real pitfalls: symptom → root cause → fix. Crashes from start-up races, UI that silently moved off-screen, pooled XHR objects "poisoned" by fake responses, saves that never hit disk… |

## 🏆 Proven on real games

The playbook was distilled from reviving two commercial mobile games whose servers shut down:

- **Case A — Unity + Lua**: full single-player memorial build, verified on a physical Android 14 phone.
- **Case B — LayaAir native + JavaScript**: 315 server endpoints reimplemented locally, 700+ regression assertions, all major systems (story chapters, battles, gacha, pets, dating, tower, events) clicked through on a device, plus offline license codes (Ed25519, no BigInt) and per-copy watermarks for private sharing.

Both case studies are included (anonymized) in [`references/`](skills/offline-game-revival/references).

## 🚀 Install

**Claude Code (plugin marketplace)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Any agent that reads `SKILL.md`** — copy the folder into your agent's skills directory, e.g. for Claude Code:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/
```

Then just ask: *"This game's servers shut down — make it playable offline"* or *"Extract the shop prices and gacha rates from these 15 GB of screen recordings."*

## 🎞️ Rescue data from screen recordings (standalone)

The harvester works without any agent:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
```

- **Keyframes that matter**: keeps a frame only when the screen *changed and settled* — skips transition animations and motion blur; long scrolling lists still get sampled.
- **Cross-source dedupe**: the same screen from a screenshot and from a recording is merged (status bar ignored).
- **Local OCR** (RapidOCR / ONNX, CPU-only, CJK + Latin) with boxes and reading order.
- **Output**: `for_llm/*.txt` chunks + a ready-made prompt and JSON schema in [`media-harvest.md`](skills/offline-game-revival/references/media-harvest.md).

## 🧭 Philosophy

1. **Patch at build time, not at runtime.** A Frida script that "works" still needs to be injected forever. Changes baked into the package install and just work.
2. **Single entry point + anchor assertions.** Silent skips ship broken builds.
3. **Artifacts are not source.** Fix the patch script, never hand-edit the output.
4. **"It opens" is not "it works."** Verify state changes, survive restarts, write down what's verified vs. merely implemented.

## ⚖️ Responsible use

This project is about **game preservation**: keeping games playable **after their official service has ended**.

- Only use it on games whose official servers are **permanently shut down**. Never on live games, never to cheat, bypass anti-cheat, or affect other players.
- The repository contains **no game assets, no game code, no keys** — only methods and the author's own tooling.
- Respect copyright: keep memorial builds private / non-commercial, and follow the laws of your jurisdiction. If a rights holder relaunches the game, support the official version.

## 🤝 Contributing

Revived a game with this skill? Hit a new pitfall? Issues and PRs with **new engine case studies** (Cocos, Unreal, Godot, IL2CPP…) and **new entries for the failure ledger** are very welcome.

If this saved a game you loved, a ⭐ helps other players find it.

## 📄 License

[MIT](LICENSE)

<sub>Keywords: game preservation · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · 停服游戏 · 单机化 · 离线版 · 游戏保存 · 録画OCR · サービス終了 · 서비스 종료</sub>
