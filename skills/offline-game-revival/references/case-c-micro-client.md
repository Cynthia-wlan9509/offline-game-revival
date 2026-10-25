# 案例 C：大厂发行的 Unity 微端（Unity Mono + SLua）

2026-10-21 开始。项目目录 `<项目根>`，结论文档 `docs\RECON.md`（事实和推断分开写）。
这一页记"大厂系 Unity 游戏长什么样、哪些东西第一天就该查"，给下一个同类项目当模板。

## 一眼认出大厂系

`lib/` 下有 `libMSDK.so`、`libgcloud*.so`、`libtersafe.so`、`libTDataMaster.so`、`libBugly.so`；
`assets/` 下有 `MidasPay.zip`、`msdkconfig.ini`。对应：MSDK 登录、GCloud（Dolphin 版本更新 + Puffer 按需下载 + TConnd）、
TP 反作弊、TDM 埋点、Bugly、Midas 支付。

## 第一天就要做：资源完整性

**先对清单，再谈改造。** 这个包 1.2 GB，看着像全量包，实际是微端：

- `assets/manifest.native`（`ResourceManager.ManifestNATIVE` 的 BinaryWriter 格式：版本串、uint 版本、long 总大小、
  字符串表、每个包的 size + 16 字节哈希 + 依赖 + 资源）列了 42,700 个包 / 4.62 GB，APK 里只有 12,120 个 / 1.05 GB。
- 按服装数据表对模型：约 5040 件衣服只有 466 件的模型在包里。
- `launchconf` 里 `_ClientType: 2`（MICRO）是同一件事的另一个证据。

脚本：`tools\parse_manifest.py`（输出缺失按目录的统计）。资源从哪来是用户要拍板的事，要在动手改代码之前问。

## 逻辑层：Lua 5.1 字节码，"加密"只是改了头

- 8420 个 TextAsset 在 `res/lua.assetbundle`，头是 `1B 4C 75 61 51 01 01 04 04 04 08 00`。
  标准 5.1 第 6 字节（format）是 `00`，这里是 `01`——unluac 报 "non-standard lua format: 1"。改回 `00` 就能全量反编译，操作码没打乱。
- 判断能不能直接放明文补丁：看 C# 加载器传给 Lua 的 `bytecodeOnly`/mode 参数。这里从 bundle 读是 `false`，补丁可以是明文 Lua，
  不用找 32 位 `luac`。
- 并行反编译：每个文件起一次 JVM，16 线程，8420 个约 25 分钟。

## TP 加固壳：重签名的包 2 秒后 `exit(4)`

- 认法：`AndroidManifest` 的 `Application` 是 `com.<厂商>.tpshell.TPShellApplication`；`lib/` 里有 `libtprt.so`，字符串里有
  `FileChecker`、`tpshell_crc`、包名、`mono_patch`；`assets/` 里有 `__tpinfo.tsa`、`__tpcfinfo.tsa`、`comm.t.p.sin`、`tpginf.dat`。
- 症状：改过内容或重签名的包，停在 MSDK 协议页约 2 秒后进程退出，logcat 只有 `Process … exited cleanly (4)`，没有 Java 异常。
- 程序集前 0x1000 字节的"强加密"就是它在运行时用 `mono_patch` 解的，`libmono.so` 是普通的。
- **去壳**（已验证能进登录页）：
  1. 开关在 dex 的字符串常量里（`TPConfig.sReflectedShellInfo = "sReflectedShellInfo: true"`，取冒号后的值和 `"true"` 比）。
     把 `sReflectedShellInfo` 和 `sReflectedTP2Info` 的值改成 `TRUE`：长度、字符串池排序都不变，只重算 dex 头的 SHA-1 和 adler32。
     TP2 也要关，否则壳关了以后会去加载不存在的 `libtersafe2.so`。
  2. 壳不在了就没人解程序集，所以要换成明文——从**原版游戏的进程内存**里导出：root 下读 `/proc/<pid>/maps`，逐个匿名区
     `adb exec-out su -c "dd if=/proc/<pid>/mem …"` 流到电脑上，用已知的异或明文主体定位。壳在 Mono 解析完后只清零了前 0x80 字节
     DOS 头，用同一构建里普通 DLL 的 DOS 头补回即可。脚本 `tools\dump_managed.py`，产物存 `recovered\`（不可再生）。
  3. 结果：去壳后普通 Mono 直接加载明文程序集，C# 也变成可改的了。

## C# 层：Mono 程序集"半加密"

- `Assembly-CSharp.dll` 和 `-firstpass.dll`：前 0x1000 字节强加密（TP 壳运行时解，见上节），其余整体异或单字节密钥（`<单字节密钥>`）。
  认法：自相关看不出周期，但深处成片出现同一个字节（明文的 0 变成了那个密钥字节）。
- 不逆 `libmono.so` 也能反编译：异或掉尾部，按 mcs 布局重建 PE 头。全部从尾部的地标反推并断言：
  `_CorDllMain`/`mscoree.dll` 导入表、`FF 25 00 20 40 00` 跳板（入口 RVA）、`.reloc` 块指向跳板、`.rsrc` 里的
  `VS_VERSION_INFO`、`BSJB` 元数据头。
  - 有的程序集多一个 `.sdata` 节（静态字段初值）：表现为 `.text` 和 `.rsrc` 之间有空洞、`.text` 文件偏移是 0x400 而不是 0x200。
    漏了它 ILSpy 会报 "Field data (rva=…) could not be found in any section"。
  - 丢失的只是落在前 4KB 里的方法体（这次 87 + 123 个小构造函数/getter）。
  - 脚本：`tools\rebuild_managed.py`；反编译用 NuGet 上的 `ilspycmd` 8.2（net6，本机只有运行时没有 SDK 也能 `dotnet ilspycmd.dll` 跑）。
- 只做静态分析时这样就够了。真要改包，走上节的去壳 + 内存导出（重建的头和真实头只差十来个字节，验证了这条路是对的）。

## 启动链路上的开关

- `Launcher.__StartGame`：`LaunchConf.CheckVersion == false` 就直接 `EnterGame()`，不连 Dolphin。
- `LaunchConf` 是 `Resources.Load("launchconf")` 的 TextAsset，头 4 字节 + 异或 `<密钥>`，内容是 JSON。改数据就能关掉版本检查。
- 启动 Activity 是 MSDK 的 `MSDKPolicyActivity`（发行方的用户协议和隐私政策）。原包跑在模拟器上会先停在这里，点"同意"是替用户签发行方的协议，要先问用户。

## 开屏和协议页：一层层找，别只找一处

用户说"去掉发行方和开发商的开屏"，实际分散在五个地方，**每一层的改法都不同**（2026-10-21）：

| 画面 | 在哪 | 改法 |
|---|---|---|
| 首启协议页、权限说明 | MSDK `MSDKPolicyActivity`：正文是 `assets/msdk_*_content.html`（`Html.fromHtml` 进 TextView），标题是 `resources.arsc` 字符串 | 换 HTML；arsc 字符串池是 UTF-8 时可以原地缩短（新长度 + NUL + 零补位，偏移不动） |
| 开发商 logo（白底 2 秒） | **Unity 引擎开屏**，配置在 `globalgamemanagers` 的 PlayerSettings（`m_SplashScreenLogos`，贴图在 `globalgamemanagers.assets`）。认法：贴图名搜得到、所在文件是 `globalgamemanagers.assets` | `m_ShowUnitySplashScreen` 置 0。5.5 没有 TypeTree 也没有 `SplashScreen.Stop`，按字段顺序数偏移：productGUID(16) + 4 个 int + accelerometerFrequency + companyName/productName（长度前缀字符串）+ defaultCursor(12) + cursorHotspot(8) + 背景色(16) → 0x64 |
| 发行方 logo 视频 | `assets/android.mp4`，C# `Launcher.Awake` 里 `Handheld.PlayFullScreenMovie` | 程序集是明文（去壳后）就直接 NOP 掉那段 IL（`ldloc.0 … pop`，栈平衡、长度不变），dnfile 核对调用令牌 |
| 游戏内协议框 | Lua 面板 | 借外框换皮成免责声明 |
| **开场 CG 开头又一段开发商 logo** | `start.mp4`（92 秒）前 5 秒，新角色第一次点开始才播 | ffmpeg 从 CG 第一帧（恰好是关键帧）流复制截掉开头，不重编码；`pip install imageio-ffmpeg` 自带 ffmpeg |

最后一处只有真机走到建角才看得到——**找开屏要把所有 mp4 抽帧看一遍**，不能只看启动时播的那个。健康游戏忠告页底部有著作权人和版号，是静态法定页，保不保留问用户。

## 网络：自研 RPC，协议表在 Lua 里

- C# `RpcChannelMgr` 只管 TCP；方法表、参数类型、实体属性定义都在 `manager/net/rpc/dump.lua`（772 个方法）。
- 收发都经过 Lua（`RpcChannel.sendRpc` / `NetMgr:revcRpcCall`），所以本地服务器可以整个写在 Lua 里，回包直接调实体的 client 方法，不经序列化。

### 本地服务器怎么接（已跑通：握手 → 建角 → 主界面 → 重启读档）
- 接管 `RpcChannel.sendRpc/connect/isConnected/disconnect/reconnect`、`NetMgr.makeChannel`、`ClientStatic.setNetSeed`，C# 网络一次都不碰。
- **回包不序列化**：服务器给的就是 Lua 值，照抄 `revcRpcCall` 写一个 `deliver()` 分发（txn 释放、coid 回值、静态/实体方法）。
- **实体属性**原版是 LZ4 字节流，交给 `createEntity → initRpcEntity → refreshEntityProperty`。不必实现序列化：做一个"属性袋"表（带空的 `Lz4Decode` 方法）冒充 ByteArray，`refreshEntityProperty` 是模块函数、调用时按名字查，包一层见到属性袋就按表赋值，原版建实体的整条路一行不改。
- 发给客户端前按 rpcdef 类型"整形"：线上读出来的结构体是"位置键 + 字段名键 + 元表"，数组是 `rpctype.array` 对象（带 `_type`、`add`），照这个样子造。
- 两个方向都深拷贝、都排到下一帧：原版界面常常"先发请求，再设等待标记"，同步回包会抢在标记之前被丢掉。
- 带 `txn` 的方法处理完要把 `txn` 属性 +1，否则客户端一直锁着。
- **只发存档里有的属性**，其余让客户端填默认值；需要非默认值的属性从报错里一个个找（`home.homeSkinId`、`home.<npc>Id`、`homeTree.treeLv`……）。全补零会出事，见 `pitfalls.md`。
- 不走 MSDK：`GameApp.isMsdk` 恒 false，原版内部开发用的"账号 + 令牌"登录流程就出来了。
- 打包时拿包里的 `dump.lua` 核对本地服务器用到的每个方法名和方向，写错直接打包失败。

## 去服务器找资源（停服后）：让游戏自己的 SDK 去问

- 域名形如 `<服务>.<区>.<appid>.<云厂商域名>`，停服后 DNS 仍能解析到云厂商的通用网关，8080 能连但对 HTTP 回空——**那是公共网关，
  端口通说明不了任何事**。不要试图手写 GCloud 协议（Puffer 是 pebble RPC + eifs 清单）。
- 可靠的办法是看 SDK 自己的日志（`E/GCloud`，`SetLogger(4)` 默认就开着）：
  - 原包：停在 MSDK 协议页（点"同意"要先问用户）→ Dolphin 走 TGCP `tcp://<ip>:10062`，失败就弹"更新失败:网络错误"，原版本身就进不去了。
  - Puffer 在版本检查之后才初始化，原包走不到。要用**关掉版本检查的探针包**（去壳 + `launchconf` 改 `_CheckVersion` + 打开日志），
    MicroAssetMgr 启动时就会初始化 Puffer：走 TGCP `:10072`，失败时日志是 `MakeSureGetUrlFromServer connect server timeout` →
    `get url from server failed <code>`。
- 本例（2026-10-21）的结论：游戏服、Dolphin、Puffer 全停，缺的 3.32 GB 只能找民间来源（玩家手机的 `Android/data/<pkg>/files/`）。
  仍然活着的只有 TDM 埋点和 GCloud 云控，离线版要关掉，不往发行方发数据。
- Puffer 配置在 Lua 表 `data/packdef`：产品号（安卓微端正式环境有几个 id）、服务器地址、落盘目录。

## 玩家手机备份 = 终版客户端 + 全部资源（2026-10-22）

用户找来一份小米手机的应用备份（5.4 GB zip），一天之内把"1/4 资源的纪念版"变成了"停服前最后一版、资源 100%"。做法可以照搬：

**1. 认格式，流式解。** zip 里是 `descript.xml`（`<MIUI-backup>`）+ `<应用名>(<包名>).bak`。`.bak` = 几行文本头
（`MIUI BACKUP\n2\n<包名> <名字>\n102\n0\n`）+ 标准 Android Backup（`ANDROID BACKUP\n5\n0\nnone\n` = v5、不压缩、不加密）+ tar。
不用解压 zip 到磁盘：`zipfile.open()` → 跳过头 → `tarfile.open(mode='r|')` 流式写出（6 GB 约 90 秒）。tar 里：
`apps/<包>/a/base.apk`（安装包）、`ef/`（= `Android/data/<包>/files/`，**微端下载的资源就在这**）、`f/ db/ sp/ r/`（内部数据）。
其他品牌的备份（华为、OPPO、vivo）多半也是"厂商头 + tar 或 ab"，先看前 512 字节。脚本：`tools\extract_backup.py`。

**2. 三方对账，不要假设备份里的 APK 和你手上的一样。** 这次备份里的 base.apk 和我们一直在改的 APK **版本号、versionCode 完全相同，
却有 1518 个文件不同**（程序集、lua bundle、清单、dex、上千个资源包）——同版本号的后期重打包。资源清单有三份，版本号依次是
手上的旧 APK < 备份 APK < 外部目录（热更后终版）。拿**外部那份清单**逐个对 MD5（`tools\backup_coverage.py --md5`）：
43,245 个包 = 31,153 个在 `ef/assets/` + 12,091 个在备份 APK 里，全部吻合。清单里的 16 字节哈希是 4 个小端 int，按 4 字节反转才是文件 MD5。

**3. 底包换成备份里的 APK。** 终版资源是配终版程序打的；即使 Lua 绑定接口一模一样（这次 13,594 个成员逐一比过），
C# 也有改动。原签名的 APK 壳能正常跑，所以再从内存导一次明文程序集：装原版，**root `am start -n <包>/.<Unity 主 Activity>` 直接进 Unity，
绕开 MSDK 协议页（不替用户点"同意"）**，Mono 加载完就能导。补丁脚本的锚点全带断言，换底包后只有一处 PPtr 号变了（0xb8b → 0xb8c），
其余原样通过——这就是断言的价值。

**4. 热更层要并进包里，不能留在外面。** 外部目录里除了资源包还有：
- `upl/<md5(小写脚本名)>`：热更 Lua 字节码（411 个 = 299 个覆盖旧脚本 + 112 个全新脚本），`LuaProxy.LoadLua` 先读它再读 bundle；
- `lua.bytes`（异或 JSON）：终版全部 8532 个脚本的名字、MD5、长度，用来核对每个 upl 文件；
- `manifest.native`：终版资源清单。

微端启动器在**新装首启**会跑 `ClearUnversionFilesCompareWithPackage`：删外部清单、删 `upl/`，再按**包内**清单检查外部资源——
包里也有同名文件的删外部那份，包里没有的算 MD5、和包内清单不符就删。所以离线包必须：
①把终版清单当包内清单；②把 upl 并进 `lua.assetbundle`（新脚本要往 bundle 里**新增** TextAsset，见 `tools\bundle_tool.py` 的 `add_raw`）；
③把"包里有、后来又热更过"的 28 个资源包（shader、几个 UI 图集和 prefab）在 APK 里直接换成终版文件。
第一次没做③，首启后外部少了 28 个文件，游戏回头去读包里的旧版，而清单说的大小已经是新版的。

**5. 外部资源怎么交付**：3.7 GB 加 1.2 GB 的 APK 超过单个 APK 的 4 GB，塞不进去。做法：资源打成几个 **STORED（不压缩）zip 分卷**，
每卷 < 2 GB（游戏是 32 位 ARM，Lua `io` 的偏移是 32 位），第一项放一个小标记文件写"第几卷 / 共几卷 / 清单版本"（改了文件名也认得出）；
游戏里在原版"您还需下载 X GB"那一步换成导入流程：申请存储权限 → 在 Download、网盘目录里找 zip → 查剩余空间 → 纯 Lua 从头顺序读、
`.tmp` 再改名、已存在且大小相同就跳过（可中断续导）→ 进度写在启动阶段现成的对话框里 → 导完问要不要删 zip。模拟器上 3.7 GB 导入 329 秒。
真机（Android 14）同样能读 Download，导入只要 32 秒；但删不掉别的程序放进 Download 的文件，要提示玩家手动删。
整个导入逻辑是 Lua 模块，不碰 Java/C#：SLua 绑定里现成有 `AndroidPlugin.checkPermission/requstePermission`、`FileTools.GetFiles`、`readSDCardM`。
脚本 `tools\respack.py`、模块 `tools\lua\offline_resimport.lua`。

**6. 文件导进去了，还要把下载器的"账本"销掉。** 微端判断某个资源下完没有，查的是它自己的缺失表（`MicroAssetMgr.allBundles_`，新装时按包内清单
把所有外部包记成缺失、存成 `res.dat`；原版下载器每下完一个删一条），不查文件。只导文件不销账，凡是资源不在 APK 里的剧情都提示"尚未完成下载"
——前三关能玩是因为它们的资源恰好在 APK 里，差点就漏过去。修法：在资源启动流水线收尾时，把文件已在的条目删掉、重写 `res.dat`（3 万多个文件检查，
分帧做，模拟器 2.8 秒）。验收时专门挑资源**只在外部**的内容去点（`offline_micro.lua`）。

## 本地服务器：并行写模块（2026-10-23）

接口多（这个游戏 355 个客户端请求），一个系统一个 Lua 文件，按下面的顺序拆给子代理并行写，一天内补齐了商店、签到、每日任务、成就、邮件、工坊、抽取：
1. scout 先出**请求↔回调对照表**：每个请求的参数、客户端在哪发、等哪个回调（`RPCWaitSend` 第二个参数就是它在等的回调名）、回调拿到数据干什么、用哪些数据表。主会话抽查几条再用。
2. 主会话写一份**模块编写约定**（框架 API、存档放哪、发奖走哪个函数、错误码、跨天、禁止碰构建）和一个**几秒钟的自检脚本**（Lua 5.1 语法 + 方法名和方向对得上协议表），worker 各自只改自己的文件、各自跑自检，互不抢构建目录。
3. 主会话负责**跨模块的连线**（任务进度事件：剧情、购物、抽取……谁在哪调）、合并构建和真机验收。worker 在 lupa 里拿真数据表单测过，但跨模块联动和 UI 时序只有真机能验。
4. worker 会顺手发现别的模块的 bug（这次：奖励表的掉落池 `quantity` 是"掷几次"，原来只掷一次），由主会话判断后修。
