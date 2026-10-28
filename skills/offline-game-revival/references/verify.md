# 真机验收闭环

「能点开」只算亮了；存档变了、杀掉重开还在，才算活了。

## 每轮改动的固定流程

1. 记录改动前的 `git diff --stat`
2. 改补丁 / 模块，加断言
3. 跑补丁脚本 —— 必须看到**全部自检通过**
4. 跑构建脚本 —— 确认产物大小 / 时间变化
5. 用与已验证包**相同**的签名方式签名
6. 安装 → force-stop → 启动
7. 抓 logcat + 截图 + 记录操作路径
8. 通过后才更新文档

```powershell
adb install -r --no-incremental <candidate.apk>
adb shell am force-stop <package>
adb shell monkey -p <package> 1
```

## 几个项目共用一台测试设备

用户的 BlueStacks（实例 `Pie64`，Android 9，1600x900，自带 root）和手机由案例 A、B、C 等多个项目共用。规矩：

1. **用前登记、用完销账**：唯一一份登记表是 `<项目根>\docs\<分档目录>\设备占用.md`。开始前把自己写进"谁在用"，
   结束时改回"空"并写清装了/卸了什么包、存档是否还原、应用是否 force-stop。
2. **各走各的 adb 服务端口**：BlueStacks 用 `<项目根>\work\platform-tools\adb.exe -P 5038 -s 127.0.0.1:5555`
   （起服务时带 `ADB_USB=0`，不碰手机）；手机走 5037；另一个项目的环境走 5039。启动模拟器：
   `"C:\Program Files\BlueStacks_nxt\HD-Player.exe" --instance Pie64`，再轮询 `getprop sys.boot_completed`。
3. **只动自己的包**。别的项目的包要卸载/覆盖，先把存档（`/data/data/<pkg>/shared_prefs/*.xml`，BlueStacks 上用 `su -c` 读）
   备份到那个项目的 `logs\`，确认安装包本身在硬盘上还有一份，再动手。
4. **演示包用完就收**：给用户演示的定制包装上后往往一直留在设备上（曾清掉过一个几天前装上的定制样例包）。
   交付时在登记表写清"装着哪些包、各是干什么的"，确认不再需要就卸掉。
5. BlueStacks 上 `run-as` 不可用，读写存档用 `su -c`；`adb install` 拒绝非 `.apk` 后缀（`xxx.apk.1` 这种原包先建一个 `.apk` 硬链接）。

## 日志里必须确认"没有"的东西

- `LuaException`
- `attempt to index`（空对象访问）
- `CRC Mismatch`
- `SIGSEGV` / 主线程冻结
- 资源加载失败

## 验收判据

- **状态真的变了**：数量、进度、可领取 → 已领取
- **重启后仍然正确**：杀进程重启 / 冷启动 / 飞行模式冷启动
- **退出再进不重复、不丢失**
- **返回路径干净**：来回切页面没有残留面板、黑屏、按钮失效
- **联网时也不外发**：平时都在断网下测，从来看不到联网行为。至少验一次"网络全开冷启动"：root 下 iptables 对游戏 uid 丢包（`-m owner --uid-owner <uid> -j DROP`，数据不出去），
  轮询 `/proc/net/tcp*` 按 uid 读 SYN_SENT 的目标、tcpdump 记 53 端口；修完撤掉规则再测一遍，要求零套接字、零 DNS。没 root 的真机上 `adb shell` 也能读 `/proc/net/tcp*`；uid 取自 `ps -o UID -p $(pidof 包名)`，并对一个在联网的应用跑一次对照。正式包检查脚本里加一项"清单不许有 INTERNET"。案例见 `case-b-laya-native.md` 末节。

## 常见"假通过"

| 看起来通过 | 实际 |
|---|---|
| 界面能打开 | 只是面板渲染了，功能没跑 |
| 一次操作成功 | 没覆盖重复进入 / 连续点击 |
| 有网环境下测过 | 没测离线 |
| 没触发崩溃 | 只是没触发，不等于不会崩 |

## 高风险功能要单独加长回归

凡是涉及随机、动画、异步加载的功能，回归步骤要显式写全。例如本地抽卡：

1. 单抽 → 返回主面板
2. 十连 → 动画完整播放
3. 返回后仓库数量正确
4. 重复进入池子不冻结
5. 杀进程重启不崩溃

## 拿"落盘证据"，别只信界面和内存日志

"重启后仍然正确"要有**落盘层**的硬证据，不能只看界面数字或 logcat 里的内存值——两者都可能来自
"启动时重新灌一遍默认数据"，看起来一样，实际没存。

Unity/Android 常见做法是直接读登录态 SharedPreferences（`run-as` 只对 debuggable 包有效）：

```powershell
adb shell run-as <package> ls /data/data/<package>/shared_prefs
adb shell run-as <package> cat /data/data/<package>/shared_prefs/<package>.v2.playerprefs.xml
```

对着键值判断，例如 `OFFLINE_PLAYER_LEVEL_V1=120`、`OFFLINE_MAIN_TASK_ID_V2=10203`、
`OFFLINE_CARD_STARS_V1=220500:2`。这些键既证明"写进去了"，也证明"任务/进度真的推进了"。

同一套证据还能反证"不卡主线"：任务 ID 在 prefs 里前进了，就是结算链路真的走完了。

## 装机状态以现场读数为准，不信口头描述

"我已经把包删了 / 手机上装的是最新版"这类说法（包括自己上一轮写的）不能直接写进交接文档：
本轮实测就是用户说"包已删"，`pm list packages` 读出来**仍装着**，而且装的是实验配置那一版。

```powershell
adb shell pm path <package>
adb shell dumpsys package <package> | Select-String "versionName|lastUpdateTime"
adb shell run-as <package> ls /data/data/<package>/shared_prefs
```

三件事都要现场读：**包装没装 / 装的是哪个时间点的包 / 存档是什么状态**。读不出来就当"未知"，
不要用推测填空；交接文档里的每一个"当前状态"都应该是某条命令的输出。

## 把结论边界写清楚

同一个"通过"里，往往混着两种完全不同的结论，报告里必须拆开：

- **不卡主线**：即使评分/条件不达标，流程仍判定通过并推进。（本次案例 A 的 2-2 剧情战斗要求 5250，
  实测评分仅个位/十位，仍结算并推进到 2-3。）
- **达到阈值**：评分/条件真正满足需求线。

只验证了前者就不要写成"战斗已通过"——写成"结算链路通畅 + 低分不卡主线，达标路径未验证"。
