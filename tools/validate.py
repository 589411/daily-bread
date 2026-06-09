#!/usr/bin/env python3
# =====================================================================
#  每日靈糧 資料驗證器  —  改完 data/ 後務必跑這支，確認沒問題再 commit
#  用法：  python3 tools/validate.py
#  通過會印 "ALL OK"；有問題會逐條列出。任何模型都能據此修正。
# =====================================================================
import json, re, sys, os, calendar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)

# 書卷簡稱 → (聖經編號, 全名)。新增月份轉錄時只能用這些簡稱。
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
SINGLE = {"俄","門","約貳","約參","猶"}                 # 單章書卷（簡稱即全名）
ABBR = sorted(BOOKS, key=lambda x: -len(x))             # 長的先比，避免「約」吃掉「約壹」

def parse_ref(s):
    s = re.sub(r"[（(][^）)]*[）)]", "", (s or "").strip())   # 去掉 (1-53節) 之類
    for k in ABBR:
        if s.startswith(k):
            rest = re.sub(r"[章篇]", "", s[len(k):])
            m = re.match(r"\d+", rest)
            return {"abbr": k, "full": BOOKS[k][1], "ch": int(m.group()) if m else 1,
                    "single": k in SINGLE}
    return None

def yt_key(p):  # 對應 data/yt_map.json 與 data/summary.json 的 key
    return p["full"] + ("" if p["single"] else str(p["ch"]))

def main():
    sched = load("data/schedule.json")
    ytmap = load("data/yt_map.json")
    summ  = load("data/summary.json")
    errs, warns = [], []

    # 1) 每天的三欄都在、靈修可解析、yt 有對應
    by_month = {}
    for k in sorted(sched):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", k):
            errs.append(f"{k}: 日期格式須為 YYYY-MM-DD"); continue
        by_month.setdefault(k[:7], set()).add(int(k[8:10]))
        row = sched[k]
        for col in ("d", "s5", "s10"):
            if col not in row or not row[col]:
                errs.append(f"{k}: 缺欄位 {col}")
        p = parse_ref(row.get("d", ""))
        if not p:
            errs.append(f"{k}: 靈修『{row.get('d')}』無法解析（書卷簡稱不在清單？）"); continue
        if yt_key(p) not in ytmap:
            warns.append(f"{k}: 靈修 {row['d']} → 第一遍無影片（yt_map 缺 {yt_key(p)}）")
        if yt_key(p) not in summ:
            warns.append(f"{k}: 靈修 {row['d']} 無摘要（可選）")
        # 速讀起點要可解析
        for col in ("s5", "s10"):
            start = row.get(col, "").split("-")[0]
            if start and not parse_ref(start):
                errs.append(f"{k}: {col} 起點『{start}』無法解析")

    # 2) 每個月日數要連續、不缺天
    for ym, days in by_month.items():
        y, m = int(ym[:4]), int(ym[5:7])
        full = set(range(1, calendar.monthrange(y, m)[1] + 1))
        miss = sorted(full - days)
        if miss:
            warns.append(f"{ym}: 該月缺少日期 {miss}（若教會該月未到月底可忽略）")

    print(f"schedule 天數：{len(sched)}　yt_map 章數：{len(ytmap)}　摘要：{len(summ)}")
    if warns:
        print(f"\n⚠️  提醒 {len(warns)} 則：")
        for w in warns: print("   -", w)
    if errs:
        print(f"\n❌ 錯誤 {len(errs)} 則（請修正後再 commit）：")
        for e in errs: print("   -", e)
        sys.exit(1)
    print("\n✅ ALL OK — 資料結構正確，可以 commit / push。")

if __name__ == "__main__":
    main()
