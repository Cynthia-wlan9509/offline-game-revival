# 时间快进测试：东西到底有没有正常给

本地假服务器最容易藏的 bug 都和时间有关，而且真机上很难测：
签到第 2 天领不了、每日限购不重置（或者在午夜而不是 4 点重置）、体力回复算错、离线挂机收益翻倍、
回包里写着"获得 50 钻石"但存档没加、杀进程后进度回退……在真机上等一天测一次不现实，改手机时间又会被很多游戏识破。

做法：把假服务器的源码放进 Node 的沙箱里，**把时钟换成虚拟时钟**，然后在一秒钟内跑完一个月。

工具：`scripts/timewarp/timewarp.js`（Node ≥ 16，零依赖），可运行示例 `scripts/timewarp/examples/`。

## 1. 接上你的假服务器

前提只有一个：假服务器是一组能在浏览器环境里执行的脚本，暴露一个"处理请求"的入口（多数 JS 引擎游戏都是这样，
Laya / Cocos / Egret / H5 都适用）。不需要改服务器代码去适配测试：沙箱里的 `Date`、`setTimeout`、`setInterval`
本身就是虚拟的，服务器直接调 `Date.now()` 也能被快进。

```js
const tw = require("./timewarp");
const S = tw.create({
    root: __dirname,
    files: ["offline/00_core.js", "offline/20_user.js", "offline/30_daily.js"],   // 和打包时一样的顺序
    entry: (g) => g.window.MyOffline,                    // 服务器挂在全局上的对象
    handle: (api, path, params, method) => api.handle(path, params, method),   // 默认就是这个
    start: "2026-01-05T08:00:00",                        // 虚拟起点（本地时间）
    globals: { Laya: {/* 需要的话放桩 */} },
    quiet: true,
    // 下面两项打开"奖励对账"
    inventory: (api) => ({ gold: api.user().gold, gem: api.user().diamond, stamina: api.user().power }),
    granted: (resp) => (resp.data && resp.data.reward || []).map((x) => ({ key: TYPE_NAME[x.type], num: x.num })),
});
```

服务器自己有时钟钩子（如 `ctx.now`）也可以接上：`onBoot: (api, now) => { api.ctx.now = now; }`。
判断业务成功的规则默认是 `success===1` / `code===0` / `ok===true` 且 `data.result !== false`，不一样就传 `isOk`。

## 2. 写用例

```js
S.ok("checkIn/claim");                     // 期望成功；同时自动对账：回包说给了什么，存档就得真的多了什么
S.fails("checkIn/claim");                  // 期望失败；失败了还改了存档也算错
S.ok("shop/buy", { id: 3 }, { expect: { gold: -100, gem: 5 } });   // 显式断言这次调用的存档变化
S.advance("12m"); S.at("04:01"); S.nextDay(); S.set("2026-02-01T10:00:00");
S.eq(S.ok("user/info").data.stamina, 56, "12 分钟回 2 点体力");
S.checkPersist("打完一关");                // 记下库存 → 重新加载全部代码（存档和时钟保留）→ 比对
S.report();                                // 汇总；有失败时退出码 1，方便 agent / CI 判断
```

每次调用都记在 `S.log` 里（虚拟时间、参数、是否成功、库存变化、回包声称的奖励），出问题时直接翻。

## 3. 一个月的经济曲线和门槛

```js
S.simulate({
    days: 30,
    routine: (s, day) => {                 // 每个虚拟日 08:00 执行一次"正常玩家的一天"
        s.call("checkIn/claim");
        while (s.call("stage/fight").data.result) s.advance("1m");
        s.call("shop/buyDaily");
    },
    gates: [
        { name: "第 5 章 Boss（战力 426）", test: (inv, api) => api.bestTeamPower() >= 426 },
        { name: "攒够十连", test: (inv) => inv.gem >= 1600 },
    ],
});
```

输出每天的库存表，以及每道门槛**第几天**能过；一直过不去的标 `NOT reached`。这就是 `playtest.md` 里"门槛分项记录"的自动化版本：
数值改了以后重跑一次，就知道有没有把玩家卡死，或者把养成一天送满。

## 4. 应该覆盖的时间类用例（清单）

| 类别 | 用例 |
|---|---|
| 每日重置 | 重置点前一分钟 / 后一分钟（多数游戏是 4:00 或 5:00，不是 0:00）；跨月、跨年；连续两天不上线再上线 |
| 签到 | 7 天循环、第 8 天新一轮、断签规则、同一天重复领取 |
| 体力 / 次数回复 | 按间隔回复、到上限停止、超上限（道具加的）不被回复逻辑削掉、离线很久后一次性结算 |
| 计时类 | 派遣/外出/挂机：未到时间领取失败、到点领取、立即完成扣费、领取后重开 |
| 限时 | 活动开/关时间、限时商店、周常（周一刷新）|
| 持久化 | 每类写操作后 `checkPersist()`；重启后计时器继续算、不重置也不翻倍 |
| 奖励对账 | 打开 `inventory` + `granted` 后，所有成功调用自动对账；"回包写了但没加"和"加了但回包没写"都会报 |

## 5. 和真机验收的关系

timewarp 只证明**服务器逻辑**对；客户端是否正确显示、红点是否刷新、引导能不能点通，仍然要真机（`verify.md`）。
推荐顺序：timewarp 全绿 → 打测试包 → 真机按引导点一遍（案例 B 的调试通道、热加载、跟着引导高亮框点击的做法见
`case-b-laya-native.md`）→ 冷启动复验。

Lua 服务器（如案例 A）同理：用独立的 Lua 解释器（或 Python 的 `lupa`）加载服务器脚本，把 `os.time` / `os.clock`
换成可控函数，存档读写换成内存表。用例和清单完全通用。
