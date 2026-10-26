# Contributing · 参与贡献

[English](#english) · [简体中文](#简体中文)

## English

Thanks for helping keep dead games playable.

### Ways to take part

1. **Report or ask** — open an [issue](https://github.com/Cynthia-wlan9509/offline-game-revival/issues): a step in the skill that misled your agent, a pitfall you hit, a game you are not sure can be saved.
2. **Change something** — fork the repo, make your edit on a branch, and open a pull request. Every PR is reviewed before it is merged; small, focused PRs get merged fastest.
3. **Help maintain it** — after a few merged PRs, say so in an issue. Regular contributors can be invited as collaborators with write access.

### What is most useful

- **New failure-ledger entries** in [`pitfalls.md`](skills/offline-game-revival/references/pitfalls.md): a bold one-line title with the date, then **Symptom → Cause → Fix**. Say how you confirmed the cause.
- **New engine case studies** (Cocos, Unreal, Godot, IL2CPP…) as a new `references/case-*.md`: where the logic layer is, how the scripts are packed or encrypted, which entry points you patched, how you verified on a device.
- Fixes to the scripts in `skills/offline-game-revival/scripts/`, with a short note on how you tested them.

### What must never go into the repo

- Game assets, decompiled or decrypted game code, or anything extracted from an APK.
- Decryption keys, signing keys, keystore passwords, API keys, tokens.
- Player data: saves, account IDs, device serials, license codes, names or messages from player communities.
- Download links to modified builds.

Describe the method instead: "the key is a constant returned by a method named like `ScriptKey()`" is fine; the key itself is not.

### Scope

Only games whose official service has permanently ended. Nothing for live games, cheating, bypassing anti-cheat, or affecting other players. If a rights holder relaunches a game, support the official version.

---

## 简体中文

谢谢你帮忙让停服的游戏还能玩。

### 怎么参与

1. **反馈或提问**：开一个 [Issue](https://github.com/Cynthia-wlan9509/offline-game-revival/issues)。比如 skill 里哪一步把你的 AI 带偏了、你踩到了什么新坑、某款游戏拿不准能不能救。
2. **想改内容**：Fork 仓库，在自己的分支上改，然后提 Pull Request（PR）。每个 PR 都会先审再合并；改动小而集中的合得最快。
3. **想一起维护**：合并过几个 PR 以后，在 Issue 里说一声。常来的贡献者可以被邀请成为协作者，直接有修改权限。

### 最需要什么

- **失败账本新条目**，写进 [`pitfalls.md`](skills/offline-game-revival/references/pitfalls.md)：加粗的一行标题带日期，下面写 **现象 → 原因 → 修法**，再说一句原因是怎么确认的。
- **新引擎案例**（Cocos、Unreal、Godot、IL2CPP……），新建 `references/case-*.md`：逻辑层在哪、脚本怎么打包或加密、补了哪些入口、真机上怎么验收。
- 修 `skills/offline-game-revival/scripts/` 里的脚本，附一句怎么测的。

### 绝对不能放进仓库的

- 游戏资源、反编译或解密出来的游戏代码，以及任何从 APK 里拆出来的东西。
- 解密密钥、签名私钥、keystore 密码、API key、token。
- 玩家数据：存档、账号 ID、设备序列号、授权码、玩家群里的昵称和聊天内容。
- 改版安装包的下载链接。

写方法，不写原物：「密钥是某个叫 `ScriptKey()` 之类的方法返回的常量」可以写，密钥本身不行。

### 范围

只用于官方服务已经永久结束的游戏。不碰仍在运营的游戏，不作弊、不绕反作弊、不影响其他玩家。版权方重新上线的，请支持官方版本。
