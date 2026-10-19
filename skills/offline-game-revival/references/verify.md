# 真机验收闭环

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
