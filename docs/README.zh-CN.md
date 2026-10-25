<div align="center">

# 🎮 停服游戏复活术 · Offline Game Revival

### 让 AI Agent 把已经停服的手游，变成一台手机就能玩完的离线纪念版。

**服务器会关，游戏不该消失。**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

每年都有大批手游停服。安装包还躺在玩家手机里，可服务器一关，登录不了、读不了档、什么都做不了——那些剧情、角色和回忆，就这样再也打不开了。

**Offline Game Revival** 是一套在真实停服游戏上反复验证过的方法论，打包成 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)。把停服游戏的 APK 交给你的编程 Agent（Claude Code，以及其他能读 `SKILL.md` 的 Agent），它就知道怎么把它改成**独立运行的纪念版**：装上就能从头玩到尾，不联网、不 root、不依赖电脑、不靠运行时注入。

## ✨ 包含什么

| | |
|---|---|
| 🔍 **解包侦察** | 拆开 APK，找到真正的逻辑层（Lua / JS / C# 转译产物），摸清加密方式和资源完整性校验。 |
| 🧩 **锚点断言补丁** | 唯一构建入口，每一处代码替换都断言锚点存在——上游包一变，构建**大声失败**，绝不把静默失效的补丁发出去。 |
| 🖥️ **本地假服务器** | 拦截 HTTP/JSON 网络层，用本地存档回应几百个接口；附一套"先摸清每个接口的调用方读了哪些字段，再生成安全默认值"的方法。 |
| 📦 **重打包签名** | 重算引擎缓存校验、重建资源表、对齐、签名。含逆向得到的 LayaAir 原生缓存校验算法和加载器补丁。 |
| ✅ **真机验收** | "界面能打开"≠"功能能用"。状态必须真的变化、并且冷启动后依然正确；用游戏自己的新手引导步骤做真实点击验收。 |
| 🎞️ **从截图录屏里抢救数据**（新） | 商店价格、卡池概率、奖励、卡牌数值这些服务端配置会随停服消失。`scripts/harvest.py` 把玩家**几十 GB 的截图和录屏**在本地压成几百 KB 的分类文字——关键帧 → 近似去重 → 本地 OCR → 按界面分组——**全程离线、0 token**，再用 `scripts/llm_structure.py` 批量交给 DeepSeek / OpenAI / 通义 / Kimi / 本地 Ollama，合并成 JSON + CSV。 |
| ⏩ **时间快进测试**（新） | `scripts/timewarp` 把假服务器放进虚拟时钟沙箱：快进几天、模拟杀进程重开、**每次调用自动对账**——回包写着"获得 50 钻石"但存档没变就报错。一秒跑完 30 天游玩，看每道门槛第几天能过。零依赖。 |
| 🤝 **任何 Agent、任何模型**（新） | 通过 `SKILL.md` + `AGENTS.md` 支持 Claude Code、Codex、Cursor、Copilot、OpenCode、Gemini CLI 等；自带 scout / worker / verifier 三种子 agent 角色，贵模型做判断、便宜模型干体力活。没有 Agent？把 `prompts/chat-playbook.md` 贴进 DeepSeek / ChatGPT，照它给的命令跑就行。 |
| 📚 **失败账本** | 100 KB 真实踩坑记录：现象 → 根因 → 修法。启动竞态崩溃、被悄悄挪到屏幕外的 UI、被假回包"毒化"的复用 XHR、从没落盘的存档…… |

## 🏆 在真实游戏上验证过

这套方法提炼自两款已停服商业手游的完整复活：

- **案例 A —— Unity + Lua**：完整单机纪念版，在 Android 14 真机上验收。
- **案例 B —— LayaAir 原生 + JavaScript**：本地重写 315 个服务端接口，700+ 条回归断言，主线、战斗、抽卡、宠物、约会、爬塔、活动等主要系统逐项真机点通；另有离线授权码（Ed25519，无需 BigInt）和按份水印，方便小范围私下分享。

两个案例都已脱敏收录在 [`references/`](../skills/offline-game-revival/references)。

## 💸 花了多少

大部分工作是用 Claude Code（订阅制）完成的。为了让大家对规模有个数，下面是本地会话记录（含子代理）里的 token 用量，按 Anthropic API 标价折算成钱——只是折算，不是实际扣费，实际付的是订阅费。

| 案例 | 天数 | token | 按 API 标价折算 |
|---|---|---|---|
| A —— Unity + Lua | 18 | 74 亿 | ≈ $2,140（约 1.5 万元） |
| B —— LayaAir 原生 + JS | 9 | 26 亿 | ≈ $720 |
| C —— Unity 微端（Mono + SLua） | 5 | 23 亿 | ≈ $620 |
| 游戏复活合计（A + B + C，外加一款只侦察了一天的） | | 124 亿 | ≈ $3,500（约 2.5 万元） |

表里只算 Claude。算上下面的 Codex 阶段，总计约 $3,900（约 2.8 万元）。

- 98.5% 是缓存读取：AI 每一轮都要把前面的对话重新读一遍，这部分单价很低。AI 真正写出来的只有约 3500 万 token。（这两个数按同期全部 Claude 用量 141 亿 token 统计，没有按案例拆。）
- 案例 A 早期有约 10 天是在 Codex 里跑的，背后接的是 DeepSeek V4.1 Flash 和 GPT-6 Astra，一共约 22.5 亿 token，按标价约 $420（约 3,000 元）。其中 DeepSeek 约 20 亿 token，只要约 $27–54（约 190–380 元，按空闲价到高峰价）；GPT-6 Astra 约 2.6 亿 token，约 $387（约 2,750 元）。
- 统计截至 2026-10-25，汇率按 1 美元 ≈ 7.1 元。

## 🚀 安装

**Claude Code（插件市场）**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**支持 Agent Skills 的 Agent**（Claude Code、OpenAI Codex、Cursor、GitHub Copilot、OpenCode、Goose……）——把目录复制进对应的 skills 目录：

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

其它 Agent 会读仓库根目录的 [`AGENTS.md`](../AGENTS.md)，由它指向 skill。子 agent 角色在 [`agents/`](../agents)。

**只有聊天网页（DeepSeek / ChatGPT / Kimi）**——第一条消息贴 [`prompts/chat-playbook.md`](../prompts/chat-playbook.md)，模型就成了你的主程，你按它给的命令跑、把输出贴回去。

然后直接说：*"这个游戏停服了，帮我做成离线版"*，或者 *"从这 15 GB 录屏里把商店价格和卡池概率整理出来"*。

## 🎞️ 单独使用：从录屏里抢救数据

不需要 Agent 也能用：

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./玩家录屏 ./out --limit 50   # 先试跑
python skills/offline-game-revival/scripts/harvest.py ./玩家录屏 ./out              # 全量，可中断续跑
export DEEPSEEK_API_KEY=sk-...                                                       # PowerShell：$env:DEEPSEEK_API_KEY="sk-..."
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2           # 先结构化 2 块看质量
python skills/offline-game-revival/scripts/llm_structure.py ./out                     # 全量 → out/structured/merged.json
```

- **只留有用的帧**：画面"变了而且停稳了"才保留，跳过转场动画和拖影；长列表滚动也会定时取帧。
- **跨来源去重**：同一个界面的截图和录屏帧会合并（忽略状态栏的时间电量）。
- **本地 OCR**（RapidOCR / ONNX，纯 CPU，中日韩英），带坐标和阅读顺序。
- **输出**：`for_llm/*.txt` 分块 + 现成的提示词和 JSON 格式，见 [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md)；`llm_structure.py` 合并所有回答并标出互相矛盾的数值。

## ⏩ 单独使用：时间快进测试

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 项通过
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # 抓出 3 个埋好的 bug
```

把 `timewarp.create({ files, entry, inventory, granted })` 指向你自己的假服务器即可。值得测的时间类 bug 清单（重置时刻、签到循环、回复上限、计时、重启持久化）见 [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md)。

## 🌙 夜间值班（第二个 skill）

[`skills/night-shift`](../skills/night-shift/SKILL.md) 让 agent 在你睡觉或离开几个小时的时候，自己把一份待办清单往前推。把填空模板 [`NIGHT-RUN.md`](../skills/night-shift/templates/NIGHT-RUN.md) 复制进项目，过一遍两分钟的开跑前检查，然后不给间隔地启动 `/loop`。之后 agent 自己定醒来节奏，一次只做一项，体力活交给子代理；每个「完成」都要有证据、单独提交。要问你的事先用最保守的默认值，最后交一份五段式报告。和游戏无关的项目也能用。

在 case C 上，第一晚 4 个多小时，模拟器上验证了 11 项，每项都有截图或日志和提交，派了 5 个 worker，用了一个 5 小时额度窗口的一半左右；另一晚让它在模拟器上乱点 3000 次，0 闪退。

它依赖 Claude Code 桌面版的能力（`/loop`、`ScheduleWakeup`、`request_keep_awake`、`get_usage`、`start_session`）；缺了哪个怎么退化，skill 里写了（纯命令行里没有并行会话，就改用子代理）。插件安装会一起装上；手动复制：`cp -r offline-game-revival/skills/night-shift ~/.claude/skills/`。

## 🧭 核心理念

1. **在打包期改脚本，不在运行时注入。** 能跑通的 Frida 脚本也永远离不开注入；写进包里的改动装上就能用。
2. **单一入口 + 锚点断言。** 静默跳过会把坏包发出去。
3. **产物不是源码。** 改补丁脚本，永远不要手改输出。
4. **"能打开"不等于"能用"。** 验证状态变化、扛住重启，把"已验证"和"仅实现"分开写。

## ⚖️ 负责任地使用

本项目只关于**游戏保存**：让游戏在**官方服务结束之后**依然能玩。

- 只用于官方服务器**已永久关闭**的游戏。不要用于仍在运营的游戏，不要用来作弊、绕过反作弊或影响其他玩家。
- 本仓库**不包含任何游戏资源、游戏代码或密钥**，只有方法和作者自己的工具。
- 尊重版权：纪念版请私下、非商业地保存，遵守你所在地区的法律。如果版权方重新上线游戏，请支持官方版本。

## 🤝 参与贡献

用这个 skill 复活了一款游戏？踩到了新坑？非常欢迎提交**新引擎案例**（Cocos、Unreal、Godot、IL2CPP……）和**失败账本新条目**的 Issue / PR。

如果它帮你救回了一款心爱的游戏，点个 ⭐ 能让更多玩家找到它。

## 📄 许可证

[MIT](../LICENSE)

<sub>关键词：时间快进测试 · 多 Agent 分工 · DeepSeek · ChatGPT · Codex · 停服游戏 · 游戏停服 · 单机化 · 离线版 · 纪念版 · 私服替代 · 游戏保存 · 手游复活 · APK 重打包 · Lua · LayaAir · Unity · 录屏抽帧 · 截图 OCR · Claude Code skill · Agent Skills · game preservation · shut down game · offline mode</sub>
