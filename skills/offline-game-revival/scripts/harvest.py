#!/usr/bin/env python3
"""harvest.py — turn players' screenshots & screen recordings into searchable, structured text.

把玩家的截图 / 录屏（动辄十几 GB）在本地变成几百 KB 的结构化文字，再交给任意文本大模型整理成数值表。
全程离线、不花 token：
  1. 视频抽关键帧：只保留"画面变了、而且停稳了"的帧（跳过转场动画和滚动途中的模糊帧）；
     一直在变（长列表滚动）时每隔 --max-gap 秒兜底取一帧。
  2. 近似去重：差值哈希（dHash，256 位，裁掉顶部状态栏）+ 汉明距离；截图和录屏帧跨来源也能去重。
  3. 本地 OCR：RapidOCR（ONNX，CPU 可跑，中英日韩通用模型），输出文字 + 坐标 + 置信度，按阅读顺序拼行。
  4. 按界面分类：关键词规则（可用 --rules 自定义 JSON），每类一个文本文件，并切成适合喂给大模型的分块。
  可中断续跑：已处理的源文件记录在 <out>/state.json，OCR 结果追加写入 <out>/ocr.jsonl。

依赖：pip install opencv-python-headless numpy pillow rapidocr_onnxruntime
用法：
  python harvest.py <输入目录> <输出目录> [--scene 0.12] [--stable 0.02] [--max-gap 4] [--hash-dist 24]
                    [--rules rules.json] [--no-ocr] [--limit N] [--chunk-chars 12000]
输出：
  <out>/frames/        录屏抽出的关键帧（jpg，文件名含来源与时间点）
  <out>/ocr.jsonl      每张保留图一行：来源、时间点、尺寸、分类、文字行（text/box/score）
  <out>/index.csv      图片 → 分类 → 首行文字 速查表
  <out>/by_category/   每个分类一个 .md（图片路径 + 识别文字），人工翻阅用
  <out>/for_llm/       每个分类切好的 .txt 分块，直接粘贴给文本模型
  <out>/report.txt     统计：源文件数、抽帧数、去重后数量、各分类数量
"""
import argparse
import csv
import json
import os
import re
import sys
import time

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VID_EXT = {".mp4", ".mov", ".mkv", ".avi", ".3gp", ".webm", ".flv", ".m4v", ".ts"}

# 默认分类规则：手游常见界面。命中关键词越多分越高，取最高分；全不命中归 other。按需用 --rules 覆盖或追加。
DEFAULT_RULES = {
    "gacha_rates": ["概率", "公示", "保底", "抽卡", "祈愿", "誓约", "召唤", "招募", "十连", "单抽", "SSR", "UR", "必出"],
    "shop": ["商店", "购买", "限购", "售价", "兑换", "礼包", "折扣", "剩余", "刷新"],
    "card_detail": ["升级", "升星", "突破", "觉醒", "属性", "技能", "等级", "材料", "星级", "Lv"],
    "rewards_signin": ["签到", "第1天", "第一天", "累计", "七日", "登录奖励", "月卡"],
    "tasks_achievements": ["任务", "成就", "每日", "每周", "活跃", "进度", "领取"],
    "stages": ["关卡", "章节", "委托", "推荐", "通关", "挑战", "扫荡", "体力", "星"],
    "event": ["活动", "限时", "排行", "积分", "倒计时", "开启时间", "结束"],
    "mail_notice": ["邮件", "公告", "附件", "系统"],
    "inventory": ["背包", "道具", "物品", "数量", "使用", "出售"],
    "story_dialog": ["……", "…", "？", "！"],
    "settings_account": ["设置", "音量", "账号", "用户协议", "隐私", "客服", "兑换码"],
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- 图像工具
def load_bgr(path):
    import cv2
    import numpy as np
    data = np.fromfile(path, dtype=np.uint8)          # 支持中文路径（cv2.imread 在 Windows 上不支持）
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img


def save_jpg(img, path, q=90):
    import cv2
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    if ok:
        buf.tofile(path)
    return ok


def small_gray(img, w=96):
    """缩成固定宽度的灰度小图，用于帧间差异（与分辨率无关）。"""
    import cv2
    h = max(1, int(img.shape[0] * w / img.shape[1]))
    g = cv2.cvtColor(cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    return g.astype("float32") / 255.0


def frame_diff(a, b):
    if a is None or b is None or a.shape != b.shape:
        return 1.0
    import numpy as np
    return float(np.mean(np.abs(a - b)))


def dhash_bits(img, size=16, crop_top=0.06):
    """差值哈希：裁掉顶部状态栏（时钟/电量会让同一界面哈希不同），size×size 位。"""
    import cv2
    import numpy as np
    h = img.shape[0]
    body = img[int(h * crop_top):, :]
    g = cv2.cvtColor(body, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (size + 1, size), interpolation=cv2.INTER_AREA)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return np.packbits(bits)


class Deduper:
    def __init__(self, max_dist):
        import numpy as np
        self.np = np
        self.max_dist = max_dist
        self.hashes = None
        self.owner = []

    def check(self, h, name):
        """返回已存在的近似重复图名；否则登记并返回 None。"""
        np = self.np
        if self.hashes is not None and len(self.owner):
            x = np.bitwise_xor(self.hashes, h[None, :])
            d = np.unpackbits(x, axis=1).sum(axis=1)
            i = int(d.argmin())
            if d[i] <= self.max_dist:
                return self.owner[i]
        self.hashes = h[None, :] if self.hashes is None else np.vstack([self.hashes, h[None, :]])
        self.owner.append(name)
        return None


# ---------------------------------------------------------------- 视频抽帧
def video_keyframes(path, scene, stable, max_gap, step_s=0.25):
    """逐 step_s 秒采样：画面相对上一张保留帧变化 > scene，且相对上一采样 < stable（停稳了）才保留。
    持续变化超过 max_gap 秒（长列表滚动、播放动画）时兜底保留当前帧。yield (秒, BGR图)。"""
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        log("  ! 打不开视频（可能需要转码）:", path)
        return
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if fps <= 0 or fps > 240:
        fps = 30.0
    step = max(1, int(round(fps * step_s)))
    idx, prev, kept, kept_t = 0, None, None, -1e9
    while True:
        ok = cap.grab()
        if not ok:
            break
        if idx % step == 0:
            ok, img = cap.retrieve()
            if not ok:
                break
            t = idx / fps
            g = small_gray(img)
            moving = frame_diff(g, prev)
            changed = frame_diff(g, kept)
            if kept is None or (changed > scene and moving < stable) or (changed > scene and t - kept_t >= max_gap):
                kept, kept_t = g, t
                yield t, img
            prev = g
        idx += 1
    cap.release()


# ---------------------------------------------------------------- OCR
class OCR:
    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.kind = "v1"
        except ImportError:
            from rapidocr import RapidOCR          # rapidocr 2.x / 3.x
            self.kind = "v2"
        self.engine = RapidOCR()

    def __call__(self, img):
        out = []
        if self.kind == "v1":
            res, _ = self.engine(img)
            for box, text, score in res or []:
                out.append((box, text, float(score)))
        else:
            r = self.engine(img)
            if r is not None and getattr(r, "txts", None):
                for box, text, score in zip(r.boxes, r.txts, r.scores):
                    out.append((box.tolist() if hasattr(box, "tolist") else box, text, float(score)))
        lines = []
        for box, text, score in out:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            lines.append({"text": text, "score": round(score, 3),
                          "box": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]})
        return reading_order(lines)


def reading_order(lines):
    """按行分组（纵向重叠过半算同一行），行内从左到右。"""
    lines = sorted(lines, key=lambda l: (l["box"][1] + l["box"][3]) / 2)
    rows, cur = [], []
    for l in lines:
        if cur:
            y0, y1 = cur[-1]["box"][1], cur[-1]["box"][3]
            h = max(1, y1 - y0)
            cy = (l["box"][1] + l["box"][3]) / 2
            if abs(cy - (y0 + y1) / 2) > h * 0.5:
                rows.append(cur)
                cur = []
        cur.append(l)
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda l: l["box"][0]))
    return out


def as_text(lines):
    rows, last_y = [], None
    for l in lines:
        cy = (l["box"][1] + l["box"][3]) / 2
        h = max(1, l["box"][3] - l["box"][1])
        if last_y is None or abs(cy - last_y) > h * 0.5:
            rows.append([])
        rows[-1].append(l["text"])
        last_y = cy
    return "\n".join("  ".join(r) for r in rows)


def classify(text, rules):
    best, score = "other", 0
    for cat, kws in rules.items():
        s = sum(text.count(k) for k in kws)
        if s > score:
            best, score = cat, s
    return best


# ---------------------------------------------------------------- 主流程
def walk(root):
    for d, _, fs in os.walk(root):
        for f in sorted(fs):
            ext = os.path.splitext(f)[1].lower()
            if ext in IMG_EXT or ext in VID_EXT:
                yield os.path.join(d, f), ext


def safe_name(s):
    return re.sub(r"[^\w一-鿿.-]+", "_", s)[:80]


def main():
    for s in (sys.stdout, sys.stderr):             # Windows 控制台默认 GBK，中文文件名会乱码
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="screenshots & screen recordings -> keyframes -> dedupe -> OCR -> categorized text")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--scene", type=float, default=0.12, help="与上一保留帧的平均灰度差 > 此值才算新画面（0~1）")
    ap.add_argument("--stable", type=float, default=0.02, help="与上一采样差 < 此值才算停稳")
    ap.add_argument("--max-gap", type=float, default=4.0, help="持续变化时每隔多少秒兜底取一帧")
    ap.add_argument("--hash-dist", type=int, default=24,
                    help="256 位 dHash 汉明距离 ≤ 此值视为重复（实测：同一界面截图 vs 录屏帧 2~12，不同界面 ≥60）")
    ap.add_argument("--rules", help="分类规则 JSON：{分类名: [关键词...]}，与默认规则合并（同名覆盖）")
    ap.add_argument("--no-ocr", action="store_true", help="只抽帧去重，不做 OCR")
    ap.add_argument("--limit", type=int, default=0, help="最多处理多少个源文件（试跑用）")
    ap.add_argument("--chunk-chars", type=int, default=12000, help="for_llm 每个分块的字符上限")
    a = ap.parse_args()

    rules = dict(DEFAULT_RULES)
    if a.rules:
        rules.update(json.load(open(a.rules, encoding="utf-8")))
    os.makedirs(os.path.join(a.output, "frames"), exist_ok=True)
    state_p = os.path.join(a.output, "state.json")
    state = json.load(open(state_p, encoding="utf-8")) if os.path.exists(state_p) else {"done": {}, "stats": {}}
    ocr_p = os.path.join(a.output, "ocr.jsonl")
    ocr = None if a.no_ocr else OCR()
    dedup = Deduper(a.hash_dist)

    # 续跑：把已保留的图重新登记进去重表
    if os.path.exists(ocr_p):
        for line in open(ocr_p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            img = load_bgr(r["image"])
            if img is not None:
                dedup.check(dhash_bits(img), r["image"])

    st = state["stats"]
    for k in ("sources", "videos", "images", "frames", "kept", "dup"):
        st.setdefault(k, 0)
    n_src = 0
    t0 = time.time()
    with open(ocr_p, "a", encoding="utf-8") as fo:
        for path, ext in walk(a.input):
            key = os.path.relpath(path, a.input)
            if key in state["done"]:
                continue
            if a.limit and n_src >= a.limit:
                break
            n_src += 1
            st["sources"] += 1
            if ext in VID_EXT:
                st["videos"] += 1
                items = []
                for t, img in video_keyframes(path, a.scene, a.stable, a.max_gap):
                    st["frames"] += 1
                    name = os.path.join(a.output, "frames", "%s@%07.2fs.jpg" % (safe_name(key), t))
                    items.append((t, img, name))
            else:
                st["images"] += 1
                img = load_bgr(path)
                items = [(None, img, path)] if img is not None else []
            kept_here = 0
            for t, img, name in items:
                if dedup.check(dhash_bits(img), name) is not None:
                    st["dup"] += 1
                    continue
                if t is not None:
                    save_jpg(img, name)
                rec = {"image": name, "source": key, "t": t, "w": int(img.shape[1]), "h": int(img.shape[0])}
                if ocr:
                    lines = ocr(img)
                    rec["lines"] = lines
                    rec["text"] = as_text(lines)
                    rec["category"] = classify(rec["text"], rules)
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                kept_here += 1
                st["kept"] += 1
            fo.flush()
            state["done"][key] = kept_here
            json.dump(state, open(state_p, "w", encoding="utf-8"), ensure_ascii=False)
            log("[%d] %s -> 保留 %d（累计 保留 %d / 重复 %d，%.0fs）" % (st["sources"], key, kept_here, st["kept"], st["dup"], time.time() - t0))

    write_outputs(a.output, ocr_p, a.chunk_chars, st)


def write_outputs(out, ocr_p, chunk_chars, st):
    recs = []
    for line in open(ocr_p, encoding="utf-8"):
        try:
            recs.append(json.loads(line))
        except ValueError:
            pass
    by = {}
    for r in recs:
        by.setdefault(r.get("category", "uncategorized"), []).append(r)
    os.makedirs(os.path.join(out, "by_category"), exist_ok=True)
    os.makedirs(os.path.join(out, "for_llm"), exist_ok=True)
    with open(os.path.join(out, "index.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "image", "source", "t", "first_line"])
        for r in recs:
            first = (r.get("text") or "").split("\n")[0][:60]
            w.writerow([r.get("category", ""), r["image"], r["source"], r["t"], first])
    for cat, rs in sorted(by.items()):
        with open(os.path.join(out, "by_category", cat + ".md"), "w", encoding="utf-8") as f:
            f.write("# %s（%d 张）\n\n" % (cat, len(rs)))
            for r in rs:
                f.write("## %s%s\n\n```\n%s\n```\n\n" % (r["image"], "" if r["t"] is None else "  (t=%.1fs)" % r["t"], r.get("text", "")))
        part, buf = 1, ""
        for r in rs:
            block = "### IMAGE: %s\n%s\n\n" % (os.path.basename(r["image"]), r.get("text", ""))
            if buf and len(buf) + len(block) > chunk_chars:
                open(os.path.join(out, "for_llm", "%s_%02d.txt" % (cat, part)), "w", encoding="utf-8").write(buf)
                part, buf = part + 1, ""
            buf += block
        if buf:
            open(os.path.join(out, "for_llm", "%s_%02d.txt" % (cat, part)), "w", encoding="utf-8").write(buf)
    lines = ["源文件 %d（视频 %d，图片 %d）" % (st["sources"], st["videos"], st["images"]),
             "视频抽出关键帧 %d；去重丢弃 %d；最终保留 %d" % (st["frames"], st["dup"], st["kept"]), ""]
    lines += ["%-20s %d" % (c, len(rs)) for c, rs in sorted(by.items(), key=lambda x: -len(x[1]))]
    open(os.path.join(out, "report.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
