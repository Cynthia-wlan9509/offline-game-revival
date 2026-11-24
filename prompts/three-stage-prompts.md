# 三段式开工口令（复制就能用）

给"开工 → 批次推进 → 独立终验"这套流程用的三句话。路径按你放 skill 的位置改：下面写成 `<skill>`，
Claude Code 一般是 `~/.claude/skills/offline-game-revival`，插件安装的话 agent 自己找得到。

把原包放进一个空的工作目录（例如 `D:\新游戏\原版游戏.apk`），在这个目录里开会话，按顺序发。

## 第 1 句：只读侦察（约 10 分钟，出可行性报告）

```text
先读 <skill>/SKILL.md、references/red-lines.md 和 references/kickoff.md。
对当前目录的原版 APK 做「第 0 步只读侦察」：
1. 只读原包，不碰任何模拟器，不连线上接口；
2. 运行 <skill>/scripts/recon_apk.py，再做必要的反编译和清单核查；
3. 输出 work/analysis/STEP0-ASSESSMENT.md，明确回答：本体齐不齐（含 ZIP32 风险）、逻辑层和加密地图、
   战斗在本地算还是服务端算、推荐 references/route-*.md 里的哪一条路线、首要技术关口是什么。
做完停下来等我拍板。
```

## 第 2 句：拍板后一路推到终验

看完报告觉得值得做，把 `<>` 里的几项填好再发；其余是常用默认值，不改也行。
支持 `/goal` 一类"一直做到目标达成"的命令就加在最前面。

```text
按 <skill> 的 references/red-lines.md，用 kickoff.md → autopilot.md → independent-qa.md 三段把当前目录的 APK
做成独立离线纪念版，直到通过独立终验并交付正式 / GM 配对包。

【开局预授权（代替反复请示）】
- 唯一测试设备：<序列号，如 emulator-5558 或 127.0.0.1:16384>；ADB：<adb.exe 路径>
- 严禁触碰：<如 emulator-5556 上的用户正式档 / 其他模拟器>
- 工作区磁盘上限：<如 20 GB>（所在盘剩余 ≥ 30 GB）
- 选定路线：<第 0 步报告确认的那条>
- 工程授权：允许 git init、扁平覆写树、隔离测试包自由热推 / 热加载 / 命令桥 / GM 夹具 / 虚拟时钟、
  对目标测试包的 UID 临时 iptables 断网（测完撤回）；开发期只热推，攒够一批才打包；正式包强制关掉 debuggable、热载、命令桥和全量日志。
- 产品预设：锁死 1:1 原版 UI；原服规则查不到的按"可玩优先"补并标 [重建] 登记；写接口不许默认成功；
  付费统一改本地代金券（1 元 = 100，真扣款 + 发奖 + 涨 VIP，0 真支付、0 联网）；多人玩法做成随战力成长的本地 AI 对手；
  缺图的旧活动、开发中的入口直接关掉。

【推进与验收硬要求】
1. 先建底座（Git、AGENTS.md、交接/设备锁.json、HANDOFF.md、PROGRESS-MATRIX.csv、BUG-LIST.md）和秒级快循环，
   跑通最小闭环（断网冷启 → 登录 → 主城 → 原版战斗打一关 → 账本对上 → 杀进程重启还在）。
2. 按玩家顺序分批推进，严格 30–45 分钟 / 2 轮探针止损，修一个 bug 补一条回归，HANDOFF 覆盖维护 ≤ 120 行。
3. 全部主要系统做完后，换独立会话或子代理按 independent-qa.md 终验：T1–T5 + 清数据重装 + 空热更目录 + 真断网连续冷启两次（核对 PID 变了）
   + 真实看图 + aapt 权限校验，产出配对包和诚实的《交付说明.md》。
只有碰到 red-lines.md 的红线、磁盘熔断清不出空间、共享模拟器服务死锁，或同一外部原因连续 3 次换项都被挡住时，才停下来找我。
```

小技巧：代金券、收益倍率、要不要拟真 AI 聊天、哪些活动跳过这些还没想好，可以先让 agent 用两分钟问你一轮，
把 `交接/KICKOFF-AUTH.md`（模板在 `<skill>/templates/`）填完再发第 2 句。

## 第 3 句：换新会话 / 中途断了接着做（随时可用）

```text
先读 <skill>/references/red-lines.md 和 autopilot.md，再只读本项目的 AGENTS.md、交接/HANDOFF.md、交接/KICKOFF-AUTH.md
和交接/BUG-LIST.md（不要通读历史归档日志）。核对设备锁空闲、快集回归跑通后，从当前断点继续按批次推进。
```

## 装在 Antigravity 里

Antigravity 读工作区 `.agents\plugins\` 下的插件，或全局 `%USERPROFILE%\.gemini\config\plugins\`（一次装好，所有工作区都能用）。
把 `skills/offline-game-revival` 整个文件夹放进去即可；`scripts/guard_hook.py` 也认 Antigravity 的钩子格式，
在插件的 `hooks.json` 里给 `PreToolUse`（matcher `run_command`）挂上 `python -I <skill>/scripts/guard_hook.py`。
