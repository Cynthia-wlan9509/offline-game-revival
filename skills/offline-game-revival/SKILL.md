---
name: offline-game-revival
description: "Turn shut-down / server-dead mobile games into fully offline, playable preservation builds: unpack & recon, locate the script logic layer (Lua / JS / IL2CPP), anchor-asserted patches, local fake server, repack & re-sign, on-device acceptance, and recovering lost game data from players' screenshots and screen recordings. 把停服或断网的手游改造成可离线运行的纪念版：解包侦察、定位脚本逻辑层（Lua / JS / IL2CPP）、锚点补丁、本地回包、重打包签名、真机验收，以及从玩家截图和录屏中找回丢失的游戏数据。当用户要求离线化、单机化、复活一个已停服的游戏，继续维护/重建一个已离线化的 APK，或要从截图、录屏里还原停服游戏的数值和资料时使用。"
metadata:
  short-description: 停服手游离线化改造
---

# 离线化改造（Offline Game Revival）

把"服务端已死"的游戏改成"只装 APK、不联网、不 root、不依赖电脑"的纪念版。

## 核心判断

**在打包期改脚本，不要在运行时注入。**

运行时方案（Frida / hook / 内存补丁）无论调得多通，都留下"必须运行中注入"的外部依赖，用户拿到手就废了。脚本层（Lua / JS / C# 转译产物）的改动写在包里，安装即用。这条决定了整个技术路线：先把逻辑层从包里挖出来，再在打包期改写它。

## 工作顺序

1. **侦察** — 解包，定位逻辑层（脚本 / 数据 / 资源），确认加密与校验方式。**第一天就拿资源清单对一遍包里的文件**：微端/分包游戏的 APK 可能只带一小部分资源，缺的那部分随服务器一起没了，资源从哪来要先问用户，再动代码。→ `references/recon.md`
2. **定补丁点** — 找出必须拦截的入口：启动流程、登录、网络发送、资源校验、进度存档。
3. **写补丁** — 锚点替换 + 断言，逻辑放独立模块，打标记。→ `references/patch.md`
4. **时间快进自测** — 上真机之前，把假服务器放进虚拟时钟沙箱：每日重置、签到、体力、计时、限购、重启持久化，并对账"回包说给了的东西存档里真有"。→ `references/timewarp.md`（`scripts/timewarp/`）
5. **重打包** — 合并资源、替换产物、修正校验字段、签名、对齐。
6. **真机验收** — 断网冷启动、全链路功能、杀进程重启。→ `references/verify.md`
7. **正常游玩复测** — 功能都通了之后，从全新档按玩家顺序玩一遍，量资源和门槛（可先用 timewarp 的 `simulate` 跑 30 天经济曲线）。→ `references/playtest.md`
8. **数值与内容抢救** — 服务端配置随停服消失，用玩家截图/录屏还原：本地抽帧 + 去重 + OCR（`scripts/harvest.py`，0 token）→ 任意便宜文本模型批量结构化（`scripts/llm_structure.py`）→ 写进数值表。
   语音通话、聊天短信这类剧情配置另有一套：音轨对齐认通话、声纹定归属、本地 ASR 补字幕、截图逐图人工校对；每项标 `[实测]/[推断]/[语音识别]/[自造]`。→ `references/media-harvest.md`
   同时拿配置清单对镜像做差集，找"文件还在、终版没登记"的被埋没内容（案例见 `references/case-b-laya-native.md`）。
9. **固化** — 把"已实现"和"已验证"分开写，记录失败账本。

## 分工

量大的阶段（接口清单、按模块实现假服务器、读长日志、OCR 结构化）适合拆给子 agent 并行：主 agent 做判断和收货，
worker 按规格实现，scout 只读搜索。交接格式、各阶段怎么拆、在不同工具（含只有聊天网页的 DeepSeek / ChatGPT）里怎么落地：
`references/multi-agent.md`。子 agent 交回的结论要自己复核后再告诉用户。

## 四条硬规则

1. **单一主入口 + 锚点断言。** 所有代码改动集中在一个构建期脚本里，每处替换都配 `assert`。源包一变就必须构建失败，绝不允许静默跳过——静默跳过会让"看起来成功"的包带着没生效的补丁发出去。

2. **逻辑放模块，不放生成物。** 补丁逻辑写在独立的脚本模块里，由主入口拼接。不要直接编辑反编译产物、解包目录或构建输出；它们下次构建就被覆盖。

3. **产物不是源码。** 打出来的 APK、bundle、解包目录、日志都是可再生的。修 bug 去改补丁脚本，不要"手工修一下包里的文件"——手工修的东西一旦产物被删就永久丢失，无法追溯。

4. **"界面能打开"不等于"功能完成"。** 只有状态真的变了（数量、进度、可领取→已领取，且杀进程重启后仍然正确）才算通过。未验证的项一律写成"代码已实现，真机待验证"。

## 常见失败模式

微端资源不全（包里只有一部分）、跨域 UI 层级残留、资源校验失败、存档不持久、离线网络层抛异常打断调用方、配置表未就绪就进游戏、文档漂移导致新 Agent 走旧链路、交付包与源码基线不一致（装了旧包）、放行类开关硬编码导致校验静默失效、真机存档读写卡顿（每次变更读好几个大 blob，模拟器看不出，还容易误诊成 Save 慢）、"离线版"一联网就被原生 SDK 带着往外发设备信息（测试都在断网下做所以看不到；去掉 INTERNET 权限并在发包检查里拦）。逐条见 `references/pitfalls.md`。
复活下线活动时另有一类：终版客户端把界面"藏"了（入口挪到屏外、入场动画删半截、布局和图集错配）、离线后付费兜底消失把原版数据缺陷放大成卡死、
共用图集被后一期活动覆盖（图还在但已是别的图、九宫格按旧图配会坏）、两期活动共用接口且 id 撞号——见 `references/case-b-laya-native.md`。

## 参考

- `references/recon.md` — 侦察：从 APK 到可改写逻辑层
- `references/patch.md` — 锚点补丁与重打包
- `references/verify.md` — 真机验收闭环
- `references/playtest.md` — 全新档正常游玩复测、门槛分项记录、数值校准顺序
- `references/media-harvest.md` — 从玩家截图/录屏抢救数值：抽关键帧、去重、本地 OCR、分类、交给文本模型的提示词与 JSON 格式；还原语音通话和聊天短信（第 4 节）
- `scripts/harvest.py` — 上面流程的脚本（OpenCV + RapidOCR，可中断续跑）
- `scripts/llm_structure.py` — 把 OCR 分块批量交给任意 OpenAI 兼容模型（DeepSeek / OpenAI / 通义 / Kimi / Ollama）结构化并合并
- `references/timewarp.md` — 时间快进测试：虚拟时钟、重启持久化、奖励对账、N 天经济模拟（`scripts/timewarp/`，Node 零依赖）
- `references/multi-agent.md` — 主 agent / worker / scout 分工与交接格式
- `references/pitfalls.md` — 失败账本（现象 → 原因 → 修法）
- `references/distribution.md` — 发新包不丢存档、一种包按授权码分档、活动开期、玩家自定义内容、存档迁移
- `references/case-a-unity-lua.md` — 完整案例：案例 A（Unity + Lua 手游）离线纪念版
- `references/case-b-laya-native.md` — 案例 B（LayaAir 原生 + JS 的剧情养成卡牌手游）：DCC 缓存校验算法、加载器补丁、启动竞态、本地服务器骨架；授权码、分档、复活隐藏活动、手机通话 / 短信、被埋没的支线和自制资源、正式包验收
- `references/case-c-micro-client.md` — 案例 C（大厂微端，Unity Mono + SLua）：资源清单对账、Lua 头字节、Mono 程序集半加密与 PE 头重建、加固壳的去除（改 dex 开关 + 从进程内存导出明文程序集）、launchconf 开关、用探针包让游戏自带的云 SDK 自己探测服务器；五层开屏 / 协议页换成免责声明（引擎开屏、C# 播的视频、剧情 CG 开头）；整个写在 Lua 里、回包不序列化的本地服务器（属性袋冒充字节流）；从玩家手机备份（小米 `.bak` = 头 + Android Backup + tar）补齐全部资源、换成终版底包、把热更层（Lua、清单、热更过的包内资源）并进 APK，避开微端首启清理