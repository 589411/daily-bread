#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生「一年讀完整本聖經」官方排程 data/year_plan.json（字數加權版）

為什麼要用字數而不是章數（見 CLAUDE.md §17）：
「章」不是等量單位。詩篇117篇只有 50 字，詩篇119篇有 3304 字，差 66 倍；
固定「每天 3 或 4 章」會讓某些日子輕鬆 10 分鐘、某些日子讀到力竭。
改以「每天字數盡量相等」為目標，章數自然變成浮動的結果。

規則：
- 正典順序創→啟，1189 章一章不漏、不跳段。
- 365 天讀完，目標是每天字數接近 總字數/365。
- 仍然盡量讓每一卷在某一天整卷讀完；字數太少的書卷才與相鄰書卷併成一個群組。
- 每卷（群組）內用動態規劃切成 k 段連續章節，最小化各日字數與目標值的平方差，
  所以字數多的日子章數少（詩篇119 可能自成一天），字數少的日子章數多（短卷可一天讀完）。

用法：python3 tools/gen_year_plan.py  → 覆寫 data/year_plan.json 並印出驗證與統計
"""
import json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = json.load(open(os.path.join(ROOT, "data/bible_books.json"), encoding="utf-8"))
YTMAP = json.load(open(os.path.join(ROOT, "data/yt_map.json"), encoding="utf-8"))
CHARS = json.load(open(os.path.join(ROOT, "data/chapter_chars.json"), encoding="utf-8"))["chars"]

TARGET_DAYS = 365
# 一個群組至少要有這麼多字才值得單獨佔一天，否則與下一卷合併
MIN_GROUP_RATIO = 0.55


def key_of(book, ch):
    return book["full"] if book["chapters"] == 1 else book["full"] + str(ch)


FLAT = [(b, c) for b in BOOKS for c in range(1, b["chapters"] + 1)]
KEYS = [key_of(b, c) for b, c in FLAT]
W = [CHARS[k] for k in KEYS]
TOTAL_CHARS = sum(W)
TOTAL_CH = len(KEYS)
TARGET = TOTAL_CHARS / TARGET_DAYS


def dp_table(weights, maxk):
    """一次 DP 算出「切成 j 段」的最小成本與切法（j = 1..maxk）。
    成本 = Σ(每段字數 - TARGET)^2。回傳 (cost[j], cut[j][i])。"""
    n = len(weights)
    maxk = min(maxk, n)
    pre = [0]
    for w in weights:
        pre.append(pre[-1] + w)
    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(maxk + 1)]
    ch = [[-1] * (n + 1) for _ in range(maxk + 1)]
    dp[0][0] = 0.0
    for j in range(1, maxk + 1):
        for i in range(j, n - (maxk - j) + 1 if False else n + 1):
            best, bi = INF, -1
            for t in range(j - 1, i):
                if dp[j - 1][t] == INF:
                    continue
                seg = pre[i] - pre[t]
                c = dp[j - 1][t] + (seg - TARGET) ** 2
                if c < best:
                    best, bi = c, t
            dp[j][i], ch[j][i] = best, bi
    return [dp[j][n] for j in range(maxk + 1)], ch


def cuts_from(ch, n, k):
    out, i = [], n
    for j in range(k, 0, -1):
        t = ch[j][i]
        out.append(i - t)
        i = t
    return out[::-1]


# 第一步：把字數太少的書卷與後面的書卷併成群組
groups, pending, pchars, pchs = [], [], 0, 0
for b in BOOKS:
    ks = [key_of(b, c) for c in range(1, b["chapters"] + 1)]
    pending.append(b); pchars += sum(CHARS[k] for k in ks); pchs += b["chapters"]
    if pchars >= TARGET * MIN_GROUP_RATIO:
        groups.append({"books": pending, "chars": pchars, "chapters": pchs})
        pending, pchars, pchs = [], 0, 0
if pending:  # 最後殘留的併進前一組
    groups[-1]["books"] += pending
    groups[-1]["chars"] += pchars
    groups[-1]["chapters"] += pchs

# 第二步：每組先用一次 DP 算出「切成 k 天」的真實最小成本，
# 再依「多給一天能減少多少成本」的邊際效益，把 365 天分配出去（成本對 k 為凸，貪婪即最佳）。
MAXK_CAP = 40
pos = 0
for g in groups:
    n = g["chapters"]
    w = W[pos:pos + n]
    maxk = min(n, MAXK_CAP)
    cost, ch = dp_table(w, maxk)
    g["cost"], g["ch"], g["maxk"], g["w"] = cost, ch, maxk, w
    g["k"] = 1
    pos += n
assert pos == TOTAL_CH

import heapq
# heap 放 (-邊際效益, 組序號)：多給這組第 k+1 天能省下的成本
heap = []
for idx, g in enumerate(groups):
    if g["maxk"] >= 2:
        heapq.heappush(heap, (-(g["cost"][1] - g["cost"][2]), idx))
remaining = TARGET_DAYS - len(groups)
assert remaining >= 0, f"書卷群組數 {len(groups)} 已超過 {TARGET_DAYS} 天"
while remaining > 0:
    gain, idx = heapq.heappop(heap)
    g = groups[idx]
    g["k"] += 1
    remaining -= 1
    if g["k"] + 1 <= g["maxk"]:
        heapq.heappush(heap, (-(g["cost"][g["k"]] - g["cost"][g["k"] + 1]), idx))
assert sum(g["k"] for g in groups) == TARGET_DAYS

# 第三步：依分配到的 k 取出切法
days, pos = [], 0
for g in groups:
    n = g["chapters"]
    for ln in cuts_from(g["ch"], n, g["k"]):
        days.append(KEYS[pos:pos + ln]); pos += ln
assert pos == TOTAL_CH

out = {
    "name": "一年讀完整本聖經",
    "order": "canon",
    "weighted": "chars",
    "totalDays": len(days),
    "totalChapters": TOTAL_CH,
    "totalChars": TOTAL_CHARS,
    "targetCharsPerDay": round(TARGET),
    "generatedAt": datetime.date.today().isoformat(),
    "note": "正典順序、365 天讀完、以每日字數均衡為目標（章數浮動）。由 tools/gen_year_plan.py 產生，勿手改。",
    "days": days,
}
json.dump(out, open(os.path.join(ROOT, "data/year_plan.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))

# ── 驗證 ──
flat = [k for d in days for k in d]
errs = []
if len(days) != TARGET_DAYS: errs.append(f"天數 {len(days)}")
if flat != KEYS: errs.append("章節順序與正典不符")
if len(set(flat)) != TOTAL_CH: errs.append("有重複章節")
miss = [k for k in flat if k not in YTMAP]
if miss: errs.append(f"{len(miss)} 章查無影片")

dc = [sum(CHARS[k] for k in d) for d in days]
nc = [len(d) for d in days]
import statistics as st
print(f"總字數 {TOTAL_CHARS:,}｜目標每天 {round(TARGET)} 字")
print(f"每日字數：最少 {min(dc)}、最多 {max(dc)}、中位數 {round(st.median(dc))}、標準差 {round(st.pstdev(dc))}")
print(f"每日章數：最少 {min(nc)}、最多 {max(nc)}、中位數 {st.median(nc)}")
dist = {}
for n in nc: dist[n] = dist.get(n, 0) + 1
print("章數分布：", " ".join(f"{k}章×{v}天" for k, v in sorted(dist.items())))
fin = sum(1 for d in days if any(CHARS.get(k) is not None and k == key_of(b, b["chapters"]) for k in d for b in BOOKS))
print(f"有整卷收尾的日子：{fin} 天")
print("驗證：", "ALL OK" if not errs else errs)
