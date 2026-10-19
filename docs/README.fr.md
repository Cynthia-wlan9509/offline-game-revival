<div align="center">

# 🎮 Offline Game Revival

### Une skill d'agent IA qui ressuscite les jeux mobiles dont les serveurs ont fermé — 100 % hors ligne, sur un vrai téléphone.

**Quand les serveurs s'éteignent, le jeu ne devrait pas s'éteindre avec eux.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

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
| 🎞️ **Sauvetage de données depuis des captures et des enregistrements** *(nouveau)* | Les chiffres côté serveur (prix de la boutique, taux de gacha, récompenses, stats des cartes) disparaissent avec le serveur. `scripts/harvest.py` transforme **des dizaines de Go de captures d'écran et d'enregistrements de joueurs** en quelques centaines de Ko de texte classé : images clés → suppression des quasi-doublons → OCR local → regroupement par écran, **entièrement hors ligne, zéro token**, prêt à être structuré par n'importe quel LLM texte bon marché. |
| 📚 **Registre des échecs** | 80 Ko de pièges bien réels : symptôme → cause racine → correctif. Plantages dus à des courses au démarrage, interface qui sort de l'écran sans prévenir, objets XHR du pool « empoisonnés » par de fausses réponses, sauvegardes qui n'atteignent jamais le disque… |

## 🏆 Éprouvé sur de vrais jeux

Ce guide est né de la résurrection de deux jeux mobiles commerciaux dont les serveurs ont fermé :

- **Cas A — Unity + Lua** : édition commémorative solo complète, vérifiée sur un téléphone Android 14 physique.
- **Cas B — LayaAir native + JavaScript** : 315 endpoints serveur réimplémentés en local, plus de 700 assertions de non-régression, et tous les grands systèmes (chapitres d'histoire, combats, gacha, familiers, rendez-vous, tour, événements) parcourus à la main sur un appareil, avec en prime des codes de licence hors ligne (Ed25519, sans BigInt) et des filigranes propres à chaque copie pour un partage privé.

Les deux études de cas (anonymisées) sont incluses dans [`references/`](../skills/offline-game-revival/references).

## 🚀 Installation

**Claude Code (marketplace de plugins)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Tout agent qui lit `SKILL.md`** : copiez le dossier dans le répertoire de skills de votre agent, par exemple pour Claude Code :

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/
```

Il ne reste qu'à demander : *« Les serveurs de ce jeu ont fermé — rends-le jouable hors ligne »* ou *« Extrais les prix de la boutique et les taux de gacha de ces 15 Go d'enregistrements d'écran. »*

## 🎞️ Sauver des données depuis des enregistrements d'écran (autonome)

L'extracteur fonctionne sans aucun agent :

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
```

- **Des images clés qui comptent** : une image n'est conservée que si l'écran a *changé puis s'est stabilisé* ; les animations de transition et le flou de mouvement sont ignorés, et les longues listes défilantes restent échantillonnées.
- **Dédoublonnage entre sources** : un même écran issu d'une capture et d'un enregistrement est fusionné (barre d'état ignorée).
- **OCR local** (RapidOCR / ONNX, CPU uniquement, CJK + latin) avec boîtes englobantes et ordre de lecture.
- **Sortie** : des fragments `for_llm/*.txt`, plus un prompt prêt à l'emploi et un schéma JSON dans [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md).

## 🧭 Philosophie

1. **Patcher à la compilation, pas à l'exécution.** Un script Frida qui « marche » doit être injecté pour toujours. Des modifications intégrées au paquet s'installent et fonctionnent, tout simplement.
2. **Point d'entrée unique + assertions d'ancre.** Les remplacements ignorés en silence produisent des builds cassés.
3. **Les artefacts ne sont pas des sources.** Corrigez le script de patch, ne retouchez jamais la sortie à la main.
4. **« Ça s'ouvre » ne veut pas dire « ça marche ».** Vérifiez les changements d'état, leur survie aux redémarrages, et notez ce qui est vérifié et ce qui est seulement implémenté.

## ⚖️ Usage responsable

Ce projet est consacré à la **préservation du jeu vidéo** : garder les jeux jouables **une fois leur service officiel terminé**.

- À n'utiliser que sur des jeux dont les serveurs officiels sont **définitivement fermés**. Jamais sur un jeu en service, jamais pour tricher, contourner un anti-triche ou nuire à d'autres joueurs.
- Le dépôt **ne contient aucune ressource de jeu, aucun code de jeu, aucune clé** — uniquement des méthodes et les propres outils de l'auteur.
- Respectez le droit d'auteur : gardez les éditions commémoratives privées et non commerciales, et respectez les lois de votre pays. Si un ayant droit relance le jeu, soutenez la version officielle.

## 🤝 Contribuer

Vous avez ressuscité un jeu avec cette skill ? Vous êtes tombé sur un nouveau piège ? Les issues et PR proposant de **nouvelles études de cas de moteurs** (Cocos, Unreal, Godot, IL2CPP…) et de **nouvelles entrées pour le registre des échecs** sont les bienvenues.

Si cela a sauvé un jeu que vous aimiez, une ⭐ aide d'autres joueurs à le trouver.

## 📄 Licence

[MIT](../LICENSE)

<sub>Keywords: game preservation · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · jeu fermé · fermeture des serveurs · jouer hors ligne · préservation du jeu vidéo · jeu mobile sans serveur · fin de service</sub>
