# 引擎路线：Unity C# 热更层包内拦截（Mono / ET Hotfix / HybridCLR）

> 来自三款 Unity 手游：Unity 2019.4 Mono/ET Hotfix（`code.unity3d` + `Hotfix.dll`）、一款 Unity Mono（扁平覆写树 + Cecil 宿主补丁 + AXML 删网）、Unity 2021.3 IL2CPP + HybridCLR（`bytes.unity3d` + `Game.dll` + `BattleSystem.dll`）。

## 适用条件

- 核心业务代码以标准 .NET DLL 存放在热更 AssetBundle（`code.unity3d` / `bytes.unity3d`）或 `assets/bin/Data/Managed/` 中；
- 即使底层为 IL2CPP，只要采用 HybridCLR / ILRuntime，热更 DLL 往往是明文标准 IL（或仅带轻量固定前缀）。

## 核心侦察与解包要点

1. **固定偏移前缀不是加密**：
   - `code.unity3d` 常见 **7 字节零前缀** + `UnityFS`（宿主 `LoadFromFile(path, 0, 7)` 跳过）；
   - 那款 HybridCLR 游戏全部 15,550 个 `.unity3d` 均带 **22 字节双头前缀** `UnityFS\x00\x00\x00\x00\x085.x.x\x002021`；
   - UnityPy 回写 bundle 时**必须原样拼回前缀并立即回读校验**，同步检查 `.manifest` CRC / `listsetting` MD5。
2. **区分真热更 DLL 与 AOT 补充元数据 DLL**：
   - HybridCLR 的 `bytes.unity3d` 同时包含完整 IL 业务 DLL（如 `Game.dll`、`BattleSystem.dll`）与 stripped AOT 补充元数据 DLL（`mscorlib`、`System`、`Root` 等，`extern` 空体），反编译看 `extern` 与 `return` 数量一眼分清。
3. **常见配置表魔数**：
   - **Tabtoy v4**（`GameConfig.bin`）：头 `\x02\x00\x00\x00TT` + ver=4 LE + build + MD5 + TLV，可直接解析客户端 `Deserialize` case 表自动转 JSON；
   - **UTF-8 明文 TSV**（如 `configbyte.unity3d` 1,434 表）：自带类型/注释/字段名三行表头。

## 补丁、脱壳与进程内模拟服架构

1. **首选工程组织：扁平覆写树（取代几十个 `patch_*.py` 长链）**：
   - 缓存只读反编译原树 `hotfix_ilspy_raw/`；
   - 日常改动全放 `hotfix_overrides/`（少量覆写原文件）+ `offline/`（全部离线业务模块），构建时先拷原树再叠覆写目录，极大降低合并冲突与维护成本。
   - 若原热更 DLL 极大（如 16.5 MB / 13,047 类型），优先采用 **Mono.Cecil 极小锚点织入 + 独立编译 `OfflineLogic.dll`**，编译只需 2 秒。
2. **宿主脱 SDK 与零 apktool 删权限**：
   - **Mono 宿主 Cecil 5 锚点**：`HasSdk=false`、假 CDN、内置 `GlobalVersion`、`internetReachability=1`、埋点空返；注意 **修改 `async` 方法为直接 kickoff 时必须清掉 `AsyncStateMachineAttribute`**，`br.s` 跳转做后置覆写；
   - **smali 6 锚点**（必要时）：禁渠道 Application / Splash WebRequest 与注册、`PlatformSdkFactory -> Empty`、删 `mInstrumentation` Hook（保留正常生命周期）；
   - **零 apktool 删 `INTERNET`**：正式包直接用 `scripts/strip_internet_axml.py` 对 `AndroidManifest.xml` 做等长 UTF-16LE 原地替换 `INTERNET -> NO_NET__`；隔离测试包才用 `apktool d`（不带 `-r`）改包名/authorities/删重名广告 `FileProvider`。
   - **IL2CPP AOT 启动关口**：先装原包断网冷启，核查 `sharedassets0.assets` 内 `ScriptableObject`（如 `lzCfg.IsUseSDK`）能否免改 `.so` 绕过。
3. **进程内模拟服防重入与写接口红线**：
   - 拦截 `Session.Call` / `GameNetBase.Access` 路由至本地 Handler（配 `check_handler_owners.py` 强制唯一归属，防重复注册）；
   - **`OfflineChannel` 与本地回包必须异步下一帧回注**（严禁在 `Call` 栈内同步回调触发 `OnShow` 递归死锁！）；
   - 动态创建 UI 激活后显式调用 `GraphicRegistry.RegisterGraphicForCanvas` 防按钮穿透；
   - **未接写接口严禁默认成功兜底**（仅只读查询允许反射兜底，未实现写接口必须显式拒签并记日志）。

## 快循环与构建避坑

- **~17s 增量热推**：优先利用热更读盘路径（如 `persistentDataPath/<productName>/Bundles/independent/code.unity3d`），增量编译 bundle（~7.5s）→ 事务热推冷启（~10s）；每次热推必核日志 **Build ID** 防 `GlobalVersion` 清掉热更目录；
- **独立 UID 隔离测试包**（`.offlinetest`）：正式包与测试包并存互不干扰；操作前后核正式档 SHA-256；用带 `instanceId + nonce` 的文件命令（`clock/gm-command.json`）驱动跨日与 GM；
- **MSBuild 隔离 `obj/`**：切换正式/测试条件编译时必须分离 `BaseIntermediateOutputPath`，在 `.targets` 排除 `obj/bin/**/*.cs` 且用追加模式 `$(DefineConstants);...` 防重复 `AssemblyAttributes` 编译错；
- **大数与异步原子写档**：LitJson 遇到超 `int.MaxValue` 数值（`Int64→UInt64`）易崩，统一存为 `string`；存档改为后台队列 + `BeginBatch` + `File.Replace` 原子落盘 + 退后台强制刷盘，避免同步 `fsync` 卡顿与残留 `.pending`。
