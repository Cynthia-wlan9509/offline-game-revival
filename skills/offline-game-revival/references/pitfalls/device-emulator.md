# 设备、模拟器、注入调试工具的坑

真机和 BlueStacks、adb 和多 adb server、往设备推资源、Frida / 调试通道注入、录屏、Windows shell 的路径改写。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

## 工具链 / 环境（实测坑）

**Frida 探针从注入线程调用 Unity / 配置表 API 直接把游戏搞崩**
- 症状：`Error: access violation accessing 0x...`，脚本在 `LuaDoString` 那一行炸掉，游戏进程也可能不稳。
- 原因：注入线程不是 Unity 主线程；`CSLTypes.DataTableMgr.getInstance()` 这类会碰 Unity 对象的调用不安全。
- 实测**安全**的调用：`UnityEngine.PlayerPrefs`（读写+Save）、部分纯逻辑单例（`ComUIPanelMgr.GetIntance()`）。
- 修法：探针只做「读结果 / 写 PlayerPrefs」这种轻量动作，把结果落到 `shared_prefs` 再读回来；
  需要读配置表就**离线解包**，别在运行时穿。

**正确姿势：让注入的代码「在主线程上跑」——用游戏的调度器中转（本篇最有价值的一条）**
- 背景：注入工具（Frida 等）的回调跑在**自己的线程**上，直接碰 Unity / 配置表 / UI 必崩或卡死。
  但"只看不敢摸"会让验证退化成猜。
- 解法：注入时**只做一件事——把真正的工作登记给游戏自己的调度器**，让它在主线程执行：
  ```lua
  local holder = {}                       -- tolua 需要 table+function 形式
  local function body()                   -- 这段会在 Unity 主线程跑
    local dt = CSLTypes.DataTableMgr.getInstance()
    -- 这里可以安全地读配置、读/写模型、调游戏自己的业务函数
    GameNS.UnityEngine.PlayerPrefs.SetString('PROBE_OUT', 结果)
    GameNS.UnityEngine.PlayerPrefs.Save()
  end
  -- 关键：第一个参数传 nil！见下方说明
  CSLTypes.LuaScheduler.delay(nil, 0.2, CSLNewfunc(holder, body))
  ```
- **`obj` 参数一定要传 `nil`**。很多调度器的实现是「obj 为空则挂到全局系统对象」，
  例如本项目 `LuaScheduler._getNode(nil)` 会回退到 `LuaFrame.LuaGameSystem.Instance.gameObject`。
  这样外层段落**完全不需要在注入线程上取任何 GameObject**——而"取 GameObject"正是导致
  `access violation` / 游戏进程被杀的主要原因（实测约 1/3 概率崩，且会把游戏带下去）。
  传 nil 后连续多次调用都稳定。
- 反例：写 `CSLTypes.CommonFuncion.GetIntance():GetCurRunUIList().gameObject` 虽然多数时候能过，
  但要在这个不稳定的调用上赌运气，没必要。
- 取结果：写进 `PlayerPrefs`，再从 `shared_prefs` 的 XML 里读回来（跨线程/跨进程都稳）。
- 注意：**外层段落本身仍在注入线程**。`GetCurRunUIList()` 这类取 GameObject 的调用多数时候能过，
  但并非绝对安全（实测会偶发 `access violation`）。要更稳就把"取 go"也放进更早一次调度里，
  或者干脆只调用这个已知可用的取法。
- 收益：用这个方式可以**直接调游戏自己的业务函数做端到端验证**，
  不用辛辛苦苦走 UI（实测用它验证了「卡牌升级 / 突破 → 属性真的上涨 → 落盘」整条链）。
- 纪律：**动了玩家存档要还原**。验证完把临时写入的 prefs 键删掉并重启让种子重建，
  确认关键字段回到原值，再向用户汇报。

**从注入线程调用会「改 UI」的游戏函数 → 游戏整体卡死（比 crash 更阴）**
- 症状：进程还活着、无异常日志、CPU 空闲，但画面定格、点击毫无反应。
  用 `dumpsys gfxinfo <pkg>` 会看到 `Total frames rendered: 0`（正常应是持续增长），`50th percentile` 是个巨大值。
- 触发例：从探针线程直接调 `SomeUI:OnCancel()` / `popLayout:dispose()` 这类会动 Unity UI 对象的方法。
- 平反：这**不是游戏 bug**，重启即恢复。别据此判定"修复把游戏搞坏了"。
- 修法：**交互必须走主线程**。要么用 `adb shell input tap`（走系统输入链路，安全），
  要么只让探针做"读状态"，然后用游戏自己的日志回读判断进度。
- 关键习惯：**游戏自己的 `[TAG]` 日志就是最好的断言器**。驱动交互时每步 grep 日志
  （如 `xxx show step=N` / `xxx completed`）比截图判断可靠得多，也能立刻分辨
  "没推进"到底是"没点中"还是"逻辑错了"。

**`adb install` 报空错误时改用 push + pm install**
- 症状：`Failed to install xxx.apk: `（原因串为空），1 秒就返回，像是没传文件。
- 修法：`adb push xxx.apk /data/local/tmp/a.apk` 然后 `adb shell pm install -r /data/local/tmp/a.apk`，
  报错会完整得多，也能装上。

**模拟器（BlueStacks）里 `input tap` 命中区域偏**
- 症状：按钮视觉位置正确，点上去只听到点击音、日志 `Button On Click empty`，弹窗/入口毫无反应。
- 排查：用坐标扫描（同一点附近 ±40px 打几发）确认是「命中区偏移」而不是「事件没绑」；
  再调 Lua 直接触发回调对照——回调能跑就说明逻辑没坏，纯是输入层问题。
- 修法：优先改成**游戏内 Lua / 回调驱动**的验证路径；必须用点击时多试几个坐标，
  别把「点不中」误判成「功能坏了」。

**`adb shell input text` 灌不了长文本：会被按键序列打断，还有单次长度上限**
- 症状：把授权码 / token 一类长串（几百字符）灌进输入框，结果只剩尾部几十个字符，或半路触发
  ESC / TAB 把界面搅乱；看起来像"校验失败"，实际是输入根本没进全。
- 原因：`input text` 走的是按键事件模拟，特殊字符要转义，且单次调用有长度上限。
- 修法：长文本别指望自动化输入——**留给人手工粘贴**，或换通道（先写进 prefs / 文件再让游戏读）。
  验证"输入 → 放行"这类链路时，如果自动化输入失败，只能报告"输入通道未验证"，
  不要写成"授权码校验不通过"。

**注入通道在一次失败的调度之后一直超时**
- 症状：往游戏主线程排一段脚本，日志报调度失败；之后每次注入都 `TransportError: timeout`，游戏本身还活着。
- 修法：重启游戏再注入。调度用的宿主对象换成一直存在的那个（主界面），不要用"当前界面列表"。

**注入的脚本里遍历宿主语言的容器，游戏原生层直接崩**
- 症状：往游戏里注入一段只读的诊断脚本，进程直接退出，`pcall` 接不住。
- 实例：用游戏自带的遍历函数（`CSLEach`）走 C# 字典 `m<玩法>CardDic`，两次复现。
- 修法：要枚举就从配置表拿编号，再逐个问模型的查询函数；不要在注入线程里直接遍历 C# 容器。
- 相关：游戏连续运行近一小时、注入过几十次后，一次普通注入也可能崩在注入工具自己的线程里（`gum-js-loop`）。长测试隔一段重启一次，崩了先看栈在谁的线程，别急着怀疑游戏逻辑。

**系统悬浮条（录屏、游戏加速条）会自己挪位置，固定的"禁点区"不可靠**
- 症状：照着坐标点游戏里的按钮，点到了压在上面的录屏悬浮条，打开了系统相册，游戏被盖住。
- 修法：每次点击前看当前截图里悬浮条在哪，而不是记一个固定区域；开测前请设备主人把悬浮条关掉最省事。点出去以后立刻停手，报告前台是谁，不要在别的应用里继续点。

**Windows 的 Git Bash 里 `adb push x /sdcard/...` 报 `secure_mkdirs failed`，目标路径变成了 `<Git 安装目录>/sdcard/...`**
- 原因：Git Bash 会把以 `/` 开头的参数当成 Unix 路径转换成 Windows 路径。
- 修法：命令前加 `MSYS_NO_PATHCONV=1`，或者用 PowerShell 调 adb。

**大 APK 装不上、adb 自己起不来、降级装旧包不干净（案例 G 2026-11-12~15）**
- 症状：1 GB 左右的包 `adb install -r` 报空白错误；开发脚本跑完后 adb 服务反复挂；“装回旧版再覆盖安装”的回归里，旧版跑的其实是之前推进去的测试脚本。
- 原因：流式安装在大包上不稳；脚本里用了变量名 `TMP`，盖掉系统临时目录，adb 重启时找不到路径；降级安装不会清掉推到应用目录里的测试 JS。
- 修法：大包用 `install -r --no-streaming`，失败先强行停掉应用再装；脚本变量别叫 TMP / TEMP / PATH 这类系统名；要测“干净的旧版”，先清掉应用目录里推过的测试文件，或卸载重装（签名不同必须卸载，先备份存档）。

**调试通道只有一条：自动脚本和手工命令抢同一个文件，结果会串（案例 G 2026-11-10）**
- 症状：查一个值，返回的是自动脚本上一条命令的结果；或者自动脚本整轮没点到任何东西。
- 原因：调试通道是“游戏每隔几百毫秒读一个文件并执行”，两边写同一个文件；另一个会话把别的游戏推到了前台，脚本点的是别的程序。
- 修法：自动脚本运行时不插手动命令（或给结果带序号）；每一步先确认前台是自己的游戏。

## 游戏内读相册 / 自定义图片（案例 A 2026-10-17，tier/custom-media）

**注入测试的代码太长时：先 adb push 到游戏目录，再注入一小段 `loadstring(File.ReadAllText(...))()`**
- `v3_dev.py luamainfile` 把整段代码放进命令行，60 KB 的模块报 `WinError 206 文件名或扩展名太长`。

**真机是用户自己的手机：他一碰屏幕就停手**
- 本轮两次：安装后用户正好在用手机，脚本拒绝重启；进游戏后进程被用户划掉（logcat 只有 `signal 9 (Killed)`，前后没有任何 Lua / Unity 报错）。先用 `phone_guard.seconds_since_user_activity()` 等到空闲几分钟再继续，别把「被杀」当成自己的 bug 去查。

**frida 注入 `luamain` 会和主线程抢 Lua 虚拟机：偶尔直接 SIGSEGV（tolua_getvaluetype）**
- 主界面静止时注入一段只读状态的代码，主线程在 `lua_pcall` 里崩、画面冻住、进程还活着（frida 吞了信号）。看起来像「自己的模块把游戏卡死了」，其实是注入。
- 做法：上机验收尽量点界面 + 模块自己打的日志（把状态写进 `installed ...` 这类日志行），注入只在必要时用，崩了先查崩溃栈里有没有 frida / 注入时间点。

**脚本用裸 `adb shell input` 点屏幕，会被当成「用户在用手机」**
- `phone_guard` 只认 `v3_dev.py` 自己发的输入；裸 adb 点完立刻 `v3_dev.py restart` 会被拒绝。要么全程用 `v3_dev.py tap`，要么等 60 秒以上。

### 零散条目

**注入工具（Frida 把 Lua 源码当命令行参数传）在 Windows 上有长度上限**
- 超过约 32k 字符的自测脚本直接 `WinError 206`，脚本根本没跑；批量跑自测时如果把输出丢掉，看起来就像「没有任何日志」。要么拆小脚本，要么让注入工具改成读文件。
- 另一个现象（案例 A BlueStacks）：跑完带拨时间的长自测后，排到主线程执行的注入（ScheduleOnce 回调）常常不再触发，普通注入照常；冷启动恢复。批量跑时每个之前先做一次主线程 ping，失败就冷启动。

**注入探测要排到游戏主线程跑，不要在注入线程里直接执行 Lua**
- 案例 A：`v3_dev.py lua`（Frida 线程里直接跑 Lua）在游戏开着时探测几次，游戏主线程就卡死：点不动、Unity 日志停，进程还在。`luamain`（排到主线程的定时器里跑）一直没事。
- 卡死后再用 `luamain` 也不执行，像是「注入坏了」，其实是游戏已经卡住。批量自测前后、探测状态，一律走主线程。

**Windows 的 Git Bash 没有 pkill**：`pkill -f xxx 2>/dev/null` 静默失败，以为停了的后台脚本其实还在跑，会和新开的脚本抢设备。用 PowerShell 的 `Get-CimInstance Win32_Process | ? CommandLine -like '*xxx*' | Stop-Process`。

**整行注释删除要认得块注释**：只删「以 `--` 开头的行」时，块注释 `--[[ ... --]]` 的结尾行 `--]]` 也会被删，注释关不上，后面的代码全被吞掉（语法检查才抓得到，运行时是静默少了一大段）。瘦身器必须跟踪长括号状态（含 `--[[` 开头和同一行就关上的 `[[...]]`），并且对瘦身的每个文件做「长字符串内容前后一致 + 语法」两条自检。

**MIUI 对首次安装的新应用（新包名）弹「USB 安装提示」，10 秒没点自动拒绝（案例 A，和分身测试相关）**
- 症状：`adb install` 报 `INSTALL_FAILED_USER_RESTRICTED`，提示约 50~60 秒后才弹、只停 10 秒。
- 修法：让用户在手机旁，或把包放进手机下载目录让用户自己点；只有用户明确授权后，才在前台确实是该提示时（焦点是 `AdbInstallActivity`）由脚本点一次「继续安装」，不循环重试（2026-10-22 补：另一台同系统真机直接忽略 adb 注入的点击，两次都被系统取消。脚本代点不一定管用，首选让用户亲手点）。同包名同签名的覆盖安装不弹。推送文件设 `MSYS_NO_PATHCONV=1`，否则 Git Bash 把 `/sdcard` 路径转坏。

## frida 注入的「排到主线程执行」也会偶发崩溃（案例 A 2026-10-18）
- 连续两次注入（设参数 + 跑文件）或连跑多个自测时，主线程在 lua_pcall → strstr → frida 钩子里 SIGSEGV。
- 做法：把参数拼进同一个脚本文件一次注入；每次注入之间留几秒；崩了冷启动，别把它记成游戏 bug（栈里有 frida-gadget 就是工具问题）。

## Your own `adb input text` trips the "someone is using the device" guard (2026-10-18)

The guard reads the system's last-user-activity time. Input sent with raw `adb shell input text/tap` (not through the tool that records its own input times) counts as a human. Every later scripted tap is then refused. If the refusal message is piped to /dev/null, this looks exactly like "the button does nothing" and gets misread as a game bug. Send all input through the same guarded tool, or wait about 60 s afterwards, and never discard the tool's output.

### 案例 C 侦察（2026-10-21）（续，原节在 `ui-assets.md`）

**Shell quirks that wrote files to the wrong place (Git Bash on Windows)**
- `/tmp_xxx` in Git Bash is the Git install directory (`<Git install dir>\tmp_xxx`), not a temp folder; the safety check then refuses to `rm` it. Use the session scratchpad or a project path.
- The heredoc backslash pitfall recorded above (Bash tool folds `\\` to `\`) bit twice more here, once while appending this very entry. Write scripts and docs with the file-writing tool, not heredocs.
- Git Bash also rewrites device paths in arguments: `adb pull /data/local/tmp/x` became `<Git install dir>/data/local/tmp/x`. Prefix the command with `MSYS_NO_PATHCONV=1`, or avoid device paths on the host side altogether (next entry).

**Root-owned files cannot be pulled; stream instead**
- Symptom: `su -c "dd … of=/data/local/tmp/x"` worked, then `adb pull` failed with "remote open failed: Permission denied".
- Fix: skip the temp file: `adb exec-out su -c "dd if=/proc/<pid>/mem bs=4096 skip=<page> count=<n> 2>/dev/null" > local.bin`.

**BlueStacks changes orientation between launches; taps from an old screenshot miss**
- Symptom: the "同意" tap that worked in one run did nothing in the next; the dialog had switched from landscape (1600x900) to portrait (900x1600).
- Fix: take a fresh screenshot and read its size right before every coordinate tap, or find the control in the UI dump.

## 案例 C：玩家备份接入（2026-10-22）

**Backed up the test save, then uninstalled in the same line; the backup had failed** (2026-10-22)
- Symptom: `adb pull /sdcard/…/save.mp …; adb uninstall <pkg>` — the pull printed "failed to stat remote object '<Git install dir>/sdcard/…'", the uninstall went ahead, the test save was gone.
- Cause: Git Bash rewrote the device path again (entry above), and `;` does not stop on failure.
- Fix: `export MSYS_NO_PATHCONV=1` at the top of every Bash call that passes device paths, and chain "back up → destroy" with `&&`, never `;`. Check the backup file exists before any uninstall or `pm clear`.

**`pm clear` wipes the pushed resources too** (2026-10-23)
- Symptom: after `pm clear` for a fresh-save test, `Android/data/<pkg>/files/` was gone, 3.7 GB with it.
- Cause: on Android 9+ clearing app data also clears the app's external files dir.
- Fix: for a fresh save while keeping resources, delete only the save file; use `pm clear` only when you mean to test first-run resource import.

**The phone was attached, but `adb devices` did not show it** (2026-10-24)
- Symptom: Windows listed the phone as a USB device, yet `adb devices` only showed an emulator.
- Cause: several projects share the machine, and each runs its own adb server port. The USB device was claimed by the server on port 5038, not the default 5037.
- Fix: run `adb -P <port> devices` on each port in use (find them with the process list: `adb -L tcp:<port> fork-server`) and target the phone through that server. Don't kill another project's adb server to grab the device.

**Old-style storage permission still reads Download on Android 14, but can't delete there** (2026-10-24)
- Symptom: a targetSdk 28 build found and read resource zips in `/sdcard/Download` after the storage permission prompt, but `os.remove` on them silently failed.
- Cause: scoped storage (Android 11+) lets an app delete only files it created itself; the zips came from another app (browser, file manager, adb).
- Fix: after importing, check whether the file is really gone and, if not, tell the player to delete it in the file manager.

**Measured the wrong UID on the phone** (case B, 2026-10-24)
- Symptom: a real-phone "zero sockets" result that proved nothing.
- Cause: the UID was taken from the owner shown on files in `/sdcard/Download` (`u0_a203`, the storage mapping), not from the game process (10360).
- Fix: take it from `ps -o UID -p $(pidof <pkg>)`, and run the same poller once against an app that is known to be online as a control.

**scrcpy recorded silence with `--audio-dup`** (2026-10-24)
- `--audio-dup` (keep the phone playing while recording) uses Android's playback capture, which an app targeting < 29 does not allow by default, so the game was silent. Without it scrcpy records the output mix via shell privileges (the phone speaker is muted meanwhile) and the game audio is there.
- Point scrcpy at the project's adb and port (`ADB=…`, `ANDROID_ADB_SERVER_PORT=…`), or its bundled adb starts a server on 5037 and fights for the device. Its matroska files carry a color-matrix tag swscale rejects; `setparams=colorspace=bt709:…` before scaling.
- Starting scrcpy on the portrait launcher and then launching the landscape game left the mkv header with the portrait SPS; every landscape frame decoded as smear. Remuxing with `-c copy -bsf:v h264_mp4toannexb x.ts` lets the decoder pick up the in-band SPS, and the footage was fine.

**演示视频：点按打时间戳，用画面运动量对齐录像，自动剪掉空等（案例 C 2026-10-24）**
- 症状：真机录一遍，原始素材 24 分钟，大半是等待和加载，手工找起止点很费劲。
- 修法：录屏的同时，脚本每次 adb 点按都记下主机时间。剪辑前先算录像的逐帧运动信号，用一次已知的点击标出主机时钟和录像之间的偏移（实测误差约 0.5 秒），再按点按记录生成剪辑表：空等段加速，高光段保持原速。成片抽帧拼成总览图，逐段检查开头有没有残留的加载画面或主界面。本例从 5 分半压到 3 分钟出头。
- 没声音时：先查是哪种静音（响铃模式、勿扰、媒体音量为 0）。只在录制期间临时调高媒体音量，录完调回原值；录制时声音被接走，手机本身不会外放。本来就没有背景音乐的开头（免责页、登录页），用主界面的音乐垫上。录完要还原测试存档、删掉授权码文件、释放设备登记。

## 原生层崩在 ARM 转译库里，不一定是转译器的问题（案例 D，2026-10-29）
- 现象：模拟器上冷启动约 1/5 闪退，SIGSEGV，栈全在 libhoudini。
- 原因：竖屏游戏在横屏窗口里启动被重建，Live2D 的 `onPause` 先于渲染视图的 `onStart` 到达，原生层在主线程、无 GL 时建模型。
- 做法：失败时整段 logcat 存下来，看游戏自己打印的原生事件顺序，和一次正常启动逐行对比。修在 Java 侧：没收到开始就忽略暂停。至少统计 10 次冷启动再下结论。

## 真机上 adb 打字会被用户的中文输入法改掉（案例 D，2026-10-29）

## 手机本地模型被系统后台限速、发热降频，慢到每秒一个字（案例 D）
- 症状：llama.cpp 在手机上跑小模型，测速程序前台跑还行，丢后台当服务只有约 1 token/s；充电发热时每句等 15~30 秒。
- 原因：MIUI 对后台进程限速；系统在发热 / 充电时把大核降频；线程落在小核上更慢。
- 修法：服务由游戏 App 内部拉起，按本机 CPU 频率自动选大核绑核（骁龙 888 选 4~7 核、4 线程）；提示词缩短、固定样本句以复用缓存、回复限长、流式显示；关掉思考模式。文档写明拔线凉机后才快。
- 随游戏发出去：APK 里只带 llama-server 和依赖库（约 +66MB，无需额外 C++ 运行时），模型 1~2.5GB 首次使用时游戏内下载——先显示本机内存和剩余空间（内存不足建议改用 API、空间不够直接拦），多镜像排序、慢了自动换源、断点续传、下完校验 SHA-256，按核数 / 频率自动定绑核和线程数。国内源可能很慢（模拟器实测 20~30 KB/s），镜像顺序要能调。
- 现象：`adb shell input text "http://127.0.0.1:8765/v1"` 得到 `12700：//..1.：8765/1v…`。
- 做法：不改用户的输入法。验接口做成“预设一键填好 + 测试按钮自动发一句”，用 `adb reverse` 把手机端口映射到电脑上的假接口。小米“USB 安装提示”10 秒自动拒绝，要在脚本里轮询前台、看到安装确认 Activity 就点。凌晨测带语音的游戏用 `appops set <包名> PLAY_AUDIO ignore`，测完改回 allow。

## BlueStacks 上 adb 打不了中文：用电脑剪贴板粘贴（案例 D，2026-10-29）
- 现象：`adb shell input text "中文"` 在安卓 9 上什么都不输入，中文的验收（关键词匹配、轻生分支）一直没法在设备上测。
- 做法：BlueStacks 会同步电脑剪贴板。PowerShell `Set-Clipboard -Value '中文'` → 点输入框 → `adb shell input keyevent 279`（KEYCODE_PASTE）。测前存下用户原来的剪贴板，测完还原。真机不要这么做（会动用户手机的剪贴板）。

## 真机"连上了"但 adb 看不到：被别的 adb 服务占了（案例 D 2026-10-31）
- 现象：设备管理器里有手机，`adb devices` 里没有（连 unauthorized 都没有）；重开默认 adb 服务也没用。
- 原因：电脑上同时开着几个 adb 服务（这次是另一个项目在另一个端口上的），先抢到 USB 的那个独占手机。
- 做法：列出所有 adb.exe 进程和端口，逐个用 `ANDROID_ADB_SERVER_PORT=<端口> adb devices` 查；找到后用那个服务**同版本**的 adb 客户端去连（版本不同的客户端会把服务杀掉重启，打断别人的会话）。动手前先看前台是不是有人在用。
- 游戏内下载大文件：国内镜像速度差别很大（hf-mirror 远快于魔搭），按实测排顺序，并在开头 20 秒测速、太慢就换源续传。

## 热注入一次别塞太多（案例 A 2026-11-16）
- 现象：通过调试通道一次注入约 60 KB 的整个模块，游戏随即 SIGSEGV 闪退。
- 做法：只注入改动的那几个函数；改动多就直接重新打开发包装上。

## 往模拟器推十几 GB 资源：Windows adb 管道会截断（2026-11-17）
- 现象：电脑上流式读备份里的 tar，`adb shell` 管道往设备送，只送了约 24 字节就停；BlueStacks 也不支持 `exec-in`；busybox 的 `nc`、`tar` 在设备上段错误。
- 原因：Windows 版 adb 往 shell 管道送二进制不可靠；`adb forward` 关闭时会丢掉还在路上的数据。
- 修法：`adb forward tcp:N tcp:N` + 设备上 `toybox nc -l` 接收、`toybox tar` 解开；设备解完回一句确认（如 `TAR_RC=0`）后电脑端才关 socket。16 GB 约 17 分钟，不占电脑硬盘，推完核一遍 md5。
- 从设备拉文件到中文路径会失败：先拉到英文路径，或用 `adb exec-out cat` 重定向。

## BlueStacks 上推到 /sdcard 的文件，属主别改成 App 的 uid（2026-11-17）
- 原因：BlueStacks（Android 9）的 `/sdcard` 是 FUSE，直接往底层 `/data/media/0` 写时，属主要是 `1023:1023`（media_rw），App 会自动看成自己的；chown 成 App uid 反而读不到。
- 修法：root 下写底层目录后 `chown -R 1023:1023`，再用 App 读一遍确认。

## 改 bluestacks.conf 弄坏编码 / 实例被系统杀（2026-11-17）
- 现象：用 PowerShell 改了 `bluestacks.conf` 一行，整个文件编码变了；6 GB 内存的实例被系统杀了两次。
- 修法：先停那台实例、备份，按字节只改一行，保留原编码。31 GB 内存的主机最多同时跑两台，单台 4 GB 够用。实例默认 `max_fps=30`，录演示视频改 60 要重启实例。
