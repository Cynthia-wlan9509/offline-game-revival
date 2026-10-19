# 案例 B（LayaAir 原生 + JS 的剧情养成卡牌手游）：Conch 离线化

做 Laya 原生包（`liblayaair.so` + `assets/scripts/*.js` + `assets/cache/<域名>/<8位哈希>`）时照这份走。
项目根 `<项目根>`，唯一构建入口 `tools\build.py`，离线逻辑 `tools\offline\*.js`，进度见 `<项目根>\README.md`。

## 识别

- `lib/*/liblayaair.so`、`libv8*.so`；`assets/scripts/{index,apploader,config}.js`；`assets/config.ini`（`CheckNetwork`/`ThreadMode`）
- `assets/cache/https.__<host>_<path>/`：资源按 **`'%08x' % crc32(相对路径)`** 命名（路径以 `/` 开头，如 `/js/bundle.js`），
  同目录 `allfiles.txt`（路径清单）、`filetable.txt`、`filetable1.txt`、`filetable.bin`、`assetsid.txt`
- 游戏逻辑在 `js/bundle.js`（明文压缩 JS）。**先去 CDN 找 `js/bundle.js.map`**：本项目线上有，含 470 个 TS 源文件全文，等于拿到源码。
- 启动 URL 在 Java 的 `GameConfig.GAME_URL`；原生加载器 `assets/scripts/index.js` 的 `loadApp()` 走 DCC 更新。

## DCC 缓存机制（关键，踩了三轮）

- `filetable.txt`：`ffeeffee 1` 头 + **assetsid 拆成两行**（各 8+8 位）+ 每行 `fileid chksum`；`filetable1.txt` = 去掉这 3 行的包内资源表。
- **chksum 算法**（用原包 8943 个文件反推，8940 吻合）：按 8 字节块，把小端 uint32 逐个异或；剩余 0~7 字节逐字节异或。
  ```python
  n=(len(d)//8)*2; h=0
  for w in struct.unpack('<%dI'%n, d[:n*4]): h^=w
  for b in d[n*4:]: h^=b
  ```
  反推窍门：找 2 字节的文件（`{}` → `0x7b^0x7d = 6`），再按"长度 mod 8"分组看吻合率。
- 引擎**按内容重算校验**判断包内文件是否有效；不一致就联网重下 → 离线时 `JsAppCache::loadCachedURL Error, no cache data` / `Load start url error`。
- **线上 CDN 的 filetable 与文件内容并不一致**（同内容不同值）。所以：打包时**按实际内容重算全部 chksum、重生成四个元文件**，不要照搬线上表。这样 bundle.js 也能随意改。

## 原生加载器补丁（`assets/scripts/index.js`，不在缓存里，可直接改）

1. 跳过 `updateDcc()`（离线下载 assetsid 失败且本地有 netassetsid 会 `onLayaInitError` 退出）
2. 但要补上它里面的 `cache.setResourceID('appurl', urlpath)`
3. **再 `yield` 等 ~3 秒**：原来联网更新耗时掩盖了一个竞态；离线秒进会在 GL 线程 `JCScriptRuntime::dispatchLayaGLBuffer` SIGSEGV（x86/arm 都崩，和资源、补丁 JS 无关——用"只留加载器补丁、不带任何 JS 模块"的对照包确认）
4. 启动脚本先 `cache.loadCachedURL(url)`，原逻辑网络失败读到缓存后直接 `return`
5. `loadLib()` 是**异步**的（script 标签排队）：钩子装在 `loadLib('js/bundle.js')` 之前时 `Laya` 还不存在，要轮询安装
6. `require("offline_server")` 会加载 `assets/scripts/offline_server.js`（conch 的 require 读 assets/scripts）

## 本地服务器（JS 层）

- 网络层是 HTTP+JSON（`{"success":1,"data":...}`），在 `Laya.HttpRequest.prototype.send` 和 `XMLHttpRequest` 两层拦截，按路径路由。
- 315 个接口：先让子代理按模块分三组做"调用方怎么读 data"的清单（含最小安全默认值），生成 `10_defaults.js` 兜底，再手写有状态的。
- 存档放 `localStorage`，落盘在 `/data/data/<pkg>/LayaCache/localstorage/<host>.txt`（JSON），root 下可直接读作落盘证据。
- JS→Java 桥：包一层 `PlatformClass.createClass(...).call`，把 SDK 登录 `doLogin` 改成直接回调 `LoginWin.loginSucceed(...)`；支付/广告/实名/埋点改本地。
- `conch.config.getNetworkType()` 离线返回 0 会被登录页拦下，改成恒 1。
- 坑：成功响应里 `data.state` 为真值会弹错误码提示；非法 JSON 会被无限重发。

## 引擎层护栏（`tools/offline/06_laya_guard.js`）

- **一次渲染异常 = 整个游戏冻住**：laya.core 的主循环是 `rAF(function loop(){ stage._loop(); rAF(loop) })`，
  `_loop` 抛错后不再续帧。现象：黑屏/画面不动，但调试通道（走 conch 的 timerqueue）照常响应；
  判据 `Laya.timer.currFrame` 不增长。修法：包 `Laya.stage._loop` 加 try/catch（实例属性覆盖即可，loop 每帧按属性名取）。
- 触发源：剧情加载 `particles/*.part` 偶发失败时回调拿到 undefined 仍 `new Particle2D(undefined)`，render 读 `_canvasTemplate.sv` 抛错。
  给 `Particle2D.prototype.customRender/advanceTime` 加"无模板不画"。
- UI 里 skin 写成字面量 `""` 的图片：原生下载器每次连不上要 3 秒、占下载线程，别的资源随之加载失败。
  XHR 层和 `Laya.Loader.prototype._loadImage` 都要直接判失败。

- **伪造 XHR 回包会"毒化"复用的实例**：Laya 的 Loader 被池化复用，且 `this._http || (this._http = new HttpRequest)`，
  XHR 实例跟着复用。用 `Object.defineProperty(xhr,'status',{value:404})` 伪造的字段不清掉，之后这个实例上的每个请求都"秒失败"
  （日志：同一毫秒内连续 `Retry to load` → `Failed to load`，资源随机失败、剧情打不开）。修法：`open()` 里先 `delete` 这些自有属性。
- 终版客户端把 `plot/markRead` 连同**成功回调**一起注释掉了：除了记进度，回调里还有"同步 `userInfo.plotId`、触发新手引导
  （1-2 后战斗、1-8 后抽卡、1-14 后委托、3-1 后支线）、`updataPlotInfo` 刷新章节界面"。补丁要整段恢复，只记进度的话章节界面不刷新。

- **终版更新会把旧功能的 UI 挪到屏幕外**（不删代码）：章节星级领奖 `polt_rewardUI` 整组控件 x 左移 331（旧包 `img_reward_box` x=86，终版 -245），
  但新手引导配置仍指向旧坐标。判别：`localToGlobal` 落在舞台外 + 截图不见；**拿原包里的旧 bundle 对比同一 uiView**。
  修法：bundle 补丁在组件 `addEvent` 里平移回来。凡是"引导卡住、按钮不见"，先查控件坐标。
- 新手引导（`HelpManagerNew.ts` 步骤表）是好的验收脚本：每步写明表单名 + 控件名，照着点能一路验证"领奖 → 返回 → 抽卡"。

## 调试通道（测试包专用，强烈推荐）

conch 里有 `readFileSync(path,'utf8')` 和 `fs_writeFileSync`。在 `--debuggable` 包里加一个模块：每 400ms 读
`conch.getCachePath()+"/<proj>_cmd.js"`，非空就 eval，结果写 `<proj>_out.txt`。主机侧 `tools/devjs.sh '<js>'`（adb push + su cp）。
用途：直接读存档/状态、按**属性名**找 UI 节点并派发点击（Laya UI 的控件是表单对象上的属性，`name` 常为空；派发时要
`e.setTo(Laya.Event.CLICK, n, n)` 带 target，否则处理器读 `e.target` 报错）、填输入框、调用表单方法快进。
比截图找坐标省 token 一个量级；配合"屏幕连续不变才截缩略图"的自动点击脚本（`tools/autoplay.py`）跑剧情。
Git Bash 下给 adb 传设备路径要 `MSYS_NO_PATHCONV=1`，本地文件要写成 `<盘符>:/...`。

## 测试环境

- BlueStacks 多开新建 Pie64 实例（多开管理器"全新的多开引擎"，不要克隆正在用的实例），`/system/xbin/su` 可用即有 root；
  用**独立 adb server 端口**（`ANDROID_ADB_SERVER_PORT`）避免干扰别的会话。资源给够就行（2 核 / 3 GB / 30 fps）。
- 只断游戏网络：`iptables -I OUTPUT -m owner --uid-owner <uid> -j REJECT`，比整机断网好用（adb 不受影响）。
- 原版包能在同一实例上进登录页 = 环境没问题；自己的包崩就做"逐项去掉补丁"的对照包二分。
- 线上 CDN 还活着时**先全量镜像**（证书过期要 `-k`；并发高了会被掐，6~8 路 + curl 超时重试）；镜像到 2026-10-17 为 16049 个文件。

## 授权码 + 水印（JS 引擎版，2026-10-18，已在正式包上验收）

- 选 **Ed25519** 而不是 RSA-2048：码长 130 字符（RSA 签名 344 字符太长，玩家粘贴易出错）。
- **conch 的 V8 没有 BigInt**（真机 `ReferenceError`）：验签用 tweetnacl 式 16×16 位域运算 + 32 位高低两半的 SHA-512
  （`tools/offline/07_license.js`）。曲线常数运行时由小整数现算；SHA-512 的 80 个常数用 node 按定义生成后写入，
  `tools/test_license.js` 和 node crypto 对拍（20 组随机密钥 + 篡改）。
- **本机码别用 `conch.config.getDeviceInfo()`**：guid 是 MAC（Android 6+ 统一 02:00:00:00:00:00）、imei Android 10+ 拿不到，
  所有人会得到同一个码。用 smali 给 `demo/JSBridge` 加静态方法 `getDeviceId()` 取 `Settings.Secure.ANDROID_ID`
  （按签名证书区分，卸载重装不变，实测通过）；拿不到再退回安装随机种子。启动早期桥接没就绪时不要缓存结果。
- **Laya 的输入框长按调不出系统粘贴菜单**、conch 也没有剪贴板 API：smali 加 `getClip()/setClip(s)`
  （`JSBridge.mMainActivity` → ClipboardManager），门禁页放"复制本机码""粘贴授权码"按钮，打开时剪贴板里有 `LIC1.` 就自动填。
  BlueStacks 和 Windows 共享剪贴板：`Set-Clipboard`/`Get-Clipboard` 就能测复制粘贴。
- 发码：`node tools/license.js issue --device … --chapter N --expires …`（node 自带 Ed25519）。私钥、台账在 `private/`；
  构建时把公钥 hex 替换进 `@LIC_PUBKEY@`，缺了就构建失败。
- 门禁挂在**假 SDK 登录回调前**（`doLogin` → `M.licenseGate(go)`）。原文存 localStorage，每次启动重新验签。
- 章节分档：载荷里带"开放到第 N 章"，`plot/queryPlot.openMaxChapterCount` 和解锁判定都读它；升档发新码，不用重装。
- 可见水印：舞台最上层半透明小字"本机码 + 授权序号"，`mouseEnabled=false`，定时置顶。
  按份水印：`tools/stamp.py`（追加 `assets/rel_mark.bin` + ZIP 注释 → zipalign → 发布证书重签，关掉 v4 签名免得多出 .idsig），
  台账 `private/watermarks.json`，`stamp.py read` 取证。2 GB 包一份约 45 秒。
- 发布证书 `private/release.jks` 和测试证书不同：测试机从测试包换正式包要先卸载（存档会丢）。正式包不带调试通道，
  只能靠截图 + 真实手势验收（`autoplay.py` + `adb input swipe`）。

## 玩家数据

服务器数据（卡牌/进度/货币）不在手机上；手机里只有 LayaCache（资源 + localStorage）。导出指南见 `<项目根>\玩家数据导出指南.md`
（普通玩家无 root 访问不到 /data/data，主推截图/录屏经微信/QQ 原图或国内网盘发送；adb backup 仅作附录给会用电脑的人）。

**实测一份真实小米备份（<渠道>渠道服，2026-10-18）之后，不再向玩家要手机备份**：
- 格式：zip 里一个 `.bak` = `MIUI BACKUP
2
<包名> <名称>
102
0
` + 标准 Android backup 头 `ANDROID BACKUP
5
0
none
`（未压缩未加密）+ tar。
  跳过头后 `tarfile.open(fileobj=f, mode='r|')` 流式解；`apps/<pkg>/a/base.apk` 就是渠道 APK，`r/` 是 /data/data 下的目录。
- 内容：localStorage 只有设置；LayaCache 运行时缓存文件带 **48 字节头**（`ffee8877 0230 xx01` + 校验），只有头的 48 字节文件是"已校验包内资源"的占位；
  去头后与线上镜像比对即可判断客户端版本——本例 bundle.js 与官服最新版逐字节相同，渠道包内置缓存与官方包也相同。
- 结论：渠道服的"逻辑不同"只在原生 SDK 层；JS 层按渠道分支的只有极少处（本例仅 <另一渠道> 的取消分享）。备份里还有渠道账号票据与昵称，**不能外发**。
- 运行时缓存能反推玩家看过哪些资源（剧情文件、卡面），但不是进度数据。

## 引导驱动的真机验收（v0.5t，2026-10-18）

- 按 `HelpManagerNew` 的步骤表**照引导真实点击**是最有效的验收：一天里找出 10 个"界面能开、引导卡死"的问题，全是服务端假数据与引导预设不符：
  好感 Lv5 奖励里没礼物 → "把刚获得的礼物送给他"无物可送；宠物首次开放草为 0 / 宠物粮已有 3 → "收草"失败、跳过了"兑换"分支；
  合成引导第二段缺第二件材料。**写默认数据前先读引导步骤表，引导要用到的东西新档必须有。**
- `tools/guidetap.sh`：读 `Help.img_choose_frame`（高亮框）的舞台坐标换算成屏幕坐标 `adb input tap`，没框就点屏幕推进对话；
  长按类步骤（摸宠物进度条 ~7 秒）用 `input swipe x1 y1 x2 y2 8500`。devjs 派发 CLICK 会绕过引导遮罩，验收要用真实触摸。
- 热加载：测试包里 `(0,eval)(模块源码)` 重新执行离线模块即可验证修复，免得每次重打 2 GB 包；会包装既有入口的模块要先保存/还原入口，
  否则叠两层。冷启动后热加载失效——**重启后要重新加载**，否则测到的是包里的旧代码（踩过一次）。
- 图标：客户端按"类型白名单走物品图、其它走小货币图"取图，终版图集删掉了部分货币小图（两种货币）→ 格子空白或显示成别的图标。
  写了 `tools/check_icons.py` 按 ImageManager 规则校验所有离线表奖励，进回归。
- 原版 bug 也要修：终版 `Good_list.buyClickHandle` 要求服装和场景都已选中才响应"购买"，玩家不先点场景页就买不了衣服。
