# timewarp — time-travel tests for offline fake servers

Zero-dependency Node harness. Loads your fake-server files into a browser-like sandbox with a **virtual clock**, then:

- `advance("1d 6h")`, `at("12:30")`, `nextDay()` — fast-forward; sandbox `Date`, `setTimeout`, `setInterval` all follow
- `restart()` / `checkPersist()` — reload the code with the same save, like killing and reopening the app
- **reward audit** — every call diffs the player's inventory and compares it with what the response *claims* it gave
- `simulate({ days: 30, routine, gates })` — play a month in a second, print the economy curve, report when each gate becomes reachable

```bash
node examples/mini.test.js            # 51 passed
BUGGY=1 node examples/mini.test.js    # catches 3 planted bugs: phantom reward, unsaved fight, daily limit never resets
```

Full guide (Chinese): [`../../references/timewarp.md`](../../references/timewarp.md).
