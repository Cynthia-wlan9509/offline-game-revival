# 失败账本（索引）

现象 → 原因 → 修法。下次遇到同样症状直接查这里。读到的坑花一分钟，踩进去的坑花一晚上。

2026-11-19 起按阶段拆成 `pitfalls/` 下的文件，条目原文没改，共约 300 条；2026-11-25 加了 `windows-emulator-build.md`。只打开和眼前症状有关的那一份，别整目录读进来（最大的一份约 65 KB）。

- `pitfalls/recon-unpack.md` — 侦察和解包：先核实停服状态、改头不是加密、微端只有 1/4、同版本号不同包、首启清理删掉推上去的资源、导入后仍说"没下载"、反编译内容和文件名对不上、protobuf 解配置表、镜像 CDN 限流、导出素材。
- `pitfalls/patch-build.md` — 补丁和打包：分配内存失败 / CRC Mismatch、宿主文件和脚本包体积上限、压缩后等于原大小的块、锚点在多个类重复、补丁 ID 抄错版本、转义换行写坏宿主、heredoc / PowerShell 改文件吃反斜杠、模块按文件名拼接互相覆盖、smali 别整段重写、降 minSdk、aapt2 中文路径、拆分包合成。
- `pitfalls/local-server.md` — 本地回包和离线玩法（最大的一份）：进得太早拿到空表、伪造回包毒化请求池、静默 gate、自造数值丢成长维度、服务器推送类玩法、默认回空包、领奖报错、虚拟玩家、等回包计数、只有 setX 没有 onX、os.date 错、红点、等不到的推送和 CDN 视频、客户端错误码表、语音时长取整、AI 聊天（清洗、人设、出戏、轻生话题、记忆游标）。
- `pitfalls/save-data.md` — 存档和物品：重启回到初始、种子数据重置、prefs 先备份、收菜卡顿是读大存档串、拉满只增不减、一次性奖励邮件漏新奖励、种子清掉第二个模型的计数、给老存档补发、未 root 备份存档、物品进错背包分类。
- `pitfalls/ui-assets.md` — 界面和美术：面板盖住 / 被盖住、嵌套 Canvas、快路径不刷新、引导遮罩吞点击、空白对话框、原生弹窗要 dispose、确认框只有 4~5 行、飘字看不见、活动皮肤分层藏、开屏 logo 藏在剧情 CG、Unity 中文空格折行、提示队列卡住后续弹窗、繁转简、自制界面换原作素材、换皮后的补充、Laya 单例反复 init。
- `pitfalls/device-emulator.md` — 设备和工具：Frida 必须排到主线程、注入通道超时、热注入别塞太多、adb install 空错误、input tap 偏、input text 长度和中文、BlueStacks 转屏、Git Bash 改写设备路径、多个 adb server 抢设备、pm clear 清掉资源、量错 UID、scrcpy 没声音、往模拟器推十几 GB（toybox nc）、/sdcard 属主、bluestacks.conf 编码。
- `pitfalls/test-verify.md` — 测试和验收：动手前想副作用会不会自己消失、纯逻辑模块用 lupa 测、开发脚本抬门槛、开发包过了正式包没过、偶现问题先复现、按总数断言的回归、浸泡测试、单测的坑（真时钟、vm 原型、LCG 统计、保底比例、老档模拟、资产账本）。
- `pitfalls/release-distribution.md` — 发包和授权：本机码一样 / BigInt、签名绑定逐项比、载入时算一次的开关、开发覆盖键、按开期过滤、剥资源后入口和面板不同包、活动码"已过期"、派生文件重算、授权入口首启后要能进、去 INTERNET 后仍外发 / 弹 WLAN 框、正式包带了开发包的东西、免费包硬检查和误报。
- `pitfalls/windows-emulator-build.md` — Windows、打包和模拟器（多项目并行时）：雷电 `svc wifi disable` 断 adb、共享 Ld9BoxSVC 死锁、32 位包装不上、adb 中文路径、PowerShell 5.1 把 adb 的 stderr 当错误、管道弄坏二进制流、.vmdk 膨胀和推回存档属主、绝对路径写死、ZIP32 上限、音频被压缩、`7za u` 的工作目录、改 DEX 漏算头校验、MSBuild 残留 obj、热推被旧热更遮住、Debug 首帧 SIGABRT、同步回包重入、原子写档、Lua 5.1 裸 return、PB 负数和默认值、年月表跨年。
- `pitfalls/agent-workflow.md` — 工作流和沟通：文档漂移、产物里的手工补丁丢失、交付包自证基线、交接给第一件必做事、两个会话改同一仓库、方向误判（调不通的注入、依赖探针、侦察工具当交付）、worktree 和目录链接删除、清理产物目录、子代理卡在自己的后台、演示视频没按用户要的剪、用户说停就冻结、动大东西先说为什么、磁盘清理脚本。

## 怎么查

先按症状挑文件；拿不准就全目录搜关键词（日志里的报错原文、函数名、引擎名都行）：

```bash
grep -rn -i "关键词" references/pitfalls/
grep -rn "^## \|^\*\*" references/pitfalls/<文件>.md   # 只看一份文件的条目标题
```

常用关键词：`CRC`、`16 MiB`、`SIGSEGV`、`NullReference`、`主线程`、`Frida`、`junction`、`worktree`、`heredoc`、`BlueStacks`、`adb`、`INTERNET`、`授权码`、`本机码`、`存档`、`种子`、`弹窗`、`Canvas`、`红点`、`微端`、`Laya`、`conch`、`smali`。

新坑写进对应分文件的末尾，格式照抄：`## 标题（案例 X 日期）` + `- 现象 / 原因 / 修法`。案例名用字母，不写真实游戏名。
