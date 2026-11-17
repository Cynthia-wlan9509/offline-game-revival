## What

Adds `references/case-h-unity-il2cpp-tcp.md`, an engine case study for a topology the existing cases don't cover.

Cases A/B/C/G all assume the server is dead and the client has to be patched into an offline build. This one is the opposite: **the original server is still running**, the client is untouched, and a small self-written server takes its place on the local network.

## Why it's useful

1. **Original server still alive — capture before you infer.** When you can diff against the real server, most guesswork disappears. It's worth confirming this first, before committing to any reverse-engineering route.
2. **cmd numbers from metadata string order.** `CS_CMD_*` strings in `global-metadata.dat` are ordered by cmd number within a protocol family, so one known cmd yields a whole range by index arithmetic. Pitfall: `CS_MAX_*` also consumes a slot.
3. **Packet length wrong → looks like lag.** A hand-built 13-byte push vs. the real 78-byte one made the client report a generic network error, reconnect, and loop — indistinguishable from a stutter. Diff against a real capture instead of trusting the field table.
4. **Reproduce on the original server before changing your own.** A number that would not refresh was chased through six candidate data sources before testing the original server — which also showed the old value. It was computed client-side. This one step would have replaced the whole hunt.
5. **The delayed-reply advice is situational.** `pitfalls.md` suggests delaying replies 0.15–0.6 s when the UI isn't ready. Here it was strictly worse: 350 ms left a dialog stuck, 120 ms caused intermittent disconnects, 0 was correct. A synchronous reply is right when the real server is also effectively synchronous.
6. **Anchor assertions without a build artifact.** No repack means no byte-offset anchors. They land on data files instead (binary header fields, config table records, save-file consistency), replacing a pile of throwaway scripts with one `verify_data.py`.

## Anonymization

No game name, package name, host, port, key or device id. cmd numbers and protocol field values are given as relative offsets; the encryption algorithm is named but not its key. No APK content is included.

## Files

- `skills/offline-game-revival/references/case-h-unity-il2cpp-tcp.md` (new)
- `skills/offline-game-revival/SKILL.md` (one line in the reference list)
