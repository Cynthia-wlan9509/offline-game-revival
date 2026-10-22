# 发布与分档：发新包不丢玩家存档

> 来源：案例 A 离线纪念版 2026-10-17 的分档分发设计。只讲技术，不涉及定价和商业规则。

## 1. 覆盖安装保住存档的硬条件

Unity 游戏的存档一般在 `/data/data/<包名>/shared_prefs/<包名>.v2.playerprefs.xml`，卸载就没了。覆盖安装能保住存档，要同时满足：

| 条件 | 做法 |
|---|---|
| 包名不变 | 所有版本、所有档位都用同一个包名。别为某个客户单独改包名，那等于新装一个游戏，存档带不过去 |
| 签名不变 | 发布 keystore 至少备份两处（另一块盘 + 离线介质）。丢了它就再也发不了能覆盖安装的更新 |
| versionCode 不降 | 相同可以覆盖，降了会被系统拒绝 |
| 存档格式只加不改 | 新功能用新键，「键不存在 = 老行为」；旧键不改名、不改含义。项目里如果有「存档纪元」一类会清档的开关，发布后永远别动 |
| 防旧包写坏新档 | 加一个存档版本号键；包里写死自己认识的最高版本，读到更高的就拒绝进入并提示更新 |
| 已分发的包可重现 | 出包前提交源码并打标签，记下哈希。发现分发包是用未提交的工作区打的，立刻补提交、核对源文件修改时间早于出包时间 |

## 2. 分档：一种包 + 授权码里的功能位

不要按档位各出一个包：维护量翻倍，玩家在档位之间换包时，存档里引用的内容在低档包里没有配置，会报空值。

做法：
- 授权码（设备码绑定、私钥签名）的载荷里带一个**功能位**字段，档位只是功能位的预设组合。
- 授权码**原文**存进存档，每次启动重新验签再算功能位。不要只存一个算好的数字，那样改存档就能升档。
- 升档：在游戏里输入一个新授权码，不用重装。旧格式的授权码继续有效，映射成最低档，已分发的玩家不受影响。
- 代价要讲清楚：低档玩家的包里其实也有高档内容。如果脚本层能被解包，这些内容挡不住铁了心的人。所以要配合按份水印，并且只在信得过的范围分发。

## 3. 活动开期

- 日常活动：内置日历，从一个固定锚点按真实日期轮换，不用存档，所有人同一天看到同一个。
- 限定活动：签名兑换码，载荷是「活动 ID + 开始日期 + 天数 + 范围（全体 / 某设备）」，群里发码就等于开活动。私钥只在开发者本机，别人伪造不了。
- 领奖记录按「活动 ID + 开期」分开存，防止拨系统时间重复领。

## 4. 每个玩家不同的内容（头像、卡面）放进游戏里做

- 不为每个客户打一个包。在底座配置里**一次性预留空槽位**（头像位、卡位，带齐配套的子表行），游戏内编辑器只往槽里填内容。
- 图片和视频从手机相册导入，复制到游戏自己的目录，存档里只记文件名。
- 先查原包有没有现成的权限封装，往往不用改 Java 层就能弹相册授权框（见 `pitfalls.md`）。

## 5. 存档迁移（换手机）

游戏内导出存档文件，带上来源设备码和校验 → 开发者用工具重签到新设备码 → 新设备导入，只接受签给本机的文件，导入前自动备份。离线做不到吊销旧设备，这是已知上限。

实现要点（两个案例都做过：Unity/PlayerPrefs 一次、Laya conch/localStorage 一次）：
- **签名复用授权码那把私钥**，消息加域前缀（如 `"<MAGIC>|" + SUM + "|" + 目标设备码`），防止授权码签名被挪来当存档签名。导出文件不带签名，所以玩家自己备份的文件也要经开发者重签才能导回去——这正是防篡改的那道门。
- 导出排除绑设备的键（授权码、本机种子），导入时也跳过它们、保留新机原值。
- 导入顺序：**先备份当前存档到用户可见的文件夹，写不出备份就整个取消** → 冻结离线服务端的内存存档（否则定时落盘会把刚导入的数据盖掉）→ 清旧键写新键 → 提示后自动退出进程，重开时所有缓存从新存档读。
- 文件放「下载」：targetSdk ≤ 28 的老包仍是旧式存储，补 `READ/WRITE_EXTERNAL_STORAGE` 清单权限 + 运行时 `requestPermissions`（只在点导出 / 导入时弹）。查找文件要递归两层子目录，覆盖聊天软件保存到「下载」下的子文件夹。
- 开发者工具配 `inspect`（看导出时间、键数、昵称、进度）和 `migrate`，台账单独一张表；签之前先 inspect 一眼，可疑就不签。
- 新机要先有授权码进过一次游戏才看得到"导入"按钮（入口挂在授权后的公告 / 设置页），在玩家说明里写清顺序。

## 6. 并行开发的分工

- 先写接口规格（全局函数名、功能位名、存档键），每个会话在自己的 git worktree 和分支里干活，只改自己负责的文件。
- 调用方要对「依赖的函数还不存在」做兜底，各分支才能独立构建、独立验证。
- 真机一次只给一个会话用，设备占用写在一张登记表里。

## Per-chapter issuing plus free module checkboxes (LIC3, 2026-10-17)

- Payload: `LIC3|group|device|expires|open-up-to-chapter|module-bits-hex|activity-list|serial`. The chapter is a number, not a bit. Parse module bits one hex digit at a time, never through a float, so new modules can take higher bits without hitting the 53-bit limit. Activity list: `*` = all, or a comma-separated list of IDs.
- Old codes must map into the new model (e.g. LIC1 → chapter 2; LIC2 with the MAIN bit → the highest chapter at the time it was issued). Keep the old APIs (`Allows('MAIN')` = cap ≥ old top) so unchanged callers keep working.
- The cap only blocks moving forward; never take away a chapter the save has already entered.
- The issuing tool appends every code to a ledger CSV outside git, and can look up history by device.
- Lua 5.3: `tostring(99901.0)` gives `"99901.0"`. Normalize numeric IDs with `string.format('%d', n)` before any set lookup.
- Pacing: the user chose original pacing for every tier, with "max out" as the paid shortcut. Don't propose global speed-ups; check that max-out clears every level gate.
