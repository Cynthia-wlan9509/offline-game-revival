---
name: offline-game-revival
description: "Turn shut-down / server-dead mobile games into fully offline, playable preservation builds: unpack & recon, locate the script logic layer (Lua / JS / IL2CPP), anchor-asserted patches, local fake server, repack & re-sign, on-device acceptance, and recovering lost game data from players' screenshots, screen recordings and phone backups. Also use when a game is about to shut down (first check how far the shutdown has gone), and when distributing an offline build (license tiers, save migration) and handling player bug reports. 把停服或断网的手游改造成可离线运行的纪念版：解包侦察、定位脚本逻辑层（Lua / JS / IL2CPP）、锚点补丁、本地回包、重打包签名、真机验收，以及从玩家截图和录屏中找回丢失的游戏数据。当用户要求离线化、单机化、复活一个已停服的游戏，判断一款停服游戏还能不能救，继续维护/重建一个已离线化的 APK，或要从截图、录屏里还原停服游戏的数值和资料时使用。"
metadata:
  short-description: 停服手游离线化改造
---

# 离线化改造（Offline Game Revival）

把"服务端已死"的游戏改成"只装 APK、不联网、不 root、不依赖电脑"的纪念版。

## 核心判断

**在打包期改脚本，不要在运行时注入。**

运行时方案（Frida / hook / 内存补丁）无论调得多通，都留下"必须运行中注入"的外部依赖，用户拿到手就废了。脚本层（Lua / JS / C# 转译产物）的改动写在包里，安装即用。这条决定了整个技术路线：先把逻辑层从包里挖出来，再在打包期改写它。注入是借来的命，写进包里的才是自己的。

## 第 0 步：先判断能不能救（半天内给结论）

不是所有游戏都救得回来。先搜停服公告、问用户停服到了哪一步：还没关服就只做技术侦察，离线版等官方服务结束再发（`references/recon.md` 第 1 节）。再回答三个问题，写成半页结论交给用户拍板：

1. **规则在不在手机里？** 剧情、养成、卡牌这类，规则大多写在客户端脚本里，服务器只管存档和发奖，希望很大。
   战斗、抽卡结果由服务器算、客户端只负责播放的，离线版就得自己重写这部分规则。判断办法：在脚本里找战斗结算的回包处理，
   看客户端是"自己算完再上报"，还是"等回包里的结果（整场伤害序列、胜负、掉落）再播放"。
2. **本体在不在包里？** 拿游戏自己的资源清单和 APK 做差集（`references/recon.md` 第 1 节）。进游戏后才下载本体的微端，
   服务器一关本体就没了，只能找老玩家手机里的备份或缓存。
3. **服务器上的数据还能找回多少？** 商店价格、抽卡概率、活动配置常常只存在服务器上。先看玩家录屏、截图、攻略站能还原多少（第 8 步）；
   实在找不到可以自己编一套，但要在文档和游戏里标明"自造"，那就不算原汁原味了。

结论分三档：能原样复活 / 能玩，但部分规则是自造的 / 缺本体或缺核心规则，先停下征集材料。第三档别硬耗：
实例里一款 2023 年停服的游戏，拆包发现本体是进游戏后才下载的，半天就停了，转去向老玩家征集手机备份。

### 侦察脚本和开工三段式

第 0 步可以先跑 `python -B scripts/recon_apk.py <原包.apk> work/analysis`：只读，一次列出引擎、ABI（只有 32 位要先查模拟器支不支持）、
条目数和体积是否逼近 ZIP32 上限、加固壳和渠道 SDK 痕迹、`global-metadata.dat` 头、UnityFS 前缀（固定前缀不是加密）、资源清单差集。

项目大、要长时间无人值守时，按三段走，每段一页：
1. **开工** `references/kickoff.md` — 侦察 + 10 分钟破壳探针 → 按引擎选路线（`references/route-*.md`）→ 让用户花 2 分钟勾预授权单（`templates/KICKOFF-AUTH.md`，常用默认值见 `references/policy-presets.md`）→ 建 Git、锁唯一测试设备、磁盘熔断 → 先搭秒级热推和命令桥，再写业务 → 跑通最小闭环（断网冷启 → 原版战斗打一关 → 账本对上 → 杀进程重启还在）。
2. **批次推进** `references/autopilot.md` — 一次只推一项，30–45 分钟或 2 轮探针没进展就记下换项；开发期只热推，攒够一批才打包；修一个 bug 补一条回归；交接文件 ≤ 120 行。
3. **独立终验** `references/independent-qa.md` — 换一个会话或子代理来验：先审"已通过"的含金量，再跑 T1–T5（全按钮遍历、文字体检、战斗胜负对账、满级档长测 + 事务中途强杀、10 天虚拟时钟 + 跨年），最后清数据、空热更、真断网连续冷启两次（核对 PID 变了）。

几台模拟器、几个项目共用一台电脑时，先读 `references/red-lines.md`；`scripts/guard_hook.py` 是可选的工具钩子，拦 `svc wifi disable`、`adb kill-server`、`ldconsole quitall` 这类会打断别人的命令。

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
10. **上线后收 bug**（自己做的游戏，或在授权下分发的版本、二创、同人）— 玩家在论坛发帖，机器人定时收集、归类，AI 复现、修复、起草回复，用户点头才发出去。→ `references/distribution.md` 第 7 节

## 分工

量大的阶段（接口清单、按模块实现假服务器、读长日志、OCR 结构化）适合拆给子 agent 并行：主 agent 做判断和收货，
worker 按规格实现，scout 只读搜索。交接格式、各阶段怎么拆、在不同工具（含只有聊天网页的 DeepSeek / ChatGPT）里怎么落地：
`references/multi-agent.md`。子 agent 交回的结论要自己复核后再告诉用户。

钱主要花在模型重读旧对话上（实测 98.5% 的 token 是这部分）。每轮结束写一份几 KB 的快照，下一轮开新会话读快照接着做；
单次工具输出控制在 8 KB 左右。做法见 `references/multi-agent.md`「省 token」。

## 和用户怎么配合

用户多半不写代码：用户说想要什么、看结果，不满意就接着说。拆包、写代码、装到设备上测，这些都是你的活。
要用户拍板的只有三类事：做到什么程度（第 0 步的结论）、缺的材料去哪找（玩家备份、录屏）、对外发什么（发包、回帖）。
汇报结果时带证据（截图、录屏、日志里的那一行），不要只说"已完成"。
对外说「修好了」时要拆开讲：能玩（粗修）、按反馈逐条修（精修）、完整还原原版，各给一个时间范围，并按「玩家看得出来的先做」分成上线前必须、建议上线前做、上线后补三档。给第三方（例如委托方自己的 AI）写交接提示词时，默认写短：东西放在哪、先看哪份说明、先做什么、动手前备份、哪些别动。严格的分步版本留在文件里，对方卡住了再给。

动用户机器的大动作（新建模拟器、改模拟器配置、操作桌面）先用一句话说明为什么、给选项；用户说"停"就停在干净点、写好恢复入口，不删现场（`references/multi-agent.md`「暂停时留恢复点」）。

不可恢复的操作（删公告、删帖、删存档）在列确认单时就单独标出来，写清点哪里，让用户自己动手，不要代点。

## 四条硬规则

1. **单一主入口 + 锚点断言。** 所有代码改动集中在一个构建期脚本里，每处替换都配 `assert`。源包一变就必须构建失败，绝不允许静默跳过——静默跳过会让"看起来成功"的包带着没生效的补丁发出去。

2. **逻辑放模块，不放生成物。** 补丁逻辑写在独立的脚本模块里，由主入口拼接。不要直接编辑反编译产物、解包目录或构建输出；它们下次构建就被覆盖。

3. **产物不是源码。** 打出来的 APK、bundle、解包目录、日志都是可再生的。修 bug 去改补丁脚本，不要"手工修一下包里的文件"——手工修的东西一旦产物被删就永久丢失，无法追溯。

4. **"界面能打开"不等于"功能完成"。** 只有状态真的变了（数量、进度、可领取→已领取，且杀进程重启后仍然正确）才算通过。未验证的项一律写成"代码已实现，真机待验证"。

## 两条安全底线

这两条都是真出过事才定下来的：

1. **共用手机，每点一次先看前台。** 新包装上两秒就闪退回了桌面，AI 没检查，接着往屏幕上点，点开了用户自己的二手交易 App，好在什么都没买。
   每次点击前确认前台是自己的游戏（`dumpsys activity activities | grep topResumedActivity`），每次启动后确认它还活着；不是就停手，不要猜着点。→ `references/playtest.md`
2. **删东西前先看是不是链接。** 硬盘满了让 AI 写清理脚本，脚本顺着目录链接（Windows junction）把另一头的源码和签名私钥一起删了，靠原始安装包和备份才重建回来。
   删之前先列出目录里的链接，拆掉链接再删；源码、签名私钥、授权记录在工作区之外常备一份（被 .gitignore 排除的目录尤其要备份：推到私有仓库前先扫一遍大文件和私钥，备份后逐文件比对哈希）。→ `references/pitfalls/agent-workflow.md`

## 常见失败模式

微端资源不全（包里只有一部分）、跨域 UI 层级残留、资源校验失败、存档不持久、离线网络层抛异常打断调用方、配置表未就绪就进游戏、文档漂移导致新 Agent 走旧链路、交付包与源码基线不一致（装了旧包）、放行类开关硬编码导致校验静默失效、真机存档读写卡顿（每次变更读好几个大 blob，模拟器看不出，还容易误诊成 Save 慢）、"离线版"一联网就被原生 SDK 带着往外发设备信息（测试都在断网下做所以看不到；去掉 INTERNET 权限并在发包检查里拦）。默认回空包悄悄锁住玩法或清零数值、领奖被拒时玩家只看到一句拟声词（连点 / 过零点 / 存档冻结三个触发）、多人系统做成虚拟玩家后衣服不全被投诉、繁转简把拿来比较的字也转了、离线加载卡在等永远等不到的服务器推送或 CDN 视频（标成"已看过"）、测试用真时钟（日期一进活动期就全红，一律钉时钟）。逐条见 `references/pitfalls.md`（索引，按阶段分文件）。
复活下线活动时另有一类：终版客户端把界面"藏"了（入口挪到屏外、入场动画删半截、布局和图集错配）、离线后付费兜底消失把原版数据缺陷放大成卡死、
共用图集被后一期活动覆盖（图还在但已是别的图、九宫格按旧图配会坏）、两期活动共用接口且 id 撞号——见 `references/case-b-laya-native.md`。

## 署名（可选）

帮用户写要公开的东西（项目 README、发布页、视频简介）时，可以问一句要不要加上这一行：

`Made with [offline-game-revival](https://github.com/Cynthia-wlan9509/offline-game-revival)`

用户说好才加；说不要或没回答就不加。署名只放在用户看得见、能自己删的地方，不要写进代码、APK、存档、提交信息或其他不显眼的位置。

## 参考

- `references/recon.md` — 侦察：从 APK 到可改写逻辑层；先核实停服状态；引擎速查
- `references/kickoff.md` — 开工：第 0 步脚本侦察、10 分钟破壳探针、路线决策表、换薄壳前必核 5 项、预授权、Day-0 建基、秒级快循环四件套、最小垂直闭环
- `references/route-unity-il2cpp-python.md` — 路线：Unity IL2CPP 没有脚本层时，同进程内嵌 Python 本地回环服 + SQLite + 网页 GM
- `references/route-unity-hotfix-cs.md` — 路线：Unity Mono / ET Hotfix / HybridCLR，包内 C# 模拟服；固定前缀不是加密、热更 DLL 和 AOT 元数据 DLL 怎么分、扁平覆写树、Cecil 锚点、下一帧回注防死锁
- `references/route-cocos-js-lua.md` — 路线：Cocos JS / Lua / 双 Lua 线程 / LuaJIT + Protobuf，包内内存环回；加密容器配方、零 apktool 换入口、薄壳 Activity 接管、PB 负数和默认值两个坑、超 ZIP32 上限
- `references/route-webgl-h5-worker.md` — 路线：WebView 壳 + Unity WebGL/H5，先 H5 闭环后封壳，常驻原版 DLL 做战斗 Worker，无头通关机器人
- `references/policy-presets.md` — 产品默认值：1:1 原版 UI、`[重建]` 规则登记、付费改本地代金券、AI 对手随战力成长、收益倍率、GM 隔离
- `references/autopilot.md` — 批次推进：开工检查顺序、推进优先级、七条防空转规矩、什么时候停下找用户
- `references/independent-qa.md` — 独立终验：防虚绿审计、回包契约扫描、T1–T5、清数据真断网双冷启、发行门禁、诚实交付说明
- `references/red-lines.md` — 多项目并行时的硬红线：零绝对路径、写接口不许默认成功、原子写档、磁盘熔断、单设备锁
- `scripts/recon_apk.py` · `device_guard.py` · `disk_budget.py` · `qa_oracle.py` · `strip_internet_axml.py` · `apk_replace.py` · `guard_hook.py` — 只读侦察、设备锁和安全推送、磁盘熔断和防目录链接的清理、日志裁判、零 apktool 去 INTERNET 权限、保留压缩方式换 APK 条目、可选的命令拦截钩子（都只用标准库）
- `templates/` — `KICKOFF-AUTH.md`、`PROJECT-AGENTS.md`、`HANDOFF.md`、`PROGRESS-MATRIX.csv`、`BUG-LIST.md`
- `references/patch.md` — 锚点补丁与重打包；脚本游戏不重编也能注入
- `references/verify.md` — 真机验收闭环；录演示视频
- `references/playtest.md` — 全新档正常游玩复测、门槛分项记录、数值校准顺序
- `references/media-harvest.md` — 从玩家截图/录屏抢救数值：抽关键帧、去重、本地 OCR、分类、交给文本模型的提示词与 JSON 格式；还原语音通话和聊天短信（第 4 节）
- `scripts/harvest.py` — 上面流程的脚本（OpenCV + RapidOCR，可中断续跑）
- `scripts/llm_structure.py` — 把 OCR 分块批量交给任意 OpenAI 兼容模型（DeepSeek / OpenAI / 通义 / Kimi / Ollama）结构化并合并
- `references/timewarp.md` — 时间快进测试：虚拟时钟、重启持久化、奖励对账、N 天经济模拟（`scripts/timewarp/`，Node 零依赖）
- `references/multi-agent.md` — 主 agent / worker / scout 分工与交接格式；省 token（快照 + 新会话、控制输出大小）；新游戏三路并行出 demo、暂停时留恢复点、共用模拟器、会话归档
- `references/pitfalls.md` — 失败账本索引（现象 → 原因 → 修法）；条目按阶段分在 `references/pitfalls/`：recon-unpack / patch-build / local-server / save-data / ui-assets / device-emulator / test-verify / release-distribution / agent-workflow / windows-emulator-build，查法是 `grep -rn 关键词 references/pitfalls/`
- `references/distribution.md` — （适用于自己做的游戏、有授权的分发和二创/同人）发新包不丢存档、一种包按授权码分档、活动开期、玩家自定义内容、存档迁移、上线后的 bug 反馈闭环；包被外传之后、分档第三版和机器人按档位签码、自动私信安全阀、把工具交给不写代码的人
- `references/case-a-unity-lua.md` — 完整案例：案例 A（Unity + Lua 手游）离线纪念版
- `references/case-b-laya-native.md` — 案例 B（LayaAir 原生 + JS 的剧情养成卡牌手游）：DCC 缓存校验算法、加载器补丁、启动竞态、本地服务器骨架；授权码、分档、复活隐藏活动、手机通话 / 短信、被埋没的支线和自制资源、正式包验收
- `references/case-c-micro-client.md` — 案例 C（大厂微端，Unity Mono + SLua）：资源清单对账、Lua 头字节、Mono 程序集半加密与 PE 头重建、加固壳的去除（改 dex 开关 + 从进程内存导出明文程序集）、launchconf 开关、用探针包让游戏自带的云 SDK 自己探测服务器；五层开屏 / 协议页换成免责声明（引擎开屏、C# 播的视频、剧情 CG 开头）；整个写在 Lua 里、回包不序列化的本地服务器（属性袋冒充字节流）；从玩家手机备份（小米 `.bak` = 头 + Android Backup + tar）补齐全部资源、换成终版底包、把热更层（Lua、清单、热更过的包内资源）并进 APK，避开微端首启清理
- `references/case-d-native-ai-chat.md` — 案例 D（原生 Kotlin + Live2D，核心玩法是服务器大模型聊天）：带 PairIP 的版本直接放弃；smali 只删调用不整段重写；接用户自己的 OpenAI 兼容接口（含局域网 / 手机本机模型）；用包内原台词做人设卡和语气样本防 OOC、出戏重试与兜底；装扮部件；minSdk 29 的包在安卓 9 模拟器上跑；拆分包合成单个 APK；假接口 + adb reverse 验聊天
- `references/case-g-laya-sproto.md` — 案例 G（LayaAir + 长连接 sproto 协议的剧情养成手游，整包在手）：协议定义文件转 schema、网络层替换点、启动死循环、客户端算 / 服务端算的分法、引导的隐性前提、自动推进脚本、正式包的全局异常处理器；默认回空包、领奖报错、虚拟玩家等玩家反馈批见 `pitfalls.md`
