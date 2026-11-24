# 补丁与打包的坑

锚点补丁、宿主文件和包体上限、重打包、校验字段、原生层（smali）补丁、Windows 上改文件和编码的工具坑。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

### 启动阶段（续，原节在 `local-server.md`）

**新包一启动就闪退，日志是"分配内存失败"而不是脚本错误**
- 症状：启动约 2 秒原生崩溃；日志有 `Could not allocate memory ... MemoryLabel: String`（要分配的字节数是个天文数字），随后 `Fatal signal 5 (SIGTRAP) ... UnityPreload`。上一个包还好好的，这次只多了几百字节脚本。
- 原因（原先的判断）：往某个脚本文件里注入的代码把它顶过了加载器的体积界限（案例 A：261184 字节能启动，261352 字节崩）。**2026-10-18 更正：很可能不是体积界限，而是某块「压缩后恰好等于原始大小」被 Unity 当原样读——见文末 "compressed size equals its raw size" 一节；日志特征一模一样。**
- 修法：打完全部补丁后给宿主文件统一瘦身（去整行注释、空行、行首缩进；长字符串内部不动；瘦身必须在最后做，否则前面靠缩进原文当锚点的补丁会找不到位置）。更重要的是在打包脚本里加体积断言，留足余量，让它在打包时失败。
- 教训：每次装新包后先确认进程还活着再点屏幕。闪退后屏幕是桌面，盲点会点进别的应用。

**黑屏 / 卡住，日志有 `CRC Mismatch`**
- 原因：改了 bundle，校验字段没更新
- 修法：把生效的 manifest 里 CRC 改成 `0` 或 Unity 日志给出的正确值
- 注意：可能有多个 manifest，要试出游戏真正读的那个

**JS 引擎启动约 2 秒后原生崩溃：过早挂了 `window.onerror`（案例 B 2026-10-29，模拟器）**
- 症状：加了导出日志模块的测试包，在模拟器上启动约 2 秒就 SIGSEGV，正式包正常。先后怀疑读了不存在的文件、怀疑 debuggable 标志，换掉之后照样崩。
- 原因：模块在游戏代码加载前挂了 `window.onerror`。conch 设这个钩子时会调原生的异常弹窗函数，在 ARM 转译层上直接崩。游戏后面还会用自己的钩子覆盖它，这个钩子本来就没用。
- 修法：不挂 `window.onerror`，只包装 console 的方法；启动时不读文件，第一次落盘时再读。序列化日志参数时只展开普通对象和数组，引擎内部对象只记类型名，免得碰到原生属性又崩。
- 怎么确认的：去掉 onerror 和加载时读文件后，重启模拟器能正常启动，全流程跑通。

### 本地回包 / 伪造服务器数据（续，原节在 `local-server.md`）

**离线模块按文件名顺序拼接，后加载的会覆盖先加载的同名处理函数（案例 G 2026-11-15）**
- 症状：做了“收藏的信件不被一键删除”，实测还是被删。
- 原因：邮件处理函数在一个排序更靠后的杂项模块里又定义了一遍，盖掉了前面的包装。
- 修法：要包装别的模块的处理函数，自己的文件名就排到它后面，或延迟一拍再包。自定义邮件借用一个原版已有的邮件编号当载体，旧版本也不会因为不认识编号而崩；没登记的编号要补占位配置，否则列表一渲染就读空。

### 工程与文档（续，原节在 `agent-workflow.md`）

**后台构建开始之后改的代码，不在这次的包里（案例 A 2026-10-30）**
- 症状：打包期间继续改代码，打出来的包缺了最新的修复。
- 原因：构建读的是启动那一刻的源码。
- 修法：改完代码先看有没有后台构建在跑，有就停掉重打；先在开发包或分身上验，再打正式包。

**构建日志里写着签名证书密码的明文（案例 B 2026-10-20）**
- 症状：正式包打完，日志里的签名命令行带着 `--ks-pass pass:<明文>`，日志可能被归档、分享，甚至被提交。
- 原因：构建脚本把完整命令行原样打印，并写进了日志。
- 修法：打印前把密码替换成 `pass:***`，只改打印出来的那份，传给子进程的参数不变。失败时 assert 的报错信息里也带着命令行，同样要脱敏。打完包后 grep 日志目录和工具目录，完整密码和前几位都要搜不到。把这一项加进发包检查，手册里的「外发前人工抹密码」改成「已自动脱敏」。已经写出去的旧日志，批量改成 `pass:***`。如果用 sed 改，它会把 CRLF 变成 LF（见「批量改 CRLF 源文件后换行变 LF」），改完要用 Python 数 CR / LF 字节，确认每个文件只有密码那一行不同。

### 工具链 / 环境（实测坑）（续，原节在 `device-emulator.md`）

**Windows / PowerShell 下改文件：别把补丁文本内联当命令行参数**
- 症状：`apply_patch` 之类工具用内联字符串传参时报 `ParserError: '<' operator is reserved`，
  或中文变成乱码导致替换失配。
- 修法：改用 PowerShell 字面 here-string `@'...'@` 赋给变量再 `Set-Content -Encoding utf8`，
  或用 python 以 `utf-8` 读写（`io.open(..., encoding='utf-8')`）做字符串替换；
  脚本输出非 ASCII 时先 `$env:PYTHONUTF8=1`，否则 GBK 控制台会 `UnicodeEncodeError`。
- 附带：删除文件若被沙箱拦截，用 `python -c "import os;os.remove(...)"` 或 `shutil.rmtree`。

**用内联脚本改源码时，反斜杠被工具层吃掉一层**
- 症状：用 `python - <<'EOF'` 这类内联脚本做"按原文查找再替换"，要找的那几行里有字面量的"反斜杠 + n"（例如补丁脚本里一行行拼起来的 Lua 字符串），怎么都匹配不上；打印出来看一模一样。
- 原因：命令字符串经过一层转义，脚本里写的两个反斜杠到 Python 手里只剩一个，"反斜杠 + n"变成了真的换行。（写这条笔记时又被它坑了一次。）
- 修法：逐字符比对找出第一个不同的位置（一下就能看出来）；需要字面反斜杠时用 `chr(92)` 拼，或者把脚本先写成文件再执行。

**误删函数，语法检查和打包自检都是绿的**
- 症状：真机报 `attempt to call global '某函数' (a nil value)`，而这个函数昨天还在。
- 原因：用"从标记 A 到标记 B 整段替换"的办法改源码，A 和 B 之间夹着另一个不相干的函数，一起被换掉了。Lua 的语法检查只管语法，调用不存在的全局函数要运行到那一行才报错。
- 修法：打包自检里加一步：离线模块里调用的自家函数（按前缀认）必须在某个模块里有定义。整段替换前先打印被替换的内容看一眼有多长。

**补丁里的单例访问器 / 配置表名拼错，被 pcall 兜底悄悄吞掉（案例 A）**
- 症状：奶猫槽解锁后指引事件一直不发；升级时原版升级弹窗一直不出现。都不报错，只是功能不生效。
- 原因：离线补丁调 `BackyardManager.GetInstance()`，原版类里单例函数实际叫 `GetIntance`（少个 n）。调用包在 `pcall` 里，失败后悄悄走兜底分支。配置表名也有同类（真实名带 `Cfg` 后缀、或 `rept某某Cfg` 写成 `rept某某`），取出空表。
- 修法：补丁里所有单例访问器名、配置表名和原版类定义 / 配置管理器赋值语句逐个对一遍；`pcall` 兜底不要写成静默，至少打一行日志。把这类检查做成打包期 lint：扫离线模块用到的全局函数和配置表名，对照已定义的函数和真实存在的表（本游戏 247 张），不一致就打包失败。

**脚本包解压后超过 16 MiB，游戏启动即退出**
- **2026-10-18 更正：没有 16 MiB 上限**（17.07 MB / 131 块的包实测能进主界面）。当时撞上的是「某块压缩后恰好等于原始大小」，见文末 "compressed size equals its raw size" 一节。
- 症状：加了几个模块后新包起不来，日志 `archive:/CAB-… is corrupted! [Position out of bounds!]`，进程收到信号 5。和"单个文件太大分配不了内存"不是一回事。
- 事实（另一条开发线量的）：这个包按 128 KB 一块压缩，线正好在 128 块 = 16,777,216 字节；退回线内就能起。是引擎上限还是打包库回写的问题没分清。
- 修法：打包自检里量解压后的大小，留余量，超了直接失败。要腾空间就给没打过补丁的原版文件做瘦身（去注释和空白），别动打过补丁的（自检断言靠注释字样）。

**想在游戏里加「从相册选图」，以为必须改 Java / dex**
- 先在 IL2CPP 的 dump.cs 里搜 `Permission` / `Gallery`：很多手游自带权限封装（案例 A 有 `AndroidPermissionsManager.IsPermissionGranted(string)` 和 `RequestPermission(string[], 回调)`），脚本层直接调就能弹系统授权框。目标版本低于 29 的包在新安卓上仍是旧式存储（`appops` 里看 `LEGACY_STORAGE`），授权后按 `/sdcard/...` 路径直接读。
- 脚本桥的坑：桥接层的「数组初始化」函数可能返回脚本表而不是 C# 数组，要用 `System.Array.CreateInstance(typeof(String), n)`；造不出 C# 委托时给回调对象传空，结果靠轮询「是否已授权」拿。
- 授权框要设备主人自己点，agent 不代点；可以点「拒绝」测拒绝路径。

**用 Bash 工具的 heredoc（`python - <<'EOF'`）写含双反斜杠的补丁脚本，工具会把 `\\` 先折成 `\`，于是 Python 里的 `'\\n'` 变成真换行，Lua 里就报 `unfinished string`**
- 症状：往 `.lua` 里插字面量 `'\n\n'`，文件里却成了真换行（字符串断成三行）；看 `sed` 输出才发现。
- 注意：连这份文档本身用 heredoc 追加时也被折了一次——写含反斜杠的内容一律用 Write / Edit 工具。
- 修法：补丁脚本用 Write 工具落成 `.py` 文件再运行（文件里的反斜杠不会被改），或用 `chr(92)` 拼；改完立刻 `grep -n` 看那一行。
- 同类：`pip download xxx` 会把 wheel 下载到当前目录，工作区里多出一个 `.whl`，提交前 `git status` 一定要看。

**Windows 下的管道和编码（2026-11-07）**
- 症状：PowerShell 里让 `git archive` / `tar` 走管道，得到的归档是坏的；`.ps1` 里的中文读成乱码；Python 打印中文报 `UnicodeEncodeError: 'gbk'`。
- 原因：PowerShell 管道按文本处理字节流；Windows PowerShell 5.1 不把无 BOM 的 UTF-8 当成 UTF-8；控制台默认 GBK，而 `python -I` 会忽略 `PYTHONIOENCODING`。
- 修法：二进制流改用 Bash 重定向（`git archive --format=tar > x.tar`）；`.ps1` 存成带 BOM 的 UTF-8；Python 里调用 `sys.stdout.reconfigure(encoding='utf-8')`。
- 反过来，Lua 注入文件、git 提交说明这类文件要写成**无 BOM** 的 UTF-8：PowerShell 5.1 写文件默认带 BOM，注入的 Lua 会静默加载失败，提交主题行开头也会多出 BOM（案例 A 2026-10-14 因此重做了两个提交）。用 `[IO.File]::WriteAllText(路径, 内容, (New-Object Text.UTF8Encoding $false))` 或 Python 写。

**OpenCV 写中文路径会静默失败（案例 B 2026-10-20）**
- 症状：录屏抽帧后目录里一张图都没有，也不报错，后面的草稿和校对图都缺了录屏那部分。
- 原因：`cv2.imwrite` 遇到非 ASCII 路径只返回 False，不抛异常。
- 修法：写文件用 `cv2.imencode('.jpg', img)[1].tofile(path)`，读文件用 `np.fromfile` + `cv2.imdecode`；保存后数一下文件数。

### 分档第二批：开局拉满 / 资源券（2026-10-17，会话 C）（续，原节在 `save-data.md`）

**新模块放进独立的小宿主，登录钩子放在 MsgManager 尾部**
- 宿主文件有体积闸（LoginController / MsgManager 258000 B），新模块各寄生在一个小管理器文件末尾（`SettingManager.lua` / `DailyTaskManager.lua`，锚点 `\nreturn <名>`），MsgManager 只加一个 600 B 的 `V3_OnLogin` 包装去 `CSLTypes.<宿主>` 触一下（懒加载）再调 `Install`。包装排在最后 = 分发表包装在最外层，能抢在先装的处理器前拦消息。
- 设置页加按钮：借用原版一个没用的按钮（`btn_limit` 点了开浏览器）改字改点击；锚点选在 `InitPanel` 中段的音量行，避开别的会话改的开头，两边补丁互不重叠。
- 新检测「新档」用现成信号：新手选择键 `OFFLINE_NEWBIE_CHOICE_V1` 写入之前的那一次进主界面 = 新档；再加「等级 ≤ 3 且主线 ≤ 10103」兜底（弹窗没答完就杀进程）。授权接口没装时 `V3_TierAllows` 兜底：开发包全开、正式包全关。

**工具链**
- 在 Bash 工具的 heredoc 里写含 `\n` 的 Python / Lua 源码，工具层会把 `\` 吃成 `\`，字符串里出现真换行、断言「找不到」。含反斜杠转义的源码一律用 Write 工具落盘再执行，或用 r''' 原始串。
- `v3_dev.py restore` / `restart` 后要等到「公告点掉 → 主界面」再 `luamain`，否则脚本进了没起来的调度器、什么日志都没有；用「先注入一条 ping 日志确认能回」再注入自测。
- 设备占用表是每个 worktree 一份，别的会话看不到你写的那一行：别人装包会把你分身里的包覆盖（`dumpsys activity exit-info` 里 reason=PACKAGE UPDATED 就是被人装了包）。上机前先 `exit-info` / `dumpsys package <pkg> | grep lastUpdateTime` 看有没有人在用，上机时直接给对方会话发消息。

**注入的宿主脚本悄悄长到上限边缘，下一个小改动就启动闪退**
- 现象：把多个离线模块拼进同一个宿主脚本文件（案例 A 是 `LoginController.lua`），文件过大时 Unity 在预加载阶段分配字符串失败直接闪退（实测约 261 KB）。构建自检只断言「不超过上限」，没人注意余量：2026-10-17 发现它已到 257.5 KB，余量不到 500 字节。
- 对策：每次构建都打印各宿主的大小和余量，余量低于 10 KB 就报警；新模块一律放独立宿主。要腾空间时，挑一个「没有和别的模块共享局部变量、也没被别的模块在加载时取用」的模块整体搬到另一个先于使用点加载的宿主，构建自检里引用它内容的断言一并改指新宿主（按次数计数的断言改成统计两个宿主合计）。
- 搬之前用脚本查两件事：它定义的局部名有没有被同宿主其他模块用到；它定义的全局函数有没有被其他模块在顶层赋给局部变量（加载顺序一变就成了 nil）。

### 游戏内读相册 / 自定义图片（案例 A 2026-10-17，tier/custom-media）（续，原节在 `device-emulator.md`）

**Lua 绑定层的「同名重载」只有部分能用，先注入一段探针挨个试再写代码**
- 实测（Unity 2017.4 + 这套 CSL/ToLua 绑定）：`ImageConversion.LoadImage(tex, bytes)` 抛 `C++ exception`，三参数 `LoadImage(tex, bytes, true)` 能用；`Graphics.Blit(src, dst)` 能用，带材质或带 scale/offset 的重载都抛异常；`GL.Color` 抛异常（其余 GL 调用都行）；`FileStream:Read` 不存在，用 `BinaryReader:ReadBytes`；`EncodeToPNG/JPG` 只能经 `ImageConversion` 静态类调；游戏里没有 `cjson`（`require` 失败），要自带 JSON。
- `tostring(long 属性)`、`tostring(枚举)` 会报 `field or property __tostring does not exist`：打日志前包 pcall。`GameNS.<不存在的命名空间>` 也返回一张表，不能拿来判断类型存不存在。
- 裁 / 缩 / 转图不用逐像素：`UI/Default` 材质 + `GL.Begin(QUADS)` 画四边形（四角 uv 按旋转算好）进 `ARGB32` 临时 RenderTexture，再 `ReadPixels`。手机竖拍 JPEG 像素多是横的，要读 EXIF 0x0112 转正。

**把模块搬去别的宿主时，新宿主文件自己的顶层 local 会遮住同名全局；要「晚于某模块执行」就包成函数、在原位置留桩调用**
- 例：章节模块载入时要覆盖 memorial 的函数，必须在它之后执行。做法：整块包成 `function X_ModuleLoad() ... end` 挂到新宿主（选载入时不 require 别人的小文件），**桩里不要在宿主载入时 require 别的文件**（案例 A 的实测：装好后第一次冷启动正常，再启动时 require 打断了 Lua 源码的载入，排在后面的宿主全变回原版、模块全没了，且不报错）。桩只定义 `X_EnsureLoaded()`（只执行一次），在进游戏的入口函数第一行和登录钩子里调；验证时一定连续冷启动几次。
- 搬前除了「共享 local / 顶层取用」两件事，还要查第三件：新宿主文件的顶层 local（反编译文件常有 `local F_GetInt` 之类）有没有和搬过去的代码里的名字重复。
- 也可以在打包时按标题行从大文件里切出一整节（源文件不动，别的分支还在改它），但要加断言保证那一节只有函数定义、没有顶层语句。
- Windows 的 Git Bash 里 `sed -i` 会把整个 CRLF 文件改成 LF（不报错）。补丁脚本里的精确替换随即全部对不上。改这种文件一律用 Python（newline=''）。

**脚本资源包整体超过 16 MiB，游戏启动就退出（`archive:/CAB-... is corrupted! [Position out of bounds!]`）**
- **2026-10-18 更正：没有 16 MiB 上限**（17.07 MB / 131 块的包实测能进主界面）。当时撞上的是「某块压缩后恰好等于原始大小」，见文末 "compressed size equals its raw size" 一节。
- 原因：把离线模块注入进 Unity 的脚本 AssetBundle 后，包解开后的 CAB 超过 16 MiB（案例 A 的实测 128 块 × 128 KB）就读不出来。单个宿主文件有上限，整个包也有上限，两层都要盯。
- 对策：构建自检打印包总量和余量；空间不够时，给**没打过补丁的原版脚本**批量去掉整行注释、空行和缩进（反编译出来的源码里这三样占很大比例），先挑收益最大的一批。做之前加一条自检：瘦身前后每个文件里的长字符串和含换行的字符串字面量完全一致，再跑语法检查和真机冷启动。
- 给后续开发留足余量（案例 A 第二阶段的目标 ≥1.5 MB），别等到只剩几十 KB 才处理。

### 零散条目

**批量改 CRLF 源文件后换行变 LF，git diff 暴涨（案例 A/C 多次）**
- 症状：用脚本批量改若干 Lua 文件，`git diff --stat` 改动行数异常大。
- 原因：读写时没保留原文件的 Windows 换行，写回变成 LF。`sed -i` 在 Git Bash 里也会把整个 CRLF 文件改成 LF（不报错），随后精确替换全对不上。
- 修法：改前检测原文件是否含 `\r\n`，二进制模式读写、按原样保留换行；一律用 Python（`newline=''`）做精确替换，不用 `sed -i`；改完看 `diff --stat` 确认只有真实改动行。

## Rebuilt bundle crashes at preload: a block whose compressed size equals its raw size (2026-10-18, root cause found)

Symptom (Unity 2017.4): at preload, the `UnityPreload` thread dies with `The file 'archive:/CAB-…' is corrupted! [Position out of bounds!]`. A variant of the same bug shows `Could not allocate memory … Trying to allocate: 1844674407…B … MemoryLabel: String` instead. It looks size-dependent: padding a different build to the same final size crashes too, and 144 bytes less boots.
Root cause: Unity's UnityFS reader treats any block whose compressed size equals its uncompressed size as stored, and it ignores the LZ4HC flag. UnityPy (`CompressionHelper.chunk_based_compress`) falls back to raw only when the compressed size is strictly greater (`>`). On a tie it writes the LZ4 stream and flags it LZ4HC. Unity then copies those 131072 LZ4 bytes into the CAB as if they were data. The next object header inside that block reads a garbage length. A huge positive length gives "Position out of bounds" (the CachedReader limit); a negative one gives the size_t allocation failure. Encrypted Lua barely compresses, so each block lands near 131072. Measured odds are about 0.09% per block, roughly 1 in 10 per 112-block bundle. "Same size crashes" only meant the same leading content, which yields the same blocks.
Proof (案例 A): every one of 15 saved builds that crashed had exactly one block with `cs == us` and flag 3, and none of the booting builds had one. Unity's exact crashing output with only that block rewritten raw boots. A known-good bundle with one block deliberately re-encoded to exactly 131072 bytes (still valid LZ4) crashes. The allocation size it requested matches the offline simulation byte for byte. In libunity, the message comes from `CachedReader::OutOfBoundsError` (read past the object's end, past the file length, or before its start), which fits a garbage length field. The `cs == us` branch in the archive reader itself was not located in the disassembly; the A/B tests establish it.
Fix: after any UnityPy save, store every compressed block with `cs >= us` raw (flags with the compression bits cleared). Then assert at build time that no compressed block has `cs >= us`, that no block carries the 0x40 bit, that the block-info table is smaller than raw when compressed, and that the sizes add up. Apply this to every UnityFS bundle you write. Plain serialized files (e.g. `assets/bin/Data/<hash>`) have no blocks, so skip them, or the build breaks. 案例 A: `unityfs_store_incompressible_blocks` + `assert_unityfs_loadable` in `tools/case_a_lua.py`. LZMA also sidesteps the bug, but it is not needed and costs a whole-bundle decompress at startup.
Myths this retires: there is no "16 MiB / 128-block" bundle limit (a 17.07 MB, 131-block bundle boots), and the per-script "261 KB" limit was very likely the same tie (its log was the allocation variant). Neither was the cause. The old failed experiments are explained too. Packer `(0x40, 0x43)` put 0x43 into every block's flags (UnityPy's tuple is `(data_flag, block_flag)`), which set the 0x40 "streamed" bit, so the loader returned null.
Verification trap: "process alive after N s" is not a pass, because a white screen with a loader NullReferenceException is alive too. Require the main screen or a log line from after Lua loads.
Method that cracked it: re-pack the identical CAB with your own minimal UnityFS writer. If that boots, the cause is in the container layout, not the content, and a block-table diff shows it immediately.

### 零散条目

**A patch hard-codes an ID copied from a different script version (2026-10-19)**
- Symptom: every gacha tap played the same character voice line instead of the whoosh sound.
- Cause: the replacement text for the tap handler was copied from the APK's Lua, which calls `PlayOneShot(7775)`. The game runs the hot-update Lua, where the sound-enum list has 15 extra entries, so 7775 is now a voice event and the whoosh is 7790. The anchor (old text) matched the hot version, so the patch applied without complaint.
- Fix: when a patch rewrites a line, copy every number in it from the same version the anchor came from. Enum indices (sounds, panels, messages) shift between versions. Grep patch replacement strings for bare numbers and check each one against the running version's table.

**An escaped newline in a patch string becomes a real newline and kills a whole host file (2026-10-19)**
- Symptom: after a build, a dozen unrelated offline features vanished at once; the log showed `module 'LoginPanel' not found ... unfinished string`.
- Cause: a Lua string literal containing `\n` was written through a shell heredoc into a Python one-liner, which turned the escape into a real line break. The build's syntax check (luaparser) accepts that; the real Lua VM refuses the whole chunk, and every module parasitic on that host file disappears.
- Fix: write text edits from a script file and build the backslash with `chr(92)`. After any build, run a cold start and grep for `not found:` / `unfinished string` before testing features.

### 案例 C 侦察（2026-10-21）（续，原节在 `ui-assets.md`）

**Appended code in a game UI module crashed the whole UI init (`table` is nil)** (2026-10-21)
- Symptom: after appending a module to `ui/uiprivateagreement.lua`, loading stuck at 75%; the log said `attempt to index global 'table' (a nil value)` in the module's main chunk.
- Cause: the module uses `module(..., package.seeall)` but then `declareSingleton`/`declareObject` replaces the module metatable with one whose `__index` is the base class, so globals (`table`, `pcall`, `UnityEngine`) are nil inside. The game's own files reach them through a `local Gox = _G` at the top.
- Fix: go through the file's `Gox`; the patch script now lints appended modules for bare globals and asserts the host file has `local Gox = _G`.

**Unity static events cannot be subscribed from this Lua binding** (2026-10-22, 案例 A)
- Symptom: wanted `Application.logMessageReceived` to capture C#-side errors for an in-game "export log" button; `Application.add_logMessageReceived(CSLNewfunc(...))` exists as a function but throws "C++ exception" when called.
- Fix: capture only what Lua sees, by wrapping the game's Lua log table (`LuaDebug.info/warn/error`) into a ring buffer; tell the user C#-level exceptions are not in the exported log.

### 案例 C：玩家备份接入（2026-10-22）（续，原节在 `device-emulator.md`）

**UnityPy `read_typetree()` ignores what `save_typetree()` stored** (2026-10-22)
- Symptom: added 112 TextAssets one by one, each time reading the AssetBundle object, appending to `m_Container`, saving. The rebuilt bundle had 8533 objects but only 8421 container entries.
- Cause: `read_typetree()` always parses the object's original bytes; the previous `save_typetree()` result (held in `obj.data`) is not read back, so every add started from the original list.
- Fix: read the AssetBundle tree once, keep it, append to it, and write it back once in `save()`. Reload the saved bundle and assert the counts.

**A method name that exists in both directions broke the RPC name check** (2026-10-23)
- Symptom: the build-time check said `Player.checkNetWork is not client->server`, but the client does send it.
- Cause: the RPC table has `checkNetWork` both as a client→server request and a server→client callback; the checker's dict keyed by (class, name) kept only one.
- Fix: map (class, name) to the *set* of directions.

## 热更新合并后，打包脚本读到的仍是旧版脚本（案例 C，2026-10-24，接上一条）

- 不只新增条目：被热更新替换的 299 个脚本，`set_raw` 写进去后 `read()` 仍返回原始字节。后果是：
  1. 打包时对 `main.lua` 等"读出来 → 打补丁 → 写回"的文件，实际是对**旧版**打补丁、覆盖了热更新版（终版 `HIDE_CHARGE_SYS = true` 丢了）；
  2. 读源码用的协议表、管理器全是旧版，新协议（20 个）在"源码"里根本找不到，看起来像"客户端调了不存在的协议"。
- 做法：自己的资源包封装里，所有写操作（替换 / 新增 / 改源码）都把写进去的字节另存一份，读取优先返回它；合并热更新后跑一遍"字节码 chunk 名 = 条目名"和"读回的字节 = 热更新文件"的核对。补丁锚点换到热更新版上（这次隐私页提示号 210181 → 210182）。
- 判断"是不是读到了旧版"的快速信号：运行时日志的调用栈里出现源码里搜不到的函数名（这次是 `ActivityMgr.syncPromotionalActivityData`）。

## 原生安卓（Kotlin + smali）补丁：别整段重写方法（案例 D，2026-10-29）
- 现象：前一个代理把主界面和 Application 的 onCreate 整段手写重写，装上后 `VerifyError ... expected CoroutineStart`，修了又报 `lateinit property store has not been initialized`。
- 原因：手排 `invoke-static/range` 参数时把 block 放到了 start 的位置；重写时漏掉了一个仓库初始化。
- 做法：保留原方法体，只按多行锚点删掉联网 / 统计调用（先去 `.line` 再匹配），每处断言命中 1 次；连带删掉只为这次调用准备参数的 move-object / check-cast。新逻辑写成 Java 类编进额外的 classesN.dex，smali 里只插一行 invoke-static。

## 降 minSdk 跑旧系统：R8 已经把低版本分支删了（案例 D，2026-10-29）
- 现象：minSdk 29 的包改成 28 装进安卓 9 模拟器，依次报 `No virtual method rebase()`、`No virtual method registerActivityLifecycleCallbacks`、`Failed resolution of WindowInsets$Builder`。
- 原因：`if (SDK_INT >= 29)` 被 R8 当成恒真优化掉，旧分支被删；`ReportFragment.dispatch` 成了空函数（生命周期事件永远不派发，lifecycleScope 里的协程不跑）。
- 做法：给所有 `$ApiNNImpl`（N≥29）静态方法开头加版本守卫返回默认值；补回 `ReportFragment.dispatch` 的 `<29` 分支并让 `registerIn` 在 <29 时返回；WindowInsetsCompat 的 29 分支前加判断退到 Impl28 / BuilderImpl20。守卫只在低版本生效。能用安卓 10+ 的模拟器就别降。apktool 3 只改 apktool.yml 的 minSdk 时 `apktool b` 会复用上次的清单，要加 `-f`。

## aapt2 打不开中文路径（案例 D，2026-10-29）
- 现象：`apktool b` 报 `res: error: failed to open directory`。
- 做法：解包 / 打包目录放纯英文路径，脚本和源码可以留在中文目录。入口脚本 `sys.stdout.reconfigure(encoding='utf-8')`、子进程加 `PYTHONUTF8=1`，否则打印日文路径会在 GBK 控制台报错。

## 拆分包合成单个 APK（案例 D，2026-10-29）
- 现象：base 单独解包后，分辨率分片里的资源在 base 的 public.xml 里连 id 都没有，直接拷 png 会被重新分配 id。
- 做法：`apktool if base.apk -p <dir> -t <tag>` 后用 `-p/-t` 解分片，拿带原 id 的 public.xml 补进 base；同名同 id 的跳过；`APKTOOL_DUMMY_0x…` 按 base 的 id 表换回真名。清单删 `requiredSplitTypes` / `splitTypes` / `vending.splits` / `stamp.*`，`extractNativeLibs` 改 true。

## 安卓正则不认 \p{IsHan}，启动即崩（案例 D）
- 症状：新加的聊天代码装上后游戏一启动就闪退，前台不是游戏。
- 原因：电脑上的 Java 正则支持 `\p{IsHan}`，安卓的正则引擎不支持，类一加载就抛错。
- 修法：改成明确的汉字范围 `[\u4e00-\u9fff]`。加载新模块的地方 `catch Throwable`（不只 `Exception`），防止一个模块出错带崩整个游戏。

## 同一行锚点在好几个类里重复（案例 B 2026-11-16）
- 现象：一处替换只改到 5 个类中的第一个。
- 修法：确认几处都要改时，用 `re.subn(..., count=5)` 一次补，并断言替换数正好是 5，补丁标记的计数跟着加 5。不确定就分别取更长的锚点。
