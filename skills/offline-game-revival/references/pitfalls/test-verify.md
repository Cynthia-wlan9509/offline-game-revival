# 测试与验收的坑

单测和时间快进、浸泡测试、开发包和正式包结论不一样、"假通过"、偶现问题先复现。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

### 本地回包 / 伪造服务器数据（续，原节在 `local-server.md`）

**玩家报「偶现」的操作失败：先造数据复现再修，别交付没复现过的防御性修复（案例 A 2026-10-22）**
- 症状：布阵保存后喂食提示「无宠物上阵」；换一批上阵后，有的能喂、有的不能；全部换成中低品质的就不能喂，换成高品质的就能喂。
- 原因：第一轮先猜「宠物已拥有但后院模型查不到，被队伍构建剔除了」，做了一个防御性修复就报完成，其实没复现过。注入诊断证明拥有数等于后院数，这个假设不成立。真正的原因是那些宠物的等级卡在突破封顶（等级 = 突破 + 10 且经验已攒满）或者已经满级，客户端的「等级已满」判断把喂食拦死了，提示文案却误导成「无上阵」。
- 修法：服务端喂到突破点时自动突破，打开喂食面板的回包里先把卡在封顶的宠物解开；真满级了才停，并给出明确提示。流程上，先写只读诊断脚本，用数据逐个排除假设；造出能复现的状态后再改；然后走真实的打开面板回包，核对客户端拦截条件在改前改后的变化。根因确认后，更正交接文档里错误的结论。
- 怎么确认的：造出满级 / 封顶数据后，「可喂」为 false，未满级的为 true，正好对上玩家的现象；修好后，卡住的宠物升了一级，连喂 30 次能越过突破点。

**新模块往共享接口里加内容，旧模块按总数断言的回归就失败（案例 B 2026-10-20）**
- 症状：加入短信模块后，通话回归测试期望 4 张桌面卡片，实际是 8 张。
- 原因：两种卡片走同一个查询接口，旧测试数的是总数。
- 修法：旧测试按自己的类型过滤后再数；测通话时把新模块的红点桩成「没有」；红点汇总处按「任一模块有新内容」合并，某个模块不存在时也不报错。

### 随机与异步（续，原节在 `local-server.md`）

**按时间排序的测试偶发失败：两次操作落在同一毫秒（案例 B 2026-10-20）**
- 症状：通话测试单独跑能过，放进回归循环里偶尔失败。
- 原因：两通电话在同一毫秒被「接听」，按接听时间排序时出现平局；真实使用中不会发生。
- 修法：测试里用受控时钟，不用真实时间。
- 怎么确认的：换成受控时钟后连跑 8 次全过。

### 工具链 / 环境（实测坑）（续，原节在 `device-emulator.md`）

**动手验证前先想清楚「副作用会不会自己消失」**
- 离线版常常**每次启动用配置表重造仓库/背包**（如本项目把所有道具按 `OFFLINE_START_COUNT` 重发一遍）。
  这类种子会让"花掉的消耗品、抽到的东西"在**重启后回到种子值**——测试副作用天然消失，无需手工还原。
- 但**受 PlayerPrefs 落盘的状态**（等级、突破、星级、剧情进度、引导进度）不会自己回去，必须手工清理。
- 做法：验证前后各读一次关键字段 → 重启 → 再读一次。
  数值回到种子值 ⇒ 属于前者，不用管；仍然保留 ⇒ 属于后者，**要删 prefs 键再重启**，并复查。

**授权码 / 兑换码 / 存档迁移这类「纯逻辑」模块，不要等上机才发现错——用 lupa 在电脑上跑真的 Lua，GameNS 用 Python 模拟**
- 做法：`pip install lupa`，把要发布的 `.lua` 模块（和门禁一起，顺序同构建拼接）原样 `execute` 进去；在 Lua 里先建一个 `GameNS = {UnityEngine={PlayerPrefs=...}, System={Text=..., Convert=..., Security=..., IO=...}}` 的模拟层，`CSLNew / CSLNewfunc / CSLArrayGet / CSLTypes` 也各给一个。真签发（pycryptodome + 私钥）→ 真验签（模拟层的 RSA 用 `release_public.xml` 里的公钥，和游戏里是同一把）。案例 A 的 `tools/tier_selftest.py` 就是这么做的：150 项，分钟级，抓住了好几处只有真跑才暴露的语法 / 逻辑错。
- 模拟 .NET 的 `byte[]`：**用十六进制字符串**表示。lupa 把 Lua 字符串当 UTF-8 解码，二进制（签名字节）放进 Lua 字符串会炸。
- 写完测试再做「突变」：把关键判断（到期比较、设备码比对、`to` 比对）一个个改坏，确认测试会红；不会红的测试等于没测。
- 时钟、权限、文件系统都放进模拟层里可控（`V3_Now`、`IsPermissionGranted`、内存文件系统），才能测 05:00 边界、无权限退路。

## 驱动任务链的开发脚本遇到原版占位任务会「抬门槛」（案例 A 2026-10-18）
- 原版最后一条任务常是「未完待续」占位，条件不可达（如等级 999）。自动抬门槛的脚本会把存档改成 999 级。
- 做法：驱动到「最后一条真实任务」为止（DRIVE_LAST），或让脚本对超出表上限的门槛直接停下。

### 零散条目

**A visual feature passes on the dev package but not on the release package (2026-10-19)**
- Symptom: dynamic card faces animated on the emulator's dev build; on the player's phone (release build) they stayed static, although the save had the right flag.
- Cause: the release build strips asset bundles by folder rules; the dev build strips nothing. The faces' Spine and background bundles lived in chapter folders that were stripped whole (only `/cg` was kept).
- Fix: whitelist the exact bundles (derive the list from the config tables, keep it in a JSON next to the strip rules). Rule: anything that loads assets must be checked once on the release build, with a save crafted offline (release builds cannot take injected Lua).

### 案例 C：玩家备份接入（2026-10-22）（续，原节在 `device-emulator.md`）

**One daily cap reset at midnight while every other daily reset at 05:00** (case B, 2026-10-24)
- Symptom: none in play-through; found while auditing. A minigame's daily reward cap reset at 00:00 Beijing time, the rest of the dailies at 05:00, so between midnight and 05:00 the cap was already fresh while the day's other limits were not.
- Cause: the shared day-key helper takes the reset hour as an optional argument that defaults to 0; the newer module simply left it out.
- Fix: pass the hour. Then make the omission impossible to repeat: a static check in the time-warp suite scans every module for day / week key calls without an explicit reset hour and fails. A regression at 00:30, 04:59 and 05:00 covers the module itself.
- Related: the time-warp suite's generic "response says X, save gained X" reconciliation only knew the reward routes that existed when it was written. When new modules add reward routes, add them to the reconciliation table too, and keep an eye on the printed coverage line (here it had silently stayed at 26/30 while ~20 new routes were outside it).

## 浸泡测试能抓到随机点击抓不到的闪退（案例 D，2026-10-29）
- 现象：两轮 3000 次随机点击 0 崩溃，换成“每 5 分钟一段 120 次、持续两小时”的浸泡测试，第一段就闪退：点触语音的 `MediaPlayer.isPlaying()` 在播放器出错后抛 IllegalStateException（原版隐患）。
- 做法：浸泡脚本记录 pid / 内存 / 崩溃日志；抓到后用固定的 monkey 种子复现，修完用同样种子对比。原生的 MediaPlayer 检查一律包一层：出错就 `reset()` 并当作没在播。

### 零散条目

**随机点击压测把模拟器系统带崩，不是游戏的问题（案例 C 2026-10-25）**
- 症状：monkey 跑到第 2137 次报 `CRASH: null` 后中止，游戏进程号变了，游戏日志也丢了。
- 原因：随机事件里的按键类事件（trackball、nav、majornav、anyevent）在模拟器上触发了“语音搜索”，系统里没有应用能处理，system_server 崩溃重启。
- 修法：只留触摸和滑动，关掉按键类、系统键和切应用事件（`--pct-trackball 0 --pct-nav 0 --pct-majornav 0 --pct-anyevent 0 --pct-syskeys 0 --pct-appswitch 0`）。跑完看游戏日志里的 Lua 报错和未接请求。这样重跑 3000 次，0 闪退。

## 单测里的几个坑（案例 B 2026-11-16）
- **测试用真时钟是定时炸弹**：旧测试大多写在 10 月 20 日前后，正好落进新加的一期活动，按人筛之后条数全变。新测试一律钉时钟；旧测试要么挪到不在任何期的日子，要么断言写成"按当期算"。
- **vm 沙箱里的数组和测试进程的数组原型不同**，`assert.deepStrictEqual` 报"same structure but not reference-equal"。先 `JSON.parse(JSON.stringify(x))` 再比。
- **简单 LCG 不能做统计检验**：`(s*1103515245+12345) % 2^31` 在 JS 里乘法超过 2^53 丢低位，相邻两次取值相关，"先判是不是最高档、再判是不是 UP"会被带偏（60% 测成 50%）。统计用 mulberry32。
- **保底叠加后的比例要算，别抄宣传数字**：90 抽必含 + 60 抽硬保底叠加，UP 占最高档的长期比例约 42%，不是写的 30%。统计测试的区间按算出来的定。
- **"老存档不被改"别比整份存档**：登录、红点查询会触发别的模块写存档。只比自己可能碰的那块，并允许原模块按需建的空结构。
- **模拟"老包玩过的档"**：用去掉新模块的文件列表起一个沙箱玩一会儿、落盘，再用全量模块接着跑，比手写存档 JSON 真实。
- **往公共奖励列表里加"不进背包"的东西，要同步长跑的资产账本**：不加对应的键，哪天长跑跨进活动期就假报"对不上账"。现有长跑日期不在活动月，当场不会红，要专门加一段跨活动期的长跑。
- 长跑剧本的"第 N 天"从 1 数（第 1 天 = 起始日），写开关边界断言前先对一下别的剧本。
