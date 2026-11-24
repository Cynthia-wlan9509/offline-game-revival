<div align="center">

# 🎮 Offline Game Revival

### Una skill de agente de IA que devuelve a la vida los juegos móviles cerrados: totalmente offline, en un móvil de verdad.

**Cuando los servidores mueren, el juego no tiene por qué morir.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%7C%20LayaAir%20%7C%20Cocos%20%7C%20WebGL-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

Cada año cierran cientos de juegos móviles. El APK sigue en el teléfono de los jugadores, pero sin servidor no puede iniciar sesión, ni cargar una partida, ni hacer absolutamente nada. Años de historias, personajes y recuerdos quedan fuera de alcance.

**Offline Game Revival** es un manual probado en batalla, empaquetado como una [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Apunta a tu agente de programación (Claude Code y otros agentes que lean `SKILL.md`) hacia el APK de un juego muerto y sabrá cómo convertirlo en una **edición conmemorativa independiente**: instalas el APK y juegas el juego entero, sin red, sin root, sin PC y sin inyección en tiempo de ejecución.

Todo esto lo fui descubriendo por mi cuenta. Empecé sin saber nada de desarrollo de videojuegos y no he leído un solo tutorial: desde el primer día me dediqué a pedirle deseos a la IA (Claude, DeepSeek, GPT-6 Astra) y a hacerle repetir el trabajo cuando el resultado no era el que quería. Por eso es normal que algunas cosas coincidan con lo que dicen otros y otras no. Los criterios de decisión, el flujo de trabajo y los tropiezos que aquí se recogen vienen de mi propio ensayo y error con varios juegos reales.

**Hasta ahora: 16 juegos con los servidores apagados**, sobre Unity + Lua, Unity Mono / SLua, Unity IL2CPP, HybridCLR, LayaAir, Cocos (JS / Lua / LuaJIT), Unity WebGL / H5 y Kotlin nativo + Live2D: juegos de historia y de citas, de cartas, uno de xianxia, uno de chat con personajes de IA y más. La lista completa está en [Probado en juegos reales](#-probado-en-juegos-reales).

## ✨ Qué incluye

| | |
|---|---|
| 🔍 **Reconocimiento** | Desempaqueta el APK, localiza la verdadera capa de lógica (Lua / JS / C# transpilado) e identifica el cifrado y las comprobaciones de integridad de recursos. |
| ⚡ **Triaje más rápido y reconocimiento más a fondo** *(nuevo)* | Responde rápido a «¿se puede salvar?»: instala el APK original en un emulador con root, corta la red y arranca en frío. Si la pantalla de inicio de sesión se muestra completa, el juego y sus recursos están ahí y solo estorba la capa de inicio de sesión. En los paquetes de recursos donde solo se cifra un tramo, localiza la ventana cifrada exacta bloque a bloque. Los minijuegos cuyas reglas viven por completo en el cliente se ejecutan sin interfaz en un PC, así que se pueden comprobar todos los niveles de una vez. Consulta [`recon.md`](../skills/offline-game-revival/references/recon.md) y [`playtest.md`](../skills/offline-game-revival/references/playtest.md). |
| 🧩 **Parcheo con anclas verificadas** | Un único punto de entrada de compilación. Cada reemplazo de código comprueba su ancla: si el paquete original cambia, la compilación *falla con estrépito* en lugar de entregar un parche roto en silencio. |
| 🖥️ **Servidor falso local** | Intercepta la capa HTTP/JSON y responde cientos de endpoints desde una partida guardada local. Incluye una metodología para mapear quién llama a cada endpoint y qué lee, y generar valores por defecto seguros. |
| 📦 **Reempaquetado y firma** | Recalcula los checksums de la caché del motor, reconstruye las tablas de recursos, aplica zipalign y firma. Incluye un algoritmo de checksum de caché obtenido por ingeniería inversa y parches del cargador para LayaAir native. |
| ✅ **Aceptación en el dispositivo** | «La pantalla abre» ≠ «funciona». El estado tiene que cambiar de verdad y sobrevivir a un reinicio en frío. Pruebas guiadas por el tutorial: sigue los pasos de la propia guía del juego con toques reales. |
| 🛡️ **Lanzamientos seguros** *(nuevo)* | Antes de publicar, instala la versión pública anterior, juega una partida, actualiza encima y compara la partida guardada clave por clave. Al instalar en el móvil del propio usuario, haz primero una copia de seguridad de la partida y compárala byte a byte después. Cambia el nombre del paquete para que la edición conmemorativa se instale junto a la app oficial. Consulta [`verify.md`](../skills/offline-game-revival/references/verify.md) y [`patch.md`](../skills/offline-game-revival/references/patch.md) (sección 5). |
| 🎞️ **Rescate de datos desde capturas y grabaciones** *(nuevo)* | Los números del lado del servidor (precios de la tienda, probabilidades del gacha, recompensas, estadísticas de cartas) mueren con el servidor. `scripts/harvest.py` convierte **decenas de GB de capturas y grabaciones de pantalla de jugadores** en unos cientos de KB de texto categorizado: fotogramas clave → eliminación de casi duplicados → OCR local → agrupación por pantalla, **totalmente offline y con cero tokens**; después, `scripts/llm_structure.py` lo procesa por lotes con DeepSeek / OpenAI / Qwen / Kimi / Ollama local y lo fusiona en JSON + CSV. |
| ⏩ **Pruebas de viaje en el tiempo** *(nuevo)* | `scripts/timewarp` ejecuta tu servidor falso en un sandbox con reloj virtual: adelanta días, reinicia la app y **audita cada recompensa**; si una respuesta dice «+50 gemas» pero la partida guardada no cambió, la prueba falla. Simula 30 días de juego en un segundo y comprueba en qué día se vuelve alcanzable cada barrera. Cero dependencias. |
| 🤝 **Cualquier agente, cualquier modelo** *(nuevo)* | Funciona con Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI… mediante `SKILL.md` + `AGENTS.md`. Incluye roles de subagente (scout / worker / verifier) para que un modelo caro tome las decisiones y los baratos hagan el trabajo de campo. ¿Sin agente? Pega `prompts/chat-playbook.md` en DeepSeek / ChatGPT y ejecuta los comandos que te dé. |
| 🚦 **Arranque → lotes → QA independiente** *(nuevo)* | Para proyectos grandes que corren varios días sin supervisión: una hoja de preautorización de dos minutos al principio, luego un lote cada vez con límites de tiempo estrictos (dos rondas de sondeo o 45 minutos sin avance → se anota y se pasa al siguiente) y, al final, una revisión hecha por otra sesión que no se fía del «todo en verde» de la línea de desarrollo: se rebajan los aprobados optimistas, se recorre cada botón, se gana *y* se pierde cada combate y se compara con el registro, se mata el proceso a mitad de una transacción, 10 días virtuales y, por último, datos limpios + carpeta de actualización en caliente vacía + sin red, con dos arranques en frío. Incluye plantillas para la hoja, el traspaso, la matriz de progreso y la lista de bugs. |
| 🧭 **Rutas por motor** *(nuevo)* | Una página por arquitectura: Unity IL2CPP sin capa de scripts (servidor Python de loopback incrustado en el mismo proceso), Unity Mono / ET / HybridCLR (servidor C# dentro del paquete), Cocos JS / Lua / LuaJIT + Protobuf (loopback en memoria, Activity mínima que toma el control), Unity WebGL / microclientes H5 (primero H5, el envoltorio al final, la DLL original como proceso residente de combate). |
| 🧰 **Scripts de reconocimiento y protección** *(nuevo)* | Solo biblioteca estándar de Python: reconocimiento de APK de una sola pasada y de solo lectura (motor, ABI, límites de ZIP32, empaquetadores, prefijos de UnityFS, diferencias del manifiesto), bloqueo de un único dispositivo con envío seguro para rutas no ASCII, un fusible de presupuesto de disco que no sigue las junctions, un oráculo de logs, eliminación de `INTERNET` sin apktool, un reemplazador de entradas del APK que mantiene el audio sin comprimir y un hook opcional que bloquea `adb kill-server`, `svc wifi disable` y otros comandos que rompen los emuladores de otros proyectos. |
| 📚 **Registro de fallos** | Unos 230 KB y casi 300 entradas de trampas reales: síntoma → causa raíz → solución. Cierres por condiciones de carrera al arrancar, interfaces que se salen de la pantalla sin avisar, objetos XHR de un pool «envenenados» por respuestas falsas, partidas que nunca llegan al disco… |

## 🏆 Probado en juegos reales

El manual se destiló a partir de la resurrección de 16 juegos móviles comerciales cuyos servidores se apagaron:

- **Caso A — Unity + Lua**: edición conmemorativa completa para un jugador, verificada en un teléfono Android 14 físico.
- **Caso B — LayaAir native + JavaScript**: 315 endpoints de servidor reimplementados en local, más de 700 aserciones de regresión y todos los sistemas principales (capítulos de historia, combates, gacha, mascotas, citas, torre, eventos) recorridos a mano en un dispositivo.
- **Caso C — micro cliente de Unity (Mono + SLua)**: el APK solo traía alrededor de una cuarta parte de los recursos del juego; el resto salió de la copia de seguridad del teléfono de un jugador. Ensamblados Mono semicifrados, un empaquetador y un servidor local escrito por completo en Lua.
- **Caso D — Kotlin nativo + Live2D, chat con personajes por IA**: la función principal, chatear con los personajes, funcionaba con un LLM en el servidor del editor. Ahora el chat va a la API compatible con OpenAI del propio jugador o a un modelo local, y unas fichas de personaje y frases de ejemplo sacadas del guion original mantienen a cada personaje en su papel. Sin modelo, los personajes responden con sus frases originales con voz.
- **Caso G — LayaAir + protocolo sproto de conexión larga**: el juego entero venía en el APK, así que el trabajo estaba en el servidor: el paquete traía su propio esquema de protocolo (más de 400 peticiones), los sistemas se reconstruyeron en local uno por uno, con un script de juego automático que sigue las guías del juego con toques reales para encontrar el siguiente sistema que falta. Casi todo lo que enseñó está en el registro de fallos: respuestas vacías por defecto que bloquean funciones en silencio, rechazos al reclamar que muestran a los jugadores un error sin sentido, y falsos «jugadores virtuales» que parecen rotos.
- **Caso H — juego de cartas Unity IL2CPP, sin capa de scripts**: un runtime de Python incrustado en el propio proceso del juego hace de servidor local, con partidas guardadas en SQLite y una página web de GM. Hechos los 847 protocolos, 18 sistemas y 133 eventos, más 120 jugadores de IA que mantienen la sensación de «servidor en vivo».
- **Caso I — microcliente Unity WebGL / H5** (un APK de 237 KB, xianxia): primero H5 y el empaquetado al final. La `Hotfix.dll` original del juego se ejecuta como proceso residente de combate, así que toda la historia principal (990/990) y las 9 tribulaciones se completan sin cambiar una sola fórmula.
- **Caso J — Unity Mono / ET Hotfix** (`code.unity3d` + `Hotfix.dll`): un servidor en C# dentro del paquete; las respuestas vuelven un frame después para que la interfaz no se bloquee a sí misma.
- **Caso K — Unity 2021 IL2CPP + HybridCLR**: los 15,550 bundles llevaban una cabecera doble de 22 bytes: un prefijo, no cifrado. Se distinguieron las DLL de actualización en caliente reales de las DLL de metadatos AOT recortadas.
- **Caso L — Cocos Creator JS + Pomelo**: scripts con XXTEA + gzip y un servidor de bucle local en memoria dentro del paquete.
- **Caso M — Cocos2d-Lua**: Lua servido desde dentro del paquete, con envíos en caliente de 0,3 segundos durante el desarrollo.
- **Caso N — Cocos2d-x, dos hilos de Lua + TCP puro + protobuf**: la capa de red en bucle local en memoria; valores `int32` negativos y campos por defecto omitidos corregidos en ambos sentidos.
- **Caso O — Cocos2d-x 2.x + LuaJIT 2.1 + un paquete de expansión de 4.2 GB**: demasiado grande para un solo APK (límites de ZIP32), así que los datos viven fuera; una Activity nueva y ligera toma el control del lanzador sin tocar el DEX original.
- **Caso P — Unity Mono**: un árbol plano de archivos de reemplazo en lugar de una larga cadena de parches, parches de ancla con Mono.Cecil en el host e `INTERNET` eliminado del manifiesto en el sitio.

Otro juego se abandonó tras medio día: el juego en sí se descargaba después del primer inicio, y esa descarga desapareció con el servidor.

Los casos A–D y G están redactados como casos de estudio completos (anonimizados) en [`references/`](../skills/offline-game-revival/references). Los casos E y F están integrados en los archivos de referencia, y los casos H–P, en las páginas de rutas por motor (`route-*.md`), el flujo de arranque / lotes / QA y el registro de fallos.

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

**Proyectos grandes que duran días**: tres prompts para copiar y pegar (reconocimiento de solo lectura → del arranque a la QA final → retomar tras una pausa), más cómo instalarlo en Antigravity: [`prompts/three-stage-prompts.md`](../prompts/three-stage-prompts.md). ¿Trabajas en varios PC? Reúne las lecciones de cada uno con [`prompts/merge-lessons.md`](../prompts/merge-lessons.md).

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

## ⭐ Estrellas y clones

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

[![Clone history](https://raw.githubusercontent.com/Cynthia-wlan9509/offline-game-revival/traffic/clones.svg)](https://github.com/Cynthia-wlan9509/offline-game-revival/blob/traffic/clones.csv)

GitHub solo conserva 14 días del tráfico de clones, así que el gráfico de clones parte de una instantánea del 2026-11-03 y se actualiza a diario desde entonces.

## 📄 Licencia

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · Cocos · IL2CPP · HybridCLR · WebGL · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · pruebas de viaje en el tiempo · multiagente · múltiples agentes de IA · juego cerrado · servidores cerrados · jugar sin conexión · preservación de videojuegos · juego sin servidor · cierre de servidores</sub>
