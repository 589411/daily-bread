#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原文亮點驗證器（L1 程式驗證，見 insight/RULES.md §6）
用法:
  python3 insight/tools/validate_insights.py            # 全部檢查（含線上原文比對）
  python3 insight/tools/validate_insights.py --offline  # 只做 schema 檢查（無網路）
零依賴（stdlib）。原文抓 bolls.life（WLC/TR/CUV），結果快取在 insight/tools/.cache/。
必須輸出 ALL OK 才能 commit。
"""
import json, re, sys, unicodedata, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "insight" / "data" / "insights.json"
BOOKS = ROOT / "data" / "bible_books.json"
CACHE = pathlib.Path(__file__).resolve().parent / ".cache"

CATEGORIES = {"paronomasia", "name-etymology", "semantic-range", "leitwort",
              "grammar", "wordplay-vision", "acrostic", "idiom", "textual"}
CONFIDENCE = {"high", "medium", "low"}
LANG_SRC = {"he": "WLC", "el": "TR"}

errors, warns = [], []
def err(eid, msg): errors.append(f"[{eid}] {msg}")
def warn(eid, msg): warns.append(f"[{eid}] {msg}")

# ---------- 正規化 ----------
def norm_hebrew(s):
    # 去母音點/重音（U+0591–U+05C7），maqaf/sof pasuq 轉空白，僅留希伯來字母與空白
    out = []
    for ch in s:
        o = ord(ch)
        if 0x05D0 <= o <= 0x05EA:
            out.append(ch)
        elif ch in "־׀׃  ":
            out.append(" ")
        elif 0x0591 <= o <= 0x05C7:
            continue
        else:
            out.append(" ")
    return re.sub(r"\s+", " ", "".join(out))

def norm_greek(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().replace("ς", "σ")  # 尾σ
    return re.sub(r"[^α-ω ]+", " ", s)

def norm_cuv(s):
    return re.sub(r"[\s　]+", "", s)

NORM = {"he": norm_hebrew, "el": norm_greek}

# ---------- 取原文（含快取） ----------
def fetch_chapter(trans, book_no, chapter):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{trans}_{book_no}_{chapter}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    url = f"https://bolls.life/get-text/{trans}/{book_no}/{chapter}/"
    req = urllib.request.Request(url, headers={"User-Agent": "daily-bread-insight-validator"})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data

class Offline(Exception): pass

def verse_text(trans, book_no, chapter, verse):
    vf = CACHE / f"V_{trans}_{book_no}_{chapter}_{verse}.json"
    if vf.exists():
        return json.loads(vf.read_text(encoding="utf-8"))["text"]
    try:
        data = fetch_chapter(trans, book_no, chapter)
    except OSError:
        raise Offline(f"{trans} {book_no}:{chapter}:{verse} 不在快取且無法連線")
    for v in data:
        if v["verse"] == verse:
            return v["text"]
    return None

# ---------- 主檢查 ----------
def main():
    offline = "--offline" in sys.argv
    books = {b["id"]: b for b in json.loads(BOOKS.read_text(encoding="utf-8"))}
    try:
        entries = json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: insights.json 不是合法 JSON: {e}"); sys.exit(1)

    seen_ids = set()
    for ent in entries:
        eid = ent.get("id", "<no-id>")
        # id
        if eid in seen_ids: err(eid, "id 重複")
        seen_ids.add(eid)
        if not re.fullmatch(r"[a-z0-9]+\.\d+\.\d+(-\d+)?", eid):
            warn(eid, "id 建議格式：書卷代碼.章.起始節")
        # ref
        ref = ent.get("ref", {})
        b = books.get(ref.get("bookNo"))
        if not b:
            err(eid, f"bookNo 不合法: {ref.get('bookNo')}"); continue
        if ref.get("book") != b["abbr"]: err(eid, f"book 簡稱不符: {ref.get('book')} ≠ {b['abbr']}")
        if ref.get("bookFull") != b["full"]: err(eid, f"bookFull 不符: {ref.get('bookFull')} ≠ {b['full']}")
        ch = ref.get("chapter")
        if not isinstance(ch, int) or not 1 <= ch <= b["chapters"]:
            err(eid, f"chapter 超界: {ch}（{b['full']} 共 {b['chapters']} 章）"); continue
        verses = ref.get("verses", [])
        if not verses or verses != sorted(verses) or not all(isinstance(v, int) and v >= 1 for v in verses):
            err(eid, f"verses 必須為升冪正整數陣列: {verses}")
        # 基本欄位
        lang = ent.get("lang")
        if lang not in LANG_SRC: err(eid, f"lang 必須是 he|el: {lang}"); continue
        if ent.get("category") not in CATEGORIES: err(eid, f"category 不在分類法: {ent.get('category')}")
        if ent.get("confidence") not in CONFIDENCE: err(eid, f"confidence 不合法: {ent.get('confidence')}")
        if not ent.get("title") or len(ent["title"]) > 30: warn(eid, "title 缺或過長（≤25字為佳）")
        if not ent.get("loss"): err(eid, "缺 loss")
        elif len(ent["loss"]) > 80: warn(eid, f"loss 過長（{len(ent['loss'])}字）")
        essay = ent.get("essay", "")
        if len(essay) < 300: err(eid, f"essay 過短（{len(essay)}字）")
        elif not 500 <= len(essay) <= 1600: warn(eid, f"essay 長度 {len(essay)} 字（建議600–1200）")
        # words
        words = ent.get("words", [])
        if not words: err(eid, "words 至少一個"); continue
        anchored = 0
        for w in words:
            for k in ("surface", "match", "translit", "gloss"):
                if not w.get(k): err(eid, f"word 缺 {k}: {w}")
            st = w.get("strongs")
            if st is not None and not re.fullmatch(r"[HG]\d{1,5}", st):
                err(eid, f"strongs 格式錯誤: {st}")
            v = w.get("verse")
            if v is None: continue
            anchored += 1
            if verses and v not in verses: err(eid, f"word verse {v} 不在 ref.verses {verses}")
            if not offline:
                try:
                    txt = verse_text(LANG_SRC[lang], ref["bookNo"], ch, v)
                except Offline as ex:
                    err(eid, str(ex)); continue
                if txt is None:
                    err(eid, f"{b['full']}{ch}:{v} 原文抓不到（節號錯？）")
                elif NORM[lang](w["match"]) .strip() not in NORM[lang](txt):
                    err(eid, f"match「{w['match']}」未命中 {LANG_SRC[lang]} {b['full']}{ch}:{v} 原文")
        if anchored == 0: err(eid, "至少一個 word 需錨定 verse")
        # cuvQuote
        if ent.get("cuvQuote") and not offline:
            cv = ent.get("cuvVerse") or (verses[0] if verses else None)
            try:
                txt = verse_text("CUV", ref["bookNo"], ch, cv) if cv else None
            except Offline as ex:
                err(eid, str(ex)); txt = "\x00none"
            if txt is None: err(eid, f"CUV {b['full']}{ch}:{cv} 抓不到")
            elif norm_cuv(ent["cuvQuote"]) not in norm_cuv(txt):
                err(eid, f"cuvQuote 未命中和合本 {b['full']}{ch}:{cv}")
        # crossRefs
        for cr in ent.get("crossRefs", []):
            cb = books.get(cr.get("bookNo"))
            if not cb: err(eid, f"crossRef bookNo 不合法: {cr}"); continue
            cch, cv = cr.get("chapter"), cr.get("verse")
            if not (isinstance(cch, int) and 1 <= cch <= cb["chapters"]):
                err(eid, f"crossRef 章超界: {cb['full']}{cch}"); continue
            if not offline and cr.get("match"):
                # crossRef 語言依 bookNo 判斷（1-39 舊約 he；40-66 新約 el）
                clang = "he" if cr["bookNo"] <= 39 else "el"
                try:
                    txt = verse_text(LANG_SRC[clang], cr["bookNo"], cch, cv)
                except Offline as ex:
                    err(eid, str(ex)); continue
                if txt is None: err(eid, f"crossRef {cb['full']}{cch}:{cv} 原文抓不到")
                elif NORM[clang](cr["match"]).strip() not in NORM[clang](txt):
                    err(eid, f"crossRef match「{cr['match']}」未命中 {cb['full']}{cch}:{cv}")

    for w in warns: print("WARN", w)
    if errors:
        for e in errors: print("ERR ", e)
        print(f"\nFAIL: {len(errors)} 個錯誤, {len(warns)} 個警告, 共 {len(entries)} 筆")
        sys.exit(1)
    print(f"ALL OK ({len(entries)} 筆條目, {len(warns)} 個警告)")

if __name__ == "__main__":
    main()
