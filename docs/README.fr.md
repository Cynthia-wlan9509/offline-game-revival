<div align="center">

# 🎮 Offline Game Revival

### Une skill d'agent IA qui ressuscite les jeux mobiles dont les serveurs ont fermé — 100 % hors ligne, sur un vrai téléphone.

**Quand les serveurs s'éteignent, le jeu ne devrait pas s'éteindre avec eux.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

Chaque année, des centaines de jeux mobiles ferment leurs portes. L'APK reste sur le téléphone des joueurs, mais sans serveur, impossible de se connecter, de charger une sauvegarde, de faire quoi que ce soit. Des années d'histoires, de personnages et de souvenirs deviennent inaccessibles.

**Offline Game Revival** est un guide éprouvé sur le terrain, empaqueté sous forme d'[Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Pointez votre agent de code (Claude Code et les autres agents qui lisent `SKILL.md`) vers l'APK d'un jeu mort, et il saura le transformer en **édition commémorative autonome** : vous installez l'APK, vous jouez au jeu en entier, sans réseau, sans root, sans PC, sans injection à l'exécution.

## ✨ Au programme

| | |
|---|---|
| 🔍 **Reconnaissance** | Décompresse l'APK, repère la vraie couche de logique (Lua / JS / C# transpilé), identifie le chiffrement et les contrôles d'intégrité des ressources. |
| 🧩 **Patchs à ancres vérifiées** | Un seul point d'entrée de build. Chaque remplacement de code vérifie son ancre : si le paquet d'origine change, le build *échoue bruyamment* au lieu de livrer en silence un patch cassé. |
| 🖥️ **Faux serveur local** | Intercepte la couche HTTP/JSON et répond à des centaines d'endpoints à partir d'une sauvegarde locale. Une méthode pour cartographier qui appelle chaque endpoint et ce qu'il lit, puis générer des valeurs par défaut sûres. |
| 📦 **Repackaging et re-signature** | Recalcule les checksums du cache du moteur, reconstruit les tables de ressources, applique zipalign et signe. Inclut un algorithme de checksum de cache obtenu par rétro-ingénierie et des patchs de chargeur pour LayaAir native. |
| ✅ **Recette sur appareil** | « L'écran s'affiche » ≠ « ça marche ». L'état doit réellement changer et survivre à un redémarrage à froid. Tests guidés par le tutoriel : suivez les étapes du guide du jeu lui-même, avec de vrais appuis sur l'écran. |
| 🎞️ **Sauvetage de données depuis des captures et des enregistrements** *(nouveau)* | Les chiffres côté serveur (prix de la boutique, taux de gacha, récompenses, stats des cartes) disparaissent avec le serveur. `scripts/harvest.py` transforme **des dizaines de Go de captures d'écran et d'enregistrements de joueurs** en quelques centaines de Ko de texte classé : images clés → suppression des quasi-doublons → OCR local → regroupement par écran, **entièrement hors ligne, zéro token** — puis `scripts/llm_structure.py` le fait traiter par lots par DeepSeek / OpenAI / Qwen / Kimi / Ollama en local, et fusionne le tout en JSON + CSV. |
| ⏩ **Tests de voyage dans le temps** *(nouveau)* | `scripts/timewarp` exécute votre faux serveur dans un bac à sable à horloge virtuelle : avancez de plusieurs jours, redémarrez l'app et **auditez chaque récompense** — si une réponse annonce « +50 gemmes » mais que la sauvegarde n'a pas bougé, le test échoue. Simulez 30 jours de jeu en une seconde et voyez à quel jour chaque palier devient accessible. Zéro dépendance. |
| 🤝 **N'importe quel agent, n'importe quel modèle** *(nouveau)* | Fonctionne avec Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI… via `SKILL.md` + `AGENTS.md`. Fournit des rôles de sous-agents (scout / worker / verifier) pour qu'un modèle coûteux prenne les décisions pendant que les modèles bon marché font le gros du travail. Pas d'agent du tout ? Collez `prompts/chat-playbook.md` dans DeepSeek / ChatGPT et exécutez les commandes qu'il vous donne. |
| 📚 **Registre des échecs** | 80 Ko de pièges bien réels : symptôme → cause racine → correctif. Plantages dus à des courses au démarrage, interface qui sort de l'écran sans prévenir, objets XHR du pool « empoisonnés » par de fausses réponses, sauvegardes qui n'atteignent jamais le disque… |

## 🏆 Éprouvé sur de vrais jeux

Ce guide est né de la résurrection de deux jeux mobiles commerciaux dont les serveurs ont fermé :

- **Cas A — Unity + Lua** : édition commémorative solo complète, vérifiée sur un téléphone Android 14 physique.
- **Cas B — LayaAir native + JavaScript** : 315 endpoints serveur réimplémentés en local, plus de 700 assertions de non-régression, et tous les grands systèmes (chapitres d'histoire, combats, gacha, familiers, rendez-vous, tour, événements) parcourus à la main sur un appareil.

Les deux études de cas (anonymisées) sont incluses dans [`references/`](../skills/offline-game-revival/references).

## 🚀 Installation

**Claude Code (marketplace de plugins)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Tout agent compatible avec Agent Skills** (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, OpenCode, Goose…) : copiez le dossier dans le répertoire de skills de cet agent :

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

Les autres agents lisent [`AGENTS.md`](../AGENTS.md), qui les oriente vers le skill. Les rôles de sous-agents se trouvent dans [`agents/`](../agents).

**Chat uniquement (DeepSeek / ChatGPT / Kimi web)** : collez [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) comme premier message. Le modèle devient votre ingénieur en chef ; vous exécutez les commandes qu'il vous donne et lui recollez la sortie.

Il ne reste qu'à demander : *« Les serveurs de ce jeu ont fermé — rends-le jouable hors ligne »* ou *« Extrais les prix de la boutique et les taux de gacha de ces 15 Go d'enregistrements d'écran. »*

## 🎞️ Sauver des données depuis des enregistrements d'écran (autonome)

L'extracteur fonctionne sans aucun agent :

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # ou OPENAI_API_KEY, DASHSCOPE_API_KEY… (PowerShell : $env:DEEPSEEK_API_KEY="sk-...")
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # structure 2 fragments pour vérifier la qualité
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # tout → out/structured/merged.json
```

- **Des images clés qui comptent** : une image n'est conservée que si l'écran a *changé puis s'est stabilisé* ; les animations de transition et le flou de mouvement sont ignorés, et les longues listes défilantes restent échantillonnées.
- **Dédoublonnage entre sources** : un même écran issu d'une capture et d'un enregistrement est fusionné (barre d'état ignorée).
- **OCR local** (RapidOCR / ONNX, CPU uniquement, CJK + latin) avec boîtes englobantes et ordre de lecture.
- **Sortie** : des fragments `for_llm/*.txt`, plus un prompt prêt à l'emploi et un schéma JSON dans [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md) ; `llm_structure.py` fusionne toutes les réponses et signale les valeurs contradictoires.

## ⏩ Tests de voyage dans le temps (autonome)

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 réussis
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # détecte 3 bugs plantés
```

Pointez `timewarp.create({ files, entry, inventory, granted })` vers votre propre faux serveur. La liste des bugs temporels qui valent la peine d'être testés (heure de réinitialisation, boucles de connexion quotidienne, plafonds de régénération, minuteurs, persistance après redémarrage) est dans [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md).

## 🧭 Philosophie

1. **Patcher à la compilation, pas à l'exécution.** Un script Frida qui « marche » doit être injecté pour toujours. Des modifications intégrées au paquet s'installent et fonctionnent, tout simplement.
2. **Point d'entrée unique + assertions d'ancre.** Les remplacements ignorés en silence produisent des builds cassés.
3. **Les artefacts ne sont pas des sources.** Corrigez le script de patch, ne retouchez jamais la sortie à la main.
4. **« Ça s'ouvre » ne veut pas dire « ça marche ».** Vérifiez les changements d'état, leur survie aux redémarrages, et notez ce qui est vérifié et ce qui est seulement implémenté.

## ⚖️ Usage responsable et clause de non-responsabilité

Ce dépôt sert à **étudier le fonctionnement des jeux** et à préserver des jeux dont le service officiel a pris fin. Il ne contient que des méthodes et les outils de l'auteur.

- **Aucun téléchargement ici.** Ce dépôt ne contient ni ressources de jeu, ni code de jeu, ni clés de déchiffrement ou de signature, ni paquets d'installation, et ne propose aucun téléchargement. Merci de ne pas en demander ici.
- **Ne laissez pas les paquets se répandre.** Réservez ce que vous réalisez à un usage personnel et non commercial, sur une copie obtenue légalement. Merci de ne pas publier ni revendre de paquets d'installation modifiés, de ressources de jeu ou de clés, et de ne pas exploiter de serveur privé dans un but lucratif.
- **Uniquement pour des jeux dont le service officiel a pris fin.** Merci de ne pas l'utiliser sur un jeu encore exploité, pour tricher, pour contourner un anti-triche, ni d'une manière qui nuit à d'autres joueurs ou au titulaire des droits.
- **Respectez la loi de votre pays ; vous êtes responsable de votre usage.** En France, le Code de la propriété intellectuelle n'autorise la décompilation d'un logiciel que dans des cas très limités, et contourner une mesure technique de protection peut être interdit ; les règles varient selon les pays. Rien ici ne constitue un conseil juridique ni n'affirme qu'un usage particulier est légal. En cas de doute, consultez un avocat avant de commencer.
- **Aucune affiliation.** Les noms de jeux et les marques appartiennent à leurs titulaires. Ce projet n'est affilié à aucun éditeur de jeux et n'est approuvé par aucun.
- **Aucune garantie, aucune responsabilité.** Tout est fourni « en l'état » sous licence MIT. Dans toute la mesure permise par la loi, l'auteur décline toute responsabilité pour tout dommage, perte de données, sanction de compte ou conséquence juridique liés à son utilisation.
- **Titulaires de droits :** si vous estimez qu'un contenu de ce dépôt porte atteinte à vos droits, ouvrez une issue ; nous l'examinerons rapidement et le retirerons si nécessaire. Si un jeu revient officiellement, soutenez la version officielle.

En utilisant le contenu de ce dépôt, vous acceptez ce qui précède.

## 🤝 Contribuer

Vous avez ressuscité un jeu avec cette skill ? Vous êtes tombé sur un nouveau piège ? Les issues et PR proposant de **nouvelles études de cas de moteurs** (Cocos, Unreal, Godot, IL2CPP…) et de **nouvelles entrées pour le registre des échecs** sont les bienvenues.

Si cela a sauvé un jeu que vous aimiez, une ⭐ aide d'autres joueurs à le trouver.

Comment participer (issues, pull requests, devenir mainteneur) : voir [CONTRIBUTING.md](../CONTRIBUTING.md).

## ⭐ Historique des étoiles

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

## 📄 Licence

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · tests de voyage dans le temps · multi-agents · agents IA multiples · jeu fermé · fermeture des serveurs · jouer hors ligne · préservation du jeu vidéo · jeu mobile sans serveur · fin de service</sub>
