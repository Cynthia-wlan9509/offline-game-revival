<div align="center">

# 🎮 Offline Game Revival

### サービス終了したモバイルゲームを、実機でまるごとオフライン復活させる AI エージェントスキル。

**サーバーが消えても、ゲームは終わらせない。**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%7C%20LayaAir%20%7C%20Cocos%20%7C%20WebGL-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

毎年、何百ものモバイルゲームがサービスを終了します。APK はプレイヤーのスマホに残っているのに、サーバーがなければログインもセーブデータの読み込みもできません。何年分ものストーリーやキャラクター、思い出に、もう手が届かなくなってしまうのです。

**Offline Game Revival** は、実戦で鍛えられたノウハウを [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) にまとめたものです。コーディングエージェント（Claude Code や、`SKILL.md` を読み込める他のエージェント）に終了したゲームの APK を渡せば、**単体で動く記念版**へと作り替える方法をエージェントが心得ています。APK をインストールするだけで、ネットワークなし・root なし・PC なし・実行時インジェクションなしで、ゲームを最後まで遊べます。

これはすべて、私が自分で手探りで見つけてきたものです。始めたときはゲーム開発の知識がまったくなく、チュートリアルも一つも読まず、初日からずっと AI（Claude、DeepSeek、GPT-6 Astra）にお願いしては、思いどおりにならなければやり直させてきました。なので、他の人の話と重なるところや違うところがあっても、ごく自然なことです。ここにある判断の仕方、手順、ハマりどころは、どれも私が複数の実在のゲームで試行錯誤して得たものです。

**これまでに 16 本の終了したゲーム**を手がけました。Unity + Lua、Unity Mono / SLua、Unity IL2CPP、HybridCLR、LayaAir、Cocos（JS / Lua / LuaJIT）、Unity WebGL / H5、ネイティブ Kotlin + Live2D と構成はさまざまで、ジャンルもストーリー系や恋愛ゲーム、カードバトル、仙侠ゲーム、AI キャラクターチャットのゲームなどです。全リストは[実在のゲームで実証済み](#-実在のゲームで実証済み)にあります。

## ✨ 中身

| | |
|---|---|
| 🔍 **調査（Recon）** | APK を展開し、本当のロジック層（Lua / JS / トランスパイルされた C#）を特定。暗号化やリソース整合性チェックを洗い出します。 |
| ⚡ **すばやいトリアージと、より手強い調査** *(新機能)* | 「救えるか？」を素早く見極めます。元の APK を root 化したエミュレータにインストールし、ネットワークを切ってコールドスタート。ログイン画面が完全に描画されれば、ゲーム本体とアセットは手元にあり、邪魔をしているのはログイン層だけです。アセットバンドルの一部区間だけが暗号化されている場合は、ブロックごとに調べて暗号化されたウィンドウを正確に特定します。ルールがすべてクライアント内にあるミニゲームは PC 上でヘッドレス実行できるので、全ステージを一度に検証できます。詳しくは [`recon.md`](../skills/offline-game-revival/references/recon.md) と [`playtest.md`](../skills/offline-game-revival/references/playtest.md) を参照してください。 |
| 🧩 **アンカー検証つきパッチ** | ビルドの入口はひとつだけ。コードの置換はすべて自分のアンカーを検証するので、元パッケージが変わったときは、気づかないうちに壊れたパッチを出荷するのではなく、*その場で派手に失敗*します。 |
| 🖥️ **ローカル偽サーバー** | HTTP/JSON 層を横取りし、何百ものエンドポイントをローカルのセーブデータから返します。各エンドポイントの呼び出し元と読み取り内容を洗い出し、安全なデフォルト値を生成する方法論つき。 |
| 📦 **再パッケージ＆再署名** | エンジンのキャッシュチェックサムの再計算、リソーステーブルの再構築、zipalign、署名まで対応。リバースエンジニアリングで解明したキャッシュチェックサムのアルゴリズムと、LayaAir native 用ローダーパッチも収録。 |
| ✅ **実機での受け入れテスト** | 「画面が開く」は「動く」ではありません。状態が実際に変化し、コールドリスタートを越えて残ることを確認します。チュートリアル駆動テストでは、ゲーム自身のガイドの手順どおりに、実際のタップで進めます。 |
| 🛡️ **安全なリリース** *(新機能)* | 公開前に、以前の公開ビルドをインストールしてセーブデータを作り、その上からアップグレードして、セーブのキーを一つずつ突き合わせます。ユーザー自身のスマホにインストールするときは、先にセーブデータをバックアップし、あとでバイト単位で比較します。パッケージ名を変えて、記念版が公式アプリと並べてインストールできるようにします。詳しくは [`verify.md`](../skills/offline-game-revival/references/verify.md) と [`patch.md`](../skills/offline-game-revival/references/patch.md)（第 5 節）を参照してください。 |
| 🎞️ **スクリーンショット・録画からのデータ救出** *(新機能)* | ショップの価格、ガチャの排出率、報酬、カードのステータスなど、サーバー側の数値はサーバーと共に消えます。`scripts/harvest.py` は、**数十 GB ものプレイヤーのスクリーンショットや画面録画**を、分類済みの数百 KB のテキストに変換します。キーフレーム抽出 → 類似画像の除去 → ローカル OCR → 画面ごとのグルーピング、という流れで、**完全オフライン・トークン消費ゼロ**。そのうえで `scripts/llm_structure.py` が、DeepSeek / OpenAI / Qwen / Kimi / ローカルの Ollama にまとめて投げ、結合した JSON と CSV にします。 |
| ⏩ **タイムトラベルテスト** *(新機能)* | `scripts/timewarp` は、偽サーバーを仮想時計つきのサンドボックスで動かします。数日分の時間を早送りし、アプリを再起動し、**すべての報酬を監査**します。レスポンスに「ジェム +50」とあるのにセーブデータが変わっていなければ、テストは失敗。30 日分のプレイを 1 秒でシミュレートし、各ゲートが何日目に到達可能になるかも確認できます。依存ライブラリはゼロ。 |
| 🤝 **どのエージェントでも、どのモデルでも** *(新機能)* | `SKILL.md` と `AGENTS.md` により、Claude Code、Codex、Cursor、Copilot、OpenCode、Gemini CLI などで動作します。scout / worker / verifier のサブエージェントの役割を同梱しているので、高価なモデルが判断を下し、安価なモデルが下働きを担当できます。エージェントがまったくなくても大丈夫。`prompts/chat-playbook.md` を DeepSeek / ChatGPT に貼り付けて、返ってきたコマンドを実行するだけです。 |
| 🚦 **着手 → バッチ進行 → 独立 QA** *(新機能)* | 何日も無人で走らせる大きなプロジェクト向け。最初に 2 分で済む事前承認シートを用意し、あとは 1 バッチずつ、厳しい時間枠（調査 2 ラウンド、または進展なしで 45 分 → 記録して次へ）で進めます。最後は別セッションが検収し、開発側の「全部グリーン」を信用しません。甘い合格は格下げ、全ボタンを巡回、戦闘は勝ちも負けも台帳と照合、取引の途中でプロセスを強制終了、仮想時計で 10 日、そしてデータを消し・ホットアップデート用フォルダを空にし・ネットを切った状態でコールドスタートを 2 回。事前承認シート、引き継ぎ、進捗マトリクス、バグ一覧のテンプレートも付属します。 |
| 🧭 **エンジン別ルート** *(新機能)* | アーキテクチャごとに 1 ページ。スクリプト層のない Unity IL2CPP（同一プロセスに Python のループバックサーバーを組み込み）、Unity Mono / ET / HybridCLR（パッケージ内の C# サーバー）、Cocos JS / Lua / LuaJIT + Protobuf（メモリ内ループバック、薄い Activity で引き継ぎ）、Unity WebGL / H5 マイクロクライアント（まず H5 で動かし、ラッパーは最後、元の DLL は戦闘計算用に常駐）。 |
| 🧰 **調査・ガード用スクリプト** *(新機能)* | Python 標準ライブラリのみ。読み取り専用で APK を一括調査（エンジン、ABI、ZIP32 の上限、パッカー、UnityFS の接頭辞、マニフェスト差分）、1 台専用のデバイスロックと非 ASCII パスでも安全な push、ジャンクションをたどらないディスク容量ヒューズ、ログ判定、apktool なしで `INTERNET` 権限を除去、保存済み音声を無圧縮のまま保つ APK エントリ置換、そして `adb kill-server` や `svc wifi disable` など他プロジェクトのエミュレーターを壊すコマンドを止める任意のフック。 |
| 📚 **失敗台帳** | 実際にハマった落とし穴を約 230 KB・300 項目近く分収録。症状 → 根本原因 → 対処の順に整理しています。起動時のレースによるクラッシュ、いつの間にか画面外へ消える UI、偽レスポンスで「汚染」されるプール済み XHR オブジェクト、ディスクに書き込まれないセーブデータ……。 |

## 🏆 実在のゲームで実証済み

このノウハウは、サーバーが停止した商用モバイルゲーム 16 本の復活作業から抽出したものです。

- **ケース A — Unity + Lua**：完全なシングルプレイ記念版。実機の Android 14 端末で動作確認済み。
- **ケース B — LayaAir native + JavaScript**：サーバーの 315 エンドポイントをローカルで再実装し、700 以上のリグレッションアサーションを用意。主要システム（ストーリーの各章、バトル、ガチャ、ペット、デート、タワー、イベント）をすべて実機で通しプレイして確認しました。
- **ケース C — Unity マイクロクライアント（Mono + SLua）**：APK に入っていたのはリソースの約 4 分の 1 だけで、残りはプレイヤーのスマホのバックアップから復元。Mono アセンブリの半暗号化とパッカーに対処し、ローカルサーバーはすべて Lua で実装。
- **ケース D — ネイティブ Kotlin + Live2D の AI チャット**：中心機能のキャラクターとのチャットは運営サーバー上の LLM 頼みだった。接続先をプレイヤー自身の OpenAI 互換 API またはローカルモデルに変え、ゲーム本編のセリフから作ったキャラクターカードと口調サンプルでキャラ崩壊を防止。モデル未設定時はボイス付きの原作セリフで返答。
- **ケース G — LayaAir + 長時間接続の sproto プロトコル**：ゲームの全体が APK に入っていたので、作業はサーバー側。パッケージに独自のプロトコルスキーマ（400 以上のリクエスト）が同梱されており、各システムをローカルで 1 つずつ再構築。ゲーム内ガイドに実際のタップで従う自動プレイスクリプトで、次の足りないシステムを見つけた。得られた教訓の大半は失敗台帳に収録：何も入っていないデフォルト返答が機能を黙ってロックする、受け取り拒否がプレイヤーに意味不明なエラーを見せる、偽の「仮想プレイヤー」が壊れて見える。
- **ケース H — Unity IL2CPP のカードゲーム、スクリプト層なし**：ゲーム自身のプロセスに組み込んだ Python ランタイムをローカルサーバーにし、セーブは SQLite、Web の GM ページも付けました。847 プロトコル、18 システム、133 イベントをすべて実装し、「稼働中のサーバー」らしさを保つ AI プレイヤーも 120 人用意。
- **ケース I — Unity WebGL / H5 マイクロクライアント**（237 KB の APK、仙侠）：まず H5 で動かし、ラッパーは最後。元の `Hotfix.dll` を戦闘計算用のワーカーとして常駐させたので、メインストーリー全体（990/990）と 9 回の天劫をすべてクリアでき、計算式は 1 つも変えていません。
- **ケース J — Unity Mono / ET Hotfix**（`code.unity3d` + `Hotfix.dll`）：パッケージ内に C# サーバーを持たせ、返答は 1 フレーム遅らせて返すので、UI が自分でデッドロックしません。
- **ケース K — Unity 2021 IL2CPP + HybridCLR**：全 15,550 個のバンドルに 22 バイトの二重ヘッダーが付いていましたが、暗号化ではなく接頭辞でした。本物のホットアップデート DLL と、削ぎ落とされた AOT メタデータ DLL も見分けています。
- **ケース L — Cocos Creator JS + Pomelo**：XXTEA + gzip のスクリプトと、パッケージ内のメモリ上ループバックサーバー。
- **ケース M — Cocos2d-Lua**：パッケージ内から Lua を配信し、開発中のホットプッシュは 0.3 秒。
- **ケース N — Cocos2d-x、Lua スレッド 2 本 + 生 TCP + protobuf**：ネットワーク層をメモリ内でループバック。負の `int32` 値と省略されるデフォルトフィールドを、送受信の両方向で修正。
- **ケース O — Cocos2d-x 2.x + LuaJIT 2.1 + 4.2 GB の拡張パック**：1 つの APK には大きすぎる（ZIP32 の制限）ため、データは APK の外に置き、薄い新規 Activity がランチャーを引き継ぎます。元の DEX には触れていません。
- **ケース P — Unity Mono**：長いパッチの連鎖ではなく、フラットなオーバーライドツリー。ホストには Mono.Cecil のアンカーパッチを当て、マニフェストから `INTERNET` をその場で削除。

もう 1 本は半日で断念しました。ゲーム本体は初回起動後にダウンロードする方式で、そのダウンロードがサーバーと一緒に消えていたためです。

ケース A–D と G は、完全なケーススタディ（匿名化済み）として [`references/`](../skills/offline-game-revival/references) にまとめています。ケース E と F はリファレンスファイルに、ケース H–P はエンジン別ルートのページ（`route-*.md`）、着手 → バッチ進行 → 独立 QA の流れ、失敗台帳に織り込んであります。

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

**何日もかかる大きなプロジェクト** — コピーして使える 3 つのプロンプト（読み取り専用の調査 → 着手から最終 QA まで → 中断後の再開）と、Antigravity への導入手順：[`prompts/three-stage-prompts.md`](../prompts/three-stage-prompts.md)。複数の PC で作業しているなら、[`prompts/merge-lessons.md`](../prompts/merge-lessons.md) で各 PC の教訓をまとめられます。

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

## ⚖️ 利用上の注意と免責事項

このリポジトリは、**ゲームの仕組みを学び、研究すること**と、公式サービスが終了したゲームを保存することを目的としています。含まれているのは手法と作者自作のツールだけです。

- **ここではダウンロードを提供していません。** このリポジトリには、ゲームの素材、ゲームのコード、復号鍵や署名鍵、インストールパッケージは含まれておらず、ダウンロードも提供していません。ここでのご依頼はご遠慮ください。
- **パッケージが広まらないようにしてください。** 作ったものは、ご自身が正当に入手したコピーについて、個人的かつ非営利の利用にとどめてください。改変したインストールパッケージ、ゲーム素材、鍵を公開したり転売したりせず、営利目的でプライベートサーバーを運営しないでください。
- **公式サービスが終了したゲームに限ります。** 運営中のゲーム、チート、アンチチートの回避、ほかのプレイヤーや権利者の利益を損なう用途には使わないでください。
- **お住まいの地域の法律を守り、自己責任でご利用ください。** 日本では、著作権法がプログラムの著作物を保護し、技術的保護手段の回避も制限しています。また、不正競争防止法により、プロテクトを無効化するツールや改造データの提供が違法となる場合があります。改変版の配布、プライベートサーバーの運営、チートの作成・販売は、民事・刑事上の責任を問われるおそれがあります。国や地域によって規定は異なります。本リポジトリの内容は法的助言ではなく、特定の利用が適法であることを示すものでもありません。判断に迷う場合は、始める前に弁護士にご相談ください。
- **いかなるゲーム会社とも無関係です。** ゲーム名や商標は各権利者に帰属します。本プロジェクトはいかなるゲーム会社とも提携しておらず、承認も受けていません。
- **無保証・免責。** 本リポジトリの内容は MIT ライセンスのもと「現状のまま」提供されます。法律で認められる最大限の範囲で、利用によって生じたいかなる損害、データの消失、アカウントへの措置、法的な結果についても、作者は責任を負いません。
- **権利者の方へ。** 本リポジトリの内容が権利を侵害しているとお考えの場合は、Issue でお知らせください。速やかに確認し、必要に応じて削除します。ゲームが公式に復活した場合は、公式版を応援してください。

本リポジトリの内容を利用した時点で、上記に同意したものとみなします。

## 🤝 コントリビュート

このスキルでゲームを復活させましたか？新しい落とし穴にハマりましたか？**新しいエンジンのケーススタディ**（Cocos、Unreal、Godot、IL2CPP など）や**失敗台帳への新しい項目**を添えた Issue や PR を、心よりお待ちしています。

大好きなゲームを救えたなら、⭐ をひとつ。ほかのプレイヤーがこのプロジェクトを見つける助けになります。

参加方法（Issue、プルリクエスト、共同メンテナーになるには）は [CONTRIBUTING.md](../CONTRIBUTING.md) を参照してください。

## ⭐ スターとクローン

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

[![Clone history](https://raw.githubusercontent.com/Cynthia-wlan9509/offline-game-revival/traffic/clones.svg)](https://github.com/Cynthia-wlan9509/offline-game-revival/blob/traffic/clones.csv)

GitHub が保持するクローンのトラフィックは 14 日分だけなので、クローンのグラフは 2026-11-03 のスナップショットから始まり、以降は毎日更新しています。

## 📄 ライセンス

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · Cocos · IL2CPP · HybridCLR · WebGL · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · タイムトラベルテスト · マルチエージェント · 時間経過テスト · サービス終了 · オフライン化 · ゲーム保存 · 配信終了 · 録画OCR · スマホゲー復活</sub>
