// timewarp.js — time-travel test harness for offline fake servers (Node >= 16, zero dependencies).
// Copyright (c) 2026 Cynthia-wlan9509 · MIT License · part of offline-game-revival: https://github.com/Cynthia-wlan9509/offline-game-revival
//
// Loads your fake-server script files into a browser-like sandbox where the clock is virtual, then lets a test
// call endpoints, fast-forward days, restart the "app" (same save, same clock) and audit every response:
// did the reward the response *claims* actually land in the save?
//
//   const tw = require("./timewarp");
//   const S = tw.create({ files: [...], entry: g => g.window.Offline, start: "2026-01-05T04:00:00+08:00", ... });
//   S.call("checkIn/getReward", { day: 1 });      S.advance("1d");      S.at("12:30");      S.restart();
//
// See references/timewarp.md for the full guide and examples/mini.test.js for a runnable example.
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const UNITS = { ms: 1, s: 1e3, m: 6e4, h: 36e5, d: 864e5, w: 6048e5 };

/** "1d 2h 30m" / "90s" / 1500 (ms) → milliseconds */
function parseDuration(x) {
    if (typeof x === "number") return x;
    let total = 0, matched = false;
    String(x).replace(/(-?\d+(?:\.\d+)?)\s*(ms|s|m|h|d|w)/g, (_, n, u) => { total += parseFloat(n) * UNITS[u]; matched = true; });
    if (!matched) throw new Error("bad duration: " + x);
    return Math.round(total);
}

/** A Date constructor whose "now" is virtual. Instances are real Dates, so every Date method keeps working. */
function makeFakeDate(getNow) {
    const RealDate = Date;
    function FakeDate(...args) {
        if (!new.target) return new RealDate(getNow()).toString();
        return args.length ? new RealDate(...args) : new RealDate(getNow());
    }
    FakeDate.prototype = RealDate.prototype;
    FakeDate.now = () => getNow();
    FakeDate.UTC = RealDate.UTC;
    FakeDate.parse = RealDate.parse;
    return FakeDate;
}

function plain(v) { return v === undefined ? undefined : JSON.parse(JSON.stringify(v)); }   // also strips cross-realm prototypes

function diff(before, after) {
    const out = {};
    for (const k of new Set([...Object.keys(before || {}), ...Object.keys(after || {})])) {
        const d = (after[k] || 0) - (before[k] || 0);
        if (d) out[k] = d;
    }
    return out;
}

function fmtTime(ms) {
    const d = new Date(ms), p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/**
 * @param {object} o
 * @param {string[]} o.files            fake-server files, loaded in order into ONE sandbox (paths relative to o.root)
 * @param {string}   [o.root]           base dir for o.files (default: cwd)
 * @param {function} o.entry            (globalObject) => your server API object, e.g. g => g.window.MyOffline
 * @param {function} [o.handle]         (api, path, params, method) => response.  Default: api.handle(path, params, method)
 * @param {function} [o.isOk]           (response) => boolean business success.   Default: success===1 / code===0 / ok===true, and data.result !== false
 * @param {function} [o.inventory]      (api) => { currencyOrItemKey: number }     enables per-call inventory diff + audit
 * @param {function} [o.granted]        (response) => [{ key, num }]               what the response CLAIMS it gave (for the audit)
 * @param {function} [o.onBoot]         (api, setNow) => void   e.g. (api, now) => { api.ctx.now = now } if the server has its own clock hook
 * @param {string|number} [o.start]     initial virtual time (ISO string or ms). Default: next Monday 04:00 local
 * @param {object}   [o.globals]        extra globals for the sandbox (Laya stubs, etc.)
 * @param {boolean}  [o.quiet]          hide sandbox console output
 */
function create(o) {
    const root = o.root || process.cwd();
    const storage = {};                                   // survives restart(): that's the point
    let now = o.start != null ? new Date(o.start).getTime() : defaultStart();
    let timers = [], timerSeq = 0;
    let api = null, g = null;
    const log = [];                                       // every call: { t, path, params, ok, delta, claimed, audit }
    // A reward the response promises but the save never receives is a bug the player finds on day three.
    const problems = [];                                  // audit failures + failed expectations
    let pass = 0;

    function defaultStart() {
        const d = new Date(); d.setHours(4, 0, 0, 0);
        d.setDate(d.getDate() + ((8 - d.getDay()) % 7 || 7));
        return d.getTime();
    }
    const getNow = () => now;

    function boot() {
        timers = [];
        const sb = Object.assign({
            console: o.quiet ? { log() { }, warn() { }, error() { }, info() { } } : console,
            Date: makeFakeDate(getNow),
            setTimeout: (fn, ms, ...a) => addTimer(fn, ms, a, 0),
            setInterval: (fn, ms, ...a) => addTimer(fn, ms, a, Math.max(1, ms | 0)),
            clearTimeout: clearTimer, clearInterval: clearTimer,
            localStorage: {
                getItem: (k) => (k in storage ? storage[k] : null),
                setItem: (k, v) => { storage[k] = String(v); },
                removeItem: (k) => { delete storage[k]; },
                clear: () => { for (const k of Object.keys(storage)) delete storage[k]; },
                key: (i) => Object.keys(storage)[i] ?? null,
                get length() { return Object.keys(storage).length; },
            },
        }, o.globals || {});
        sb.window = sb; sb.self = sb; sb.globalThis = sb;
        vm.createContext(sb);
        for (const f of o.files) {
            const p = path.resolve(root, f);
            vm.runInContext(fs.readFileSync(p, "utf8"), sb, { filename: p });
        }
        g = sb;
        api = o.entry(sb);
        if (!api) throw new Error("entry() returned nothing — check o.entry and that the files define it");
        if (o.onBoot) o.onBoot(api, getNow);
        return api;
    }

    function addTimer(fn, ms, args, every) {
        const id = ++timerSeq;
        timers.push({ id, at: now + Math.max(0, ms | 0), fn, args, every });
        return id;
    }
    function clearTimer(id) { timers = timers.filter((t) => t.id !== id); }

    /** Move the virtual clock forward, firing any sandbox timers that fall due on the way. */
    function advance(d) {
        const target = now + parseDuration(d);
        for (; ;) {
            timers.sort((a, b) => a.at - b.at || a.id - b.id);
            const t = timers[0];
            if (!t || t.at > target) break;
            now = t.at;
            if (t.every) t.at += t.every; else timers.shift();
            t.fn(...t.args);
        }
        now = target;
        return S;
    }
    /** Jump to the next local occurrence of "HH:MM" (today if still ahead, else tomorrow). */
    function at(hhmm) {
        const [h, m] = String(hhmm).split(":").map(Number);
        const d = new Date(now); d.setHours(h, m || 0, 0, 0);
        if (d.getTime() <= now) d.setDate(d.getDate() + 1);
        return advance(d.getTime() - now);
    }
    /** Next calendar day at the given local hour (default 04:00 — after most daily resets). */
    function nextDay(hour = 4) {
        const d = new Date(now); d.setDate(d.getDate() + 1); d.setHours(hour, 0, 0, 0);
        return advance(d.getTime() - now);
    }
    function set(when) { now = new Date(when).getTime(); return S; }

    const defaultIsOk = (r) => {
        if (!r || typeof r !== "object") return false;
        const top = ("success" in r) ? r.success === 1 || r.success === true
            : ("code" in r) ? r.code === 0 || r.code === 200
                : ("ok" in r) ? !!r.ok : true;
        const d = r.data;
        return top && !(d && typeof d === "object" && !Array.isArray(d) && d.result === false);
    };
    const isOk = o.isOk || defaultIsOk;
    const inv = () => (o.inventory ? plain(o.inventory(api)) : null);

    /**
     * Call an endpoint. opts: { method, expect: { key: delta }, allowFail, noAudit }
     * Records inventory delta; audits claimed rewards vs. actual delta.
     */
    function call(p, params, opts) {
        opts = opts || {};
        const before = inv();
        let r, threw = null;
        try { r = plain((o.handle || ((a, pp, q, m) => a.handle(pp, q, m)))(api, p, params || {}, opts.method || "GET")); }
        catch (e) { threw = e; }
        const after = inv();
        const delta = before ? diff(before, after) : null;
        const entry = { t: now, path: p, params, ok: !threw && isOk(r), delta, response: r };
        log.push(entry);
        if (threw) { problem(`${p} threw: ${threw && threw.stack || threw}`); return r; }

        if (delta && o.granted && !opts.noAudit && entry.ok) {
            const claimed = {};
            for (const x of o.granted(r) || []) claimed[x.key] = (claimed[x.key] || 0) + x.num;
            entry.claimed = claimed;
            for (const k of Object.keys(claimed)) {
                if (opts.expect && k in opts.expect) continue;     // an explicit expectation (e.g. reward minus a cost in the same currency) wins
                if ((delta[k] || 0) !== claimed[k]) problem(`AUDIT ${p}: response says +${claimed[k]} ${k}, save changed by ${delta[k] || 0}`);
            }
        }
        if (opts.expect && delta) for (const [k, v] of Object.entries(opts.expect)) {
            if ((delta[k] || 0) !== v) problem(`${p}: expected ${k} ${v >= 0 ? "+" : ""}${v}, got ${delta[k] || 0}`); else pass++;
        }
        return r;
    }
    function ok(p, params, opts) {
        const r = call(p, params, opts);
        const e = log[log.length - 1];
        if (e.ok) pass++; else problem(`${p} should succeed: ${JSON.stringify(r).slice(0, 240)}`);
        return r;
    }
    function fails(p, params, opts) {
        const r = call(p, params, Object.assign({ noAudit: true }, opts));
        const e = log[log.length - 1];
        if (!e.ok) pass++; else problem(`${p} should fail but succeeded: ${JSON.stringify(r).slice(0, 240)}`);
        if (e.delta && Object.keys(e.delta).length) problem(`${p} failed but still changed the save: ${JSON.stringify(e.delta)}`);
        return r;
    }

    /** Re-load every file into a fresh sandbox. Storage and clock survive — like killing and reopening the app. */
    function restart() { boot(); return S; }
    /** Snapshot inventory, restart, compare. Catches "it worked until I reopened the app". */
    function checkPersist(label) {
        const a = inv(); restart(); const b = inv();
        const d = diff(a || {}, b || {});
        if (Object.keys(d).length) problem(`PERSIST ${label || ""}: after restart inventory changed by ${JSON.stringify(d)}`); else pass++;
        return S;
    }
    function check(cond, msg) { if (cond) pass++; else problem(msg); return !!cond; }
    function eq(a, b, msg) { return check(JSON.stringify(plain(a)) === JSON.stringify(plain(b)), `${msg}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); }
    function problem(msg) { problems.push(`[${fmtTime(now)}] ${msg}`); }

    /**
     * Play N in-game days with a routine and watch the economy.
     * routine(S, dayIndex) runs once per day (clock starts at o.dayStart, default 08:00).
     * gates: [{ name, test: (inventory, api) => bool }] — reports the first day each becomes reachable.
     * Returns { rows: [{ day, inventory }], gates: { name: day|null } }.
     */
    function simulate({ days, routine, gates = [], dayStart = 8, print = true }) {
        const rows = [], reached = {};
        for (let d = 1; d <= days; d++) {
            const t = new Date(now); t.setHours(dayStart, 0, 0, 0); if (t.getTime() < now) t.setDate(t.getDate() + 1);
            advance(t.getTime() - now);
            routine(S, d);
            const iv = inv() || {};
            rows.push({ day: d, inventory: iv });
            for (const gt of gates) if (!(gt.name in reached) && gt.test(iv, api)) reached[gt.name] = d;
            nextDay(0);
        }
        for (const gt of gates) if (!(gt.name in reached)) reached[gt.name] = null;
        if (print) printCurve(rows, reached);
        return { rows, gates: reached };
    }
    function printCurve(rows, reached) {
        const keys = [...new Set(rows.flatMap((r) => Object.keys(r.inventory)))];
        const pick = rows.filter((r, i) => i < 7 || r.day % 7 === 0 || i === rows.length - 1);
        console.log("\nday  " + keys.map((k) => k.padStart(10)).join(""));
        for (const r of pick) console.log(String(r.day).padEnd(5) + keys.map((k) => String(r.inventory[k] ?? "").padStart(10)).join(""));
        for (const [n, d] of Object.entries(reached)) console.log(`gate "${n}": ${d ? "day " + d : "NOT reached"}`);
    }

    /** Print summary; exit code 1 when anything failed (for CI / agents). */
    function report({ exit = true } = {}) {
        for (const p of problems) console.log("  FAIL " + p);
        console.log(`\n${pass} passed, ${problems.length} failed  (virtual time now ${fmtTime(now)})`);
        if (exit && problems.length) process.exitCode = 1;
        return { pass, fail: problems.length, problems: problems.slice() };
    }

    const S = {
        call, ok, fails, advance, at, nextDay, set, restart, checkPersist, check, eq, simulate, report,
        get api() { return api; }, get global() { return g; }, get now() { return now; },
        get storage() { return storage; }, get log() { return log; }, inventory: inv,
        last: () => log[log.length - 1],
    };
    boot();
    return S;
}

module.exports = { create, parseDuration, makeFakeDate };
