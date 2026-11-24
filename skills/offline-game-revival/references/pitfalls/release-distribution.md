# 分档、授权、发包的坑

授权码和本机码、分档开关、免费包硬检查、正式包剥资源、联网权限、发包后台任务。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

### 启动阶段（续，原节在 `local-server.md`）

**授权码：所有玩家的本机码一样 / 设备上验签代码报 BigInt 未定义**
- 原因：引擎自带的"设备信息"多是 MAC/IMEI，新版 Android 统一返回假值；嵌入式 JS 引擎（如 LayaNative 的 V8）可能很老，没有 BigInt。
- 修法：本机码从 Java 层取 `ANDROID_ID`（smali 加一个静态方法，走引擎已有的 JS→Java 反射桥）；验签用不依赖 BigInt 的实现，并与标准库对拍。
- 实例：案例 B，见 `case-b-laya-native.md`「授权码 + 水印」。

### 工程与文档（续，原节在 `agent-workflow.md`）

**正式包悄悄带着开发包的东西发出去（案例 A 2026-10-14、10-20）**
- 症状：加了 `--final` 打出来的包里仍然带着 Frida gadget（监听本机端口的调试后门）；另一次，正式包里的开发开关 `OFFLINE_V3_DEV` 还是 true，构建清单却写着已关闭。
- 原因：构建脚本不区分开发包和正式包，无条件把调试通道打进去；`--skip-patch` 复用了上一次开发构建打过补丁的 Lua，正式模式下设置发布标记的补丁步骤被跳过了。
- 修法：正式构建时换回原包的 classes.dex，不带 gadget 库，并在末尾自检（包内没有 gadget 条目、dex 里没有加载行、清单写明 `debug_gadget:false`）；`--final` 和 `--skip-patch` 同时出现就直接退出；发包前从包里解出 Lua 核对开关值，不信清单。去掉调试通道后，用正式包做的分身在真机上启动并玩一段，证明能正常运行。
- 怎么确认的：对比两份 classes.dex，类、方法、字段数完全一样，字符串表只多一条 `frida-gadget`；解出正式包里打过补丁的 Lua，看到开关为 true，带上补丁步骤重打后变成 false。

**出正式包的后台任务被会话结束或机器重启打断，留下半成品（案例 B 2026-11-03）**
- 症状：出包停在签名阶段，后台任务显示已停止，机器当天还重启过。
- 原因：会话结束时后台任务被一起终止，加上内存不足和重启。
- 修法：复工时先看中断留下了什么，把半成品挪到别的目录（不删）。确认内存和磁盘够用后，用同样的命令重出。比对源码指纹，和半成品一致才沿用之前的回归结果。

### 工具链 / 环境（实测坑）（续，原节在 `device-emulator.md`）

**签名绑定要「载荷里签过名的值」对「包内 / 本机的生效值」逐项比，别只验签名就放行**
- 授权码载荷里的群号、设备码、到期日、功能位都取自签过名的载荷，再和包里的群号、本机设备码、今天的日期比；功能位不要另存一个可手改的数字，存授权码**原文**，每次启动重新验签再算。
- 到期日别和包里的常量做字符串相等（改包里常量就绕过了，签发新到期日也会全部失效）；`YYYY-MM-DD` 字符串可直接按字典序和今天比大小，注意用固定时区（北京时间 +8）。
- 过期的授权码不要把已经玩过的人挡在门外：保留旧的「已解锁」标记当兜底，档位退回最低档。
- 门禁整体关闭开关（`gate_bypass`）要在**正式包构建的自检里断言为 false**，不要只断言赋值存在。

**去掉 INTERNET 后，推送 / 统计 SDK 在后台线程抛异常杀进程（案例 G 2026-11-10）**
- 症状：没有 INTERNET 的正式包装上后启动就回桌面，日志里是 SecurityException；带调试通道的测试包一切正常。
- 原因：和本文件前面“去掉 INTERNET”几条是同一类：包里带的 Firebase 一类 SDK 初始化时联网被拒，异常抛在非主线程，没人接。
- 修法：在应用最早的入口（`attachBaseContext` 里 `super` 之后）装一个全局未捕获异常处理器：非主线程的异常记日志后吞掉，主线程的交回原处理器。同时仍要补网卡枚举返回 null 的空指针补丁，两个问题叠在一起，修了一个看起来还是闪退。
- 怎么确认的：没有 INTERNET 的正式包冷启动，进主城，存档在。

## 分档 / 授权开关（案例 A 2026-10-17 合并时）

**「载入时算一次」的开关跟不上授权：授权码是登录时才验、还能在设置页中途换**
- 症状：封顶章节写成模块顶层的 `if ... then MAX = X end`，载入时授权模块还没验码（或玩家后来升档），封顶就一直是旧值。
- 修法：做成函数（`V3C_ApplyCap(why)`），载入时、登录钩子最前面各调一次，并把它暴露给授权模块在换码后调；依赖封顶的其它改写（七日任务恢复原版）也挪进这个函数，降档时能放回去。

**开发用的覆盖键一定要挂在开发开关下面**
- 症状：调试时加的「存档键 X 存在就把封顶改成 X」在正式包里照样生效，能动存档（Android 备份还原）的人就能绕过付费 / 授权位。
- 修法：所有 `*_DEV_*` 存档键只在 `OFFLINE_V3_DEV = true` 时读；正式包打包时把开发开关关掉（`--final`），自测脚本里断言这一点。

**按开期过滤活动：在「判当前期」的唯一入口把关，但规划 / 诊断类调用要另给一个不过滤的版本**
- 做法：十几个活动模块判「现在是哪一期」都经过同一个 `TrackState`，把授权和开期规则塞进它，模块一行不用改。
- 坑：有些模块拿同一个函数扫未来几十天算日历、查和别的活动撞不撞期；过滤后它们看到的是「全关」，算出来的日历是错的。把原函数改名 `TrackCalendar`（纯日历），扫日历的调用和自测里核对日历的断言改调它。
- 外部窗口函数（兑换码 / 自排）由别的会话提供：不存在、报错、返回 nil 一律当没有；进行期以外的兑换期由本线按轨道参数补，接口文档里写清楚「返回的是进行期」。

**从活动轮换里拿掉一期：挖成空档，别删条目（案例 A 2026-10-20）**
- 症状：把轮换表里的一期删掉后出开发包，补丁自检卡在“该活动没有入口图”上，构建失败。
- 原因：核对脚本默认轮换表里每一期都有入口图。另外，直接删条目会让后面几期的日期整体前移，打乱手机上正在进行的那一期。
- 修法：删期改成“挖空档”（槽位保留，但不开），让核对脚本认得空档。动手前先对比改前、改后的轮换日期。

**放开类补丁别把门槛一起放没了（案例 A）**
- 症状：全新档一进游戏所有功能全开；半仙阁所有关卡全开；花笺突破一次后升级上限变成 100。
- 原因：离线补丁用总开关让主线解锁判断直接返回 true、把强制显示按钮的旧补丁留着；解锁 / 上限条件写得太宽（没判主角等级和上一关通关，上限公式写错）。
- 修法：关掉绕过开关，让原版的解锁判断（`ComUnLockMgr:CheckUnLock`，含 0 等级 / 1 猫数 / 2 主线任务 / 3 店铺等级 / 4 无条件）走完整；强制显示按钮的补丁改成按配置表行判断；按原版条件实现（半仙阁每章第一关要主角等级 + 通过上一章，花笺上限 `min(突破数+10, 100)`）。自测要覆盖「不该开的没开」，用全新档验证。
- 相关：汇报「某功能锁着」之前，先读代码确认那条规则是否真的被执行，别凭印象——曾报半仙阁第二章锁着，实际离线代码根本没判主角等级，用户的档正好满足所以看不出差别。

### 游戏内读相册 / 自定义图片（案例 A 2026-10-17，tier/custom-media）（续，原节在 `device-emulator.md`）

**剥资源的正式包：活动「入口」和「面板」不在同一个资源包里**
- 活动图标在共享包（案例 A 是 `prefab/<活动目录>`），面板在各自的包（`prefab/activity/<名字>`）。只剥面板时入口照样出现，点进去才 asset isnull。
- 修法：保留名单和「运行期允许开哪些活动」用同一份清单（`release_content.json` 的 activities 由打包脚本填进 Lua），不在清单里的活动有兑换码也不开。
- 验收要用「资源按正式包剥、脚本开发开关还开着」的测试包，才能在没有真授权码时模拟高档位；真正的 `--final` 包只能验无位的情况。

**留下的资源包在总清单里依赖已剥掉的包，整包加载为 null（案例 A 2026-10-24）**
- 症状：瘦身包里点活动商店，回包正常，窗口始终不出现；日志只有 assetbundle null，没有缺文件报错。把窗口所在的包补回保留名单后照样打不开。
- 原因：几个活动的兑换商店共用一个窗口，预制体在一个已剥活动的包里。补回这个包后，它在 Unity 总清单（名为 `Android` 的 AssetBundleManifest）里还登记了两个已被剥掉的图片包作依赖。加载器先按清单加载依赖，缺一个整包就返回 null，哪怕窗口根本没用到那两个包里的图。
- 修法：打包期用 UnityPy 改总清单的 typetree，把每个保留包依赖列表里已被剥掉的项删掉；存回后照样走「压缩块不能等于原始大小」那套处理和可加载自检（见文末 compressed size equals its raw size 一节）。开关只放在瘦身 profile，全资源版先干跑一遍确认没有这种情况。删依赖前先用 UnityPy 看预制体实际引用了哪些依赖包的资源，真用到的要补包，不能删依赖。剥任何活动之前，先 grep 面板类名和包路径，看有没有别的活动在借它的面板。
- 怎么确认的：读总清单列出该包的依赖，只有那两条是被剥的；只剪这两条后重打，窗口和兑换确认框都正常，剥离自检全过。

**群里按日期发的活动码，在某些玩家手机上提示「已过期」**
- 原因：离线版的统一时钟带着「开发时间偏移」（测试时用来模拟过天），正式包为了不打乱已有存档的天数进度，会沿用存档里的偏移。按真实日期签发的码，拿游戏时钟去比就错开了偏移的天数。
- 修法：码「现在有没有生效」用真实时间判断；交给活动面板的开始 / 结束时间再加上偏移，平移成游戏时钟，这样活动里显示的剩余时间也一致。授权码的到期日同理。
- 查法：上机检查时故意用一份带偏移的存档跑一次。

### 零散条目

**给用户双击的 .bat 要纯 ASCII + CRLF，并按双击方式实测（案例 A）**
- 症状：用户双击后窗口一堆乱码报错。
- 原因：文件是 UTF-8 中文 + LF 换行，cmd 读不了；中文文件名在命令行里也传不过去。
- 修法：批处理文件和文件名都用英文、CRLF 换行；确实要用中文时，整个文件存成 GBK + CRLF（简体中文 Windows 按 GBK 读）。结尾加 `pause`，出错时窗口不会一闪就没。会删东西的脚本，先给一份只显示、不删除的空跑版跑通。交付前按用户双击的方式（`Start-Process`）真的启动一遍。

## 改了「发哪些内容」的清单，正式包的派生文件要跟着重算（案例 A 2026-10-18）
- 现象：发布清单从第 1-5 章改成第 1-15 章，`--final` 打出来的包第 6-15 章对白全没了，构建全绿。
- 原因：正式包读的是一份预先剥离好的配置文件，只有手动跑剥离脚本才更新；构建脚本只打印「using stripped config」。
- 做法：正式构建里无条件重算所有由清单派生的文件；或者至少比较派生文件和清单的修改时间，旧了就失败。

## License entry must be reachable after first launch

Once a device is unlocked, the startup gate is skipped, so upgrading needs an in-game entry. Ours is avatar → System Settings → "授权码 / 兑换码". The original panel's text fields were sized for short strings; enable `resizeTextForBestFit` and show the device code plus the current tier on two lines. The chapter cap is computed at load, so tell the player to reopen the game after redeeming.

### 案例 C：玩家备份接入（2026-10-22）（续，原节在 `device-emulator.md`）

**"Offline" build still phoned home whenever the phone had a network** (case B, 2026-10-24)
- Symptom: none visible. Every test had run with the game's network blocked, so nobody had looked. With the network open, the build sat on the disclaimer page and tried 22 addresses within 100 s (publisher analytics and gateway, one-tap-login SDK, QQ Connect with the phone model).
- Cause: only the privacy dialog had been skipped; the publisher SDKs still initialize in `Application.onCreate` and after the privacy callback.
- Fix: drop `INTERNET` from the manifest and add a release check that fails if it is back. Then cold start with the network open and expect zero sockets and zero DNS queries for the app's uid.
- Side effect to look for: without `INTERNET`, Java DNS lookups throw `SecurityException` (not `IOException`), and `NetworkInterface.getNetworkInterfaces()` returns null. The SDKs caught theirs; the engine's MAC lookup did not, and startup died on an empty device-info JSON. Keep the network-*state* permissions, because a missing one throws as soon as an SDK calls it.

**Removing INTERNET made a vendor ROM ask "allow this app to turn WLAN on or off?" on every launch** (case B, 2026-10-24, HyperOS)
- Symptom: three seconds after each cold start a system dialog from the security center asked whether the game may toggle WLAN. The emulator never showed it.
- Cause: the publisher SDK reads the MAC address by enumerating network interfaces; without INTERNET that returns null, so it falls back to `setWifiEnabled(true)`, reads `/sys/class/net/wlan0/address`, then restores the old state. A targetSdk < 29 app can still really toggle WLAN on Android 10+; MIUI/HyperOS intercepts it as a prompt.
- Fix: stub the fallback (return empty, the SDK's own "no MAC" branch). Lesson: after removing a permission, cold-start on a real vendor-ROM phone, not only an emulator, and grep the SDKs for calls that change device state (`setWifiEnabled`, `requestNetwork`, `startUsingNetworkFeature`).

**去掉 INTERNET 后，真机上点进设置就闪退（案例 C 2026-10-24）**
- 症状：手机上点头像进设置就闪退，模拟器上不崩，所以夜里的自动测试没抓到。
- 原因：设置界面会经发行方 SDK 发 HTTP 请求，真机上没有联网权限，直接抛 `SecurityException`。
- 修法：在离线网络补丁里，把全局 HTTP 客户端的 get / post 一类方法换成只记日志、不发请求（日志打 `http ... dropped (offline)`）。去掉权限之后，要在真机上把每个入口都点一遍，并在脚本层拦掉所有 HTTP。

## 分档：免费版不许带的东西要有硬检查（案例 A 2026-11-16）
- 用户要求免费版里不能有任何 AI 相关的东西。除了打包时按功能剥代码，还加了两道"出现就失败"的检查：构建时在整个 Lua 包里搜关键字，验证脚本在 APK 里查额外的 dex、模型推理库、模型文件。
- 免费版的验证脚本要带和构建时同一个环境变量（内容清单的绝对路径）。不带的话它按全资源版的期望行数算，会误报失败；用相对路径时构建脚本换了工作目录也可能找不到清单。

## 免费包硬检查的误报（案例 A 2026-11-16）
- 现象："不许带 AI"的检查在干净的免费包上报失败。
- 原因：一是原版自己就有同名的词；二是功能前缀被别的模块共用（这次和天气模块撞了前缀）。
- 修法：检查只用功能专有的名字；再拿全资源包跑一次，确认检查真能抓到。
