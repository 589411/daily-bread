#!/usr/bin/env python3
# =====================================================================
#  讀經順序「預測 / 驗證」工具
#  依教會傳統順序 data/reading_order.json，以「現有排程最後一天」為錨點，
#  預測未來日期的靈修進度，或比對教會新公布的月曆表，回報命中率與差異。
#
#  用法（在 repo 根目錄執行）：
#    python3 tools/predict_check.py                 # 自我檢查：對現有 schedule 各月算命中率
#    python3 tools/predict_check.py gen 2026-07-01 2026-07-31
#                                                   # 產生該區間「預測靈修」的 schedule.json 片段（d 欄；s5/s10 留空待填）
#    python3 tools/predict_check.py verify 2026-07  # 比對 schedule.json 中該月既有 d 與預測，列出不符（=局部換書）
#
#  ▶ 每月實際更新流程（給接手的人／LLM）：
#    1. 先 `verify 該月` 看順序是否穩定（命中高→可信）。
#    2. 用 `gen` 產生草稿 d，貼進 data/schedule.json；s5/s10 仍須照教會月曆表填。
#    3. 對照教會月曆表修正 verify 報出的局部差異。
#    4. 跑 tools/validate.py → ALL OK → commit。
# =====================================================================
import json, re, sys, os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)

# 書卷簡稱 → (編號, 全名)；與 tools/validate.py 一致
BOOKS = {
 "創":(1,"創世記"),"出":(2,"出埃及記"),"利":(3,"利未記"),"民":(4,"民數記"),"申":(5,"申命記"),
 "書":(6,"約書亞記"),"士":(7,"士師記"),"得":(8,"路得記"),"撒上":(9,"撒母耳記上"),"撒下":(10,"撒母耳記下"),
 "王上":(11,"列王紀上"),"王下":(12,"列王紀下"),"代上":(13,"歷代志上"),"代下":(14,"歷代志下"),
 "拉":(15,"以斯拉記"),"尼":(16,"尼希米記"),"斯":(17,"以斯帖記"),"伯":(18,"約伯記"),"詩":(19,"詩篇"),
 "箴":(20,"箴言"),"傳":(21,"傳道書"),"歌":(22,"雅歌"),"賽":(23,"以賽亞書"),"耶":(24,"耶利米書"),
 "哀":(25,"耶利米哀歌"),"結":(26,"以西結書"),"但":(27,"但以理書"),"何":(28,"何西阿書"),"珥":(29,"約珥書"),
 "摩":(30,"阿摩司書"),"俄":(31,"俄巴底亞書"),"拿":(32,"約拿書"),"彌":(33,"彌迦書"),"鴻":(34,"那鴻書"),
 "哈":(35,"哈巴谷書"),"番":(36,"西番雅書"),"該":(37,"哈該書"),"亞":(38,"撒迦利亞書"),"瑪":(39,"瑪拉基書"),
 "太":(40,"馬太福音"),"可":(41,"馬可福音"),"路":(42,"路加福音"),"約":(43,"約翰福音"),"徒":(44,"使徒行傳"),
 "羅":(45,"羅馬書"),"林前":(46,"哥林多前書"),"林後":(47,"哥林多後書"),"加":(48,"加拉太書"),"弗":(49,"以弗所書"),
 "腓":(50,"腓立比書"),"西":(51,"歌羅西書"),"帖前":(52,"帖撒羅尼迦前書"),"帖後":(53,"帖撒羅尼迦後書"),
 "提前":(54,"提摩太前書"),"提後":(55,"提摩太後書"),"多":(56,"提多書"),"門":(57,"腓利門書"),"來":(58,"希伯來書"),
 "雅":(59,"雅各書"),"彼前":(60,"彼得前書"),"彼後":(61,"彼得後書"),"約壹":(62,"約翰一書"),
 "約貳":(63,"約翰二書"),"約參":(64,"約翰三書"),"猶":(65,"猶大書"),"啟":(66,"啟示錄"),
}
SINGLE = {"俄","門","約貳","約參","猶"}
ABBR = sorted(BOOKS, key=lambda x: -len(x))
FULL2ABBR = {full: ab for ab,(i,full) in BOOKS.items()}
FULLS = sorted(FULL2ABBR, key=lambda x: -len(x))

def abbr_to_key(dev):           # "代下8" / "約貳" → reading_order 的 key（全名＋章號）
    dev = re.sub(r"[（(].*?[）)]", "", (dev or "").strip())
    for k in ABBR:
        if dev.startswith(k):
            rest = re.sub(r"[章篇]", "", dev[len(k):]); m = re.match(r"\d+", rest)
            full = BOOKS[k][1]
            return full if k in SINGLE else f"{full}{int(m.group()) if m else 1}"
    return None

def key_to_abbr(key):           # "歷代志下8" → "代下8"；"約翰二書" → "約貳"
    for full in FULLS:
        if key.startswith(full):
            ab = FULL2ABBR[full]; num = key[len(full):]
            return ab if ab in SINGLE else f"{ab}{num or 1}"
    return key

def main():
    order = load("data/reading_order.json")
    sched = load("data/schedule.json")
    idx = {c: i for i, c in enumerate(order)}
    N = len(order)

    # 錨點＝現有排程「最後一個能對到順序」的日子（排程擴充時自動跟進）
    anchor = None
    for d in sorted(sched, reverse=True):
        k = abbr_to_key(sched[d].get("d", ""))
        if k in idx:
            anchor = (date.fromisoformat(d), idx[k]); break
    if not anchor:
        print("找不到錨點：schedule.json 的靈修章節都對不到 reading_order"); sys.exit(1)
    a_date, a_idx = anchor

    def predict(dt):            # 某日期 → 預測靈修（簡稱）
        return key_to_abbr(order[(a_idx + (dt - a_date).days) % N])

    args = sys.argv[1:]
    print(f"錨點：{a_date.isoformat()} = {key_to_abbr(order[a_idx])}（reading_order index {a_idx} / {N}）\n")

    if not args:               # 自我檢查
        months = sorted({d[:7] for d in sched})
        for m in months:
            ds = sorted(d for d in sched if d.startswith(m))
            hit = sum(1 for d in ds if sched[d].get("d") and key_to_abbr(abbr_to_key(sched[d]["d"]) or "") == predict(date.fromisoformat(d)))
            print(f"  {m}: 既有靈修 vs 預測 命中 {hit}/{len(ds)}")
        print("\n（gen 產生草稿、verify 比對某月，見檔頭用法）")
        return

    cmd = args[0]
    if cmd == "gen" and len(args) >= 3:
        d0, d1 = date.fromisoformat(args[1]), date.fromisoformat(args[2])
        print("// 預測草稿（d 為靈修；s5/s10 請照教會月曆表填）")
        d = d0
        while d <= d1:
            print(f'"{d.isoformat()}": {{"d": "{predict(d)}", "s5": "", "s10": ""}},')
            d += timedelta(days=1)
    elif cmd == "verify" and len(args) >= 2:
        m = args[1]; ds = sorted(d for d in sched if d.startswith(m))
        if not ds: print(f"schedule.json 沒有 {m} 的資料，無法比對"); return
        bad = []
        for d in ds:
            act = sched[d].get("d", ""); pred = predict(date.fromisoformat(d))
            if key_to_abbr(abbr_to_key(act) or "") != pred: bad.append((d, act, pred))
        print(f"{m}: 命中 {len(ds)-len(bad)}/{len(ds)}")
        for d, act, pred in bad: print(f"  ✗ {d}  實際={act}  預測={pred}")
        if not bad: print("  全部吻合，順序穩定。")
    else:
        print(__doc__ if False else "用法：見檔頭註解（gen <起> <迄> / verify <YYYY-MM>）")

if __name__ == "__main__":
    main()
