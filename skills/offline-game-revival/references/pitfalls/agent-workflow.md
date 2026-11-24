# 工作流、多会话、沟通的坑

文档漂移、交付基线、多会话和 worktree、目录链接和删除安全、子代理卡住、方向误判、和用户沟通。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

## 工程与文档

**文档自相矛盾，新 Agent 按旧文档走错路**
- 原因：多份文档各自演化；构建脚本存在新旧两套，旧的仍留在推荐路径上
- 修法：定一份"当前事实源"，其余文档指向它；废弃脚本明确标注，不要让它出现在推荐流程里
- 2026-11-02 补：旧探索文档里的数字（件数、来源、价格）也会过期。要交给用户拍板的数字，先用脚本从配置表和代码里逐条列出来，再下结论；旧文档只当线索，发现矛盾要在回复里明说更正（案例 A：一份旧文档说「原版没写来源的有 12 件」，逐条核对后只有 2 件）。

**手工修在产物里的补丁丢失**
- 原因：改动只落在 APK / bundle / 解包目录，没回到补丁脚本
- 修法：产物一律视为可再生；定期核对临时脚本是否已合并进主入口，确认后删除或纳入

**未提交改动被误清理**
- 原因：脏工作区 + 清理脚本
- 修法：清理前先看 `git status`；禁止 `git reset --hard` / `git checkout -- .` / `git clean`

**交付包不能自证基线 → 装了旧包才发现改动没进去**
- 原因：产物目录里堆着多个历史包，包名只带时间戳；构建清单不记录策略开关（如门禁 bypass、
  各调试旋钮），于是"哪个包是哪个配置"不可考。本轮实测：真正要装的"最新改动 + 默认策略"包
  根本不存在，只有"最新改动 + 实验策略"和"旧改动 + 默认策略"两种，光看目录判断不出来。
- 修法：把**策略注入值写进构建清单**（manifest 记 `gate_bypass` 之类的开关取值）；发/装之前先比
  「包构建时间 vs 最近改动时间」；交接文档里把"**重新出包**"写成第一步，别写"直接装某个现成的包"。

**支线/实验收尾必须回到默认基线并重签**
- 原因：为验证某个开关（门禁、封锁、调试旋钮）临时改了策略文件，验证完忘了改回来，
  之后每个包都带着实验配置，而清单里看不出来。
- 修法：支线停放时显式恢复 `policy.json` 一类策略文件的默认值、重签签名文件、并重出一版默认包；
  在快照里写明"现为默认值 X，行为等同做该支线之前"。

**交接要给"第一件必做事"，不是给一堆背景**
- 原因：新 Agent 没有会话记忆，只凭文档判断"现在该干嘛"，于是最容易在第一步就装错包 / 走旧链路。
- 修法：写一份**可直接复制**的接力提示文件（基线时间戳 + 第一步命令 + 硬纪律 + 指向压缩快照），
  用显式"复制开始/结束"标记包裹，别用嵌套代码块（复制时容易截断）。

**两个会话同时改同一个仓库，互相重做、互相覆盖**
- 症状：一边修好的系统级问题另一边没有；同一个共享文件出现两种改法；一边的包把另一边的设备状态弄乱。
- 修法（案例 A 2026-10-13 的做法）：
  1. 每条线一个 git worktree、一条分支；构建目录、日志、存档各用各的，只读输入用目录联接共享。
  2. 每条线一台设备（真机 / 模拟器），模拟器走单独的 adb 服务端口，让两边互相看不见对方的设备。
  3. 按"谁拥有哪些文件"分工：一条线拥有共享主体文件和发布包；另一条线只写自己的模块文件，在主入口里只加登记行。
  4. 共享代码里发现的 bug 用一条消息告诉拥有方，由拥有方核实后修；另一方只合并，不重做。合并方向固定（发布线 → 探索线）。
  5. 探索线的模块要进发布包，由发布线自己拿、自己在发布设备上验证；"在模拟器上过了"不算发布线的验证。
- 接手时先看两边的 `git log` 和各自的总览文档，再回答"现在做到哪了"；只读一边的快照会漏掉另一边一半的事实。

**"章节打通了"被当成"可以发了"**
- 回答"是不是彻底完成"要分开四件事，各自要有证据：① 内容：全新档按玩家顺序打到终点（哪个包、哪份报告）；② 修复：每条修复在**最终那个包**上复验过，不是在修它的那个中间包上；③ 交付物：正式包重新打过、哈希记下、已装到用户的正式安装、对外副本目录是同一个哈希；④ 发布卫生：调试开关、注入后门、未开放内容是否还在包里。
- 常见的假完成：章节在候选包上通关 → 之后又修了十几处 → 用户设备上和对外目录里还是旧包。

## 方向误判（最贵的错误）

**长时间调不通某个注入 / 加载机制，认定卡点就在这里**
- 原因：真正的阻塞在别处。运行时看不到"某个分支永远不会触发"这类事实
- 修法：**先把上一阶段留下的日志读完，再动手调。**
- 实例：前一阶段花了大量时间调 Frida Gadget 自动脚本模式。后来读 logcat 才发现，卡点是另一个"8 秒后弹窗盖住画面"的强制跳转，而它的触发条件（`sendCount >= 3`）在整份日志里永远不可能满足——**即使 Gadget 修好也照样进不去**

**越依赖运行时探针，效率越低**
- 原因：注入类工具对 C# 对象遍历不稳定、反复超时，会话越长越容易失败
- 修法：运行时只用来**生成假设**；关键结论用静态方式复核（在包里查字符串、比对文件内容）

**把侦察工具当成交付方案**
- 原因：注入方案在调试机上"能跑"，但验收标准要求"不 root、不用电脑、只装 APK"
- 修法：明确区分阶段。侦察用什么工具都行；交付必须落到包内改写。不要在让注入方案"跑通"上继续投入

**功能"没有反应"其实是被离线补丁主动关掉的（用一个哨兵值关掉整块功能）**
- 症状：某个系统（新手引导、活动、限时玩法）在游戏里**完全看不到、也不触发**，
  既不报错也不卡——因为它根本没被调用。
- 排查：不要只搜"这个功能怎么实现"，**先搜它是怎么被关的**。离线补丁为了让流程跑通，
  常会写下类似 `_G.OFFLINE_DISABLE_XXX = true` 的总闸，或者给状态字段灌一个哨兵值
  （如 `guideFlag = -1`）让 `IsXXX()` 直接走"已完成/已跳过"分支。
- 实例：案例 A 的离线版用 `_G.OFFLINE_DISABLE_GUIDES = true` + `ng.guideFlag = -1` 关掉了整条
  新手引导链。关键在 `IsGuided()` 的写法：**对负数一律 `return true`**，
  于是"标记为 -1"等于"所有引导都已完成"，一行就把 18 组引导全部静默关闭。
- 教训：**看到 `= -1` / `= 999` 这类哨兵值，先确认下游对它的处理是不是"全放行/全跳过"**。
  想恢复时，先把它改成"读存档/默认值"，再补上本地持久化，别直接改回 0 就完事。

### 分档 / 授权开关（案例 A 2026-10-17 合并时）（续，原节在 `release-distribution.md`）

**合并两条长期分叉的分支：先看清哪边的文档只是旧副本**
- 探索线里的发版说明 / 用户反馈表是从发布线早期抄过去的副本，没有自己的新行；直接取发布线那份即可，不用重新编号。动手前用 `git diff <merge-base> HEAD -- 文件` 看本分支到底加了什么。
- 同一仓库里 `.py` 是 CRLF、`.lua` 是 LF：用 Python 精确替换前先 `repr()` 看一眼换行，别让断言「找不到」浪费一轮。

## Worktrees with junctions to the main repo (2026-10-17)

Worktrees that link `src/`, `private/` (keystore!) and `analysis/` back to the main repo through junctions must have those junctions removed first (`rmdir` without `/s`). Check that the main repo's keystore is still there, and only then run `git worktree remove`. Archiving a session that cleans up its worktree carries the same risk, so remove the junctions before archiving.

## Device booking table inside git branches (2026-10-18)

A booking file committed in git has one copy per branch or worktree. Two sessions each edited their own copy, and both used the emulator at the same time; one swapped the package and the save under the other's test run. Keep exactly one booking file: an absolute path in the main checkout's working tree. Edit it directly; don't wait for merges.

### 零散条目

**`git worktree remove --force` followed a junction and emptied the main checkout (2026-10-19)**
- Symptom: after a cleanup script removed two merged worktrees, the main checkout's untracked `src\`, `private\` (keystore, license ledger) and `analysis\` were empty; nothing was in git or in a disk snapshot.
- Cause: the worktrees had NTFS junctions pointing to those folders in the main checkout. Git for Windows deletes through a junction instead of unlinking it.
- Fix: before any recursive delete, list reparse points under the target (`Get-ChildItem -Recurse -Attributes ReparsePoint`) and remove the links first (`cmd /c rmdir <link>` removes only the link). Keep keys and ledgers backed up off the work drive, and record where every untracked build input came from so it can be rebuilt.

**清理产物目录：只认严格命名的直接子目录，逐层查链接，默认只打印（2026-11-04）**
- 症状：每份约 2.4 GB 的带时间戳构建目录越积越多。这块盘出过递归删除顺着 junction 删掉源码和私钥的事故，不能用通配符递归删。
- 原因：构建脚本只建不清；普通递归删除会顺着链接跑到目录外面。另外，Python 3.10 在 Windows 上的 `os.path.islink` 认不出 junction（只认符号链接），会把它当成普通目录进去删。
- 修法：写成独立的清理脚本。① 只处理名字完全匹配规则的直接子目录（如 `<模式>-<日期>-<时间>[-final]`），同名的普通文件不碰。② 目标本身和里面每一层都查链接：看 `lstat().st_file_attributes` 里的 reparse point 标记，junction 和 symlink 都认得出；有链接就整份跳过。真删时每层再查一次，碰到链接立即停止。③ 默认只打印“可以删哪些”，加 `--apply` 才真删。④ 保留最近 N 份，再额外保留每一类（模式 × 正式 / 开发）的最新一份，免得把别的工具当输入的包挤掉。⑤ 出错只打警告，不影响构建结论。⑥ 升级测试目录只清 APK，截图和 diff 保留。
- 多会话共用仓库时：开工前先看进程列表，谁的命令行里带着哪些产物路径，就不碰那些产物。除了名字里是今天的，24 小时内写过的也保留（跨午夜的构建，名字里是昨天的日期）。删之前和已发布目录里的副本比一次 SHA-256。超过保留期的旧包仍可能被别的任务读取，这个残余风险要告诉用户。
- 怎么确认的：在临时目录里用真实的 junction 和 symlink 跑了 25 项测试；对真实目录空跑一遍，前后文件对比没有变化。

### 案例 C：玩家备份接入（2026-10-22）（续，原节在 `device-emulator.md`）

**A scout "waited on its own background work" for 40 minutes** (case C, 2026-10-24)
- Symptom: the scout reported "waiting on background work" twice and never delivered; the goal check listed a background shell that never ended.
- Cause: its shell command started with `cat > /tmp/x` with no input, so `cat` blocked on stdin forever; the scout parked itself waiting for that command.
- Fix: when a subagent stalls, list background tasks and read the command line; stop the stuck shell and the agent, and do the work yourself if you already have the context. In briefs, say "finish within N minutes, no background jobs".

**Demo video: the first cut missed what the user asked for** (2026-10-24)
- Asked for "today is <character>'s birthday, show the event", the cut ended on another character's birthday event because that was the only birthday event in the game. Say up front what the game actually has for that character (here: two birthday phone calls) and build the video around them, plus that character's own story, cards and gift screen. Do not pad it with someone else's event.
- Asked to show the build was "made unpaid by <team>", the captions added "free to share" on top. The user had not shared it and objected. Caption only what the user asked for.
- The game draws its in-game phone rotated 90° (players turn the device); transpose that segment upright in the edit instead of leaving it sideways.
- Keep the raw capture until the user has seen the cut; after deleting it, every fix means recording again.

## 用户说"停"就原样冻结，不要拆现场（2026-11-17）
- 现象：用户对外说"先不做了"，有个会话理解成放弃，删了模拟器上的注入文件；其实用户私下还要接着做，恢复时得重新放回去。
- 修法：暂停 = 停在干净点 + 写恢复入口（见 `multi-agent.md`「暂停时留恢复点」），不删东西。对外口径和实际进度是两回事，拿不准就问一句。

## 动用户机器的大动作，先用一句话说明为什么（2026-11-17）
- 现象：环境会话一上来要新建模拟器实例，用户打断问"为什么要建模拟器"。
- 原因：没先说明理由和代价（新实例约占 25 GB C 盘、只能在图形界面里点），也没先看能不能复用。
- 修法：新建模拟器、改模拟器配置、操作桌面这类事，先用一句话说明为什么、给选项（复用现有实例 / 新建）。这次结论是复用现有实例就行。

## 磁盘清理脚本的另外几个坑（2026-11-16）
- 一次清理脚本没删对东西：自定义函数名叫 `Kill`，撞了系统命令；脚本文件编码让中文路径乱码，结果只清了回收站。修好、先空跑列清单，再真跑。
- 删压缩包前核对已经完整解压；名字带 `.zip` 的可能其实是文件夹。
- 解压出来的游戏已经被改过（主程序打了补丁）时，那个压缩包就是唯一的原版，必须留。
- 清理期间可用空间被别的会话吃掉，别当成清理出了问题。被工具按路径引用的副本只隐藏、不删。删了什么记日志；永久删除先问用户。
- 盘根整理：真文件夹留在原路径并隐藏，分类文件夹里放目录链接指过去，脚本路径不用改。删分类文件夹前照样先拆链接。
