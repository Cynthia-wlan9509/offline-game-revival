<div align="center">

# 🎮 Offline Game Revival

### Ein KI-Agenten-Skill, der abgeschaltete Mobile Games wieder zum Leben erweckt – komplett offline, auf einem echten Smartphone.

**Wenn die Server sterben, muss das Spiel nicht mitsterben.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%7C%20LayaAir%20%7C%20Cocos%20%7C%20WebGL-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

Jedes Jahr werden Hunderte Mobile Games eingestellt. Die APK liegt weiter auf den Handys der Spieler – doch ohne Server lässt sich niemand mehr einloggen, kein Spielstand laden, nichts mehr tun. Jahre voller Geschichten, Charaktere und Erinnerungen sind plötzlich außer Reichweite.

**Offline Game Revival** ist ein praxiserprobtes Playbook, verpackt als [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Richte deinen Coding-Agenten (Claude Code und andere Agenten, die `SKILL.md` lesen) auf die APK eines toten Spiels, und er weiß, wie man daraus eine **eigenständige Gedenkausgabe** macht: APK installieren, das ganze Spiel durchspielen – ohne Netzwerk, ohne Root, ohne PC, ohne Laufzeit-Injection.

All das habe ich mir selbst erarbeitet. Am Anfang hatte ich von Spieleentwicklung keine Ahnung, und ich habe kein einziges Tutorial gelesen: Vom ersten Tag an habe ich der KI (Claude, DeepSeek, GPT-6 Astra) einfach Wünsche genannt und sie nachbessern lassen, wenn das Ergebnis nicht so war, wie ich es wollte. Dass sich manches mit dem deckt, was andere sagen, und manches nicht, ist also ganz normal. Die Entscheidungskriterien, der Ablauf und die Stolperfallen hier stammen alle aus meinem eigenen Ausprobieren an mehreren echten Spielen.

**Bisher: 16 abgeschaltete Spiele** auf Unity + Lua, Unity Mono / SLua, Unity IL2CPP, HybridCLR, LayaAir, Cocos (JS / Lua / LuaJIT), Unity WebGL / H5 und nativem Kotlin + Live2D – Story- und Dating-Spiele, Kartenkämpfer, ein Xianxia-Spiel, ein KI-Charakter-Chat-Spiel und mehr. Die vollständige Liste steht unter [An echten Spielen bewährt](#-an-echten-spielen-bewährt).

## ✨ Was drinsteckt

| | |
|---|---|
| 🔍 **Recon** | Entpackt die APK, findet die eigentliche Logikschicht (Lua / JS / transpiliertes C#) und identifiziert Verschlüsselung sowie Integritätsprüfungen für Ressourcen. |
| ⚡ **Schnellere Triage & härtere Recon** *(neu)* | Beantworte „Ist es zu retten?" schnell: Installiere die originale APK auf einem gerooteten Emulator, kappe das Netzwerk und starte kalt. Wird der vollständige Login-Bildschirm angezeigt, sind Spiel und Assets vorhanden, und nur die Login-Schicht steht im Weg. Bei Asset-Bundles, in denen nur ein Abschnitt verschlüsselt ist, grenzt du das verschlüsselte Fenster Block für Block genau ein. Mini-Games, deren Regeln komplett im Client liegen, laufen headless auf dem PC, sodass sich alle Level auf einmal prüfen lassen. Siehe [`recon.md`](../skills/offline-game-revival/references/recon.md) und [`playtest.md`](../skills/offline-game-revival/references/playtest.md). |
| 🧩 **Patching mit geprüften Ankern** | Ein einziger Build-Einstiegspunkt. Jede Code-Ersetzung prüft ihren Anker – ändert sich das Original-Paket, *scheitert der Build laut und deutlich*, statt stillschweigend einen kaputten Patch auszuliefern. |
| 🖥️ **Lokaler Fake-Server** | Fängt die HTTP/JSON-Schicht ab und beantwortet Hunderte Endpunkte aus einem lokalen Spielstand. Dazu eine Methodik, um für jeden Endpunkt zu ermitteln, wer ihn aufruft und was er liest, und daraus sichere Standardwerte zu erzeugen. |
| 📦 **Repack & Neu-Signierung** | Berechnet Cache-Prüfsummen der Engine neu, baut Ressourcentabellen um, führt zipalign aus und signiert. Enthält einen per Reverse Engineering rekonstruierten Cache-Prüfsummen-Algorithmus und Loader-Patches für LayaAir native. |
| ✅ **Abnahme auf dem Gerät** | „Der Bildschirm öffnet sich" ≠ „es funktioniert". Der Zustand muss sich tatsächlich ändern und einen Kaltstart überleben. Tutorial-gesteuertes Testen: den Schritten der spieleigenen Anleitung mit echten Taps folgen. |
| 🛡️ **Sichere Releases** *(neu)* | Installiere vor der Veröffentlichung die vorherige öffentliche Version, spiele einen Spielstand, aktualisiere darüber und vergleiche den Spielstand Schlüssel für Schlüssel. Wenn du auf dem eigenen Handy des Nutzers installierst, sichere zuerst den Spielstand und vergleiche ihn danach Byte für Byte. Benenne das Paket um, damit die Gedenkausgabe parallel zur offiziellen App installiert werden kann. Siehe [`verify.md`](../skills/offline-game-revival/references/verify.md) und [`patch.md`](../skills/offline-game-revival/references/patch.md) (Abschnitt 5). |
| 🎞️ **Datenrettung aus Screenshots & Aufnahmen** *(neu)* | Serverseitige Zahlen (Shop-Preise, Gacha-Raten, Belohnungen, Kartenwerte) sterben mit dem Server. `scripts/harvest.py` verwandelt **dutzende GB an Spieler-Screenshots und Bildschirmaufnahmen** in wenige hundert KB kategorisierten Text – Keyframes → Entfernen von Beinahe-Duplikaten → lokales OCR → Gruppierung pro Screen –, **komplett offline, null Token**, danach verarbeitet `scripts/llm_structure.py` alles stapelweise über DeepSeek / OpenAI / Qwen / Kimi / lokales Ollama und führt es zu JSON + CSV zusammen. |
| ⏩ **Zeitreise-Tests** *(neu)* | `scripts/timewarp` lässt deinen Fake-Server in einer Sandbox mit virtueller Uhr laufen: Tage vorspulen, die App neu starten und **jede Belohnung prüfen** – steht in der Antwort „+50 Edelsteine", der Spielstand hat sich aber nicht geändert, schlägt der Test fehl. Simuliere 30 Spieltage in einer Sekunde und sieh, an welchem Tag jede Hürde erreichbar wird. Null Abhängigkeiten. |
| 🤝 **Jeder Agent, jedes Modell** *(neu)* | Funktioniert mit Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI … über `SKILL.md` + `AGENTS.md`. Mit Sub-Agent-Rollen (scout / worker / verifier): Ein teures Modell trifft die Entscheidungen, günstige erledigen die Fleißarbeit. Gar kein Agent? Füge `prompts/chat-playbook.md` in DeepSeek / ChatGPT ein und führe die Befehle aus, die es dir gibt. |
| 🚦 **Kickoff → Batches → unabhängige QA** *(neu)* | Für große Projekte, die tagelang unbeaufsichtigt laufen: vorab ein Freigabeblatt, das zwei Minuten dauert, danach immer nur ein Batch mit harten Zeitlimits (zwei Probe-Runden oder 45 Minuten ohne Fortschritt → protokollieren und weiter) und zum Schluss eine Abnahme durch eine separate Sitzung, die dem „Alles grün“ der Entwicklungslinie nicht traut: optimistische Passes werden herabgestuft, jeder Button wird durchgeklickt, Kämpfe werden gewonnen *und* verloren und gegen das Logbuch abgeglichen, Prozess mitten in der Transaktion beenden, 10 virtuelle Tage, dann saubere Daten + leerer Hot-Update-Ordner + Netzwerk aus, zweimal kalt starten. Vorlagen für Freigabeblatt, Übergabe, Fortschrittsmatrix und Bug-Liste liegen bei. |
| 🧭 **Engine-Routen** *(neu)* | Eine Seite pro Architektur: Unity IL2CPP ohne Skriptebene (eingebetteter Python-Loopback-Server im selben Prozess), Unity Mono / ET / HybridCLR (C#-Server im Paket), Cocos JS / Lua / LuaJIT + Protobuf (Loopback im Speicher, Übernahme durch eine schlanke Activity), Unity WebGL / H5-Mikro-Clients (erst H5, Hülle zuletzt, Original-DLL als dauerhafter Kampf-Worker). |
| 🧰 **Recon- & Schutzskripte** *(neu)* | Nur Python-Standardbibliothek: einmalige, schreibgeschützte APK-Recon (Engine, ABI, ZIP32-Grenzen, Packer, UnityFS-Präfixe, Manifest-Diff), eine Ein-Geräte-Sperre mit sicherem Push bei Nicht-ASCII-Pfaden, eine Speicherplatz-Sicherung, die Junctions nicht folgt, ein Log-Orakel, `INTERNET` entfernen ohne apktool, ein APK-Eintrags-Ersetzer, der gespeicherte Audiodateien unkomprimiert lässt, und ein optionaler Hook, der `adb kill-server`, `svc wifi disable` und andere Befehle blockiert, die die Emulatoren anderer Projekte stören. |
| 📚 **Fehler-Logbuch** | Rund 230 KB und knapp 300 Einträge echter Stolperfallen: Symptom → Ursache → Lösung. Abstürze durch Race Conditions beim Start, UI, die unbemerkt aus dem Bild gerutscht ist, gepoolte XHR-Objekte, die von Fake-Antworten „vergiftet" wurden, Spielstände, die nie auf der Platte landen … |

## 🏆 An echten Spielen bewährt

Das Playbook entstand aus der Wiederbelebung von 16 kommerziellen Mobile Games, deren Server abgeschaltet wurden:

- **Fall A – Unity + Lua**: vollständige Singleplayer-Gedenkversion, verifiziert auf einem physischen Android-14-Smartphone.
- **Fall B – LayaAir native + JavaScript**: 315 Server-Endpunkte lokal nachgebaut, über 700 Regressions-Assertions, alle wichtigen Systeme (Story-Kapitel, Kämpfe, Gacha, Haustiere, Dating, Turm, Events) auf einem Gerät durchgeklickt.
- **Fall C – Unity-Microclient (Mono + SLua)**: Die APK enthielt nur etwa ein Viertel der Ressourcen des Spiels; der Rest kam aus dem Handy-Backup eines Spielers. Halb verschlüsselte Mono-Assemblies, ein Packer und ein lokaler Server, komplett in Lua geschrieben.
- **Fall D – natives Kotlin + Live2D, KI-Charakterchat**: Die Kernfunktion, der Chat mit den Figuren, lief über ein LLM auf dem Server des Publishers. Jetzt geht der Chat an die eigene OpenAI-kompatible API des Spielers oder an ein lokales Modell; Charakterkarten und Beispielsätze aus dem Originalskript halten die Figuren in ihrer Rolle. Ohne Modell antworten sie mit ihren originalen vertonten Zeilen.
- **Fall G – LayaAir + Langzeitverbindung mit sproto-Protokoll**: Das ganze Spiel steckte in der APK, die Arbeit lag also auf der Serverseite: Das Paket brachte sein eigenes Protokollschema mit (400+ Requests), die Systeme wurden lokal eines nach dem anderen nachgebaut, mit einem Autoplay-Skript, das den Spielanleitungen mit echten Taps folgt, um das nächste fehlende System zu finden. Das meiste, was es gelehrt hat, steht im Fehler-Logbuch: leere Standardantworten, die Funktionen stillschweigend sperren, abgelehnte Claims, die Spielern einen sinnlosen Fehler zeigen, und falsche „virtuelle Spieler", die kaputt aussehen.
- **Fall H – Unity-IL2CPP-Kartenspiel, keine Skriptebene**: Eine im eigenen Prozess des Spiels eingebettete Python-Laufzeit dient als lokaler Server, mit SQLite-Spielständen und einer GM-Webseite. Alle 847 Protokolle, 18 Systeme und 133 Events sind fertig, dazu 120 KI-Spieler, die das Gefühl eines „Live-Servers“ erhalten.
- **Fall I – Unity-WebGL-/H5-Mikroclient** (ein APK mit 237 KB, Xianxia): Erst H5, ganz zuletzt der Wrapper. Die originale `Hotfix.dll` läuft als dauerhafter Kampf-Worker, daher lässt sich die ganze Hauptgeschichte (990/990) samt allen 9 Tribulationen durchspielen, ohne eine einzige Formel zu ändern.
- **Fall J – Unity Mono / ET Hotfix** (`code.unity3d` + `Hotfix.dll`): Ein C#-Server im Paket; die Antworten kommen einen Frame später zurück, damit sich die Oberfläche nicht selbst blockiert.
- **Fall K – Unity 2021 IL2CPP + HybridCLR**: Alle 15,550 Bundles trugen einen doppelten 22-Byte-Header – ein Präfix, keine Verschlüsselung. Echte Hot-Update-DLLs ließen sich von gestrippten AOT-Metadaten-DLLs unterscheiden.
- **Fall L – Cocos Creator JS + Pomelo**: XXTEA- + gzip-Skripte, ein In-Memory-Loopback-Server im Paket.
- **Fall M – Cocos2d-Lua**: Lua wird aus dem Paket heraus ausgeliefert, Hot-Pushes während der Entwicklung dauern 0,3 Sekunden.
- **Fall N – Cocos2d-x, zwei Lua-Threads + rohes TCP + Protobuf**: Die Netzwerkschicht läuft im Speicher als Loopback; negative `int32`-Werte und weggelassene Standardfelder sind in beide Richtungen behoben.
- **Fall O – Cocos2d-x 2.x + LuaJIT 2.1 + ein Erweiterungspaket mit 4.2 GB**: Zu groß für eine einzige APK (ZIP32-Grenzen), deshalb liegen die Daten außerhalb; eine schlanke neue Activity übernimmt den Launcher, ohne die originale DEX anzufassen.
- **Fall P – Unity Mono**: Ein flacher Override-Baum statt einer langen Patch-Kette, Mono.Cecil-Anker-Patches auf dem Host und `INTERNET` direkt im Manifest entfernt.

Ein weiteres Spiel wurde nach einem halben Tag aufgegeben: Das eigentliche Spiel wurde erst nach dem ersten Start heruntergeladen, und dieser Download verschwand mit dem Server.

Die Fälle A–D und G sind als vollständige Fallstudien (anonymisiert) in [`references/`](../skills/offline-game-revival/references) ausgearbeitet. Die Fälle E und F sind in die Referenzdateien eingeflossen, die Fälle H–P in die Engine-Routen-Seiten (`route-*.md`), den Ablauf Kickoff / Batches / QA und das Fehler-Logbuch.

## 🚀 Installation

**Claude Code (Plugin-Marketplace)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Jeder Agent, der Agent Skills unterstützt** (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, OpenCode, Goose …) – kopiere den Ordner in das Skills-Verzeichnis dieses Agenten:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

Andere Agenten lesen [`AGENTS.md`](../AGENTS.md), das sie auf den Skill verweist. Die Sub-Agent-Rollen liegen in [`agents/`](../agents).

**Nur Chat (DeepSeek / ChatGPT / Kimi im Web)** – füge [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) als erste Nachricht ein. Das Modell wird zu deinem leitenden Entwickler; du führst die Befehle aus, die es dir gibt, und fügst die Ausgabe wieder ein.

**Große Projekte, die über Tage laufen** – drei Prompts zum Kopieren (reine Erkundung ohne Schreiben → Kickoff bis zur finalen QA → Weitermachen nach einer Pause) und die Installation in Antigravity: [`prompts/three-stage-prompts.md`](../prompts/three-stage-prompts.md). Du arbeitest an mehreren PCs? Hol dir die Erkenntnisse jedes Rechners mit [`prompts/merge-lessons.md`](../prompts/merge-lessons.md) zusammen.

Dann einfach fragen: *„Die Server dieses Spiels wurden abgeschaltet – mach es offline spielbar"* oder *„Zieh die Shop-Preise und Gacha-Raten aus diesen 15 GB Bildschirmaufnahmen."*

## 🎞️ Daten aus Bildschirmaufnahmen retten (eigenständig)

Der Harvester funktioniert ganz ohne Agent:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # oder OPENAI_API_KEY, DASHSCOPE_API_KEY … (PowerShell: $env:DEEPSEEK_API_KEY="sk-...")
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # 2 Chunks strukturieren, Qualität prüfen
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # alles → out/structured/merged.json
```

- **Keyframes, die zählen**: Ein Frame bleibt nur erhalten, wenn sich der Bildschirm *verändert und beruhigt* hat – Übergangsanimationen und Bewegungsunschärfe werden übersprungen; lange Scroll-Listen werden trotzdem abgetastet.
- **Deduplizierung über Quellen hinweg**: Derselbe Screen aus einem Screenshot und aus einer Aufnahme wird zusammengeführt (Statusleiste wird ignoriert).
- **Lokales OCR** (RapidOCR / ONNX, nur CPU, CJK + Latein) mit Bounding Boxes und Lesereihenfolge.
- **Ausgabe**: `for_llm/*.txt`-Chunks plus ein fertiger Prompt und ein JSON-Schema in [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md); `llm_structure.py` führt alle Antworten zusammen und markiert widersprüchliche Zahlen.

## ⏩ Zeitreise-Tests (eigenständig)

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 bestanden
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # findet 3 eingebaute Bugs
```

Richte `timewarp.create({ files, entry, inventory, granted })` auf deinen eigenen Fake-Server. Eine Checkliste der Zeit-Bugs, die sich zu testen lohnen (Reset-Uhrzeit, Login-Schleifen, Regenerationsgrenzen, Timer, Persistenz nach Neustart), findest du in [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md).

## 🧭 Philosophie

1. **Zur Build-Zeit patchen, nicht zur Laufzeit.** Ein Frida-Skript, das „funktioniert", muss für immer injiziert werden. Änderungen, die ins Paket eingebrannt sind, werden installiert und laufen einfach.
2. **Ein Einstiegspunkt + Anker-Assertions.** Stillschweigend übersprungene Ersetzungen führen zu kaputten Builds.
3. **Artefakte sind kein Quellcode.** Repariere das Patch-Skript, bearbeite niemals die Ausgabe von Hand.
4. **„Es öffnet sich" heißt nicht „es funktioniert".** Zustandsänderungen und Neustarts verifizieren und festhalten, was geprüft und was nur implementiert ist.

## ⚖️ Verantwortungsvolle Nutzung und Haftungsausschluss

Dieses Repository dient dazu, **zu verstehen, wie Spiele funktionieren**, und Spiele zu bewahren, deren offizieller Dienst eingestellt wurde. Es enthält nur Methoden und eigene Werkzeuge des Autors.

- **Hier gibt es keine Downloads.** Dieses Repository enthält keine Spiel-Assets, keinen Spielcode, keine Entschlüsselungs- oder Signaturschlüssel und keine Installationspakete und bietet nichts zum Herunterladen an. Bitte frag hier nicht danach.
- **Pakete bitte nicht weiterverbreiten.** Nutze, was du erstellst, nur privat und nicht kommerziell mit einer rechtmäßig erworbenen Kopie. Bitte veröffentliche oder verkaufe keine veränderten Installationspakete, Spiel-Assets oder Schlüssel und betreibe keine privaten Server mit Gewinnabsicht.
- **Nur für Spiele, deren offizieller Dienst eingestellt wurde.** Bitte nicht für laufende Spiele, zum Cheaten, zum Umgehen von Anti-Cheat-Systemen oder auf eine Weise, die anderen Spielern oder dem Rechteinhaber schadet.
- **Halte dich an die Gesetze deines Landes; du bist für deine Nutzung selbst verantwortlich.** In Deutschland erlaubt das Urheberrechtsgesetz Eingriffe in Computerprogramme, etwa das Dekompilieren, nur in engen Grenzen, und auch das Umgehen technischer Schutzmaßnahmen kann verboten sein; in anderen Ländern gelten andere Regeln. Nichts hier ist Rechtsberatung, und nichts hier behauptet, dass eine bestimmte Nutzung legal ist. Im Zweifel frag vorher einen Anwalt.
- **Keine Verbindung zu Spielefirmen.** Spielnamen und Marken gehören ihren jeweiligen Inhabern. Dieses Projekt steht mit keinem Spieleunternehmen in Verbindung und wird von keinem unterstützt.
- **Keine Gewährleistung, keine Haftung.** Alles wird unter der MIT-Lizenz „wie besehen“ bereitgestellt. Soweit gesetzlich zulässig, haftet der Autor nicht für Schäden, Datenverlust, Kontosperren oder rechtliche Folgen, die aus der Nutzung entstehen.
- **Rechteinhaber:** Wenn du der Meinung bist, dass etwas hier deine Rechte verletzt, eröffne bitte ein Issue; wir prüfen es umgehend und entfernen den Inhalt bei Bedarf. Wenn ein Spiel offiziell zurückkehrt, unterstütze bitte die offizielle Version.

Mit der Nutzung der Inhalte dieses Repositorys erklärst du dich mit dem Obigen einverstanden.

## 🤝 Mitmachen

Hast du mit diesem Skill ein Spiel wiederbelebt? Bist du in eine neue Falle getappt? Issues und PRs mit **neuen Engine-Fallstudien** (Cocos, Unreal, Godot, IL2CPP …) und **neuen Einträgen fürs Fehler-Logbuch** sind sehr willkommen.

Wenn dieses Projekt ein Spiel gerettet hat, das du geliebt hast, hilft ein ⭐ anderen Spielern, es zu finden.

Wie du mitmachen kannst (Issues, Pull Requests, Mitbetreuer werden): siehe [CONTRIBUTING.md](../CONTRIBUTING.md).

## ⭐ Sterne & Klone

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

[![Clone history](https://raw.githubusercontent.com/Cynthia-wlan9509/offline-game-revival/traffic/clones.svg)](https://github.com/Cynthia-wlan9509/offline-game-revival/blob/traffic/clones.csv)

GitHub speichert den Clone-Traffic nur 14 Tage lang. Das Klon-Diagramm beginnt deshalb mit einer Momentaufnahme vom 2026-11-03 und wird seitdem täglich aktualisiert.

## 📄 Lizenz

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · Cocos · IL2CPP · HybridCLR · WebGL · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · Zeitreise-Tests · Multi-Agent-System · KI-Agenten · Spiel eingestellt · Server abgeschaltet · Offline spielen · Spielebewahrung · Mobile Game ohne Server · Serverabschaltung</sub>
