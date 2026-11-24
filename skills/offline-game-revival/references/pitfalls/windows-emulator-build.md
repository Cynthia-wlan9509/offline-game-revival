# Windows、打包与安卓模拟器的坑（多项目并行时）

现象 → 原因 → 修法。索引见 `../pitfalls.md`。致命的几条已写进 `../red-lines.md` 与 `../scripts/guard_hook.py`。

---

## 一、模拟器与 ADB 环境坑

### 1. 雷电模拟器（LDPlayer）断网测试致命陷阱
- **现象**：执行 `adb shell svc wifi disable` 测断网，设备瞬间 `offline`，ADB 彻底失联。
- **根因**：雷电 ADB 通道走 `wlan0`，关 WiFi 等于自断网线。
- **规避**：**永禁 `svc wifi disable`**。改用目标 UID `iptables`（测毕撤回）或 guest 侧 `nohup` + `trap` 超时自动恢复 Wi-Fi，且纯包内版直接剥离 `INTERNET` 权限。

### 2. 多项目共享 `Ld9BoxSVC.exe` COM 死锁
- **现象**：多开实例时 `ldconsole launch` / `VBoxManage` 无限挂起。
- **规避**：**严禁擅自强杀 `Ld9BoxSVC`**（会拖死其他项目实例）。先切去做完所有 Host 侧代码与构建，再请用户手动拉起或批准统一重启。

### 3. 装包 `NO_MATCHING_ABIS`（32 位包遇纯 64 位模拟器）
- **现象**：`armeabi-v7a` 老游戏装包报 `INSTALL_FAILED_NO_MATCHING_ABIS`。
- **规避**：开局用 `device_guard.py --check-abi` 核查 `ro.product.cpu.abilist` 含 32 位；并在交付说明写明纯 64 位新机兼容边界。

### 4. ADB 非 ASCII / 中文路径失败（`fchown`/push 报错）
- **现象**：旧版 `adb` 对带中文路径的本地/设备文件操作报错或写坏属主。
- **规避**：统一使用 `device_guard.py --push-safe` 经 `/data/local/tmp/<guid>.bin` ASCII 路径中转，再 `shell cp/mv` + `chown`/`chmod`，当轮删 tmp。

### 5. PowerShell 5.1 `$ErrorActionPreference = 'Stop'` 误杀 `adb`
- **现象**：`adb` 成功但往 stderr 输出进度/提示时，PowerShell 5.1 直接抛出终止性 `ErrorRecord` 中断流水线。
- **规避**：封装 `Adb-Run`，调用前临时设 `$ErrorActionPreference = 'Continue'`，**唯一以 `$LASTEXITCODE` 判定成败**。

### 6. PowerShell 管道损坏 `adb exec-out` 二进制流
- **现象**：`adb exec-out screencap -p > a.png` 或 `tar` 重定向后文件损坏。
- **根因**：PowerShell 管道和雷电 `su` 终端默认做文本编码与换行转换。
- **规避**：用 Python `subprocess.run(..., capture_output=True)` 直接写 raw bytes，或设备落盘后 `adb pull` 再删设备文件。

### 7. 模拟器 `.vmdk` 静默膨胀 & 恢复存档属主变成 `root:root`
- **规避**：① 每次 `adb push` 后当轮 `device_guard.py --clean-tmp` 清 `/data/local/tmp/*.apk|*.tar|*.bin`；② 向 `/data/user/0/<pkg>/` 推回正式档后必须同步 `chown <app_uid>:<app_uid>` + `chmod 0600`。

### 8. `monkey` 压测误触语音搜索 & 多开/闪退盲点误触他 App
- **规避**：① `monkey` 必带 `-p <pkg> --pct-trackball 0 --pct-nav 0 --pct-majornav 0 --pct-anyevent 0`；② 每次点击前 `device_guard.py --check --require-game-fg` 确认前台是目标包；③ 2 GB RAM 模拟器多场景连跑每 4–5 关主动重启防 LMK；④ 透明 SDK WebView 吞 `tap` 时换 `swipe` 或命令桥。

---

## 二、构建、打包与跨机迁移坑

### 9. 绝对路径硬编码致换目录/换机 400+ 处报错
- **规避**：所有脚本从 Day-0 起严禁硬编码盘符和绝对路径，统一用 `$PSScriptRoot` / `Path(__file__)` 相对推导工作区与 `tools/`。

### 10. Windows Junction / 符号链接误删灾难
- **规避**：清理任何目录前必查 `is_reparse_or_link`（已内置于 `disk_budget.py`）；源码与签名私钥在工作区外另备一份。

### 11. ZIP32 上限（65,535 条目 / 4 GB）打包或装包失败
- **现象**：合入 2 GB+ 扩展包（十几万文件或总包 >4 GB）后 APK 损坏或安装失败。
- **规避**：改用**外置 `Android/data/<pkg>/files/`（零权限 + `chown` UID）**或**单条 `ZIP_STORED` 首启自解压（严格校验 `CanonicalPath` 防穿越）**。

### 12. 音频被压缩无声 & `7za u` 未切 cwd 平铺包根 & 改 DEX 漏算头校验
- **规避**：① 音频/视频保持 `ZIP_STORED`（用 `apk_replace.py` 自动保留）；② 用 `7za u -tzip -mx=1` 增量更新时**必须先切 cwd 到 staging 根目录再传相对路径**，尾检条目数与标记；③ 改 DEX 字节后必重算 SHA-1（`[12..32]` 覆 `[32:]`）和 Adler-32（`[8..12]` 覆 `[12:]`），否则 ART 报 `ClassNotFoundException`。

### 13. MSBuild 切模式残留 `obj/` 报重复 `AssemblyAttributes`
- **规避**：按正式/测试模式分离 `BaseIntermediateOutputPath`，在 `.targets` 排除 `obj/bin/**/*.cs`，用 `$(DefineConstants);...` 追加符号而非覆盖。

---

## 三、运行态、热推、脚本与存档坑

### 14. 无日志静默盲打 & 热推被旧热更/`GlobalVersion` 覆盖失效
- **现象**：改了十几版没变化——要么游戏内 `isshowlog=false` 早退致 `logcat` 无输出，要么旧热更目录遮盖新 APK，要么 `GlobalVersion` 比对把刚热推的 bundle 清掉了。
- **规避**：排障先强抛错验堆栈通畅；每次热推核对日志 **Build ID + 文件哈希**；封版必测 **彻底清数据 + 空热更目录 + 断网双冷启**（顺手揪出清数据跳首次解压漏音效/空 map 的缺陷）。

### 15. Debug 首帧 `SIGABRT`（`-Xcheck:jni`）与 `libhoudini.so` 无栈崩
- **现象**：① `debuggable=true` 开启 `-Xcheck:jni`，原代码用点分隔类名调 `FindClass` 直接 `SIGABRT`；② x86_64 模拟器 ARM 转译层崩在 `libhoudini.so` 看不到 C++ 帧（常见于缺 `.ccbi`/`.plist` 传进 native 空指针）。
- **规避**：① 入口全桩 Lua/JS→Java 桥，发版关 `debuggable`；② 用 `debug.sethook` 实时记 Lua 最后调用栈定位，所有读/删资源统一前置 `isFileExist` 转可控异常。

### 16. 同步回包重入死锁、动态 UI 穿透与急清缓存崩
- **规避**：进程内模拟服回包**必须下一帧异步回注**防 `OnShow` 递归死锁；Unity 动态激活 UI 显式调 `GraphicRegistry.RegisterGraphicForCanvas` 防按钮穿透；缓存用 dirty flag 懒刷新，禁止业务回调中急清缓存。

### 17. 存档损坏、双线程互踩、LitJson 溢出与重复入账
- **规避**：① 严禁“先 `remove` 再 `rename`”，改用 `<file>.<tid>.tmp` + `flush` + 备 `.bak` + POSIX `rename`/`File.Replace` 原子落盘，读档支持 `主 → .bak → .tmp` 自愈；② 发奖/扣费一律用 `tx_key` 幂等防重，新实体 ID 从 `max + 1` 起步；③ LitJson 超 `int.MaxValue` 存 `string` 并走后台批量队列 + 退后台刷盘；④ `tolua++` userdata 禁挂字段，改纯 Lua table 桩。

### 18. Lua 5.1 裸 `return` 语法错、PB 坑与年月表跨年过期
- **规避**：① Lua 5.1 块中早退必须写 `do return end`（盯 `error decode module`）；② `protoc-gen-lua` 负数 `int32` 输出 10B 64 位 varint，`lua-pbc` 省略的 `0` 与 `{}` 在入库和回包层双向补齐；③ 所有 `sign_YYYYMM` 类年月表必须加循环/默认兜底防跨年 `nil`。
