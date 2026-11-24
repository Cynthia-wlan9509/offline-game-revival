# 界面、弹窗、美术资源的坑

UI 层级、弹窗、文字排版、新手引导遮罩、活动皮肤分层、开屏和视频、自制界面换原版皮。

现象 → 原因 → 修法。原来都在一份 `pitfalls.md` 里，2026-11-19 按阶段拆开，条目原文没改，按原来的先后排。原来的分节标题留在条目最多的那份文件里，别的文件用三级标题注明出处。索引见 `../pitfalls.md`。

## UI 层级

**某个面板打开后盖住别的画面 / 整屏黑**
- 原因：为抬高某层改了 `Canvas.sortingOrder` / `overrideSorting`，之后没还原
- 修法：抬升前先记住原状态，退出时还原。**每次抬层都要配一个还原**

**地图盖住界面，或反过来按钮点不动**
- 原因：不同 canvas 抢排序
- 修法：明确分层（地图 / HUD / 面板 / 对白各一档），新面板接入时确认不会打乱已有分层

**弹窗被底下的界面盖住，早期的绕法是"弹窗一开就把底下那层藏起来"**
- 症状：关卡详情弹窗背后不是关卡列表，而是更底下的地图。翻补丁发现有人写了"打开详情时隐藏列表，避免详情被列表盖住"。
- 根因：另一个补丁为了让某个入口卡片"肯定在地图上面"，把它所在的画布层级直接设成 9000——那块画布其实是整个主界面的根。
  游戏自己的弹窗管理器把弹窗固定从 100 排起（并且每次显示都会重设），所以之后所有弹窗都被 9000 压住。
- 修法：先搞清游戏原有的层级带（这里：地图内部 <= 35、主界面按钮 40-47、弹窗 >= 100），自己加的层级一律落在带内（改成 60）。
  不要用"抬得比谁都高"解决遮挡，也不要去和管理器抢弹窗自己的层级（设了也会被它改回去）。
- 排查办法：写一个只打印的函数，量出"下层面板用到的最高层级"（根画布 + 往上的祖先画布 + 它里面单独排序的小画布）和上层面板的根画布、渲染模式，打一行日志。
  数字一出来就知道是谁不对（这次一眼看到 baseRoot=UIList/9000）。
- 教训：见到"把 A 藏起来免得挡住 B"的补丁，多半是层级没理顺留下的债，值得回头找根因。

**嵌套 Canvas 在父 Canvas 未激活时被重新激活，会被当成根画布重排（案例 A，踩了多轮）**
- 症状：去过历练区再回主线地图，当前任务节点看不见，实际被摆到了屏幕右侧（锚点 x≈1855）；节点是激活的。
- 原因：节点自带嵌套 Canvas，父 Canvas 不活跃时重新激活它，Unity 把它当根画布重排：锚点变 (0,0)、尺寸等于屏幕、缩放变成画布缩放系数（这里 0.456）。
- 修法：加布局自检：正常时记一份 RectTransform（锚点、轴心、尺寸、位置、缩放）；切地图时检查，锚点 x 异常或缩放不为 1 就还原（`OfflineTaskTipSanity`）。别去追是哪一次激活弄坏的。
- 怎么确认的：探针对比往返前后节点的完整布局值；修后日志出现 `task tip layout restored`，往返几次节点都在。

**地图把根列表 Canvas 改成 Overlay 后：粒子 / 模糊特效失效，相机模式弹窗被盖住（案例 A）**
- 症状：小游戏里蝴蝶 / 光圈看不见、对白里雾气雪花不显示、对白开头一整块白框；某些弹窗（指引后弹窗、关卡详情框）也看不见。一度怀疑缺图，但包里资源都在。
- 原因：进地图时把 `UIList` / `NormalList` / `PopList` 等根列表画布切成了 `ScreenSpaceOverlay`。Overlay 下粒子特效不渲染、抓屏模糊（grab-pass）抓不到屏渲染成白块；留在 Overlay 的列表画布还会盖住相机模式的弹窗。
- 修法：进剧情 / 小游戏时把这些画布切回 `ScreenSpaceCamera` 并恢复原 sortingOrder（`UIList` 10、`NormalList` 60、`PopList` 100）；对白模糊用运行时开关关掉；做一个自检函数在非地图 / 非回顾 / 非剧情状态下每次面板加载和页签切换后跑一次（`OfflineListCanvasSanity`）。
- 教训：遇到白框 / 特效看不见，先怀疑 Overlay 画布遮挡，而不是缺图；基础画布不要抬到超过 100（不要用大 order 或藏底层界面绕层级，先测画布链）。

**面板抬到 Overlay / 高层后，它的嵌套 override 画布没跟着抬，新开弹窗被盖住（案例 A 男主页）**
- 症状：男主页里点语音，语音面板看不见；点返回后男主页按钮全消失只能卡死；确认框也被盖住。
- 原因：男主页（panel 1024）把基础画布抬到 Overlay 8000，嵌套画布（`UISort` / `btn_back` / `btn_busy`）没跟着抬；之后新开的面板 order 比它低。
- 修法：抬面板时把它里面带独立排序的嵌套画布一起抬同样的量；在面板管理器每次显示面板后加钩子（`OfflinePanelOverHero`）：某页开着且新面板不是它时，把新面板根画布切 Overlay、嵌套画布抬到它之上；关掉该页后还原。

**界面元素只在"完整刷新"时才开关，而离线版切页面走的是快路径**
- 症状：某个小图标去过别的页签再回来就不见了；反方向又残留在不该出现的页签上。
- 原因：原版在重新初始化界面时按当前模式设它的显隐；离线版为了省加载时间复用了已经建好的界面，不再经过那个初始化。
- 修法：在快路径的"应用目标页面"函数里，把依赖模式的显隐各设一次。写快路径的时候，把原版初始化函数里所有 SetActive 过一遍，逐个确认。

**离线代码把「原版打开子面板时顺手关掉地图面板」当成离开功能，子面板几秒就被顶回地图（案例 A 2026-10-23）**
- 症状：在某个玩法区里点兑换所，不到 3 秒就弹回历练区地图，商店被关掉；同一区里的编队按钮也是这样。
- 原因：原版打开商店时会先关掉该玩法的地图面板。离线补丁里有个监视器，把「该功能的面板关闭」当成离开，于是把外层地图重新挂了回来。商店（面板 1）和编队（面板 111）不在该功能的放行名单里。
- 修法：查出子面板号，加进该功能的放行名单。凡是写了「离开某功能就恢复 X」的监视器，都要把该功能里会打开的所有子面板列一遍。
- 怎么确认的：logcat 里看到关闭地图面板后紧跟着 feature leave 和地图恢复；加进名单后，商店开着 6 秒以上不会被关掉，返回和真正离开时地图都能正常挂回。

**修弹窗被压住时，补救检查查错了节点，修了两次都没生效（案例 A 2026-11-05）**
- 症状：进某个角色页时，当天有互动事件的角色，对白看不见、也挡不住点击。玩家连点屏幕就变成一直在触摸角色，每点一下排一句对白，退出页面后才一股脑弹到地图上。
- 原因：引擎里有两个同名的弹窗列表节点。对白实际挂在 `[Stage] MainStage/PopList` 下，而之前的补救逻辑只检查了 `ApplicationObject/PopList`，等于什么都没碰到。
- 修法：页面开着时，每隔约 0.3 秒检查一次对白是不是掉到了页面下面，掉了就抬回来；重复的事件对白不再排队；退出页面前清掉排队的对白。修「盖住 / 压住」类问题之前，先在运行中把画布层级 dump 出来，确认弹窗真实挂在哪个节点，别按名字猜。修过一次没生效，先怀疑检查的对象不对。
- 怎么确认的：构造一个「有待处理互动事件」的角色。修前连点 5 下排了 5 句，退出后弹到地图上；修后排队数为 0，退出后地图干净，好感奖励当场弹出，和玩家录屏对得上。

### 方向误判（最贵的错误）（续，原节在 `agent-workflow.md`）

**全屏引导遮罩在离线/模拟环境必然吞点击 —— 要分层处理**

- 症状：引导一开，底部导航/返回按钮全部点不动，只能停在某一个界面；日志里点击只报
  `Button On Click empty`（打在遮罩自己身上）。
- 原因：引导遮罩通常有**两层**：视觉提示层（高亮、手指动画）和**点击屏蔽层**
  （全屏 Raycast 组件 `Empty4Raycast`、以及 prefab 里的 `btn_xxxMaskBg` 这类全屏按钮）。
  原版靠点击屏蔽强制玩家只能点目标；离线版一旦有某步等不到服务器事件，屏蔽层就永远不撤。
- 修法：**保留视觉提示，拆掉点击屏蔽**——不要为了"安全"把整个引导关掉。
  实测两处注入点即可：挡住组件创建（`AddComponent(typeof(T_Empty4Raycast))` 那行）+
  让遮罩按钮永不激活（`SetActive(false)`）。这样引导能照常提示，导航永远不会被吞。
- 判断是否修好：点一个底部导航按钮，日志里应出现**真实按钮事件**
  （`Button On Click:<按钮名> instanceID:...`）而不是 `Button On Click empty`。

**补数据之前先查界面有没有入口：客户端里有「孤儿」面板和原版死代码（案例 A 2026-10-18~19）**
- 症状：后端已经把 CG、两类收藏的数据接好了，玩家却看不到；用户找不到某个功能的入口；原版功能清单里有几项一直没接上。
- 原因：终版客户端里有一个旧面板（CG 相册、玩具、收藏），已经没有任何地方会打开它。注入强行打开后，一个页是空按钮加「敬请期待」，CG 相册是空格子，配置里 47 条 CG 用的是同一张占位图。另有几项是原版开发时就砍掉的：查询函数是空的、没有调用方，或者原版处理函数本身就报错。
- 修法：补「藏品 / 奖励 / 功能」类内容之前，先 grep 谁会打开这个面板，再注入强行打开，看内容是不是占位。孤儿面板只做数据和存档，不要硬加入口，文档里写明「数据已通、界面不可见」；死代码不投入实现。把「查过、不需要做」的原因写进文档，免得下一个会话重复调研。

## 复活下线活动的皮肤（美术分层藏，别急着说丢了）

**说"这个活动只剩最后一版皮 / 美术丢了"之前，先把同名资源在各层包里比一遍**
- 背景：下线活动在终版客户端里往往只显示最后一期的皮肤，容易让人以为"其它期的美术随服务器一起没了"。其实换皮常常分层藏着，不是真丢。
- 要比的三处：① 热更包里的普通面板；② **同一热更包里的 `rep/*`（复刻）预制**——它和普通面板常带一批同名贴图，但 **path ID 不同**，是另一套皮；③ **原始安装包里的同名 bundle**——它可能在打包时被热更整包覆盖，里面还藏着一版。三处各导出同名贴图（`xxx_bg_01` / `xxx_title_01` 这类）逐一比对。
- 判据：同名贴图在不同包 / 不同 path ID 下存在不止一个版本 = 还有别的皮，没丢。
- 实例（案例 A）：一个抽取类活动一度被我判成"只有一版皮"，用户坚持"每个角色都有自己的样子、当年全解包过"，结果是对的——最后找齐三套：金色皮在热更普通面板、蓝色皮（复刻）在同包 `rep/*`、粉色皮在被热更盖掉的原始 APK bundle 里。
- 教训：**用户说"以前见过 / 解包过"时，先去各层包里找，再下结论。** 这类"美术还在、只是终版没登记或被覆盖"的被埋没内容，和"拿配置清单对镜像做差集"（见 `SKILL.md` 第 8 步）是同一类抢救。

**要发被热更 / 构建覆盖掉的那版皮：另存一份包 + 运行时按节点路径把真图拷上去，别用染色凑**
- 发法：把原始 APK 里被覆盖的那个 bundle 复制出来、**改掉 CAB 名**放到单独路径（案例 A：`assets/AssetBundles/Android/v3skin/<皮肤包>`，由 `tools/skin_bundles.py` 在构建期生成），运行时 `AssetBundle.LoadFromFile(...)` 加载，按**节点路径**把 Image / RawImage 的 sprite、贴图、尺寸、文字颜色拷到活着的预制上；切到别的皮时把拷过的东西复原。
- 选皮入口：hook 活动模型里决定"显示哪个面板"的方法（案例 A 是 `<活动>Model:IsShowFirstPanel` / `IsRestartCard`；原版靠 `ComActivityModel.RestartCardList` / `UseFirstAgain` 里的 `ShowPanelIndex` 定皮）。
- 坑一：**不要对"游戏自己稍后还要加载的那个 bundle"调 `LoadFromFile`**——会让游戏自己的加载报 "panel prefab missing"。要发的那版必须是改了 CAB 名的独立副本。
- 坑二：**染色不是换皮。** 按主题色正片叠底效果发闷（用户原话"太阴间"）；`Unlit/Gray` 不认颜色、`Graphics.Blit` 配 UI shader 渲染成黑、`GL.Color` / `DrawTexture` 不可用。真皮的美术在，就用真皮，别拿颜色凑。
- 坑三：注入一大段 Lua（约 18 KB）会把模拟器 Unity 线程冻住；调这种皮肤补丁要**打一个 dev APK** 装着测，别靠注入。

**热更包会整包替换 APK 里的同名资源包：照 APK 清单标的「有图」会失真（案例 A 2026-10-20）**
- 症状：几个复活活动的主界面入口报 `Error LoadSprite null ui/activity ActivityEntrance_<活动号>`，补丁表里明明标了有图。
- 原因：构建合并资源时，手机热更的 `ui/activity` 会整包替换 APK 里的同名包，而不是按文件合并。APK 里有这几期的入口图，热更那份没有，合并后就丢了。「有图」的标记是照 APK 清单标的。
- 修法：以合并后实际生效的资源为准来核对（用 UnityPy 分别读两份；热更文件前有 8 字节前缀，要先切掉）。缺图的期在加载处加别名兜底：用锚点把原版两处拼 `ActivityEntrance_<号>` 的地方改成先问一个别名函数，模块没加载时走原逻辑。挑别名时先导出全部入口图拼成总览图来挑；复刻期和原期活动名完全相同的，直接借原期的图。构建期自检读热更包，断言每个别名目标都存在、标记与实际一致、每个无图的期都有别名。
- 已知副作用：入口图是整张烘焙好的，借来的图带着原活动的标题文字，尺寸也可能不一样（偏大时会压到旁边的入口），要如实告诉用户；真要改，只能往资源包里加新图。
- 怎么确认的：在开发包上分别打开这几期，热刷新和冷启动都能看到入口图，logcat 里 LoadSprite null 为 0。

## 游戏内 UI / 弹窗

**自己弹一个对话框，结果是一块空白白框（没文字、没按钮图案）**
- 原因：绕过游戏 UI 框架，直接用 `AnimatedPopLayout` / `PopUtils` 加载裸 prefab
  （典型 `prefab/ui/dialog_common_msg`）。prefab 里的 `Text.font` 是 `nil`、按钮贴图依赖主题/皮肤 bundle，
  离线流程没走那套 UI 初始化，于是只剩默认白底。
- 排查：加载后用 `GetComponentsInChildren(typeof(Text))` 打印每个 Text 的
  `name / activeInHierarchy / font / text`。`font=nil` 基本就确认是没走原生对话框/皮肤。
- 修法：**优先用游戏原生的对话框 API**，不要自己拼 prefab。在 il2cpp `dump.cs` 里查 `DialogUtils`
  的静态方法；Unity Lua 侧通常是 `GameNS.<框架>.PopPanel.DialogUtils`：
  - 双选项（自定义按钮文字 + 两个回调）：`ShowTxtDialogCustom(txt, mode, confirmCb, confirmText,
    cancelCb, cancelText, isSystemDialog, isBlurBg, tweenFinishCb, title)`
  - 单按钮确认：`ShowConfirmDialog(txt, mode, confirmCb, isSystemDialog, isBlurBg, tweenFinishCb, title)`
  - 单按钮 + 取消回调：`ShowTxtDialog(txt, mode, confirmCb, cancelCb, isSystemDialog, isBlurBg, tweenFinishCb)`
  这些接口自带主题、字体与按钮，不需要自己注入字体。
- 实例：案例 A 的新玩家开局「等级 / 资源 / 解锁」三步选择，第一版裸 prefab 渲染成空白白框，
  改成 `ShowTxtDialogCustom` 后文字、双按钮、主题全部正常。

**富文本加粗把字糊成一团（案例 C 2026-11-01）**
- 症状：启动声明框里用 `<b>` 加粗的红字，笔画粘在一起，反而看不清。
- 原因：游戏字体加粗后字形粘连。
- 修法：只用 `<color=#...>` 上色，不加粗；文本组件要开 `supportRichText = true`；每句控制在一行以内，并截图确认。

**战斗 / 调查结算要点两下才进下一步：看不见的跳过按钮吞了第一下点击（案例 A）**
- 症状：结算界面第一下点击没反应，要点两下；第三下还会误点到下面的关卡。worker 曾误报成「战斗结算触发了两次」。
- 原因：战斗面板上有个不可见的 `btn_skip`，结算后仍可点，走了 skip 分支吞掉第一下点击。
- 修法：战斗一结算就把 `FightingTemplatePanel.Instance.btn_skip` 隐藏（在两个本地战斗结算函数 `FinishLevelFight` / `FinishBackFight` 开头调用）；或给 `SkipOnClick` 打补丁，结算状态下的跳过等同于点结果按钮。
- 怎么确认的：在结算页对着时间戳逐一核对收到点击的控件，发现落在 skip 身上。

**带内嵌图标的原版确认框在离线版软锁，是没装图标加载器（案例 A）**
- 症状：抽卡券为 0 时点十连毫无反应，日志有 `NullReference`，一个不可见的确认框吞掉所有点击。
- 原因：原版这里弹「用货币补买」对话框，文字里有内嵌图标，需要 `LinkImageText.funLoadSprite`。离线版没装这个加载器，`tryGetSprite` 抛空，对话框半开着挡住点击。
- 修法：登录时给 `LinkImageText.funLoadSprite` 装上图标加载函数（`CommonLoadIcon.LoadLinkImageTextSprite`）。装上后补买对话框正常弹出，流程走通。

**强制阅读 / 教程弹窗别靠计时，要看真实滚动并在设备上截图验证（案例 C）**
- 症状：新装后首次说明页按钮上没有倒计时、点一下就直接关了。
- 原因：面板在加载画面后面就已经打开并开始倒计时，玩家看到时早走完；而且找不到标准 `ScrollRect`，「滑到底」检测退回成只计时。
- 修法：用面板局部坐标看正文被拖动了多少，滑过大半才解锁（用局部坐标避免打开动画被算成滚动）；没滑到时显示提示。强制阅读类弹窗一律在真机上截图验证「没滑到不解锁、滑到底才解锁」。

**确认框点空白处会触发「取消」回调，自选翻页按钮不能放在取消键上（案例 C）**
- 做自选 / 翻页弹窗（一页一个条目，按钮「开这个 / 下一个」）时：若用普通确认框，点空白会走「取消」回调把框关掉，「下一个」若复用取消键就关不掉。要用带 `directExit` 参数、点空白直接关闭的那种确认框；「下一个」单独做一个按钮，翻页时延迟 0.3 秒再开下一页（同一帧开会叠）。

**主线走到原版最后的占位任务，任务条显示策划的玩笑话和「(0/1)」（案例 A 2026-10-18）**
- 症状：主线全部走完后，停在原版最后一条任务上（要求等级 999，没有下一任务）。任务条显示原版的调侃文案加「(0/1)」，任务面板的目标行还有另一个「(0/1)」。
- 原因：任务条总是用配置行的文字加「(当前/最大)」；面板目标行由另一个组件渲染，和主界面任务条不是同一套代码。
- 修法：把「没有下一任务」的任务认作终点，在构建任务信息时只改显示文字，任务数据不动，这样已经停在终点的旧存档下次登录就能生效。面板那个组件也要补上，并且只在文字恰好等于完结语时才去掉进度，免得影响它的其他用处。验收时两处都要看。

**从脚本里主动关掉原版的对白面板，原生层直接崩（案例 A 2026-10-30）**
- 症状：为了不让对白框挡住奖励弹窗，补丁里直接 close 了对白面板，模拟器上随即 SIGSEGV 闪退。
- 原因：原版从来不从脚本里关这个面板，这条路径在原生层会崩。
- 修法：别关面板，改提示队列。包装 `GamePromptMgr.ShowPrompt`：当前提示是对白、队首不是对白、且那个页面开着时，把当前提示置空；离开页面时清掉排队的对白提示，并同步减计数（相关条目：前面的 A queued prompt that cannot show blocks every later dialog）。
- 怎么确认的：同一套操作手点 3 轮，0 次崩溃。

**界面刚打开时按尺寸算缩放，结果接近 0，图被缩到看不见（案例 A 2026-10-30）**
- 症状：静态卡的卡池第一次打开只有底色，切走再切回来才显示卡面。
- 原因：打开的那一刻界面还没排版，按容器尺寸算出的缩放（`GetZoomRate`）接近 0。
- 修法：照动态卡的做法，先异步把图加载完、排好版再显示。

**改了按钮文字，界面上显示的还是原文（Laya，案例 B 2026-10-29）**
- 症状：把设置页一个按钮改了名，点击已经走新逻辑，文字却还是原来的。
- 原因：游戏在绑定事件之后，又按语言表把按钮文字设了一遍，提前改的文字被盖了回去。
- 修法：补丁锚点放在按语言表设文字的那一行之后（`btn_xxx.label = UtilText(...)`），在那里改名、隐藏红点。

**繁转简：别转“拿来比较的字”，转换表小心扩展区汉字（案例 G 2026-11-10~14）**
- 症状：①转简体后个别字变成乱字或问号；②简体模式下免费抽卡按钮点不了；③创角页等少数文字仍是繁体。
- 原因：①对照表里有扩展区汉字，在 JS 里占两个位置，按位置配对就错位；②客户端拿“控件上显示的字”和繁体常量比较来判断状态，字被转了就对不上；③字写在图片里，转不了。
- 修法：对照表只留基本区汉字；转换挂在文本控件的 setter 上并存原文，getter 在显示内容等于转换结果时返回原文，让比较逻辑照旧；写在图里的字接受，或换图。
- 怎么确认的：简体模式下把所有带状态的按钮（免费抽、领取、签到）各点一遍。

**临时换了“当前主角”的界面，关闭时要先换回再刷新（案例 B 2026-11-09）**
- 症状：把定制角色放到主界面后，邮件、成就、剧情的红点全没了。
- 原因：选人界面打开时临时把“当前男主”换成定制角色；关界面时先刷新主界面红点、后换回，刷新那一刻读到的还是临时角色（它没有这些数据），红点被清空。这是老问题，加了新功能才暴露。
- 修法：把“换回”挪到刷新之前。凡是临时借用全局状态的界面，关闭路径上先还原再触发任何刷新。
- 怎么确认的：选回原角色后主界面是原角色、红点都在；冷启动后主界面仍是被选的角色。

### 工具链 / 环境（实测坑）（续，原节在 `device-emulator.md`）

**原生弹窗不会自己消失，必须手动 `dispose()`；而且它不一定在「你以为的那个」PopManager 里**
- 症状：自己用游戏原生 `DialogUtils.ShowTxtDialogCustom(...)` 弹的窗，点完按钮流程走完了，**弹窗还留在屏幕上**，
  它的全屏拦截层吞掉所有点击（日志只报 `Button On Click empty`），玩家被困住，只能重启。
- 原因：原生 Dialog 与 `PopLayout` **不会自动关闭**，得调用方显式收。若流程是"每步新建一屏"，最后一屏没人收。
- 权威样例（照抄它）：`CommonMsgDlg:onClickCancelBtn → doClose → self.popLayout:dispose()`
  —— **在按钮回调里直接 dispose 是官方写法，安全**，不用担心"自己关自己"。
- 两个实测坑：
  1. `ShowTxtDialogCustom` 的返回值经 tolua 绑定**取不到（恒为 nil）**，不能存句柄。要关只能从 PopManager 里拿。
  2. 同一个引擎里可能有多个 `PopManager`。本例中弹窗注册在
     `Frame.SystemManager.getInstance().PopManager`，而 `CommonFuncion:GetIntance():GetPopManager()`
     是**另一个空实例**（`GetPoplayoutCount()` 恒为 0）——查错了会误判成"弹窗不在任何管理器里"。
- 修法：`SystemManager.getInstance().PopManager:GetTopPopLayout()` 取顶层，**核对 prefab / resName 再 dispose**，
  避免误关别的面板；`ShowStep()` 每次新建前先收上一屏，避免层叠。
- 兜底：如果拿不准关闭 API，`PopManager` 通常还有 `RemoveAllDialog()` / `RemovePopPanel(pop)` 可用。

**面板同一帧销毁再重建，新面板的按钮全失效**
- 症状：某个页面出来了但点哪都没反应，或关不掉；日志是 `某面板.Instance`（静态的"当前实例"）为空。只在"从 A 面板直接跳到同类的新面板"的路径上出现。
- 原因：Unity 的销毁延迟到帧末。旧实例的 `OnDestroy` 在新实例的 `Awake` 之后才跑，无条件把静态引用清成空。原版靠网络回包隔了几帧所以碰不到；离线版回包是同步的，就撞上了。
- 修法：`OnDestroy` 里改成"静态引用是自己才清"。同一种写法的面板一起改，别等一个个撞。

**提示文字（飘字）在某些页面上一句都看不见，点击处理和文字都是对的**
- 原因：Unity 里「相机层」画布永远画在「叠加层」画布下面，层级数字设多大都没用。为了修层级，把某些面板的根画布改成了叠加层；飘字还挂在相机层的 UI 根下，于是在这些面板上被整块盖住。给飘字自己加画布、把层级设到 31000，反而在所有页面都看不见了。
- 查法：别靠点一下再截图（飘字一秒就没，截图要一两秒）。往游戏里注入一段用游戏计时器连续 15 秒、每 0.5 秒飘一句的脚本，同一段在主界面和出问题的页面各跑一次再截图，结论一眼就清楚。日志里先确认「处理函数跑了、文字算对了」，把问题缩到显示层。
- 修法：建一块单独的叠加层画布（缩放设置照抄原 UI 根，字的大小位置不变），每次飘字后把飘字对象挂过去；第一次飘字时预制体是异步加载的，晚 0.2 秒再挂一次。
- 注入试验脚本时，PowerShell 默认写出的 UTF-8 带 BOM，Lua 加载器会静默失败（注入工具照样回报成功）。用不带 BOM 的写法生成脚本，并在脚本末尾打一行日志确认装上了。

**两个区之间切换后画面换了，底部导航高亮还停在旧按钮上，玩家以为「点不过去」**
- 原因：原版换区要等新场景加载完，由场景回调（案例 A 里是 `MainPanel:ChangeSubPanel`）移动导航高亮。离线版为了快，在两个共用同一张地图的区之间「复用地图、只换内容」，不再加载场景，那个回调永远不来。从别的界面进去走的是完整加载，所以只有「从 A 区点 B 区」这一条路坏。
- 查法：在日志里看同一下点击走的是哪条路径（复用路径和完整加载路径各打一行），再对照截图看内容和高亮是不是一致。玩家说「点不过去」时先分清是内容没换、还是只有高亮没换。
- 修法：凡是绕过原版加载流程的快捷路径，都要把原版回调里做的界面收尾（高亮、当前页签记录）自己补一遍。

**进出某个全屏页面时主界面卡一下**
- 原因：为了避免层级冲突，进全屏页前把底下的地图面板「关掉」；关面板会让面板管理器把主界面舞台重新显示一遍（背景音乐都会切），回来时再从零重建整张地图。原版关全屏页时自己还会做一次资源卸载（约 0.45 秒），两段加起来将近 1 秒。
- 查法：日志时间戳逐行看「关页面 → 资源卸载开始 / 结束 → 地图重新加载 → 地图对象创建」各花了多久，就知道卡在哪。
- 修法：底下的面板只隐藏（`SetActive(false)`）不关，回来时直接显示并重排层级；隐藏失败（面板已不在）再走老路。原版自己的资源卸载别动。

**地图被改成叠加层画布后，C# 层弹出的确认框（按返回键的「确认退出」等）被地图盖住看不见**
- 原因：同上一条飘字问题——叠加层永远盖住相机层。Lua 层的面板能在面板显示钩子里抬层，但 C# 自己弹的对话框不经过 Lua 的面板管理器。
- 对策：凡是把某块大画布改成叠加层，就要列一遍还有哪些弹窗来自 C#（在 Lua 源码里搜不到文案的就是），给它们单独想抬层的办法。

### 分档第二批：开局拉满 / 资源券（2026-10-17，会话 C）（续，原节在 `save-data.md`）

**原版确认框（DialogUtils.ShowTxtDialogCustom）的文字区只有 4~5 行高**
- 一页列 11 行选项，真机只露出前 3 行，其余被裁掉且不能滚。做「翻页选择」：一页放一项（▶ 当前项 + 第 n/N 项 + 剩余张数），「换下一项」翻页，最后一页放「暂不兑换」。
- 对话框按钮按下后不会自己关：`PopManager:GetTopPopLayout()` 核对 `resName == 'Dialog_Confirm_Cancel_UI'` 再 `dispose()`；翻页要延迟 0.3 秒再开下一页（同一帧开会叠）。

### 游戏内读相册 / 自定义图片（案例 A 2026-10-17，tier/custom-media）（续，原节在 `device-emulator.md`）

**Unity VideoPlayer 在安卓读本地文件：给绝对路径，不要 `file://`**
- 症状：`vp.url = 'file://' .. persistentDataPath .. '/x.mp4'`，画面全黑，logcat `AndroidVideoMedia: Error opening extractor: -10002`。读安装包里 streamingAssets 的视频（jar: 地址）没这个问题，所以样例里的写法搬过来就错了。
- 修法：`vp.url = '/storage/emulated/0/Android/data/<包名>/files/...'`。
- 做动态卡面（用 mp4 代替静态卡面，2026-10-15）：先注入探针试一下 Lua 绑定层。枚举要传名字，传数字不行；设了 url 后，source 会自动变成 URL。图片加载回调只是把贴图赋给控件，所以 RenderTexture 可以直接顶替 Texture2D。视频静音、循环播放；方形视频铺进竖长卡框时，左右会裁掉一些。确认在播的办法：连截两帧，看卡面区域有没有像素变化（实测约 6%），而不是定格。

### 零散条目

**A stripped background makes a page see-through and taps fall through (2026-10-19)**
- Symptom: after picking an outing scene for a character, re-entering that character's page showed the city map and main-screen buttons through it; taps went to the map, the game switched characters while the old story panel stayed on top, and a later unlock froze on a nil error.
- Cause: 5 scene backgrounds (reptXxx → reptResNameInfo → reptAssetBundlePath) were in chapter folders the release build strips.
- Fix: whitelist them like the dynamic card faces (`scene_bundles.json`). Also make the offline reply robust: before delivering an unlock reply, add any missing per-character dictionary the client will read, built from the save.

**A late event flips a page's state while a sub-view is open; back then closes the page half-way (2026-10-19)**
- Symptom: after changing a character's outing scene and pressing back, entering any character page showed nothing (map visible, pink petals, every tap "Button On Click empty").
- Cause: tapping the character fires an interaction event a moment later that sets the page state to "in dialog" even while the outing view is open. Back in that state takes the "close the whole page" branch, which SetActive(false)s the panel and leaves the sub-view open; the panel manager later "shows" it without re-activating the GameObject.
- Fix: on back, if the sub-view is open, treat it as the sub-view state. On every open, re-activate the panel, close leftover sub-views and reset the state. Reproduce such timing bugs by forcing the state with injected Lua instead of chasing taps.

**A story effect parented to a UI panel loads but never shows (2026-10-19)**
- Symptom: rain popped onto the main screen through the game's own EffectManager; logs said loaded and active, the screen showed nothing.
- Cause: story effects sit on the Default layer with sorting order 0. The main UI is drawn by a ScreenSpace-Camera canvas whose camera only renders the UI layer, and order 0 is under the canvas order.
- Fix: give the effect a sorting order above the panel's canvas (the story itself used 15) and, once it has loaded, set the layer of every child to the panel's layer. Inspect with injected Lua: layer, parent, lossyScale, renderer sortingOrder, canvas renderMode/camera.

**List cells pick icons by a type whitelist, so a valid item shows blank (2026-10-19, 案例 B)**
- Symptom: a shop cell shows the right name but no icon. The cell only looks up the item image for one type and uses `capital_icon_60_<type>` for everything else; the item's type has no such image.
- Fix: check the cell renderer's branches. Report a display-only type that the renderer handles, and grant by the real type on purchase. Also make the "持有数量" (held count) query read the ledger that the real type is stored in.

## 案例 C 侦察（2026-10-21）

**Chinese text broke lines early at ASCII spaces (Unity `Text`)** (2026-10-21)
- Symptom: "这是一个由 XX 无偿制作……" wrapped right after "由", leaving half a line empty; "1. 本版本……" wrapped after "1.".
- Fix: no ASCII spaces inside Chinese body text in Unity UI.
- Hit again 2026-10-22 in new mail text, item descriptions and dialogs written the next day ("补到 9999" broke after "补到"; "· 资源" left the bullet alone on a line). Check every new user-facing string before building, not after the screenshot: strip spaces next to non-ASCII characters inside string literals on the lines you added.

**The second copy of a splash logo was inside the story CG** (2026-10-21)
- Symptom: engine splash and logo video removed, yet the developer's logo showed up again when a new player tapped "start".
- Cause: the opening CG `start.mp4` begins with five seconds of the same logo.
- Fix: sample frames from every video in the package before calling the splash work done; trim the head with a stream copy at the CG's first keyframe.

**Item description box in the stock backpack panel shows only two lines** (2026-10-22, 案例 A)
- Symptom: a long `sDec` for new voucher items was cut off mid-sentence in 物品信息.
- Fix: keep `sDec` to about 34 CJK characters; put the full explanation in the confirm dialog that opens on 使用.

**A queued prompt that cannot show blocks every later dialog** (2026-10-22, 案例 A)
- Symptom: tapping a character many times played the mouth animation with no dialog box; all the dialogs and voices came out together after returning to the city map.
- Cause: the stock prompt queue (`GamePromptMgr`) sorts by type number, and the touch dialog (180) sits behind rewards, unlock and clap-face prompts. Such a prompt cannot display on the character page, or `DelayShow` returns without `ClearCurPrompt`, so `m_curPrompt` stays set and every new dialog only queues. A panel closing on the main screen finally drains the queue.
- Fix: before a talk dialog, if the current prompt is not a dialog and none of the panels it waits for (`curShowPanelList`) is open, move it to the back of the queue, then show the dialog directly with `DelayShow`. Reproduce by planting a fake `m_curPrompt` of type 50.

**A confirm box with no nested canvas stays under an 8000 overlay page** (2026-10-22, 案例 A)
- Symptom: tapping 「可解锁」 in a character's secrets list showed nothing. A later tap could unlock and spend items, because the invisible box still caught clicks. The box appeared on the main screen after leaving.
- Fix: while the overlay page is open, switch the `PopList` root canvas itself to overlay mode and set it between the page and the box's own lifted canvases (8900 here). If it is above them, the blur mask swallows the button clicks. Restore its mode and order when the page closes.

## 终版客户端可能只剩"告示"一种邮件界面（案例 C，2026-10-25）
- 现象：服务器发的邮件存档里有、客户端 mailbox 里也有（探针数到了），界面显示"暂无信息"。
- 根因：终版主界面的入口打开的是 UIBulletin，只列 mailType 5（告示）；系统信（mailType 1）的 UIMailBox 已经没有入口。
- 做法：发信模板选 mailType 5、带 {title}/{content} 的那个；旧存档里的模板号在下发时映射。验邮件一定要在真机界面上看到，不能只看存档。

## 游戏主题把 AlertDialog 按钮染成白字（案例 D，2026-10-29）
- 现象：自己加的对话框底部按钮看不见，uiautomator 显示按钮在。
- 做法：每个 AlertDialog `show()` 之后对 `getButton(...)` 设文字颜色。用 `uiautomator dump` 找控件坐标，别靠猜。

## 弹层被重排压到下面：监视要覆盖所有弹窗树（案例 A 2026-11-05）
- 现象：角色页和当天事件的对白同一帧弹出，对白被面板管理器重排回低层级，压在角色页下面，看不见也挡不住点击；玩家点屏幕全点到下层，退出后对白才弹到地图上。
- 原因：已有的"抬层级"监视循环只看了一棵弹窗树，这条对白挂在另一棵（Stage 下的）弹窗树里。
- 做法：每 0.3 秒巡检所有弹窗树，掉下去就重新抬上来；同一事件的重复对白丢掉；整页关闭前先清掉排队的对白。验收看日志里点击落在哪个控件上，不只看画面。

## 终版客户端可能比老版少界面（案例 B 2026-11-06）
- 现象：福利加在"签到"上，结果终版福利页左栏只剩一项，签到页根本进不去；R 卡在图鉴里有、卡牌页看不到（老版放 R 卡的那一栏终版去掉了）；设置页某个按钮原来调原生 SDK，离线版点了没反应。
- 做法：功能挂上去之前，先在终版客户端里确认入口还在；入口没了就换位置（这次把调 SDK 的按钮改成"我的生日"），或把内容挂到还在的栏位下。
- 同一批还遇到：客户端"一键删除"成功后自己清空列表、不重新拉取，服务器想留下的邮件在界面上消失、下次进来又冒出来。要改客户端那一处，或在回包里明确告诉它剩下什么。

## 自制界面换成原作素材（案例 A 2026-11-16）
- 现象：离线版自己加的弹窗是纯色方块配纯色按钮，玩家一眼就看出是后加的，说"丑"。
- 做法：
  1. 找图：用 UnityPy 把界面图集里的每个 Sprite 切出来，连同名字、尺寸、九宫格边距（m_Border）拼成带标签的总览图，对着挑。弹窗专用图集一般有名字线索（这次叫 tanchuang，就是"弹窗"）。
  2. 照原作摆：读原作确认框 prefab 的 RectTransform（锚点、位置、大小）和各个 Text 的颜色，照着放纸面、缎带标题、装饰、按钮，字色也用原作的。
  3. 运行时取图：用游戏自己的资源服务按"图集包名 + 图名"异步取 Sprite（和原作代码里同一个调用），取到后设成 Sliced；取不到就保留原来的纯色，界面照样能用。
  4. 改公用画图函数，不逐个改界面：所有自制页面一次换好，以后新加的页面也自动是原作样式。
  5. 九宫格图左右边距之和大于控件宽度时会被等比压扁：按控件宽度挑不同尺寸的按钮图，太窄的换成带小边框的方钮。

## Unity 文字的两个坑（案例 A 2026-11-15/16）
- 刚建好的 Text 当帧量 preferredHeight 会少一行，气泡里最后一行被截掉。做法：下一帧再量一次，重新排一遍。
- 中文里夹一个普通空格，Unity 会把空格后面整串中文当成一个词挪到下一行，平白空出半行。做法：显示前把空格换成不换行空格（U+00A0）。

## Laya 单例界面会被反复 init，复原用常量（案例 B 2026-11-16）
- 现象：钩子按当期角色换了图，下一期没换回来；复原时尺寸成了 0。
- 原因：单例界面每次打开都重新 init，第一次读到的 `width` 是贴图没加载完时的 0。
- 修法：复原用 uiView 里写死的坐标和图集帧尺寸（常量）。另外签到页从主界面自动弹出时走的是 `checkLogin`，不经过 `init`，要另补一处。

## 换完皮以后的几个补充（案例 A / B / G 2026-11-16~17）
- **新加的按钮避开原版按钮。** 案例 A 新加的"壁纸"按钮压住了原版标题旁的"?"，挪到另一侧；切到碎片页签时让给原版的"分解"按钮。加按钮前把这一页所有页签都点一遍看。
- **壁纸、原图这类给玩家存的页面不显示水印**，关掉页面再恢复。
- **换皮后在正式包上再验一次授权码输入。** 测试包不走授权，那块界面根本不出现，换皮把它弄坏了也看不出。
- **玩家只报了一处排版问题，修的时候把同类全修。** 案例 G 长邮件被附件挡住正文只报了一封，实际所有长邮件都会；正文改成可滑动、附件不压正文。
- **开屏公告也用原版背景图**，正文字号放大并可滑动，比纯色底像原作。
- 动态内容（视频卡面）在模拟器上"预览不播"，先查自己判断"出第一帧没有"的那行代码，别急着怀疑编码太激进（案例 A 那次就是判断写错）。
