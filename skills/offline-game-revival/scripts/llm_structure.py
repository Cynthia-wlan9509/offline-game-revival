#!/usr/bin/env python3
"""把 harvest.py 的 for_llm/ 分块批量交给任意 OpenAI 兼容的文本模型（DeepSeek / OpenAI / 通义 / Kimi / 本地 Ollama…）做结构化，
合并成一份 JSON + 每类一张 CSV。只用标准库，可中断续跑（已完成的分块不会重复花钱）。

Send harvest.py's for_llm/ chunks to any OpenAI-compatible text model, then merge the answers.
Stdlib only, resumable, API key read from an environment variable (never from the command line).

用法 / Usage:
  set DEEPSEEK_API_KEY=sk-...            (PowerShell: $env:DEEPSEEK_API_KEY="sk-...")
  python llm_structure.py <harvest输出目录> --dry-run                 # 先看要发哪些块、大约多少 token
  python llm_structure.py <harvest输出目录> --only shop,gacha --limit 2   # 试 2 块，看质量
  python llm_structure.py <harvest输出目录>                           # 全量（默认跳过 other 分类）

  --provider deepseek|openai|qwen|kimi|ollama   预设 base_url / 模型 / 环境变量名；也可用 --base-url --model --key-env 自定
输出 / Output:
  <dir>/structured/raw/<chunk>.json   每块原始回答
  <dir>/structured/merged.json        合并结果（同一条目数值冲突时两条都留，标 "conflict": true）
  <dir>/structured/<section>.csv      每类一张表，方便人工核对
"""
import argparse, csv, glob, json, os, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

PROVIDERS = {
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat", "DEEPSEEK_API_KEY"),
    "openai":   ("https://api.openai.com/v1", "gpt-4o-mini", "OPENAI_API_KEY"),
    "qwen":     ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "DASHSCOPE_API_KEY"),
    "kimi":     ("https://api.moonshot.cn/v1", "moonshot-v1-32k", "MOONSHOT_API_KEY"),
    "ollama":   ("http://localhost:11434/v1", "qwen2.5:14b", ""),
}

PROMPT = """你在帮忙还原一款已停服手游的服务端数值。下面是玩家截图经 OCR 得到的文字，每段以 "### IMAGE: 文件名" 开头，
OCR 可能有错字（0/O、1/l、8/B、5/S 混淆，形近字错认），行顺序大致是从上到下、从左到右。

任务：
1. 判断每张图是什么界面（商店 / 卡池概率公示 / 卡牌详情 / 关卡 / 奖励列表 / 活动规则 / 其他）。
2. 只提取界面上明确写出的数值，按下面的 JSON 格式输出；看不清或推断出来的值不要填，放进 "uncertain"。
3. 每条记录带上来源图片文件名（image 字段），方便回查原图。
4. 同一内容在多张图里出现时合并，数值冲突的两条都保留并标注 "conflict": true。
5. 与数值无关的图（纯剧情对话、聊天、系统设置）直接忽略。截图里出现的手机号、真实姓名等个人信息一律不要输出。

只输出一个 JSON 对象，格式：
{
  "shop":        [{"tab": "", "item": "", "price": 0, "currency": "", "limit": "", "image": ""}],
  "gacha":       [{"pool": "", "item_or_rarity": "", "rate": "", "pity": "", "image": ""}],
  "cards":       [{"name": "", "rarity": "", "level": 0, "stars": 0, "stats": {"属性名": 0}, "upgrade_cost": "", "image": ""}],
  "stages":      [{"chapter": "", "stage": "", "requirement": "", "cost": "", "rewards": [{"item": "", "num": 0}], "image": ""}],
  "reward_lists":[{"system": "签到/任务/成就/好感/活动…", "tier": "", "rewards": [{"item": "", "num": 0}], "image": ""}],
  "rules":       [{"system": "", "text": "", "image": ""}],
  "uncertain":   [{"what": "", "ocr_text": "", "image": ""}]
}"""

# 合并时判断"同一条目"的字段；其余字段不同即视为冲突
KEYS = {"shop": ("tab", "item", "currency"), "gacha": ("pool", "item_or_rarity"), "cards": ("name", "level", "stars"),
        "stages": ("chapter", "stage"), "reward_lists": ("system", "tier"), "rules": ("system", "text"), "uncertain": ("what", "ocr_text")}


def call(base, model, key, system, user, timeout, retries=5):
    body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    data = json.dumps(body).encode("utf-8")
    for i in range(retries):
        req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=data, method="POST",
                                     headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + key} if key else {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                j = json.loads(r.read().decode("utf-8"))
            return j["choices"][0]["message"]["content"], j.get("usage", {})
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(2 ** i * 3); continue
            raise RuntimeError("HTTP %d: %s" % (e.code, msg))
        except (urllib.error.URLError, TimeoutError) as e:
            if i < retries - 1:
                time.sleep(2 ** i * 3); continue
            raise RuntimeError(str(e))


def parse_json(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    s, e = text.find("{"), text.rfind("}")
    return json.loads(text[s:e + 1])


def merge(raw_dir):
    merged = {k: [] for k in KEYS}
    index = {k: {} for k in KEYS}
    for f in sorted(glob.glob(os.path.join(raw_dir, "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for sec, rows in d.items():
            if sec not in merged or not isinstance(rows, list):
                continue
            for r in rows:
                if not isinstance(r, dict):
                    continue
                r.setdefault("chunk", os.path.basename(f)[:-5])
                k = tuple(json.dumps(r.get(x), ensure_ascii=False) for x in KEYS[sec])
                body = json.dumps({x: v for x, v in r.items() if x not in ("image", "chunk", "conflict")}, ensure_ascii=False, sort_keys=True)
                prev = index[sec].get(k)
                if prev is None:
                    index[sec][k] = [(body, r)]; merged[sec].append(r)
                elif any(b == body for b, _ in prev):
                    for b, pr in prev:                       # 同值：只追加来源图
                        if b == body and r.get("image") and r["image"] not in str(pr.get("image", "")):
                            pr["image"] = (str(pr.get("image", "")) + ";" + r["image"]).strip(";")
                else:
                    r["conflict"] = True
                    for _, pr in prev:
                        pr["conflict"] = True
                    prev.append((body, r)); merged[sec].append(r)
    return merged


def write_csv(path, rows):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([json.dumps(r[c], ensure_ascii=False) if isinstance(r.get(c), (dict, list)) else r.get(c, "") for c in cols])


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", help="harvest.py 的输出目录（含 for_llm/）")
    ap.add_argument("--provider", default="deepseek", choices=sorted(PROVIDERS))
    ap.add_argument("--base-url"); ap.add_argument("--model"); ap.add_argument("--key-env")
    ap.add_argument("--only", help="只处理这些分类，逗号分隔（文件名前缀，如 shop,gacha）")
    ap.add_argument("--skip", default="other", help="跳过这些分类，默认 other")
    ap.add_argument("--limit", type=int, help="最多处理几块（试跑用）")
    ap.add_argument("--workers", type=int, default=2, help="并发数，默认 2")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--prompt", help="自定义提示词文件（替换内置提示词）")
    ap.add_argument("--dry-run", action="store_true", help="只列出要发送的分块和估算 token，不调用模型")
    ap.add_argument("--merge-only", action="store_true", help="不调用模型，只重新合并已有结果")
    a = ap.parse_args()

    base, model, key_env = PROVIDERS[a.provider]
    base, model, key_env = a.base_url or base, a.model or model, a.key_env if a.key_env is not None else key_env
    system = open(a.prompt, encoding="utf-8").read() if a.prompt else PROMPT
    out = os.path.join(a.dir, "structured"); raw = os.path.join(out, "raw")
    os.makedirs(raw, exist_ok=True)

    chunks = sorted(glob.glob(os.path.join(a.dir, "for_llm", "*.txt")))
    cat = lambda p: re.sub(r"_\d+$", "", os.path.basename(p)[:-4])
    only = set(a.only.split(",")) if a.only else None
    skip = set(a.skip.split(",")) if a.skip else set()
    chunks = [c for c in chunks if (only is None or cat(c) in only) and cat(c) not in skip]
    todo = [c for c in chunks if not os.path.exists(os.path.join(raw, os.path.basename(c)[:-4] + ".json"))]
    if a.limit:
        todo = todo[:a.limit]

    if not a.merge_only:
        chars = sum(len(open(c, encoding="utf-8").read()) for c in todo)
        print("分块 %d 个（已完成 %d 个跳过），约 %d 字符 ≈ 输入 %d k tokens（中文约 1.5 字/token 粗估）"
              % (len(todo), len(chunks) - len(todo) if not a.limit else 0, chars, chars / 1.5 / 1000 + len(todo) * 0.6))
        print("模型 %s @ %s" % (model, base))
        if a.dry_run:
            for c in todo:
                print("  ", os.path.basename(c))
            return
        key = os.environ.get(key_env, "") if key_env else ""
        if key_env and not key:
            sys.exit("没有找到环境变量 %s。先设置 API key：PowerShell 里 $env:%s=\"sk-...\"" % (key_env, key_env))

        def work(c):
            name = os.path.basename(c)[:-4]
            try:
                text, usage = call(base, model, key, system, open(c, encoding="utf-8").read(), a.timeout)
            except Exception as e:
                return name, "ERROR " + str(e)
            try:
                d = parse_json(text)
            except Exception:
                open(os.path.join(raw, name + ".bad.txt"), "w", encoding="utf-8").write(text)
                return name, "回答不是合法 JSON，原文存为 %s.bad.txt" % name
            tmp = os.path.join(raw, name + ".json.tmp")
            json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            os.replace(tmp, os.path.join(raw, name + ".json"))
            n = sum(len(v) for v in d.values() if isinstance(v, list))
            return name, "ok %d 条  tokens in/out %s/%s" % (n, usage.get("prompt_tokens", "?"), usage.get("completion_tokens", "?"))

        with ThreadPoolExecutor(max(1, a.workers)) as ex:
            for i, (name, msg) in enumerate(ex.map(work, todo), 1):
                print("[%d/%d] %s  %s" % (i, len(todo), name, msg), flush=True)

    merged = merge(raw)
    json.dump(merged, open(os.path.join(out, "merged.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for sec, rows in merged.items():
        if rows:
            write_csv(os.path.join(out, sec + ".csv"), rows)
    print("合并：" + "，".join("%s %d（冲突 %d）" % (s, len(r), sum(1 for x in r if x.get("conflict"))) for s, r in merged.items() if r))
    print("结果在 " + out)


if __name__ == "__main__":
    main()
