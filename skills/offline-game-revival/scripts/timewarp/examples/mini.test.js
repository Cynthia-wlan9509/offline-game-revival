// Runnable example:  node mini.test.js          → all pass
//                    BUGGY=1 node mini.test.js  → the harness catches 3 planted bugs (exit code 1)
"use strict";
const tw = require("../timewarp");

const S = tw.create({
    root: __dirname,
    files: ["mini-server.js"],
    globals: { BUGGY: process.env.BUGGY === "1" },
    entry: (g) => g.MiniOffline,
    start: "2026-01-05T08:00:00",                          // local time, a Monday
    quiet: true,
    // what counts as "the player's stuff": audited on every call
    inventory: (api) => { const d = api.db(); return { gold: d.gold, gem: d.gem, stamina: d.stamina }; },
    // what a response CLAIMS it gave
    granted: (r) => ((r && r.data && r.data.reward) || []).map((x) => ({ key: x.type, num: x.num })),
});

// 1. Daily sign-in: 7-day loop, one claim per business day, day 8 starts a new round
for (let d = 1; d <= 7; d++) {
    S.eq(S.ok("checkIn/query").data.day, d, `sign-in day ${d}`);
    S.ok("checkIn/claim");                                  // audit checks the claimed gold/gems really arrived
    S.fails("checkIn/claim");                               // second claim same day must fail and change nothing
    S.nextDay();
}
S.eq(S.ok("checkIn/query").data.day, 1, "day 8 starts a new round");

// 2. Stamina regenerates on the virtual clock and caps
S.ok("stage/fight", {}, { expect: { stamina: -6, gold: 50 } });
S.advance("12m");
S.eq(S.ok("user/info").data.stamina, 56, "+2 stamina after 12 minutes");
S.advance("10h");
S.eq(S.ok("user/info").data.stamina, 60, "stamina caps at 60");

// 3. Progress survives killing the app
S.ok("stage/fight");
S.checkPersist("after a fight");

// 4. Daily shop limit resets at 04:00, not at midnight
S.set("2026-01-20T10:00:00");
for (let i = 0; i < 3; i++) S.ok("shop/buyDaily", {}, { expect: { gold: -100, gem: 5 } });
S.fails("shop/buyDaily");
S.at("23:59"); S.fails("shop/buyDaily");                    // same business day
S.at("04:01"); S.ok("shop/buyDaily");                       // new business day

// 5. Economy over 30 days: one sign-in, spend all stamina, buy the daily gems. When can the player afford the 500-gem gate?
S.simulate({
    days: 30,
    routine: (s) => {
        if (!s.call("checkIn/claim").data.result) return;
        while (s.call("stage/fight").data.result) s.advance("1m");
        for (let i = 0; i < 3; i++) s.call("shop/buyDaily");
    },
    gates: [{ name: "500 gems", test: (inv) => inv.gem >= 500 }],
});

S.report();
