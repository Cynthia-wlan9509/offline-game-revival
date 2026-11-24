# 引擎路线：Cocos 脚本层包内拦截（JS / Lua / 双 Lua 线程 / LuaJIT + Protobuf）

> 来自四款 Cocos 手游：Cocos Creator JS + Pomelo、Cocos2d-Lua、Cocos2d-x 双 Lua 线程 + 裸 TCP + `*_pb.so`、Cocos2d-x 2.x + LuaJIT 2.1 stripped + `lua-pbc` + 4.2GB 扩展包（薄壳接管）。

## 适用条件

- 引擎为 Cocos Creator (`libcocos2djs.so`) 或 Cocos2d-x Lua/LuaJIT (`libcocos2dlua.so` / `libgame.so`)；
- 静态分析 `.so`（如 ARM64 `adrp+add` 反汇编）或探针能一次性解开脚本容器，客户端可加载明文或重加密后的脚本。

## 1. 加密容器与 10 分钟破壳探针

- **常见容器实测配方**：
  - **XXTEA + gzip**（Cocos Creator `.jsc`）：静态解密出明文 JS 后过 `node --check`；
  - **XXTEA + 尾 4B 源长**：密文 = `XXTEA(src + 4B零对齐 + uint32_LE(src_len))`，**缺末 4B 源长会静默失载**；编解码器必须通过 `encode(decode(x)) == x` 回环断言；Loader 先找 `.so` 再找 `.lua` 时，热推须加密成 `.so`；
  - **自定义查表 XOR**（如 `UF\0\x01` 5B 头 + `start=data[4]%33` 33B 表 XOR 得 `\x1bLJ\x02`；或 `UF` type-2 尾 5B 移首 + 前 100B XOR）：Python 侧用大整数向量化 XOR 可提速 32×。
- **10 分钟快速证伪加固**：重签 → DEX 极小改串并重算头校验 → 单 Lua 探针打印日志（若静默先强抛错验堆栈，防 `isshowlog=false` 导致盲打十几个包）。

## 2. 零 apktool 脱壳与薄壳 Activity 接管（三选一）

1. **AXML 原地换入口**（零体积变）：解析 `AndroidManifest.xml` `StringPool`（偏移 8, `0x0001`）与 `START_ELEMENT`（`0x0102`），互换 Splash 与主 Activity 的 `MAIN/LAUNCHER` 索引（属性 `+8/+16`）；
2. **DEX 锚点 NOP + 重算头校验**：验证原字节后 NOP 掉渠道 SDK / Bugly / OAID / Umeng / Hook 初始化，**必须重算 SHA-1（`[12..32]` 覆 `[32:]`）与 Adler-32（`[8..12]` 覆 `[12:]`）**，漏算会被 ART 拒载报 `ClassNotFoundException`；
3. **免改原 DEX 薄壳 `EngineActivity` 接管**（极度推荐用于渠道壳极复杂的老游戏）：原 `classes1~N.dex` 与 `.so` 原样直拷，用 `javac + d8 + aapt2` 单独编极简 `EngineActivity extends Cocos2dxActivity` 打成新的 `classes(N+1).dex` 接管 `LAUNCHER`，直接绕过原复杂 Activity/SDK/协议页，配独立包名 + 零权限 + `aapt` 断言无网。
   - **接管前必核 5 项**：① `setEGLConfigChooser(5,6,5,0,16,8)`（漏配绿白块）；② 屏幕方向；③ `.so` 加载顺序；④ `getIdentifier` 反射资源（如补 `EditBoxDialog` 入 `resources.arsc`）；⑤ 入口全桩 Lua→Java 桥（`CCLuaJavaBridge`/`luaj`/`NativeCallUtils`，防 Debug `-Xcheck:jni` 首帧 `SIGABRT`）。

## 3. 离线协议架构：研发 PC 假服 → 交付同进程内存环回

- **研发早期**：可用 PC 假服 + `adb reverse`（活服抓包参考用 `iptables DNAT` + `tcpdump`），快速摸清帧结构与黑盒回包；
- **交付终态（强烈推荐同进程包内纯 JS/Lua 假服）**：
  - **网络层拦截优于业务层零散拦截**：在 `NetManager` / `socket.request` / `network` 3 处做内存环回，保留客户端原有解包/缓存/推送链；
  - **1 帧异步回注 + 推送泵**：回包必须延后 1 帧注入防重入死锁；双 Lua 线程轮询采用“忙 0ms → 闲 40ms 休眠”；
  - **Protobuf 两大坑**：
    1. 老 `protoc-gen-lua` 编负数 `int32`（如 `-1`）会卡死，纯 Lua PB 编码器对负数必须输出 **10 字节 64 位补码 varint**；
    2. `lua-pbc` 会省略默认 `0` 值 `optional` 与空数组，导致原 UI 报 `nil`，必须在 Data 入库口与回包层双向补 `0` / `{}`；
  - **全局错误捕获**：Lua 挂接 `__G__TRACKBACK__`、`coroutine.resume`、`MessageBox` 统一打 `LUA_ERROR`（GM 弹窗、正式静默安全回退）；Cocos2dxEditBox 返回键失灵优先试零 DEX `Cocos2dxEditBox.hideNative()` 恢复焦点。

## 4. 亚秒级快循环、4.2GB 超限与打包门禁

- **0.3s–3s 热推**：
  - LuaJIT/Lua 开发包把 `writablePath/dev_lua/` 插到 `package.loaders[1]`，用 `adb run-as` 0.3s 推明文脚本；或加密推热更 `files/<ver>/compress/` 3s 生效；
  - JS 开发包读外部私有目录 `runtime.js` 覆盖；**`--release` / 正式包门禁强断言关闭热载、`debuggable`、文件命令桥与全量 `print`**；
- **6s–12s 零重压缩增量包**：用 `scripts/apk_replace.py` / `RawZipWriter` 拷贝原压缩流（清 data-descriptor、保留音频 `ZIP_STORED`），或 `7za u -tzip -mx=1`（**必须切到 staging 根传相对路径**）+ `apksigner`；
- **超 ZIP32 上限（>65,535 条目或 >4 GB，如底包 2GB + 扩展包 2.2GB）**：严禁硬塞单 APK，改用**外置 `Android/data/<pkg>/files/`（零权限 + `chown` UID）**或**单条 `ZIP_STORED` 首启自解压（严格验 `CanonicalPath` 防穿越）**；
- **宿主回归 + 20 行命令桥**：LuaJIT 项目可用 Python `lupa.luajit21` 直接挂载 APK 字节码 + Proto2 校验器跑 20 秒全量宿主回归；设备侧注入 20 行文件命令桥（`cmd.lua -> cmd_result.txt`）或只读 UI 节点导出器，替代慢速找图点击。
