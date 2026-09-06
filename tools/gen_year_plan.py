#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生「一年讀完整本聖經」官方排程 data/year_plan.json

規則（見 CLAUDE.md §17）：
- 正典順序創→啟，1189 章一章不漏、不跳段。
- 365 天讀完，每天固定讀 3 章或 4 章（271 天 3 章 ＋ 94 天 4 章 = 1189）。
- 盡量讓每一卷「剛好在某一天讀完」，不要跨到隔天的開頭；
  只有章數為 1、2、5 的書卷無法單獨湊成 3/4 的組合，才與相鄰書卷併成一個群組收尾。
- 產生的鍵格式與 data/yt_map.json 一致（全名＋章號；單章書卷只有書名），
  這樣前端查影片是直接 YTMAP[key]，不必再轉換。

用法：python3 tools/gen_year_plan.py  → 覆寫 data/year_plan.json 並印出驗證結果
"""
import json, math, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = json.load(open(os.path.join(ROOT, "data/bible_books.json"), encoding="utf-8"))
YTMAP = json.load(open(os.path.join(ROOT, "data/yt_map.json"), encoding="utf-8"))

TARGET_DAYS = 365
TOTAL = sum(b["chapters"] for b in BOOKS)
assert TOTAL == 1189, TOTAL
AVG = TOTAL / TARGET_DAYS


def key_of(book, ch):
    """與 yt_map.json 相同的鍵：單章書卷只用書名，其餘為全名＋章號"""
    return book["full"] if book["chapters"] == 1 else book["full"] + str(ch)


# 攤平成一章一單位，正典順序
FLAT = [(b, c) for b in BOOKS for c in range(1, b["chapters"] + 1)]
assert len(FLAT) == TOTAL


def feasible_k(total):
    """把 total 章分成 k 天、每天 3 或 4 章的可行 k 範圍；不可行回 None
    （3a+4b 湊不出 1、2、5）"""
    k_min, k_max = math.ceil(total / 4), total // 3
    return (k_min, k_max) if k_min <= k_max else None


# 第一步：以書卷為單位分群，章數湊不出 3/4 組合的與下一卷合併
groups, pending, ptotal = [], [], 0
for b in BOOKS:
    pending.append(b)
    ptotal += b["chapters"]
    rng = feasible_k(ptotal)
    if rng:
        groups.append({"books": pending, "total": ptotal, "k_min": rng[0], "k_max": rng[1]})
        pending, ptotal = [], 0
assert not pending, f"仍有未分配書卷：{[b['full'] for b in pending]}"

# 第二步：每群先取最接近平均速度的天數，再微調總天數到剛好 365
for g in groups:
    g["k"] = max(g["k_min"], min(g["k_max"], round(g["total"] / AVG)))
diff = TARGET_DAYS - sum(g["k"] for g in groups)
guard = 0
while diff != 0 and guard < 10000:
    guard += 1
    moved = False
    for g in sorted(groups, key=lambda x: -x["total"]):  # 大卷彈性大，優先調
        if diff > 0 and g["k"] < g["k_max"]:
            g["k"] += 1; diff -= 1; moved = True
        elif diff < 0 and g["k"] > g["k_min"]:
            g["k"] -= 1; diff += 1; moved = True
        if diff == 0:
            break
    if not moved:
        break
assert diff == 0, f"無法湊到 {TARGET_DAYS} 天，尚差 {diff}"


def spread(total, k):
    """k 天分配 total 章（每天 3 或 4），把讀 4 章的日子平均散開而非全擠在最後"""
    b = total - 3 * k
    chunks = [3] * k
    if b:
        step, pos = k / b, 0.0
        for _ in range(b):
            i = min(int(round(pos)), k - 1)
            while chunks[i] == 4:
                i = (i + 1) % k
            chunks[i] = 4
            pos += step
    assert sum(chunks) == total
    return chunks


days, pos = [], 0
for g in groups:
    for n in spread(g["total"], g["k"]):
        days.append([key_of(bk, c) for bk, c in FLAT[pos:pos + n]])
        pos += n
assert pos == TOTAL

out = {
    "name": "一年讀完整本聖經",
    "order": "canon",
    "totalDays": len(days),
    "totalChapters": TOTAL,
    "generatedAt": datetime.date.today().isoformat(),
    "note": "正典順序、每天 3 或 4 章、365 天讀完；多數書卷剛好在某天整卷讀完。由 tools/gen_year_plan.py 產生，勿手改。",
    "days": days,
}
path = os.path.join(ROOT, "data/year_plan.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write("\n")

# ── 驗證 ──
flat_keys = [k for d in days for k in d]
expect = [key_of(b, c) for b, c in FLAT]
errs = []
if len(days) != TARGET_DAYS: errs.append(f"天數 {len(days)} != {TARGET_DAYS}")
if flat_keys != expect: errs.append("章節順序或內容與正典順序不符")
if len(flat_keys) != TOTAL: errs.append(f"章數 {len(flat_keys)} != {TOTAL}")
if len(set(flat_keys)) != TOTAL: errs.append("有重複章節")
bad_sizes = sorted({len(d) for d in days} - {3, 4})
if bad_sizes: errs.append(f"出現非 3/4 章的日子：{bad_sizes}")
missing_yt = [k for k in flat_keys if k not in YTMAP]
if missing_yt: errs.append(f"{len(missing_yt)} 章在 yt_map 找不到影片，例：{missing_yt[:5]}")

sizes = {n: sum(1 for d in days if len(d) == n) for n in (3, 4)}
finish_days = 0
for i, d in enumerate(days):
    last = d[-1]
    for b in BOOKS:
        if last == key_of(b, b["chapters"]):
            finish_days += 1
            break
print(f"寫出 {path}（{os.path.getsize(path)} bytes）")
print(f"天數 {len(days)}｜3章 {sizes[3]} 天、4章 {sizes[4]} 天｜總章數 {len(flat_keys)}")
print(f"整卷收尾的日子：{finish_days} 天（66 卷中，被併讀的群組共用一個收尾日）")
print("合併群組：", [ "＋".join(b["full"] for b in g["books"]) for g in groups if len(g["books"]) > 1 ])
print("驗證：", "ALL OK" if not errs else errs)
