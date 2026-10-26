<div align="center">

# 🎮 Offline Game Revival

### サービス終了したモバイルゲームを、実機でまるごとオフライン復活させる AI エージェントスキル。

**サーバーが消えても、ゲームは終わらせない。**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

毎年、何百ものモバイルゲームがサービスを終了します。APK はプレイヤーのスマホに残っているのに、サーバーがなければログインもセーブデータの読み込みもできません。何年分ものストーリーやキャラクター、思い出に、もう手が届かなくなってしまうのです。

**Offline Game Revival** は、実戦で鍛えられたノウハウを [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) にまとめたものです。コーディングエージェント（Claude Code や、`SKILL.md` を読み込める他のエージェント）に終了したゲームの APK を渡せば、**単体で動く記念版**へと作り替える方法をエージェントが心得ています。APK をインストールするだけで、ネットワークなし・root なし・PC なし・実行時インジェクションなしで、ゲームを最後まで遊べます。

## ✨ 中身

| | |
|---|---|
| 🔍 **調査（Recon）** | APK を展開し、本当のロジック層（Lua / JS / トランスパイルされた C#）を特定。暗号化やリソース整合性チェックを洗い出します。 |
| 🧩 **アンカー検証つきパッチ** | ビルドの入口はひとつだけ。コードの置換はすべて自分のアンカーを検証するので、元パッケージが変わったときは、気づかないうちに壊れたパッチを出荷するのではなく、*その場で派手に失敗*します。 |
| 🖥️ **ローカル偽サーバー** | HTTP/JSON 層を横取りし、何百ものエンドポイントをローカルのセーブデータから返します。各エンドポイントの呼び出し元と読み取り内容を洗い出し、安全なデフォルト値を生成する方法論つき。 |
| 📦 **再パッケージ＆再署名** | エンジンのキャッシュチェックサムの再計算、リソーステーブルの再構築、zipalign、署名まで対応。リバースエンジニアリングで解明したキャッシュチェックサムのアルゴリズムと、LayaAir native 用ローダーパッチも収録。 |
| ✅ **実機での受け入れテスト** | 「画面が開く」は「動く」ではありません。状態が実際に変化し、コールドリスタートを越えて残ることを確認します。チュートリアル駆動テストでは、ゲーム自身のガイドの手順どおりに、実際のタップで進めます。 |
| 🎞️ **スクリーンショット・録画からのデータ救出** *(新機能)* | ショップの価格、ガチャの排出率、報酬、カードのステータスなど、サーバー側の数値はサーバーと共に消えます。`scripts/harvest.py` は、**数十 GB ものプレイヤーのスクリーンショットや画面録画**を、分類済みの数百 KB のテキストに変換します。キーフレーム抽出 → 類似画像の除去 → ローカル OCR → 画面ごとのグルーピング、という流れで、**完全オフライン・トークン消費ゼロ**。そのうえで `scripts/llm_structure.py` が、DeepSeek / OpenAI / Qwen / Kimi / ローカルの Ollama にまとめて投げ、結合した JSON と CSV にします。 |
| ⏩ **タイムトラベルテスト** *(新機能)* | `scripts/timewarp` は、偽サーバーを仮想時計つきのサンドボックスで動かします。数日分の時間を早送りし、アプリを再起動し、**すべての報酬を監査**します。レスポンスに「ジェム +50」とあるのにセーブデータが変わっていなければ、テストは失敗。30 日分のプレイを 1 秒でシミュレートし、各ゲートが何日目に到達可能になるかも確認できます。依存ライブラリはゼロ。 |
| 🤝 **どのエージェントでも、どのモデルでも** *(新機能)* | `SKILL.md` と `AGENTS.md` により、Claude Code、Codex、Cursor、Copilot、OpenCode、Gemini CLI などで動作します。scout / worker / verifier のサブエージェントの役割を同梱しているので、高価なモデルが判断を下し、安価なモデルが下働きを担当できます。エージェントがまったくなくても大丈夫。`prompts/chat-playbook.md` を DeepSeek / ChatGPT に貼り付けて、返ってきたコマンドを実行するだけです。 |
| 📚 **失敗台帳** | 実際にハマった落とし穴を 100 KB 分収録。症状 → 根本原因 → 対処の順に整理しています。起動時のレースによるクラッシュ、いつの間にか画面外へ消える UI、偽レスポンスで「汚染」されるプール済み XHR オブジェクト、ディスクに書き込まれないセーブデータ……。 |

## 🏆 実在のゲームで実証済み

このノウハウは、サーバーが停止した商用モバイルゲーム 2 本の復活作業から抽出したものです。

- **ケース A — Unity + Lua**：完全なシングルプレイ記念版。実機の Android 14 端末で動作確認済み。
- **ケース B — LayaAir native + JavaScript**：サーバーの 315 エンドポイントをローカルで再実装し、700 以上のリグレッションアサーションを用意。主要システム（ストーリーの各章、バトル、ガチャ、ペット、デート、タワー、イベント）をすべて実機で通しプレイして確認しました。さらに、オフライン用ライセンスコード（Ed25519、BigInt 不使用）と、限定共有向けのコピーごとの透かしにも対応。

両方のケーススタディ（匿名化済み）は [`references/`](../skills/offline-game-revival/references) に収録されています。

## 🚀 インストール

**Claude Code（プラグインマーケットプレイス）**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Agent Skills に対応した任意のエージェント**（Claude Code、OpenAI Codex、Cursor、GitHub Copilot、OpenCode、Goose など）— フォルダをそのエージェントの skills ディレクトリにコピーします：

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

それ以外のエージェントは [`AGENTS.md`](../AGENTS.md) を読み、そこからスキルへ誘導されます。サブエージェントの役割は [`agents/`](../agents) にあります。

**チャットのみ（DeepSeek / ChatGPT / Kimi の Web 版）** — 最初のメッセージとして [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) を貼り付けます。モデルがリードエンジニアになるので、返ってきたコマンドを実行し、出力を貼り戻してください。

あとは話しかけるだけ。*「このゲームはサーバーが終了した。オフラインで遊べるようにして」*、あるいは *「15 GB の画面録画から、ショップの価格とガチャの排出率を抜き出して」*。

## 🎞️ 画面録画からデータを救出する（単体利用）

この収集ツールは、エージェントなしでも動きます。

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # または OPENAI_API_KEY、DASHSCOPE_API_KEY など（PowerShell：$env:DEEPSEEK_API_KEY="sk-..."）
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # まず 2 チャンクだけ構造化して品質を確認
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # 全件 → out/structured/merged.json
```

- **意味のあるキーフレームだけを抽出**：画面が*変化して落ち着いた*ときだけフレームを残し、トランジション演出やモーションブラーはスキップ。長いスクロールリストもきちんとサンプリングします。
- **ソースをまたいだ重複排除**：スクリーンショットと録画に同じ画面があれば統合します（ステータスバーは無視）。
- **ローカル OCR**（RapidOCR / ONNX、CPU のみ、CJK＋ラテン文字対応）。バウンディングボックスと読み順つき。
- **出力**：`for_llm/*.txt` のチャンクと、すぐ使えるプロンプトおよび JSON スキーマ（[`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md) を参照）。`llm_structure.py` はすべての回答をマージし、食い違う数値にフラグを立てます。

## ⏩ タイムトラベルテスト（単体利用）

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 件パス
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # 仕込んだ 3 つのバグを検出
```

`timewarp.create({ files, entry, inventory, granted })` を自分の偽サーバーに向けるだけです。テストする価値のある時間まわりのバグ（リセット時刻、ログインボーナスのループ、回復上限、タイマー、再起動後の永続化）のチェックリストは [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md) にあります。

## 🧭 設計思想

1. **実行時ではなく、ビルド時にパッチする。** 「動く」Frida スクリプトも、結局は毎回インジェクトし続ける必要があります。パッケージに焼き込んだ変更なら、インストールするだけで動きます。
2. **入口はひとつ＋アンカー検証。** 黙ってスキップされた置換は、壊れたビルドを出荷する原因になります。
3. **成果物はソースではない。** 直すのはパッチスクリプトであり、出力を手で編集してはいけません。
4. **「開く」は「動く」ではない。** 状態の変化と再起動後の保持を確認し、検証済みのものと実装しただけのものを書き分けます。

## ⚖️ 責任ある利用

このプロジェクトの目的は**ゲームの保存**、つまり**公式サービスが終了した後も**ゲームを遊べる状態に保つことです。

- 公式サーバーが**完全に終了した**ゲームにのみ使用してください。運営中のゲームには使わないこと。チート、アンチチートの回避、他のプレイヤーへの影響を目的とした使用も禁止です。
- このリポジトリには**ゲームのアセットも、ゲームのコードも、鍵も含まれていません**。あるのはノウハウと、作者自身のツールだけです。
- 著作権を尊重してください。記念版は非公開・非営利にとどめ、お住まいの地域の法律に従ってください。権利者がゲームを再リリースした場合は、公式版を支持しましょう。

## 🤝 コントリビュート

このスキルでゲームを復活させましたか？新しい落とし穴にハマりましたか？**新しいエンジンのケーススタディ**（Cocos、Unreal、Godot、IL2CPP など）や**失敗台帳への新しい項目**を添えた Issue や PR を、心よりお待ちしています。

大好きなゲームを救えたなら、⭐ をひとつ。ほかのプレイヤーがこのプロジェクトを見つける助けになります。

参加方法（Issue、プルリクエスト、共同メンテナーになるには）は [CONTRIBUTING.md](../CONTRIBUTING.md) を参照してください。

## ⭐ スター数の推移

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

## 📄 ライセンス

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · タイムトラベルテスト · マルチエージェント · 時間経過テスト · サービス終了 · オフライン化 · ゲーム保存 · 配信終了 · 録画OCR · スマホゲー復活</sub>
