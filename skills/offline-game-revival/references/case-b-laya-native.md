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

> 用途：限制安装包被恶意传播。自己做的游戏、在授权下分发的版本、二创和同人作品都能用同样的做法，见 `distribution.md` 开头。

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
- BlueStacks 只在窗口获得焦点时同步 Windows 剪贴板；后台跑脚本时"粘贴授权码"会读到空。录屏 / 自动化里改为
  点输入框后 `adb shell input text <授权码>`（Laya Input 在 conch 上是原生 EditText，能收到）。

## 去原版品牌、免责公告、一键跳过序章（v0.6，2026-10-19，正式包实测）

用户要求去掉原版发行方的品牌，换成像案例 A 那样的免责公告。原版品牌一共出现在四处，要逐个找：
1. **SDK 闪屏**：`res/drawable/<sdk>_splash_img.png`（白底）。**加载对话框**：`res/drawable/layabox.png`（引擎 Logo）。
   不重编资源，直接在 zip 里按同名路径替换 PNG（`tools/assets/`），resources.arsc 引用不变。
2. **游戏内 Logo 动画** `LogoWin.showLogo`（发行商 Logo 掉落）→ **健康忠告页** `HealthAdivce`（整张图里带发行商 Logo）。
   补丁：`showLogo` 开头改成弹 `M.disclaimer(cb)`，同时加载原来要等的字体，两边都完成才 `new HealthAdivce()`；
   `HealthAdivce.init` 直接跳到 `loadResource()`（后面的 `destory` 照常接 `LoginWin.init` 和音量设置）。
3. **登录页底部**的著作权人、出版单位、版号、健康忠告写在内嵌 `uiView` JSON 字面量里：直接替换 text；
   JSON 字面量里也能塞 `/* MARK */` 注释，这样锚点计数照常有效。
4. 登录页的"账号管理""客服"按钮：uiView 加 `"visible": false`，并把 `loginSucceed` 里 `btn_service.visible = true` 改掉。

公告页用 Laya 原语自绘（`08_disclaimer.js`）：**引擎默认字体没有"•"（会显示成"?"）**，列表用"1. 2."；
长段末尾单独折行的句号要靠改字数避开。

跳过序章（玩家反馈序章小游戏太麻烦）：
- 序章表单 `PrefaceChapter` 只在首次游玩（plotId 空 / "000"）时放按钮；重看时原版已有返回按钮。
- **取名弹窗 `Set_name` 是 bundle 闭包里的类，外部 JS 拿不到** → 跳过逻辑以 `__skipPreface()` 方法补进 PrefaceChapter，
  外部模块（`09_preface_skip.js`）只负责按钮和撤掉叠在序章上的小游戏层。
- `__skipPreface`：用空函数覆盖实例上的 `playStory / showNewNameWindow / showNewPetNameWindow / playAnimation`
  （防止残留 Tween 回调继续推剧情、二次弹取名框把回调顶掉），`Laya.timer.clearAll(this)`、停声音、隐藏；
  名字还是默认"我"就先 `Set_name.Instance.showName(cb)`，回调里走原 `chapterEnd()`（之前已补成接主线）。
- 按钮挂钩在 `init` 里、`Laya.stage.addChild(this)` **之前**执行：判断"序章已结束"要用"上过舞台后又离开"，
  不能一上来看 `parent` 为空就收掉。点两次生效防误触。

升档入口：门禁只在未授权时弹，"发新码升档"必须另有输入处（案例 A 放在系统设置）。这里放在每次启动都出现的公告页：
已授权时显示"当前授权 #序号 · 开放至第 N 章"和"更换 / 升级授权码"，复用门禁页并加"取消"；`chapterCap()` 实时读，换码后不用重启。

录屏：`tools/record.sh start|stop <dir>`（设备内 `screenrecord` 循环 180 秒一段，SIGINT 正常收尾）。Android 9 录不到声音。

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

## 分档 + 复活被原版隐藏的活动（v0.7，2026-10-20 夜）

- 授权码载荷一开始就留了"功能位"段（`LIC1|设备|到期|章节|功能位hex|序号`），加档位时**不用改码格式**、旧码自动是"只有章节"。
  预设只放在签发工具里（体验 / 剧情 / 活动 / 全资源），游戏内只认"章节 + 功能位"。三处常量（签发 CLI、游戏模块、签发 GUI）由测试互相核对。
- 先盘点再定档位内容：真金礼包的内容全是服务端下发、已丢失，"付费福利"位做不出东西就别承诺；
  反而原版终版**客户端写死隐藏**的长线活动 hub（月度约会 65 个剧本、睡前语音 40 段、生日约会 40 个剧本）资源和剧本都在 CDN 镜像里，
  只缺服务端回包 → 补 ~9 个接口 + 入口补丁就复活了，最适合做高档内容。
- 终版客户端里活动 hub 的部分子入口坐标就在屏幕外（某入口 y=846、另一入口没 skin）。地图背景比舞台宽、按屏宽居中，
  **按全局坐标摆放**（`localToGlobal` 求差再 `pos`，再 `timer.frameOnce` 补一次），写死本地坐标换个宽高比就跑出屏幕。
- 不支持的子入口用"点击弹提示"而不是隐藏：固定地图布局，隐藏会留空洞。
- `ctx.save()` 只标脏，写盘在下一次请求结束时：从开屏页等**非请求路径**改存档（一键拉满）必须显式 `ctx.flush()`；
  调试通道改存档后直接 force-stop 会丢改动（不是玩家 bug：玩家的改动都经过请求）。
- 自动推剧情：剧情内"调查热点"（A/B/C 标签）在 `Chapter.box_inter_action` 里，点屏幕中央过不去、强制跳过会让剧情回到热点前循环；
  `playplot.sh` 先找互动层里有 click 监听的节点逐个点，再退回强制跳过。独立表单类小游戏（判断假日记、调色等）只调 `plot/addInteractRecord`，离线卡死风险低。
- 小米真机首次新装会弹"USB 安装"确认（10 秒不点自动拒绝 `INSTALL_FAILED_USER_RESTRICTED`），这是给真人的确认，夜间无人值守装不上；
  同包名同签名的覆盖安装不弹。真手机无 root：测试包（debuggable）用 `run-as` 代替 `su`（`tools/onphone.sh`）。

## 新手引导的隐性前提（v0.8.3，2026-10-20）

- 引导步骤推进常挂在**特定回包形态**上，不是"点到高亮框"就行：本例 1-2 后的战斗关引导第 2 步，客户端只有在星级奖励 `isReward==2`（可领）时才发领奖请求，
  且只有回包恰好是"单张卡牌"（`reward.length==1 && type==CARD`）才走 ShowRewardCardEx，它关闭时才 `nextStep`；后面第 7 步"选择刚刚获得的卡牌"也依赖这张卡。
  自造奖励档位（5 星、发两种货币）导致引导卡在第 2 步、只能"跳过"。**自造奖励前先 grep 引导步骤表和各弹窗的 nextStep 调用，倒推原版应发什么。**
- 客户端会**自己累加**星数刷新领奖状态（updateStarNum），口径以客户端为准：这里客户端不算序章，服务端也得不算，否则一处 2 星一处 3 星、满星显示 35/36。
- 改档位阈值 / 总数会让老存档的领取记录对不上（记录按阈值存）：读时做旧键换算，别改旧键。
- 只用 devjs 派发点击的自动化会绕过引导遮罩，测不出引导卡死；验收要从全新档跟着高亮框**真实触摸**（`tools/guidetap.sh`）。

## 从客户端残留里拼回一整套活动玩法（周年活动，2026-10-20，代码 + 回归完成）

- **服务端任务配置丢了，任务清单还在文案键里**：该活动的任务行文案是 `UtilFormat("task_condition_" + planType + "_" + isDaily + "_" + needCount + "_" + goodId)`，
  translation.json 里带具体数值的键（`task_condition_39_0_8000_0`、`task_condition_50_0_3_490007` …）就是原版逐条任务的参数。复活前先把这类"参数拼进键名"的文案全列出来。
- 一个 hub 的多个子入口往往是一条经济链（这里：战斗掉材料 → 研发 → 任务交订单 → 活动货币换东西 → 扭蛋机），**物品说明文案**（`items_desc_<id>`："可在某处研发获得，用于完成某系列任务"）
  会把链条写明；先按说明把链条画出来再定数值，比逐个接口补默认值有意义得多。
- "集齐 N 张限定卡"类界面的卡 id 不在客户端数据里时，拿界面图（`card_reward_1~4.png`）和卡面小图逐张比对。
- 客户端用 `if (data.reward)` / `if (data && data.reward)` 判断成功的接口（补签、GiftBuy 兑换），**失败回包不能带 `reward` 字段**——`[]` 在 JS 里是真值，会被当成成功弹空奖励。
- bundle 里可能有**同名枚举**（这里 `Xxx_Type` 在 hub 和换季活动页各一个），按名字正则抓枚举值要先限定到对应的那一段。
- 放行新入口别在拦截模块里写死：拦截模块读一个"额外放行"表（`M.hubExtraAllowed`），由实现该玩法的模块登记——没装那个模块就继续拦，测试里置空就能验证。
- **包装别的模块的路由时看加载顺序**：模块按文件名拼接，后加载的模块用 `M.route` 注册同一路径会把前面包好的那层整个盖掉（这里 49 号想包 50 号的出战接口，结果计数恒 0）。
  要包谁就把包装放在它后面的文件号里（另开 53 号模块），并用 `tools/check_routes.js` 看每个路由的注册 / 包装链。
- **服务端要复刻客户端的判定时，从 bundle 里把那几个函数原样抠出来跑、逐个输入对拍**（这里来电推送要和主界面手机图标同一个解锁条件：
  `FunctionOpenUtil.getPhone` + 它调用的两个 `ToolManager` 方法，按大括号配对截出函数体，`new Function` 包一层假 `CommonParams`，对全部 plotId 比结果），
  比照着读源码手写一份可靠。
- 原版"按陪伴卡推送"之类的打扰型功能离线复活时要自己加节制：来电推送只在功能入口已解锁时响、每个北京日最多一次、拒接不补响。
- **离线后"付费兜底"消失会把原版数据缺陷放大成卡死**：原版死亡分支表 `drama/errorChoose` 漏登记 2 处死亡选项，线上靠"花 30 个付费道具改选"兜底（该道具可充值购买），
  离线商店不卖该道具 → 新玩家死亡回溯后只能反复选死亡支。排查法：拿文案里的 `death_tips_*` 全集对照分支表找漏项；凡是"资源不足 → 前往购买"的路径，都要确认离线版有获取途径。
- **新玩家全程验收要用"零养成"档一路推到底**（只推主线、不做日常）：能区分"进度墙"（门槛 vs 攒下的抽卡 / 材料能否跨过，算出来）和真 bug；
  自动脚本的卡点大多是脚本问题（引导临时隐藏、上一步打开的页面没关、付费选项代码 CLICK 无效 → 改真实点击），逐个看截图再下结论。
- **下线活动的界面会被终版客户端"藏"起来，回包全对也看不见**（周年活动真机发现 4 处）：入口按钮挪到屏外（y=856 > 720）或 `visible:false`；
  入场动画删一半（只剩"透明 + 下移 800"，从不滑回）；布局和图集错配（条目底图换成 160×310，布局还按 603 高摆）；九宫格底图被换成更小的图、切坏。
  上真机前先**静态扫 uiView**：bundle 里每个 `xxxUI.uiView = {...}` 是 JSON，按图集 `sourceSize` 补宽高、按锚点算包围盒，标出出界 / 隐藏的控件（注意 `\r\n` 和 `.` 不匹配 U+2028，用 `[^\n]*`）。
  修法：入口按全局 / 地图坐标在 hub 钩子里重摆；页面控件用 bundle 补丁在渲染函数末尾调模块钩子重摆（钩子里判授权，未授权不动）。坐标先用调试通道在真机上试摆、截图定稿再写进代码。
- 来电推送一类"全局弹窗"要查客户端的抑制条件：这里 `CommonParams.inDrama` 在登录加载页被置真、要等玩家进出一次剧情类界面才复位，冷启动后推送会一直挂着（日志"still in drama"）。这是原版行为，验收时进出一次福利页即可触发。
- 直接进通话这类"跳过前置页面"的路径，前置页面顺带做的预热（通话背景裁图）就没了，要在推送 / 查询接口里补预热。

## 手机通话 / 短信的客户端坑（v0.8~v0.8.4，2026-10-20）

内容怎么从录屏、截图里还原见 `media-harvest.md` 第 4 节；这里只记客户端这一侧。
- **界面借用别处的缓存对象，关闭时把它销毁**：通话界面直接拿主界面缓存的角色骨骼来用，挂断 `removeSelf()`，同一套装扮时主界面立绘跟着消失（原版就有这个 bug）。
  修法：bundle 补丁给通话界面另建一份骨骼。同类：通话背景竖条和主界面背景共用位图，退出手机时 `disposeAllCache` 对它 `disposeBitmap()` → 实例上换成空操作，源纹理失效时换新 key 重建。
  凡是"关掉 A 界面后 B 界面的图没了"，先查两边是不是共用了同一个缓存对象。
- 短信协议的硬约束（读 `src_ts/phone` 核对，写在 `52_sms.js` 头注释）：每次选项后下发的一组**至少 2 条**，只有 1 条客户端报"配置错误"不显示，生成时并进上一组；
  空分栏给 `null`（给 `[]` 也会画标题）；玩家消息 `personId=0`；相邻消息隔 12 小时以上客户端自己插时间条，所以回复之后的时间用玩家点回复的时间。
- 新玩法未授权时**不建存档键**（`db.sms` / `db.tel` / `db.<活动>.anni`），一律回落旧回包：回归里专门断言"未授权 = 旧回包且不建档"，升级老玩家的存档才和旧版本完全一致。

## 被埋没的内容 + 自制资源（v0.8.4，2026-10-20 夜）

- **扫镜像里"有文件但配置没登记"的内容**：拿 `drama_config` 登记的剧本清单和镜像里全部剧情文件做差集，再逐个看是不是真内容（本例只有某角色的支线小章 19、20 共 14 节是真内容，
  其余是活动关和月度约会同名关的逐字重复）。场景图 / 音乐 / 立绘（含新角色）镜像里都有、译文里有章名 → 终版只是没登记。
  修法：bundle 补丁在配置读完后补登记（`DramaQuery.init`，8j）；服务端支线表改成"配置登记 ∪ 镜像里真有文件"合并生成，别手写章节数。
- **剧情资源全量静态体检**：遍历全部剧本引用的音乐 / 场景图 / 立绘，对镜像查存在性。原版 CDN 本来就缺、原版也显示不出的（本例 5 张）记下来不补，免得把"原版就这样"当 bug 修。
- **原版 CDN 上根本没有的图**（复活章节的节点缩略图）按原版同类图的规格自己生成（`gen_branch_thumbs.py`：216×100、圆角、模糊 + 点阵，用每节第一张场景图），
  放进 build.py 的"自制资源目录" `tools/assets_extra/<URL 路径>`：打包时并进缓存、追加到 allfiles 与 filetable、按内容算 chksum，**与镜像重名直接断言失败**，日志打一行 `cache: +N extra files`。
  自制资源和镜像分开放，才分得清哪些是原版、哪些是自己做的。

## 正式包怎么验需要特定进度的功能

正式包没有调试通道，但 BlueStacks 有 root：备份正式存档 → 拼一份测试存档（别的测试档的进度键 + 正式授权，把要验的节标回未读、删掉相关分支记录）写进
`LayaCache/localstorage/<host>.txt` → 冷启动真实点击验收 → 写回原存档并**用 md5 确认逐字节还原**。
注意测试包和正式包签名不同、ANDROID_ID 不同，授权码要用正式包本机码签的那张。

## 复活换季活动、拼回丢失的界面图（春节档活动，v0.8.5，2026-10-21~22）

- **换季活动常共用一个主界面按钮**：终版把按钮改开新一期的 hub，旧一期开界面的那几行只是注释掉（`mainRoom.ts` 里 `SpringMain` 三行）。
  grep 被注释的 `InitForm(FormID.XXX)`，比扫入口按钮更快找到"代码还在、没人能进"的活动。
- **界面图丢了按这个顺序找**：镜像 → 原包内置缓存（旧版本）→ 玩家手机备份的运行时缓存 → 玩家录屏截图；都没有就用现存图拼：
  把候选图集的帧裁出来拼一张总览图（带帧名、原尺寸）挑替代，先做一版实机截图给用户确认，再写服务端。
- **共用图集被后一期覆盖时，"图存在"不等于"图对"**：同名帧可能已是新一期的另一张图（本例 `item_bg.png` 变成了周年活动的人物裁图）；
  九宫格参数（sizeGrid）是按旧图配的，套在新图上会坏（本例卡面遮罩把卡遮成一大块白）→ 找一个现在还在用同一张图的界面，照抄它的 sizeGrid。
  uiView 里每张图出现两次（控件树一处 + 末尾 `loadList` 一处），替换时按 2 处断言。
- **往别的界面里加节点，用容器的本地坐标摆**：hub 首次打开先弹签到页、入场动画没走完时，按全局坐标换算出来的位置是偏的（真机压到了返回钮）。
  本例 hub 的 `main` 就是 1560×720 地图容器（居中锚点），本地坐标 = 地图坐标，随屏宽一起平移。
- **活动货币的客户端缓存可能有两条刷新路径**：本例 `queryLongTimeInfo`（hub 初始化、兑换后）和 `Library/queryActivityMoney`（`reloadNewCapital`，棋盘关闭、hub 打开时）。
  只回一条，掷完骰子回到兑换页还是旧余额、"碎片不足"挡住兑换。看每个界面 init / close 调的是哪个 reload，两条都回。
- **两期活动共用接口且 id 撞号**（春节活动奖励和生日活动都用 `queryMeetExchangeList / getMeetExchange`，meetId 101~105 两边都有）：
  bundle 补丁在春节页发请求前立一个一次性标记，服务端收到就按春节回包并清掉；另一边的同样调用不动。单测里要验"不带标记照旧"和"标记只管一次"。
- **自造数值前先读界面上的原版文案**：棋盘底部写着"活动货币获取来源：1.完成每日任务，开启活跃度宝箱获得；2.钻石购买"——照它改成活跃度宝箱附送，
  比自己发明"每天送 5 颗"更贴原版，活动里的任务入口按钮跳每日任务也因此说得通。
- **正式包上验背景音乐**：没有调试通道时，看媒体解码进程（`media.extractor`）打开的缓存文件名：`su -c 'ls -l /proc/<pid>/fd'`，
  文件名带原资源名（`…_<活动>.mp3` / `…_main.mp3`）。
- **正式包验收走真实升级路径**：先装上一版正式包 + 还原正式存档，再 `install -r` 新包，确认存档 md5 不变后再点；验完把正式存档原样写回并核 md5。

## 换机迁移、获取途径、红点（v0.8.6）

- **conch 自带任意路径文件读写**：apploader.js 里有全局 `readFileSync(path,'utf8')` / `writeStrFileSync(path,str)`（localStorage 本身就是用它写的 `LayaCache/localstorage/<host>.txt`，一个 JSON）。
  有了系统存储权限就能直接读写「下载」，不用为文件 IO 加 Java 代码；smali 桥只补权限检查 / 申请、列目录（conch 没有）和杀进程。
  `Storage` 类有 `length` / `key(i)`，能枚举全部键做导出。`PlatformClass.createClass(...).call(name, a, b)` 传两个字符串参数实测可用。
- **BlueStacks 装包时自动授予运行时权限**，看不到授权弹窗；测"没权限"路径用 `pm revoke <包> android.permission.WRITE_EXTERNAL_STORAGE`（会杀进程）再冷启动。
- Git Bash 里 `adb push x /data/local/tmp/...`、`/sdcard/...` 会被改写成 Windows 路径：命令前加 `MSYS_NO_PATHCONV=1`。推到已存在的目录名时要写完整目标文件名。
- **文案表缺货币名**：`capital_<type>` 缺键时客户端原样显示键名（"5capital_21"）。在 `StringUtil.UtilText` 找不到键的出口（已有的别名钩子）补一张小映射表，借同类物品名（经验物品的名字）。
- **"获取途径"弹窗**原版数据在服务端已丢，但离线版自己的委托掉落表 / 兑换页 / 爬塔商店都知道每种材料从哪来：
  按表算出"最早已开放的那一关 + 卖它的兑换页 + 爬塔"，客户端自带文案 `delegate_skip_desc_<类>_<委托>_<难度>` 就能显示并跳转。客户端只在材料数为 0 时弹它，验收时用调试通道把某材料清零。
- **盘点"只有兜底回包的接口"会有误报**：某个"突破"接口看着没实现，其实查询接口把所有卡固定为"已突破"，按钮根本不出现。子代理的盘点结论要回源码核对一遍覆盖关系再排期。
- **资源体检要按客户端的解析规则走，不要拿资源名直接找文件**：剧本里的场景名经 `res/json/image.json` 映射成路径，映射可以和名字不同（`chuangqian1` → `chuangqian_1.jpg`，甚至原版自己拼错的 `pitcure_main_blood.jpg`）。
  按名字找会把这类当成"缺图"（本例 5 张里 2 张是误报）；也会漏掉"名字对、映射指向不存在的文件"那种。写成常设检查脚本（场景数、缺图数）放进打包前回归。
  真缺的图先读那一句台词，再在同一条剧情线里找现成的同类场景（同一人物家的另一个名字、同一事件的上一页），映射过去比留黑屏好，标 [自造]。
- **原版代码里被注释掉的修复**值得看一眼：春节奖励页"语音播完恢复背景音乐"原版源码写了又注释掉，照原意恢复并加上"页面还开着、没换播别的"两个保护即可。
- **界面贴图体检**：Laya 皮肤短路径（`dir/sub/name.png`）是图集帧，缓存键 = 图集 `meta.prefix` + 帧名（帧名不含目录），**不能**按"去掉文件名的目录 = 图集名"推；
  运行时靠 `AtlasInfoManager.enable("fileconfig.json")` 把帧反查到图集再自动加载。写脚本把 bundle 里写死的 skin / loadList / loadImage 全部按这条规则核对镜像，
  **对打完补丁的 bundle 跑**（否则自己已经换掉的缺图会反复冒出来）。原始结果噪声很大：清理调用（`clearTextureRes` 清没加载过的图集）、IDE 默认控件占位 `comp/*`、
  不会被读的 `styleSkin`、运行时会被代码覆盖的模板默认 skin、没有任何剧本触发的动作分支、没有调用方的枚举分支——逐条回源码核对可达性再决定修不修。
- **剧情配音的路径用的是"播放时的剧本号"**（`chapte_voice/<drama_config 的键>/<voiceId>.wav`），不是剧本文件里的分段键（`drama` / `result1`）；
  按分段键拼会把上千条全判成缺失。音乐 / 音效则走 `sound.json` 映射。配置里登记了但 CDN 清单里从来没有的剧本（未上线段落）先排除，再看缺什么。
- **复活"入口被删、界面和关卡数据都在"的小游戏**（周年活动里的三消，v0.8.7）：从活动枚举 / 点击分支里找到它（`case X: load(atlas) → InitForm`），
  确认关卡数据在客户端（`res/json/game/l*.json`）、计分在客户端，服务端只管列表 / 结算 / 扫荡三个接口；入口照"复活换季活动"的办法在宿主地图上挂一张自造图，
  点击时直接调宿主原有的 `imgClickHandle(那个枚举值)`，走原版打开代码。小游戏的正式名字看选关页标题（本例代码叫"消消乐"，界面标题是另一个名字），入口牌子用界面上的名字。
- **自造阈值先实机玩一局再定**：关卡 json 里的分数要求和客户端计分差一个数量级（连锁、特殊元素、步数用完的收尾引爆都会成倍加分），只看配置定线会过松或过严。
  真机滑几步（从截图读棋盘找三连），记下一局的典型分数，把档位定成"随手玩落在中间档"。
- **UI 的尺寸也是证据**：奖励列表只有一格宽且按类型去重，说明原版每一档奖励是同一种物品；据此把各档都定成活动货币，而不是凭空混发几种。

## 复活"写死隐藏"的主界面入口（卡牌留言活动，v0.8.8）

- **找候选**：主界面构造 / 红点回调里 `xxx.visible = false` 紧挨着一行 `showRedPoint(xxx, data.showXxxRedDot)`、点击绑定被注释掉的，就是"做完了但没上线"的入口。
  逐个核对四样：界面类还在（`ui.*UI` + 页面类）、图集 / 背景 / 入口图在镜像里、请求接口在网络层、文案键在翻译表里。四样齐了才排期，缺资源的（只剩两张框图、语音缺一半）记"不复活"并写明原因。
- **入口补丁两行就够**：把 `visible = false` 换成按授权位判断，点击绑定照注释掉的原样恢复（先 `off` 再 `on`，免得重复绑定）。
  这一排图标的布局函数按名字顺序排可见的那些、而且就在设可见性之后调用，所以不用另写布局代码；先确认这一点再动手，否则要自己挪坐标。
- **服务端映射丢了就按客户端的硬约束反推，再拿界面美术核对**：客户端按卡分组、每组必须正好 2 条否则整张卡不画——数据只能是"每张卡 2 条"。
  第一版按"卡号段 × 已复活的同类内容两两配对"凑了几十条，装上一看，页面背景图上印着活动名和起止日期（某个节日那一期）；
  回头按日期筛那批内容，落在活动期里的恰好每位角色 2 条，卡数也正好是界面一屏的列数——三条独立证据对上，改成只出那一期。
  **先打开界面看一眼再定数据规模**：背景图 / 标题图上的文字（活动名、日期、玩法说明）是现成的规格书，比代码注释更可靠。
  代码注释里留下的单条回包示例（哪张卡、几级条件、exchangeId 从几开始）当锚点，其余按同批次规则补齐，模块头注释写清依据并标 [自造]。
- **内容复用已复活的模块**：这里的"留言"就是手机里那批活动短信，正文不复制、不再锁；新页面只负责"解锁领奖"，"前往"跳回已有的手机页面。
  授权上跟着那个模块的功能位走（没有短信功能位的码，这个入口不出现），不另开新位。
- **红点三处要一致**：主界面红点接口里的字段、页面里"可领"的按钮红点、领完后客户端主动刷新的主界面红点，都由同一个 `claimable()` 算；测试里把"没卡 / 卡等级差 1 / 刚好够 / 领完 / 换了没这位的码"都走一遍。
- **验收技巧**：测试存档里卡全是满级时，复制一份把指定卡分别调到"刚过第一档"和"不够第一档"再推上去，一次看到"可领 / 半锁 / 全锁"三种状态；
  不想为"没有这一位"再签一张码时，用调试通道临时把授权判断函数包一层拒掉那一位，再调主界面的红点刷新，看入口是否隐藏、接口是否回兜底（重启即恢复，不进存档）。

## 自定义头像功能位（参照另一个项目的分档，v0.8.9）

- **原生运行时自带的文件函数够用，先探一遍再决定要不要加 Java**：用调试通道列 `window` 上的全局函数，这个运行时有 `fs_readdirSync / fs_lstatSync（返回 isDirectory / isFile / size / mtime）/ fs_readFileSync（ArrayBuffer）/ fs_writeFileSync（写二进制）/ fs_exists / fs_mkdir / fs_rm`，
  选图、按修改时间排序、拷进私有目录、删旧图全在 JS 里做完；原生桥只用来查 / 申请存储权限。
- **引擎能直接加载本地图片，但要写成 `file:///绝对路径`**；只写绝对路径不报错、回调也不来（被当成相对网站根的地址）。
- **自定义头像别新增"形象 id"**：剧情立绘、对话头像按形象 id 拼路径，新 id 会处处缺图。保留原 id，只在代码设完头像贴图之后（bundle 补丁挂在那几行后面）
  换成玩家图的居中正方形子贴图（`Texture.create(tex, x, y, s, s)`）+ 圆形遮罩；没授权 / 文件没了就撤掉遮罩，原版贴图自然回来。
- **解码器不认 EXIF 方向**（实测：方向标 6 的 800×600 照片加载出来还是 800×600 横着）：手机竖拍的照片多半是横着存、靠 EXIF 竖过来的。
  读文件头时顺手解析 APP1 里 Exif 的 0x0112（大小端都要认），显示时把图片控件的轴心挪到中心、位置补回、按 90 / 180 / 270 转；撤销时还原轴心和位置。拷贝时扩展名按内容定，别信原文件名。
- **大照片先读文件头拿宽高**（PNG 看 IHDR 第 16-23 字节，JPEG 找第一个 SOFn 段），超过 GPU 贴图上限（按 4096 算）的不加载、直接提示"截个屏再用"；预览一次只加载一张，换下一张前清掉上一张的缓存。
- **验收要走的分支**：大图（3000×4000）能预览能用、超限图被拒、子文件夹（聊天软件的下载目录）能找到、换图后旧文件被删、重启后还在、换成没有这一位的码时按钮消失且头像回原版、再换回来又出现、恢复默认后私有目录清空。
- 这个游戏的"头像"就是主角形象 id（1~4）：主界面、设置页各有一处按 id 设图集帧，补丁两处都挂；形象列表里点选时的预览不挂，仍显示那个形象。
- 入口放开屏公告页（和一键拉满、导出 / 导入存档同一处）；这个授权位不进任何档位预设，签码时单独勾。

## 真正不联网：去掉 INTERNET 权限（v0.9.0，2026-10-24）

- **发现**：以前所有测试都是"只对游戏断网"，没人看过联网时离线包在干什么。网络全开冷启动、停在公告页 100 秒，原生 SDK 就向 22 个地址的 443 发起连接：
  发行方的统计 / 追踪、发行方网关（约 16 个 CDN 地址）、发行方账号接口、一键登录 SDK、QQ 互联（带机型和 appid）。
  它们在 `Application.onCreate` 和隐私回调之后初始化，我们只跳过了隐私弹窗，SDK 照常起来。公告页写的是"不联网"。
- **测法**（root 模拟器，数据不出去）：`iptables -I OUTPUT -m owner --uid-owner <uid> -j DROP`（这台内核没有 LOG 目标）；被丢的连接停在 SYN_SENT 约两分钟，
  轮询 `/proc/net/tcp*` 第 8 列 uid、第 3 列远端（每 4 字节小端），每 0.3 秒一次；tcpdump 记 53 端口拿域名，没走系统 DNS 的（HTTPDNS / 写死 IP）用 dex / so 里抽出的域名在电脑上解析后对 IP。
- **修法**：清单去掉 INTERNET，系统层面保证。没有 INTERNET 时 Java 的 DNS 查询抛 `SecurityException`（不是 IOException），实测发行方 SDK / Volley 都接住了，没有崩；
  但 Laya 引擎 `DevID.getMac()` 遍历网卡时 `NetworkInterface.getNetworkInterfaces()` 返回 null、只防了 SocketException → 空指针 → `conchConfig.getDeviceInfo()` 返回空串 → `apploader.js` JSON.parse 报错卡死启动。
  smali 让 `GetWifiMac()` 直接返回 null（原版"没找到网卡"分支）。网络状态类权限（ACCESS_* / CHANGE_*）保留，缺了 SDK 一调就抛 SecurityException；其余隐私类权限（开机自启、应用列表、读日志、改设置、电话状态、OAID）一并去掉。
- **防回退**：正式包检查脚本加"清单里有 INTERNET 就 FAIL"。测试包也没有 INTERNET；调试通道走文件，不受影响。
