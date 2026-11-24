# 侦察、解包、资源完整性的坑

停服状态、加密与反编译、资源清单和微端、玩家备份接入、镜像下载、导出素材。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

### 工具链 / 环境（实测坑）（续，原节在 `device-emulator.md`）

**离线解配置表：protobuf 描述符 + 数据文件**
- 路子：`analysis/protocols/*.bytes`（FileDescriptorSet）+ `src/phone_data.bytes`，
  用 `google.protobuf.descriptor_pb2 / descriptor_pool / message_factory` 还原 `TAllGameCfg`，再按表名取行。
- 好处：可复现、不依赖设备、可以反复试算（算理论上限、查门槛、对结构）。

**镜像 CDN 被限流：降低并发，换用 curl（案例 B 2026-10-17）**
- 症状：用 24~48 路并发加 Python urllib 下载时，连接被拒或卡死，吞吐只有每分钟 1 MB；放到后台的进程随 shell 退出而终止；优先下载的那批文件全部「失败」。
- 原因：CDN 对高并发限流；urllib 没设超时会无限挂起；用 `&` 放后台的进程会跟着 shell 一起结束；Windows 下 Python 写出的列表每行带 `\r`，URL 末尾多了一个回车。
- 修法：用 curl，加 `--speed-limit/--speed-time`、`-m` 超时和重试，证书过期加 `-k`，并发降到 6~8；按优先级先抓开场剧情、剧情文本、UI，语音放最后；用工具自带的后台运行方式；读列表时先去掉 `\r`。

### 案例 C 侦察（2026-10-21）（续，原节在 `ui-assets.md`）

**A 1.2 GB APK was only a quarter of the game (micro client)**
- Symptom: everything decompiled fine and the plan looked straightforward, until the bundle manifest was diffed against the package: 42,700 bundles listed, 12,120 present; about 91% of the clothing models missing.
- Cause: a big publisher's micro client (`_ClientType: 2`). The rest was downloaded on demand through the SDK's Puffer downloader and died with the servers.
- Fix: diff the resource manifest against the package on day one and put "where do the missing resources come from" to the user before writing patches.

**A rejected Lua header is not encryption**
- Symptom: unluac refused every script with "non-standard lua format: 1".
- Cause: byte 5 (format) of the Lua 5.1 header was changed from 0 to 1; nothing else was touched.
- Fix: compare the header byte by byte with the standard one, reset the changed byte, decompile.

**The original game stops at the publisher's privacy agreement (`MSDKPolicyActivity`)**
- Symptom: a test run on the emulator never reached Unity; logcat only showed the MSDK policy activity.
- Cause: the launcher activity is MSDK's user-agreement and privacy-policy dialog.
- Fix: clicking "同意" accepts a real agreement on the user's behalf; ask first. For the offline build its HTML and title string were replaced with the memorial disclaimer (see `case-c-micro-client.md`, "开屏和协议页").

**A re-signed build exits about 2 s after launch with code 4 (the publisher's TP shell)**
- Symptom: the patched, re-signed APK showed the MSDK agreement page, then `Process … exited cleanly (4)`; no Java exception. The original APK did not do this.
- Cause: `TPShellApplication` loads `libtprt.so`, which checks the APK (FileChecker/CRC, package name) and kills the process. The same shell decrypts the first 0x1000 bytes of the managed assemblies (`mono_patch`).
- Fix: switch the shell off through the `TPConfig` string constants in the dex (value `true` → `TRUE`, same length, refresh SHA-1/adler32), and ship plain assemblies dumped from the original game's memory. Details and script: `case-c-micro-client.md`.

### 案例 C：玩家备份接入（2026-10-22）（续，原节在 `device-emulator.md`）

**Same versionName and versionCode, different APK** (2026-10-22)
- Symptom: the APK inside the player's phone backup had the version we had been patching (same versionName and versionCode), yet 1518 entries differed, including the managed assemblies and the Lua bundle.
- Cause: the publisher re-packed the same version later (resource refresh); version numbers were never bumped.
- Fix: compare APKs entry by entry (CRC + size), and compare the resource manifests' own version fields. When the backup's APK is newer, rebase the build on it and re-dump anything that came from the old one (here: the decrypted assemblies).

**A micro client deletes your pushed resources on the first start after install** (2026-10-22)
- Symptom: 31,153 bundles pushed to `Android/data/<pkg>/files/assets/`; after the first start 31,125 were left.
- Cause: on a "new program" start the launcher compares external bundles with the *package* manifest: it deletes the external copy of every bundle the package also has, deletes bundles whose MD5 does not match, and deletes the external manifest and the Lua hot-update folder. The 28 missing ones were hot-updated versions of bundles that also exist (old) in the APK.
- Fix: ship the final manifest as the package manifest, replace hot-updated in-package bundles with the final files in the APK, and fold the Lua hot-update folder into the Lua bundle. Read the launcher's "install new program" path before deciding where resources live.

**Imported resources are on disk, but the game still says "not downloaded yet"** (case C, 2026-10-24)
- Symptom: after importing all 31,125 external bundles, level 1-4 refused to start: "story not downloaded yet, 0KB/539KB". Levels 1-1 to 1-3 had worked, so it looked like a missing file.
- Cause: the micro client decides "downloaded" from its own table of missing bundles (`MicroAssetMgr.allBundles_`), not from the files. On first install it marks every external bundle missing and saves the table (`res.dat`); the original downloader removes one entry per finished download. Importing files bypasses that, so the table never empties. 1-1 to 1-3 only worked because their bundles happen to ship inside the APK.
- Fix: at the end of the client's resource start-up jobs, drop every table entry whose file exists and re-save the table. Here that was 31,125 file checks, spread over frames, 2.8 s on an emulator. General rule: when you replace a downloader, find the state the downloader maintained (ready flags, size counters, serialized lists), not just the files it wrote, and test content whose assets are *not* in the APK.

## 反编译出来的文件内容可能和文件名对不上：用字节码里的 chunk 名核对（案例 C，2026-10-24）

- 现象：`ui/reputationshop/*.lua` 等 112 个文件读出来全是同一个无关文件（AssetDetect.lua），分析了半天才发现。游戏里这些功能是好的。
- 原因：自己写的 UnityPy 打包工具给新增 TextAsset 克隆模板对象、`save_typetree` 写新内容；写入没问题，但之后 `obj.read()` 仍解析模板的原始字节，读源码时拿到的全是模板。
- 做法：Lua 5.1 字节码头部后面就是源文件名（`@UI/xxx.lua`），批量反编译后跑一遍"条目名 vs chunk 名"的比对，0 个不符再用。自己的打包工具里，新增条目的字节码要另存一份，读取时直接返回，不要信 read()。

## 先核实停服状态：已发公告不等于已关服（另一款游戏 2026-11-17）
- 现象：侦察和补丁一路按"已停服"推进，做到一半才知道服务器还要开大半年，最后全部叫停。
- 原因：AI 没搜停服公告，也没问用户。
- 修法：第 0 步先搜公告、让用户确认停服到哪一步。服务器还开着时，只做到技术侦察：最多用只观察的钩子录用户自己账号的回包（用户自己登录、自己操作），不碰别的玩家；离线版等官方服务结束后再发，演示视频不公开宣传，对外口径写成"技术演示、关服前不发布"。

## 大批量导出素材（2026-11-17）
- 加磁盘守卫：剩余空间低于某个值（这次 70 GB）自动停。
- 长动画改成流式写文件；单个失败就跳过、不中止整批，并且能续跑。
- 和玩家共用骨骼的 NPC 会把玩家整套动作重转一遍，发现了及时停。
- 浏览器预览窗口隐藏时不刷新画面，要手动渲染一帧、数像素来判断有没有画出来。
