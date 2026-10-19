<div align="center">

# 🎮 Offline Game Revival

### Una skill de agente de IA que devuelve a la vida los juegos móviles cerrados: totalmente offline, en un móvil de verdad.

**Cuando los servidores mueren, el juego no tiene por qué morir.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

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
| 🎞️ **Rescate de datos desde capturas y grabaciones** *(nuevo)* | Los números del lado del servidor (precios de la tienda, probabilidades del gacha, recompensas, estadísticas de cartas) mueren con el servidor. `scripts/harvest.py` convierte **decenas de GB de capturas y grabaciones de pantalla de jugadores** en unos cientos de KB de texto categorizado: fotogramas clave → eliminación de casi duplicados → OCR local → agrupación por pantalla, **totalmente offline y con cero tokens**, listo para que cualquier LLM de texto barato lo estructure. |
| 📚 **Registro de fallos** | 80 KB de trampas reales: síntoma → causa raíz → solución. Cierres por condiciones de carrera al arrancar, interfaces que se salen de la pantalla sin avisar, objetos XHR de un pool «envenenados» por respuestas falsas, partidas que nunca llegan al disco… |

## 🏆 Probado en juegos reales

El manual se destiló a partir de la resurrección de dos juegos móviles comerciales cuyos servidores se apagaron:

- **Caso A — Unity + Lua**: edición conmemorativa completa para un jugador, verificada en un teléfono Android 14 físico.
- **Caso B — LayaAir native + JavaScript**: 315 endpoints de servidor reimplementados en local, más de 700 aserciones de regresión y todos los sistemas principales (capítulos de historia, combates, gacha, mascotas, citas, torre, eventos) recorridos a mano en un dispositivo, además de códigos de licencia offline (Ed25519, sin BigInt) y marcas de agua por copia para compartir en privado.

Ambos casos de estudio (anonimizados) están incluidos en [`references/`](../skills/offline-game-revival/references).

## 🚀 Instalación

**Claude Code (marketplace de plugins)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Cualquier agente que lea `SKILL.md`**: copia la carpeta al directorio de skills de tu agente; por ejemplo, para Claude Code:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/
```

Después, basta con pedirlo: *«Los servidores de este juego cerraron: hazlo jugable offline»* o *«Extrae los precios de la tienda y las probabilidades del gacha de estos 15 GB de grabaciones de pantalla.»*

## 🎞️ Rescata datos de grabaciones de pantalla (independiente)

El extractor funciona sin ningún agente:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
```

- **Fotogramas clave que importan**: conserva un fotograma solo cuando la pantalla *cambió y se estabilizó*; descarta animaciones de transición y desenfoque de movimiento, aunque las listas largas con scroll se siguen muestreando.
- **Deduplicación entre fuentes**: la misma pantalla de una captura y de una grabación se fusiona (ignorando la barra de estado).
- **OCR local** (RapidOCR / ONNX, solo CPU, CJK + latino) con cuadros delimitadores y orden de lectura.
- **Salida**: fragmentos `for_llm/*.txt` más un prompt listo para usar y un esquema JSON en [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md).

## 🧭 Filosofía

1. **Parchea en tiempo de compilación, no en tiempo de ejecución.** Un script de Frida que «funciona» hay que inyectarlo para siempre. Los cambios integrados en el paquete se instalan y funcionan sin más.
2. **Un único punto de entrada + aserciones de ancla.** Las omisiones silenciosas acaban en compilaciones rotas.
3. **Los artefactos no son código fuente.** Arregla el script de parcheo; nunca edites a mano el resultado.
4. **«Se abre» no es «funciona».** Verifica los cambios de estado, que sobrevivan a los reinicios, y deja por escrito qué está verificado y qué solo está implementado.

## ⚖️ Uso responsable

Este proyecto trata de la **preservación de videojuegos**: mantener los juegos jugables **después de que su servicio oficial haya terminado**.

- Úsalo solo en juegos cuyos servidores oficiales estén **cerrados de forma permanente**. Nunca en juegos activos, ni para hacer trampas, eludir sistemas anti-trampas o afectar a otros jugadores.
- El repositorio **no contiene recursos del juego, ni código del juego, ni claves**: solo métodos y las herramientas propias del autor.
- Respeta los derechos de autor: mantén las ediciones conmemorativas privadas y sin fines comerciales, y cumple las leyes de tu jurisdicción. Si el titular de los derechos relanza el juego, apoya la versión oficial.

## 🤝 Contribuir

¿Has revivido un juego con esta skill? ¿Te has topado con una trampa nueva? Se agradecen mucho los issues y PRs con **nuevos casos de estudio de motores** (Cocos, Unreal, Godot, IL2CPP…) y **nuevas entradas para el registro de fallos**.

Si esto salvó un juego que querías, una ⭐ ayuda a que otros jugadores lo encuentren.

## 📄 Licencia

[MIT](../LICENSE)

<sub>Keywords: game preservation · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · juego cerrado · servidores cerrados · jugar sin conexión · preservación de videojuegos · juego sin servidor · cierre de servidores</sub>
