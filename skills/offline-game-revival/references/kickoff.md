# 开工（第 0 步侦察 → 路线选型 → 快循环底座 → 垂直闭环）

这一页负责把一个陌生 APK 从“盲盒”推进到**可秒级迭代 + 已跑通最小垂直闭环**的工程态。

## 总流程（仅保留 2 个极短人工拍板闸口）

```text
[第 0 步只读侦察 + 10 分钟破壳探针] ──▶ (闸口 1：用户拍板立项 + 填 2 分钟预授权单)
       │
       ▼
[工作区建基(Git+扁平树+设备锁)] ──▶ [秒级快循环底座] ──▶ [最小垂直闭环验收]
                                                               │
                                                               ▼
                                          转 autopilot.md 批次推进
```

---

## 第 0 步：纯只读侦察（不改原包、半天内给结论）

写任何业务逻辑前，必须用实测证据回答 5 个问题，输出 `work/analysis/STEP0-ASSESSMENT.md`：

1. **运行自动侦察脚本**：
   ```powershell
   python -B <skill>/scripts/recon_apk.py <orig.apk> work/analysis
   ```
   一次核清：包名、版本、ABI（32 位包必核模拟器 `ro.product.cpu.abilist`）、**ZIP32 风险预警（条目 >65,535 或体积 >4 GB 合并扩展包会崩）**、DEX 列表、加固壳特征、`global-metadata.dat` 标准头、`UnityFS` 偏移前缀（7B / 22B）、Tabtoy v4 / `UF\0\x01` / LuaJIT 魔数、资源清单差集。
2. **判断“本体齐不齐”**：拿资源清单与 APK 逐项做差集，并核查是否存在 GB 级热更扩展包；本体缺失严重的微端**立即停下**，优先征集老玩家缓存或手机备份。
3. **判断“逻辑层在哪 & 能不能解开”**：
   - 不要把固定前缀（7B 零头 / 22B 双 `UnityFS` 头）误判成强加密；
   - `libxlua.so` 存在但包内 0 个 `.lua` 时，立刻检查 `bytes.unity3d` / `code.unity3d` 是否为 **HybridCLR / ET Hotfix C# DLL**；
   - 遇加密脚本（XXTEA+尾 4B 源长 / `UF\0\x01` 查表 XOR），先写可逆编解码并过 **`encode(decode(x)) == x` 回环断言**。
4. **判断“战斗规则在不在手机里”**：直读源码区分**本地确定性演算**（优先保留原引擎）与**纯服务端发 `BattleReport`**（评估重建成本，交用户拍板）。
5. **10 分钟快速破壳探针（可选，遇疑似壳/SDK 时必做）**：在独立测试设备跑一次“重签 → 极小 DEX/入口探针 → 单脚本打印日志”，10 分钟证伪加固与日志链路（先确认 `logcat` 能出栈，防 `isshowlog=false` 静默盲打）。

---

## 架构选型决策树（按需加载对应参考）

| 侦察命中特征 | 推荐离线架构 | 参考手册 |
|---|---|---|
| Cocos Creator (JS/JSC) 或 Cocos2d-x (Lua / 双 Lua 线程 / LuaJIT + PB) | **同进程包内 JS/Lua 拦截或内存环回服**（零 `INTERNET`、1 帧异步回注防重入；研发期可用 PC 假服 + `adb reverse` 过渡，交付切包内纯脚本；支持薄壳 `EngineActivity` 免改原 DEX 脱壳） | [arch-cocos-js-lua.md](route-cocos-js-lua.md) |
| Unity Mono / ET Hotfix / **HybridCLR**（明文或轻偏移 C# DLL，如 `code.unity3d` / `bytes.unity3d`） | **包内 C# 模拟服**（优先扁平覆写树 `raw_baseline + overrides/ + offline/` 或 Mono.Cecil 极小锚点 + 独立 `OfflineLogic.dll`；零 Socket、AXML 等长删 `INTERNET`） | [arch-unity-hotfix-cs.md](route-unity-hotfix-cs.md) |
| Unity IL2CPP 且**无** C# 热更层 / 无脚本层 | **同进程内嵌 ARM64 CPython + Secondary DEX + JNI 本地回环服 + SQLite + 网页 GM** | [arch-unity-il2cpp-py.md](route-unity-il2cpp-python.md) |
| 微端 WebView 壳 + Unity WebGL/H5（且持有原 `Hotfix.dll`） | **本地回环 Python 服务 + 常驻 `.NET` 原版战斗/属性 Worker**（先 H5 恢复全部内容，最后封壳） | [arch-webgl-h5-worker.md](route-webgl-h5-worker.md) |

> **接管主 Activity / 换薄壳前必核 5 项**：① EGL/Stencil 配置（如 `setEGLConfigChooser(5,6,5,0,16,8)` 防绿白块）；② 屏幕方向；③ `.so` 加载顺序；④ `getIdentifier` 反射资源 ID（如 `EditBoxDialog`）；⑤ 入口全桩 Lua/JS→Java 桥（防 Debug `-Xcheck:jni` 首帧 `SIGABRT`）。

---

## 闸口 1：2 分钟预授权 + Day-0 工作区建基

1. 复制 [../templates/KICKOFF-AUTH.md](../templates/KICKOFF-AUTH.md) → `交接/KICKOFF-AUTH.md`，让用户 2 分钟确认预设（参考 [policy-presets.md](policy-presets.md)）。
2. `git init` 并建立 `.gitignore`（排除原 APK、`dist/`、`tmp/`、`evidence/`、构建中间物）；**所有脚本严禁绝对路径硬编码**（统一 `$PSScriptRoot` / `Path(__file__)`），工具集中放 `tools/`。
3. 复制 [../templates/PROJECT-AGENTS.md](../templates/PROJECT-AGENTS.md) → `AGENTS.md`，以及 `HANDOFF.md`、`PROGRESS-MATRIX.csv`、`BUG-LIST.md` → `交接/`。
4. 用 [../scripts/device_guard.py](../scripts/device_guard.py) 锁定唯一测试设备（32 位包顺手跑 `--check-abi`），读一遍 [pitfalls/windows-emulator-build.md](pitfalls/windows-emulator-build.md)。
5. 用 [../scripts/disk_budget.py](../scripts/disk_budget.py) 跑基线熔断检查；若需去权限/换条目，直接复用 [../scripts/strip_internet_axml.py](../scripts/strip_internet_axml.py) 与 [../scripts/apk_replace.py](../scripts/apk_replace.py)。

---

## 关口 1：秒级快循环底座（首日四件套，建完再铺业务）

1. **缓存 + 极速构建链**：
   - Unity 热更用只读 `raw_baseline` + `overrides/` 扁平树（弃长串 `patch_*.py`）；
   - APK 封装用零重压缩拷贝流（`apk_replace.py` / `RawZipWriter` / `7za u -mx=1` 在 staging 根运行），将整包耗时压到 6–15 秒。
2. **亚秒/秒级热推通道**（仅开发/隔离包启用，`--release` 门禁强断言关闭）：
   - Cocos Lua：`writablePath/dev_lua/` 插 `package.loaders[1]` 或加密推热更 `compress/`（0.3–3 秒生效）；
   - Cocos JS：外部私有目录 `runtime.js` 覆盖；
   - Unity Hotfix：推 `code.unity3d` / `bytes.unity3d` 到 `persistentDataPath` 热更目录（~10–17 秒），**每次热推必核日志 Build ID 防 `GlobalVersion` 清目录**；
   - 内嵌 Python：仅推变更 `.py` 并重启（~8–10 秒）。
3. **Host 无头回归 + 命令桥 / UIProbe + GM 梯子**：
   - 搭建 <20 秒的宿主单测骨架（含 Protobuf/Schema 校验、虚拟时钟、重启持久化、写接口防重入）；
   - 注入只读 `UIProbe`（打坐标/裁剪框）或 20 行文件命令桥（`cmd.lua` / `clock|gm-command.json`）替代慢速找图盲点，配 `fresh / early / mid / max` 四档夹具。
4. **日志裁判 + 读写分治兜底**：
   - 接入 [../scripts/qa_oracle.py](../scripts/qa_oracle.py) 盯 `logcat` + 本地服日志；
   - 未接协议**仅允许只读查询安全兜底不断线并记频次表**，**写接口严禁默认成功兜底**（必须显式拒签防静默丢数据）。

---

## 最小垂直闭环（转入 `autopilot.md` 的准入门槛）

在**独立隔离测试包 + 断网冷启**下走通并留证：
1. 断网冷启 → 脱 SDK → 本地登录/建角 → 进入 1:1 原版主城（`logcat` 0 异常且确认自定义 Build ID 生效）；
2. 进入首关 → 原版战斗引擎真实算出胜负（或真协议结算）→ 奖励与消耗账本精确对账；
3. 原子落盘（`.tmp` + `.bak` + `rename`/`File.Replace`）→ 彻底杀进程冷重启（核换新 PID）→ 状态逐项一致保留。
