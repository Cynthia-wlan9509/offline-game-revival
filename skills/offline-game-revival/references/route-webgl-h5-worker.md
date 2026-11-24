# 引擎路线：Unity WebGL / H5 微端 + 常驻原版 DLL Worker

> 来自一款修仙手游：237 KB 微端 APK + Unity WebGL/H5 + 原 `Hotfix.dll`，主线 `990/990`、雷劫 `9/9`，不改公式通关。

## 适用条件

- APK 仅为几百 KB 的 WebView 壳，游戏本体为 Unity WebGL / H5 前端资源快照（`.wasm` / `.data` / `.unity3d`），通过 HTTP + WebSocket（Realm / Gate）与后端交互；
- 能够合法拿到对应版本的完整前端资源快照以及服务端/客户端共享的战斗与属性计算 DLL（如 `Hotfix.dll`）。

## 核心架构

1. **先 H5 闭环，最后封壳（D2 原则）**：
   - 日常全部开发与验收都在本机 `127.0.0.1:<port>` 的便携 H5 模式下进行，等玩法、平衡与长稳压测全部收官后再封装 Android WebView + 本地服务壳，避免前期白耗打包时间。
2. **本地回环 Python 服务（aiohttp + SQLite）**：
   - 仅绑定 `127.0.0.1`，校验同源 WebSocket Origin 与 CSP `connect-src 'self'`；
   - 前端构建脚本仅用精确 HTML 锚点注入 `local-network.js` 重定向 Realm/Gate WebSocket，原资源快照严格只读；
   - 对 `.wasm`/`.data`/`.unity3d`/图片/音频启用强缓存（`Cache-Control: public, max-age=86400`），HTML/JS/API 保持 `no-store`。
3. **常驻 `.NET` 原版 Worker（零改公式 + 10× 吞吐）**：
   - 直接加载未修改的原版 `Hotfix.dll` 封装为 `player-property-worker` 与 `combat-worker`；
   - **必须做常驻进程模式**（DLL 和配置只加载一次，通过 stdin/stdout 逐行收发请求），严禁每场战斗拉起一次短命 `.NET` 进程（实测常驻模式提速 ~10 倍，且需做 20 份录制输入逐字节一致性验证）；
   - Worker 每次执行完毕**自动清理临时 replay 目录**并缓存 DLL 哈希，防止长跑把磁盘打爆（曾因未清理泄漏近 20 GB）。

## 自动化推进与验收法宝

1. **未实现协议通用兜底 Ack + 频次统计**：
   - 按协议表自动为未实现请求返回类型匹配的带错误码 Ack（带原 `RpcId`），**保证不断线**，同时把客户端真实发出的未实现请求计数写入 `unhandled-seen.json`，按真实频次排优先级补齐。
2. **无头通关机器人（探路轨 / 平衡轨分轨）**：
   - 写 `headless_playtest.py` 从 0 级自动推图、穿装、学技能、渡劫，跑出第一个真实卡点来替代人工拍脑袋选题；
   - **探路轨**遇数值卡点允许临时降难度继续暴露功能/协议缺陷，记入 `difficulty-debt.json`；**平衡轨**用“战力来源拆解表”自上而下算清各养成系统贡献与合理收益倍率，统一还清难度欠账。
3. **固定 Playwright 冒烟脚本**：
   - 启动浏览器前先跑服务与登录预检；工具/参数失败不计业务重试次数；记录真实会话发出的全部请求号并做真实页面内容断言（不拿截图存在或退出码 0 当通过）。
