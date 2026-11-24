# 引擎路线：Unity IL2CPP 同进程内嵌 Python 本地回环服

> 来自一款 Unity IL2CPP 卡牌手游：847/847 协议、18 大系统、133 个活动、120 个 AI 玩家撑起的"活服"，全量验收收官。

## 适用条件

- 引擎为 Unity IL2CPP（`libil2cpp.so` + `global-metadata.dat`），且**没有**明文 C# 热更层（HybridCLR/ILRuntime）或脚本层（Lua/JS）可直接承载完整离线逻辑；
- 客户端与服务端通过 HTTP / TCP / WebSocket 通信，且客户端网络地址或 CDN 域名可在打包期改写为 `127.0.0.1` 回环地址。

## 核心架构

1. **同进程嵌入式引导**：
   - 注入 Secondary DEX，注册 `BootstrapActivity` 为新 Launcher（移除原 Unity Activity 的 LAUNCHER filter），**严禁设置独立 `android:process` 或 `singleInstance`**，必须与原 Unity Activity 同进程运行。
   - APK `lib/arm64-v8a/` 内置 `libphonebootstrap.so`（JNI 桥）+ `libpython3.14.so` + `libcrypto_python.so` + `libsqlite3_python.so` + `libssl_python.so`（按依赖顺序显式加载）。
   - `assets/python/`（精简 stdlib + `lib-dynload` + `tzdata`）与 `assets/offline/server/` + `assets/offline/data/` 在首次启动时按 SHA-256 校验流式解压到 `getFilesDir()`，通过 JNI `PyConfig` 隔离初始化启动回环服务（TCP 协议网关 + HTTP 资源/网页 GM 后台 `127.0.0.1:8080/gm`），随后拉起原 Unity Activity。
2. **数据与持久化**：
   - 使用 **SQLite 原子事务落盘**（单文件 `offline-phone.sqlite3`），杜绝写一半崩溃坏档；
   - 大配置表做**按需偏移索引 + 登录空闲分片预热 + UI 只读查询零写库快路径**，避免真机切页卡顿。
3. **DEX / SDK 与 Manifest 改造**：
   - 保留本地回环所需 `INTERNET` 权限（配 `usesCleartextTraffic` / `networkSecurityConfig` 仅放行 `127.0.0.1`），通过 DEX 补丁切断第三方渠道登录/支付/上报 SDK 回调，直接放行本地通道；
   - 彻底不依赖 PC、不依赖 `adb reverse`、不依赖 root，单装 APK 断网即玩。

## 快循环与提速做法

- **秒级热推（`hot_push.py`）**：测试期仅通过 `adb push` 替换设备应用私有目录下的 `offline/server/*.py` 并 `force-stop` 重启，**8–10 秒生效**，绝不为改一行 Python 重打 2.6 GB 的 APK；
- **网页 GM 后台 + ADB 转发**：`adb forward tcp:18080 tcp:8080`，电脑直接调 `/gm/api/action` 一键造 `early` / `mid` / `max` 三档测试夹具，也支持玩家通过世界聊天 `/gm` 或兑换码开启沙盒；
- **日志裁判（`qa_oracle`）**：直接盯 `replay.log` 中的 `unsupported local protocol` / `rejected` / `synthesized empty reply` / `Traceback` 与 `logcat` 中的 Unity `Exception`/`read code error`。

## 优缺点与注意事项

- **优点**：业务逻辑用 Python 编写迭代极快、天然适配 SQLite 事务、网页 GM 与 AI 活服生态极易实现、完全免碰复杂 ARM64 汇编修改。
- **注意**：包体会增加约 20–40 MB Python 运行时；必须在首次解压时做好路径穿越校验与 `fsync`；务必用独立测试包与正式包严格隔离热推能力（发布包零诊断钩子）。
