# 从玩家截图 / 录屏里抢救游戏数据

服务器一关，卡牌数值、商店价格、卡池概率、关卡奖励、活动规则这些服务端配置就永远没了。
手机里只剩资源和本地设置（实测过一份渠道服的完整手机备份：没有任何服务端数据）。
**玩家当年的截图和录屏是唯一的原始证据**，比任何猜测都可靠。

难点是量：老玩家一份资料动辄十几 GB，直接丢给多模态大模型看既贵又慢，纯文本模型（如 DeepSeek）又看不了视频。
做法是先在本地把它压成几百 KB 的文字，再交给便宜的文本模型做结构化，最后只拿结构化结果和少量存疑原图来校准数值。

```
十几 GB 截图/录屏 ──scripts/harvest.py（本地，0 token）──► 几千张不重复画面 + OCR 文字（按界面分类）
          ──文本模型（DeepSeek 等，便宜）──► 结构化 JSON/CSV
          ──主 agent──► 对上游戏配置 id，写进服务端数值表；只对矛盾条目回看原图
```

## 1. 本地提取：`scripts/harvest.py`

```bash
pip install opencv-python-headless numpy pillow rapidocr_onnxruntime   # 或新版：pip install rapidocr onnxruntime
python scripts/harvest.py <玩家资料目录> <输出目录> --limit 50          # 先试跑 50 个文件看效果
python scripts/harvest.py <玩家资料目录> <输出目录>                     # 全量；可随时中断，重跑自动续上
```

| 环节 | 做法 | 参数 |
|---|---|---|
| 视频抽帧 | 每 0.25 秒采样；画面相对上一张保留帧变化够大（`--scene`）**且已停稳**（相对上一采样变化 < `--stable`）才保留，跳过转场动画和滚动中的模糊帧；一直在变（长列表滚动）时每 `--max-gap` 秒兜底取一帧 | 0.12 / 0.02 / 4 |
| 去重 | 256 位差值哈希，裁掉顶部 6% 状态栏（时钟、电量会让同一界面哈希不同），汉明距离 ≤ `--hash-dist` 视为同一画面；截图和录屏帧之间也去重 | 24 |
| OCR | RapidOCR（ONNX，CPU 可跑，中英日韩），输出文字、外框、置信度，按阅读顺序拼行 | |
| 分类 | 关键词打分（商店、卡池概率、卡牌详情、签到、任务成就、关卡、活动、邮件、背包、剧情、设置），`--rules` 传 JSON 可按游戏改 | |

实测：同一界面"截图 vs 录屏帧"的哈希距离 2~12，不同界面 ≥60，阈值 24 有足够余量。
一段"6 个界面 + 一次长滚动 + 结尾回到首页"的模拟录屏，抽出 7 帧、去掉 1 帧重复，与人工判断一致。CPU 上 OCR 约 1 秒/张。

输出：`frames/`（录屏关键帧）、`ocr.jsonl`（全部结果）、`index.csv`（速查）、`by_category/*.md`（人工翻阅）、
`for_llm/*.txt`（已切成每块约 1.2 万字，直接粘给文本模型）、`report.txt`（统计）。

注意：
- 玩家截图里常有聊天记录、手机号、实名信息。OCR 全程本地；发给外部模型前先翻一遍 `for_llm/`，必要时删掉无关分类（如 `other`）。
- HEIC（iPhone 原图）OpenCV 读不了，先批量转 JPG。iPhone 录屏是 HEVC 编码的 .mov，多数 OpenCV 版本能直接读；个别打不开时日志会提示，用 ffmpeg 转成 H.264 MP4 再跑。
- 分类只是粗分，错分没关系：下一步模型按内容重新判断。

## 2. 文本模型结构化

**有 API key：用脚本批量跑**（`scripts/llm_structure.py`，只用标准库，可中断续跑，已完成的块不重复花钱）：

```bash
# PowerShell: $env:DEEPSEEK_API_KEY="sk-..."    bash: export DEEPSEEK_API_KEY=sk-...
python scripts/llm_structure.py <harvest输出目录> --dry-run                    # 看要发哪些块、约多少 token
python scripts/llm_structure.py <harvest输出目录> --only shop,gacha --limit 2   # 先试 2 块，人工看质量
python scripts/llm_structure.py <harvest输出目录>                               # 全量（默认跳过 other 分类）
```

`--provider deepseek|openai|qwen|kimi|ollama`（或 `--base-url --model --key-env` 自定任何 OpenAI 兼容接口；`ollama` 完全本地，不出网）。
输出 `structured/merged.json`（同一条目数值冲突时两条都留，标 `conflict`）和每类一张 `structured/<类>.csv`。

**没有 API、只有聊天网页**：把 `for_llm/<分类>_NN.txt` 逐块贴进去，先贴下面的提示词。提示词（脚本内置的也是这一份）：

```text
你在帮忙还原一款已停服手游的服务端数值。下面是玩家截图经 OCR 得到的文字，每段以 "### IMAGE: 文件名" 开头，
OCR 可能有错字（0/O、1/l、8/B、5/S 混淆，"钻石"识别成"钻右"等），行顺序大致是从上到下、从左到右。

任务：
1. 判断每张图是什么界面（商店 / 卡池概率公示 / 卡牌详情 / 关卡 / 奖励列表 / 活动规则 / 其他）。
2. 只提取界面上明确写出的数值，按下面的 JSON 格式输出；看不清或推断出来的值不要填，放进 "uncertain"。
3. 每条记录带上来源图片文件名，方便回查原图。
4. 同一内容在多张图里出现时合并，数值冲突的两条都保留并标注 "conflict": true。

输出 JSON（只输出 JSON）：
{
  "shop":        [{"tab": "", "item": "", "price": 0, "currency": "", "limit": "", "image": ""}],
  "gacha":       [{"pool": "", "item_or_rarity": "", "rate": "", "pity": "", "image": ""}],
  "cards":       [{"name": "", "rarity": "", "level": 0, "stars": 0, "stats": {"属性名": 0}, "upgrade_cost": "", "image": ""}],
  "stages":      [{"chapter": "", "stage": "", "requirement": "", "cost": "", "rewards": [{"item": "", "num": 0}], "image": ""}],
  "reward_lists":[{"system": "签到/任务/成就/好感/活动…", "tier": "", "rewards": [{"item": "", "num": 0}], "image": ""}],
  "rules":       [{"system": "", "text": "", "image": ""}],
  "uncertain":   [{"what": "", "ocr_text": "", "image": ""}]
}
```

多块的结果合并成一个 JSON（或每类一个文件），再交给主 agent。

## 3. 主 agent 接入

- 物品名 → 游戏配置 id：用客户端翻译表 / 物品表反查（名称完全一致优先，其次去掉空格和全半角差异），对不上的列出来人工确认。
- 写进生成数值表的脚本（不要手改生成物），每个来自截图的值在旁边注释来源图片，自定值标 `[自造]`，可区分"有证据"和"拍脑袋"。
- 只对 `conflict`、`uncertain` 和与现有表差距很大的条目回看原图（`index.csv` 按文件名找）。
- 改完重跑回归测试和图标校验，再按 `playtest.md` 从新档复测节奏。
