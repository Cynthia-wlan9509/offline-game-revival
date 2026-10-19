// A deliberately tiny browser-style fake server, used to demonstrate timewarp.js.
// Real ones are hundreds of endpoints; the shape is the same: a global object with handle(path, params, method),
// a save in localStorage, and time read from Date.now().
// Set BUGGY=1 to plant three classic bugs the harness should catch.
(function () {
    var KEY = "MINI_SAVE_V1";
    var BUGGY = !!window.BUGGY;
    var db = JSON.parse(localStorage.getItem(KEY) || "null") || {
        gold: 0, gem: 0, stamina: 60, staminaTs: Date.now(),
        checkIn: { round: 0, day: 0, lastDay: "" }, shop: { day: "", bought: 0 }
    };
    function save() { if (!(BUGGY && db.__noSave)) localStorage.setItem(KEY, JSON.stringify(db)); }

    // "business day" rolls over at 04:00 local, like most games
    function bizDay(t) { var d = new Date(t - 4 * 3600e3); return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate(); }
    var REGEN_MS = 6 * 60e3, CAP = 60;
    function settleStamina() {
        var now = Date.now();
        if (db.stamina >= CAP) { db.staminaTs = now; return; }
        var n = Math.floor((now - db.staminaTs) / REGEN_MS);
        if (n > 0) { db.stamina = Math.min(CAP, db.stamina + n); db.staminaTs += n * REGEN_MS; }
    }
    var CHECKIN = [{ gold: 100 }, { gold: 200 }, { gem: 10 }, { gold: 300 }, { gold: 400 }, { gem: 20 }, { gem: 50 }];
    function give(r) {
        var out = [];
        for (var k in r) { if (!(BUGGY && k === "gem")) db[k] += r[k]; out.push({ type: k, num: r[k] }); }   // bug 1: gems claimed, never added
        return out;
    }
    var R = {
        "user/info": function () { settleStamina(); save(); return { gold: db.gold, gem: db.gem, stamina: db.stamina }; },
        "checkIn/query": function () {
            var today = bizDay(Date.now());
            var day = db.checkIn.lastDay === today ? db.checkIn.day : (db.checkIn.day % 7) + 1;
            return { day: day, claimed: db.checkIn.lastDay === today };
        },
        "checkIn/claim": function () {
            var today = bizDay(Date.now());
            if (db.checkIn.lastDay === today) return { result: false, state: 1001 };
            db.checkIn.day = (db.checkIn.day % 7) + 1; db.checkIn.lastDay = today;
            var reward = give(CHECKIN[db.checkIn.day - 1]); save();
            return { result: true, reward: reward };
        },
        "stage/fight": function (p) {
            settleStamina();
            var cost = 6;
            if (db.stamina < cost) return { result: false, state: 2001 };
            db.stamina -= cost; if (BUGGY) db.__noSave = true;                       // bug 2: forgets to persist after a fight
            var reward = give({ gold: 50 }); save(); db.__noSave = false;
            return { result: true, reward: reward };
        },
        "shop/buyDaily": function () {
            var today = bizDay(Date.now());
            if (!BUGGY && db.shop.day !== today) { db.shop.day = today; db.shop.bought = 0; }   // bug 3: daily limit never resets
            if (db.shop.bought >= 3) return { result: false, state: 3001 };
            if (db.gold < 100) return { result: false, state: 3002 };
            db.gold -= 100; db.shop.bought++;
            var reward = give({ gem: 5 }); save();
            return { result: true, reward: reward };
        }
    };
    window.MiniOffline = {
        db: function () { return db; },
        handle: function (path, params) {
            var f = R[path];
            if (!f) return { success: 0, msg: "no route " + path };
            return { success: 1, data: f(params || {}) };
        }
    };
})();
