<div align="center">

# 🎮 Offline Game Revival

### Una skill de agente de IA que devuelve a la vida los juegos móviles cerrados: totalmente offline, en un móvil de verdad.

**Cuando los servidores mueren, el juego no tiene por qué morir.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

Cada año cierran cientos de juegos móviles. El APK sigue en el teléfono de los jugadores, pero sin servidor no puede iniciar sesión, ni cargar una partida, ni hacer absolutamente nada. Años de historias, personajes y recuerdos quedan fuera de alcance.

**Offline Game Revival** es un manual probado en batalla, empaquetado como una [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Apunta a tu agente de programación (Claude Code y otros agentes que lean `SKILL.md`) hacia el APK de un juego muerto y sabrá cómo convertirlo en una **edición conmemorativa independiente**: instalas el APK y juegas el juego entero, sin red, sin root, sin PC y sin inyección en tiempo de ejecución.

## ✨ Qué incluye

| | |
|---|---|
| 🔍 **Reconocimiento** | Desempaqueta el APK, localiza la verdadera capa de lógica (Lua / JS / C# transpilado) e identifica el cifrado y las comprobaciones de integridad de recursos. |
| 🧩 **Parcheo con anclas verificadas** | Un único punto de entrada de compilación. Cada reemplazo de código comprueba su ancla: si el paquete original cambia, la compilación *falla con estrépito* en lugar de entregar un parche roto en silencio. |
| 🖥️ **Servidor falso local** | Intercepta la capa HTTP/JSON y responde cientos de endpoints desde una partida guardada local. Incluye una metodología para mapear quién llama a cada endpoint y qué lee, y generar valores por defecto seguros. |
| 📦 **Reempaquetado y firma** | Recalcula los checksums de la caché del motor, reconstruye las tablas de recursos, aplica zipalign y firma. Incluye un algoritmo de checksum de caché obtenido por ingeniería inversa y parches del cargador para LayaAir native. |
| ✅ **Aceptación en el dispositivo** | «La pantalla abre» ≠ «funciona». El estado tiene que cambiar de verdad y sobrevivir a un reinicio en frío. Pruebas guiadas por el tutorial: sigue los pasos de la propia guía del juego con toques reales. |
| 🎞️ **Rescate de datos desde capturas y grabaciones** *(nuevo)* | Los números del lado del servidor (precios de la tienda, probabilidades del gacha, recompensas, estadísticas de cartas) mueren con el servidor. `scripts/harvest.py` convierte **decenas de GB de capturas y grabaciones de pantalla de jugadores** en unos cientos de KB de texto categorizado: fotogramas clave → eliminación de casi duplicados → OCR local → agrupación por pantalla, **totalmente offline y con cero tokens**; después, `scripts/llm_structure.py` lo procesa por lotes con DeepSeek / OpenAI / Qwen / Kimi / Ollama local y lo fusiona en JSON + CSV. |
| ⏩ **Pruebas de viaje en el tiempo** *(nuevo)* | `scripts/timewarp` ejecuta tu servidor falso en un sandbox con reloj virtual: adelanta días, reinicia la app y **audita cada recompensa**; si una respuesta dice «+50 gemas» pero la partida guardada no cambió, la prueba falla. Simula 30 días de juego en un segundo y comprueba en qué día se vuelve alcanzable cada barrera. Cero dependencias. |
| 🤝 **Cualquier agente, cualquier modelo** *(nuevo)* | Funciona con Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI… mediante `SKILL.md` + `AGENTS.md`. Incluye roles de subagente (scout / worker / verifier) para que un modelo caro tome las decisiones y los baratos hagan el trabajo de campo. ¿Sin agente? Pega `prompts/chat-playbook.md` en DeepSeek / ChatGPT y ejecuta los comandos que te dé. |
| 📚 **Registro de fallos** | 100 KB de trampas reales: síntoma → causa raíz → solución. Cierres por condiciones de carrera al arrancar, interfaces que se salen de la pantalla sin avisar, objetos XHR de un pool «envenenados» por respuestas falsas, partidas que nunca llegan al disco… |

## 🏆 Probado en juegos reales

El manual se destiló a partir de la resurrección de dos juegos móviles comerciales cuyos servidores se apagaron:

- **Caso A — Unity + Lua**: edición conmemorativa completa para un jugador, verificada en un teléfono Android 14 físico.
- **Caso B — LayaAir native + JavaScript**: 315 endpoints de servidor reimplementados en local, más de 700 aserciones de regresión y todos los sistemas principales (capítulos de historia, combates, gacha, mascotas, citas, torre, eventos) recorridos a mano en un dispositivo.

Ambos casos de estudio (anonimizados) están incluidos en [`references/`](../skills/offline-game-revival/references).

## 🚀 Instalación

**Claude Code (marketplace de plugins)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Cualquier agente compatible con Agent Skills** (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, OpenCode, Goose…): copia la carpeta al directorio de skills de ese agente:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

Los demás agentes leen [`AGENTS.md`](../AGENTS.md), que los remite a la skill. Los roles de subagente están en [`agents/`](../agents).

**Solo chat (DeepSeek / ChatGPT / Kimi web)**: pega [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) como primer mensaje. El modelo se convierte en tu ingeniero principal; tú ejecutas los comandos que te dé y le pegas la salida.

Después, basta con pedirlo: *«Los servidores de este juego cerraron: hazlo jugable offline»* o *«Extrae los precios de la tienda y las probabilidades del gacha de estos 15 GB de grabaciones de pantalla.»*

## 🎞️ Rescata datos de grabaciones de pantalla (independiente)

El extractor funciona sin ningún agente:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # o OPENAI_API_KEY, DASHSCOPE_API_KEY… (PowerShell: $env:DEEPSEEK_API_KEY="sk-...")
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # estructura 2 fragmentos y revisa la calidad
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # todo → out/structured/merged.json
```

- **Fotogramas clave que importan**: conserva un fotograma solo cuando la pantalla *cambió y se estabilizó*; descarta animaciones de transición y desenfoque de movimiento, aunque las listas largas con scroll se siguen muestreando.
- **Deduplicación entre fuentes**: la misma pantalla de una captura y de una grabación se fusiona (ignorando la barra de estado).
- **OCR local** (RapidOCR / ONNX, solo CPU, CJK + latino) con cuadros delimitadores y orden de lectura.
- **Salida**: fragmentos `for_llm/*.txt` más un prompt listo para usar y un esquema JSON en [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md); `llm_structure.py` fusiona todas las respuestas y señala los números que se contradicen.

## ⏩ Pruebas de viaje en el tiempo (independiente)

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 superadas
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # detecta 3 bugs plantados
```

Apunta `timewarp.create({ files, entry, inventory, granted })` a tu propio servidor falso. La lista de bugs temporales que vale la pena probar (hora de reinicio diario, bucles de inicio de sesión, topes de regeneración, temporizadores, persistencia tras reiniciar) está en [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md).

## 🧭 Filosofía

1. **Parchea en tiempo de compilación, no en tiempo de ejecución.** Un script de Frida que «funciona» hay que inyectarlo para siempre. Los cambios integrados en el paquete se instalan y funcionan sin más.
2. **Un único punto de entrada + aserciones de ancla.** Las omisiones silenciosas acaban en compilaciones rotas.
3. **Los artefactos no son código fuente.** Arregla el script de parcheo; nunca edites a mano el resultado.
4. **«Se abre» no es «funciona».** Verifica los cambios de estado, que sobrevivan a los reinicios, y deja por escrito qué está verificado y qué solo está implementado.

## ⚖️ Uso responsable y descargo de responsabilidad

Este repositorio existe para **estudiar cómo funcionan los juegos** y para preservar juegos cuyo servicio oficial ha terminado. Solo contiene métodos y herramientas propias del autor.

- **Aquí no hay descargas.** Este repositorio no contiene recursos de juegos, código de juegos, claves de descifrado o de firma ni paquetes de instalación, y no ofrece descargas. Por favor, no los pidas aquí.
- **No dejes que los paquetes se difundan.** Usa lo que hagas solo de forma personal y no comercial, sobre una copia obtenida legalmente. Por favor, no publiques ni revendas paquetes de instalación modificados, recursos de juegos o claves, y no ejecutes servidores privados con fines de lucro.
- **Solo para juegos cuyo servicio oficial haya terminado.** Por favor, no lo uses en juegos activos, para hacer trampas, para eludir sistemas antitrampas ni de forma que perjudique a otros jugadores o al titular de los derechos.
- **Cumple la ley de tu país; eres responsable de tu propio uso.** En la Unión Europea (incluida España), la descompilación de programas solo se permite en casos muy limitados y eludir medidas tecnológicas de protección puede estar prohibido; en los demás países hispanohablantes las normas varían. Nada de lo que hay aquí es asesoramiento legal ni afirma que un uso concreto sea legal. Si tienes dudas, consulta a un abogado antes de empezar.
- **Sin afiliación.** Los nombres de los juegos y las marcas pertenecen a sus titulares. Este proyecto no está afiliado a ninguna empresa de videojuegos ni cuenta con su respaldo.
- **Sin garantía ni responsabilidad.** Todo se ofrece «tal cual» bajo la licencia MIT. En la máxima medida permitida por la ley, el autor no se hace responsable de ningún daño, pérdida de datos, sanción de cuenta ni consecuencia legal derivada de su uso.
- **Titulares de derechos:** si crees que algo de este repositorio infringe tus derechos, abre un issue; lo revisaremos con rapidez y, si es necesario, lo retiraremos. Si un juego vuelve de forma oficial, apoya la versión oficial.

Al usar el contenido de este repositorio, aceptas lo anterior.

## 🤝 Contribuir

¿Has revivido un juego con esta skill? ¿Te has topado con una trampa nueva? Se agradecen mucho los issues y PRs con **nuevos casos de estudio de motores** (Cocos, Unreal, Godot, IL2CPP…) y **nuevas entradas para el registro de fallos**.

Si esto salvó un juego que querías, una ⭐ ayuda a que otros jugadores lo encuentren.

Cómo participar (issues, pull requests, llegar a ser mantenedor): consulta [CONTRIBUTING.md](../CONTRIBUTING.md).

## ⭐ Historial de estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

## 📄 Licencia

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · pruebas de viaje en el tiempo · multiagente · múltiples agentes de IA · juego cerrado · servidores cerrados · jugar sin conexión · preservación de videojuegos · juego sin servidor · cierre de servidores</sub>
