<div align="center">

# 🎮 Offline Game Revival

### Ein KI-Agenten-Skill, der abgeschaltete Mobile Games wieder zum Leben erweckt – komplett offline, auf einem echten Smartphone.

**Wenn die Server sterben, muss das Spiel nicht mitsterben.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

Jedes Jahr werden Hunderte Mobile Games eingestellt. Die APK liegt weiter auf den Handys der Spieler – doch ohne Server lässt sich niemand mehr einloggen, kein Spielstand laden, nichts mehr tun. Jahre voller Geschichten, Charaktere und Erinnerungen sind plötzlich außer Reichweite.

**Offline Game Revival** ist ein praxiserprobtes Playbook, verpackt als [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Richte deinen Coding-Agenten (Claude Code und andere Agenten, die `SKILL.md` lesen) auf die APK eines toten Spiels, und er weiß, wie man daraus eine **eigenständige Gedenkausgabe** macht: APK installieren, das ganze Spiel durchspielen – ohne Netzwerk, ohne Root, ohne PC, ohne Laufzeit-Injection.

## ✨ Was drinsteckt

| | |
|---|---|
| 🔍 **Recon** | Entpackt die APK, findet die eigentliche Logikschicht (Lua / JS / transpiliertes C#) und identifiziert Verschlüsselung sowie Integritätsprüfungen für Ressourcen. |
| 🧩 **Patching mit geprüften Ankern** | Ein einziger Build-Einstiegspunkt. Jede Code-Ersetzung prüft ihren Anker – ändert sich das Original-Paket, *scheitert der Build laut und deutlich*, statt stillschweigend einen kaputten Patch auszuliefern. |
| 🖥️ **Lokaler Fake-Server** | Fängt die HTTP/JSON-Schicht ab und beantwortet Hunderte Endpunkte aus einem lokalen Spielstand. Dazu eine Methodik, um für jeden Endpunkt zu ermitteln, wer ihn aufruft und was er liest, und daraus sichere Standardwerte zu erzeugen. |
| 📦 **Repack & Neu-Signierung** | Berechnet Cache-Prüfsummen der Engine neu, baut Ressourcentabellen um, führt zipalign aus und signiert. Enthält einen per Reverse Engineering rekonstruierten Cache-Prüfsummen-Algorithmus und Loader-Patches für LayaAir native. |
| ✅ **Abnahme auf dem Gerät** | „Der Bildschirm öffnet sich" ≠ „es funktioniert". Der Zustand muss sich tatsächlich ändern und einen Kaltstart überleben. Tutorial-gesteuertes Testen: den Schritten der spieleigenen Anleitung mit echten Taps folgen. |
| 🎞️ **Datenrettung aus Screenshots & Aufnahmen** *(neu)* | Serverseitige Zahlen (Shop-Preise, Gacha-Raten, Belohnungen, Kartenwerte) sterben mit dem Server. `scripts/harvest.py` verwandelt **dutzende GB an Spieler-Screenshots und Bildschirmaufnahmen** in wenige hundert KB kategorisierten Text – Keyframes → Entfernen von Beinahe-Duplikaten → lokales OCR → Gruppierung pro Screen –, **komplett offline, null Token**, bereit für jedes günstige Text-LLM zur Strukturierung. |
| 📚 **Fehler-Logbuch** | 80 KB echter Stolperfallen: Symptom → Ursache → Lösung. Abstürze durch Race Conditions beim Start, UI, die unbemerkt aus dem Bild gerutscht ist, gepoolte XHR-Objekte, die von Fake-Antworten „vergiftet" wurden, Spielstände, die nie auf der Platte landen … |

## 🏆 An echten Spielen bewährt

Das Playbook entstand aus der Wiederbelebung zweier kommerzieller Mobile Games, deren Server abgeschaltet wurden:

- **Fall A – Unity + Lua**: vollständige Singleplayer-Gedenkversion, verifiziert auf einem physischen Android-14-Smartphone.
- **Fall B – LayaAir native + JavaScript**: 315 Server-Endpunkte lokal nachgebaut, über 700 Regressions-Assertions, alle wichtigen Systeme (Story-Kapitel, Kämpfe, Gacha, Haustiere, Dating, Turm, Events) auf einem Gerät durchgeklickt – dazu Offline-Lizenzcodes (Ed25519, ohne BigInt) und kopiespezifische Wasserzeichen für die private Weitergabe.

Beide Fallstudien (anonymisiert) liegen in [`references/`](../skills/offline-game-revival/references).

## 🚀 Installation

**Claude Code (Plugin-Marketplace)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Jeder Agent, der `SKILL.md` liest** – kopiere den Ordner in das Skills-Verzeichnis deines Agenten, z. B. für Claude Code:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/
```

Dann einfach fragen: *„Die Server dieses Spiels wurden abgeschaltet – mach es offline spielbar"* oder *„Zieh die Shop-Preise und Gacha-Raten aus diesen 15 GB Bildschirmaufnahmen."*

## 🎞️ Daten aus Bildschirmaufnahmen retten (eigenständig)

Der Harvester funktioniert ganz ohne Agent:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
```

- **Keyframes, die zählen**: Ein Frame bleibt nur erhalten, wenn sich der Bildschirm *verändert und beruhigt* hat – Übergangsanimationen und Bewegungsunschärfe werden übersprungen; lange Scroll-Listen werden trotzdem abgetastet.
- **Deduplizierung über Quellen hinweg**: Derselbe Screen aus einem Screenshot und aus einer Aufnahme wird zusammengeführt (Statusleiste wird ignoriert).
- **Lokales OCR** (RapidOCR / ONNX, nur CPU, CJK + Latein) mit Bounding Boxes und Lesereihenfolge.
- **Ausgabe**: `for_llm/*.txt`-Chunks plus ein fertiger Prompt und ein JSON-Schema in [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md).

## 🧭 Philosophie

1. **Zur Build-Zeit patchen, nicht zur Laufzeit.** Ein Frida-Skript, das „funktioniert", muss für immer injiziert werden. Änderungen, die ins Paket eingebrannt sind, werden installiert und laufen einfach.
2. **Ein Einstiegspunkt + Anker-Assertions.** Stillschweigend übersprungene Ersetzungen führen zu kaputten Builds.
3. **Artefakte sind kein Quellcode.** Repariere das Patch-Skript, bearbeite niemals die Ausgabe von Hand.
4. **„Es öffnet sich" heißt nicht „es funktioniert".** Zustandsänderungen und Neustarts verifizieren und festhalten, was geprüft und was nur implementiert ist.

## ⚖️ Verantwortungsvolle Nutzung

Dieses Projekt dient der **Spielebewahrung**: Spiele spielbar halten, **nachdem der offizielle Betrieb beendet wurde**.

- Nutze es nur bei Spielen, deren offizielle Server **dauerhaft abgeschaltet** sind. Niemals bei laufenden Spielen, nie zum Cheaten, zum Umgehen von Anti-Cheat oder um andere Spieler zu beeinträchtigen.
- Das Repository enthält **keine Spiel-Assets, keinen Spielcode, keine Schlüssel** – nur Methoden und die eigenen Werkzeuge des Autors.
- Respektiere das Urheberrecht: Halte Gedenkversionen privat und nicht kommerziell und beachte die Gesetze deines Landes. Bringt ein Rechteinhaber das Spiel neu heraus, unterstütze die offizielle Version.

## 🤝 Mitmachen

Hast du mit diesem Skill ein Spiel wiederbelebt? Bist du in eine neue Falle getappt? Issues und PRs mit **neuen Engine-Fallstudien** (Cocos, Unreal, Godot, IL2CPP …) und **neuen Einträgen fürs Fehler-Logbuch** sind sehr willkommen.

Wenn dieses Projekt ein Spiel gerettet hat, das du geliebt hast, hilft ein ⭐ anderen Spielern, es zu finden.

## 📄 Lizenz

[MIT](../LICENSE)

<sub>Keywords: game preservation · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · Spiel eingestellt · Server abgeschaltet · Offline spielen · Spielebewahrung · Mobile Game ohne Server · Serverabschaltung</sub>
