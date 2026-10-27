<div align="center">

# 🎮 Offline Game Revival

### 讓停服手遊重獲新生的 AI Agent 技能——完全離線，直接在真機上執行。

**伺服器可以關，遊戲不該死。**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

每年都有數以百計的手機遊戲宣布停止營運。APK 還留在玩家的手機裡，但少了伺服器，就無法登入、讀不到存檔，什麼也做不了。多年來的故事、角色與回憶，從此再也碰不到。

**Offline Game Revival** 是一份身經百戰的實戰手冊，並封裝成 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)。只要讓你的程式開發 Agent（Claude Code，以及其他會讀取 `SKILL.md` 的 Agent）去處理一款已停服遊戲的 APK，它就知道怎麼把它變成**獨立運作的紀念版**：裝上 APK 就能玩完整款遊戲，不用網路、不用 root、不用電腦，也不需要執行期注入。

## ✨ 內容總覽

| | |
|---|---|
| 🔍 **偵察分析** | 解開 APK、找出真正的邏輯層（Lua / JS / 轉譯後的 C#），辨識加密與資源完整性檢查。 |
| 🧩 **錨點斷言式修補** | 只有單一建置入口。每一處程式碼替換都會斷言自己的錨點——上游封包一旦變動，建置會*直接大聲失敗*，而不是悄悄產出一個壞掉的修補。 |
| 🖥️ **本機假伺服器** | 攔截 HTTP/JSON 層，以本機存檔回應數以百計的 API 端點。內含一套方法：逐一釐清每個端點由誰呼叫、讀了什麼，再產生安全的預設回應。 |
| 📦 **重新封裝與簽章** | 重新計算引擎快取的校驗碼、重建資源表、zipalign、簽章。內含逆向還原出的快取校驗碼演算法，以及針對 LayaAir native 的載入器修補。 |
| ✅ **真機驗收** | 「畫面開得起來」不等於「真的能玩」。狀態必須真的改變，而且冷啟動後依然保留。以教學引導驅動測試：照著遊戲自己的新手引導步驟，用真實點擊一步步走完。 |
| 🎞️ **從截圖與錄影搶救資料** *(新)* | 伺服器端的數值（商店價格、抽卡機率、獎勵、卡牌數據）會隨伺服器一起消失。`scripts/harvest.py` 能把**數十 GB 的玩家截圖與螢幕錄影**，濃縮成幾百 KB 分好類的文字——關鍵影格 → 去除近似重複 → 本機 OCR → 依畫面分組——**全程離線、零 token**，再用 `scripts/llm_structure.py` 批次交給 DeepSeek / OpenAI / 通義 / Kimi / 本機 Ollama，合併成 JSON + CSV。 |
| ⏩ **時間快轉測試** *(新)* | `scripts/timewarp` 把你的假伺服器放進虛擬時鐘沙盒：快轉好幾天、模擬重啟 App，並**逐筆稽核每一項獎勵**——回應寫著「獲得 50 鑽石」但存檔沒變，就判定失敗。一秒鐘模擬 30 天的遊玩，看每道關卡門檻在第幾天才解得開。零相依套件。 |
| 🤝 **任何 Agent、任何模型** *(新)* | 透過 `SKILL.md` + `AGENTS.md`，支援 Claude Code、Codex、Cursor、Copilot、OpenCode、Gemini CLI 等。內附 scout / worker / verifier 三種子 Agent 角色，讓昂貴的模型負責決策、便宜的模型負責跑腿。完全沒有 Agent？把 `prompts/chat-playbook.md` 貼進 DeepSeek / ChatGPT，照它給的指令執行就行。 |
| 📚 **失敗紀錄簿** | 100 KB 的真實踩坑紀錄：症狀 → 根本原因 → 解法。包括啟動競態造成的崩潰、UI 悄悄跑到畫面外、被假回應「毒化」的池化 XHR 物件、永遠寫不進磁碟的存檔…… |

## 🏆 經過真實遊戲驗證

這套實戰手冊，提煉自兩款已停服的商業手遊的復活過程：

- **案例 A——Unity + Lua**：完整的單機紀念版，已在實體 Android 14 手機上驗證。
- **案例 B——LayaAir native + JavaScript**：在本機重新實作 315 個伺服器端點、700 多條回歸斷言，所有主要系統（劇情章節、戰鬥、抽卡、寵物、約會、爬塔、活動）都在實機上逐一點過。

兩份案例研究（已匿名處理）都收錄在 [`references/`](../skills/offline-game-revival/references)。

## 🚀 安裝

**Claude Code（外掛市集）**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**任何支援 Agent Skills 的 Agent**（Claude Code、OpenAI Codex、Cursor、GitHub Copilot、OpenCode、Goose……）——把資料夾複製到該 Agent 的 skills 目錄即可：

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

其他 Agent 會讀取 [`AGENTS.md`](../AGENTS.md)，由它指向這個技能。子 Agent 角色放在 [`agents/`](../agents)。

**只有聊天網頁（DeepSeek / ChatGPT / Kimi）**——第一則訊息貼上 [`prompts/chat-playbook.md`](../prompts/chat-playbook.md)，模型就會成為你的主工程師；你照它給的指令執行，再把輸出貼回去。

接著直接開口：*「這款遊戲的伺服器關了——幫我做成可以離線玩的版本」*，或是 *「從這 15 GB 的螢幕錄影裡，把商店價格和抽卡機率整理出來。」*

## 🎞️ 從螢幕錄影搶救資料（獨立使用）

這個擷取工具不需要任何 Agent 就能運作：

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # 或 OPENAI_API_KEY、DASHSCOPE_API_KEY…（PowerShell：$env:DEEPSEEK_API_KEY="sk-..."）
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # 先結構化 2 塊，檢查品質
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # 全量 → out/structured/merged.json
```

- **只留下有意義的關鍵影格**：只有當畫面*發生變化並且穩定下來*時才保留影格——跳過轉場動畫與動態模糊；很長的捲動清單仍會被取樣。
- **跨來源去重**：同一個畫面無論來自截圖或錄影，都會合併（忽略狀態列）。
- **本機 OCR**（RapidOCR / ONNX，僅需 CPU，支援中日韓與拉丁字母），並附帶文字框位置與閱讀順序。
- **輸出內容**：`for_llm/*.txt` 分塊文字，外加一份現成的提示詞與 JSON schema，見 [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md)；`llm_structure.py` 會合併所有回答，並標出互相矛盾的數值。

## ⏩ 時間快轉測試（獨立使用）

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 項通過
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # 抓出 3 個預先埋好的 bug
```

把 `timewarp.create({ files, entry, inventory, granted })` 指向你自己的假伺服器即可。值得測試的時間類 bug 清單（重置時刻、簽到迴圈、恢復上限、計時器、重啟後的持久化）見 [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md)。

## 🧭 設計理念

1. **在建置階段修補，而不是在執行期。** 一支「能用」的 Frida 腳本，得永遠靠注入才能運作；直接寫進安裝包的改動，裝了就能用。
2. **單一入口 + 錨點斷言。** 靜默略過的替換，只會產出壞掉的版本。
3. **產物不是原始碼。** 要修就修修補腳本，絕不手動改輸出檔。
4. **「打得開」不等於「能運作」。** 要驗證狀態確實改變、重啟後依然存在，並寫清楚哪些已驗證、哪些只是寫完了。

## ⚖️ 使用須知與免責聲明

本倉庫僅供**學習與研究遊戲軟體的設計思想與原理**，以及保存官方服務已經結束的遊戲。這裡只有方法和作者自己寫的工具。

- **這裡不提供下載。** 本倉庫不含遊戲資源、遊戲程式碼、解密或簽章金鑰，也不含任何安裝包，不提供下載，請不要在這裡索取。
- **請勿讓安裝包隨意擴散。** 做出來的東西請僅用於你合法取得的副本，個人、非商業使用。請不要公開發布或轉賣改版安裝包、遊戲資源與金鑰，不要架設私服牟利。
- **只用於官方服務已經結束的遊戲。** 請不要用於仍在營運的遊戲，不要用來作弊、規避反作弊，或做損害其他玩家與權利人利益的事。
- **遵守你所在地的法律，後果自負。** 在台灣，《著作權法》保護電腦程式著作，並禁止破解、破壞或規避防盜拷措施；未經授權散布改版遊戲、架設私服、製作或販售外掛，可能涉及民事與刑事責任。其他國家與地區的規定各不相同。本倉庫內容不構成法律意見，也不代表任何特定用法是合法的；如有疑問，請先諮詢律師。
- **與任何遊戲公司無關。** 遊戲名稱與商標歸各自權利人所有。本專案與任何遊戲公司無關，也未獲其認可。
- **不提供任何擔保。** 本倉庫內容依 MIT 授權「按現狀」提供。在法律允許的最大範圍內，因使用本倉庫內容造成的任何損失、資料遺失、帳號處分或法律後果，作者概不負責。
- **權利人請與我們聯繫。** 如果你認為這裡的內容侵害了你的權利，請提交 Issue，我們會盡快查核處理，必要時移除。遊戲若官方回歸，請支持正版。

使用本倉庫的內容，即表示你已閱讀並同意以上條款。

## 🤝 參與貢獻

用這個技能復活過一款遊戲嗎？踩到新的坑了嗎？非常歡迎透過 Issue 和 PR 提交**新引擎的案例研究**（Cocos、Unreal、Godot、IL2CPP……）以及**失敗紀錄簿的新條目**。

如果它救回了一款你深愛的遊戲，點個 ⭐ 能幫助更多玩家找到它。

怎麼參與（提 Issue、提 PR、成為共同維護者）：見 [CONTRIBUTING.md](../CONTRIBUTING.md)。

## ⭐ 收藏數變化

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

## 📄 授權

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · 時間快轉測試 · 多 Agent 協作 · 多模型協作 · 停服遊戲 · 遊戲停運 · 單機化 · 離線版 · 遊戲保存 · 螢幕錄影 OCR</sub>
