# -*- coding: utf-8 -*-
"""journey.html 功能實測（無登入路徑）"""
import json, threading, http.server, socketserver, os, functools
from playwright.sync_api import sync_playwright

_CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
LAUNCH_KW = {"executable_path": _CH} if os.path.exists(_CH) else {}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo 根目錄
PORT = 8912

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

BASE = f"http://127.0.0.1:{PORT}/journey.html"
results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  — " + str(detail)) if detail else ""))

with sync_playwright() as p:
    browser = p.chromium.launch(**LAUNCH_KW)
    ctx = browser.new_context()
    page = ctx.new_page()

    errors, dialogs = [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append("console.error: " + m.text) if m.type == "error" else None)
    page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))

    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(600)

    # 1. 沒有 JS 執行期錯誤（排除 Firebase CDN 在容器內被擋掉的網路錯誤）
    real = [e for e in errors if "gstatic" not in e and "ERR_" not in e and "Failed to load resource" not in e]
    check("頁面載入無 JS 錯誤", not real, real[:3])

    # 2. 66 卷都渲染出來
    rows = page.locator("#bookList .book").count()
    check("渲染 66 卷書", rows == 66, f"實際 {rows}")

    # 3. 初始雙軌歸零
    check("初始書卷進度 0/66", page.locator("#stDone").inner_text() == "0/66")
    check("初始字數進度 0%", page.locator("#stCharPct").inner_text() == "0%")

    # 4. 容器內 Firebase CDN 被擋，應優雅降級不炸掉（登入路徑由 test_groups.py 覆蓋）
    gt = page.locator("#groupBody").inner_text()
    check("Firebase 無法載入時優雅降級", "雲端尚未設定" in gt or "登入" in gt, gt[:40])

    # 5. 核心：刷短卷會讓兩條進度條拉開差距（Goodhart 修正）
    data = json.loads(open(os.path.join(ROOT, "data", "book_journey.json"), encoding="utf-8").read())
    shortest = sorted(data["books"], key=lambda b: b["totalChars"])[:5]
    page.evaluate("ids => ids.forEach(id => toggleBook(id, true))", [b["id"] for b in shortest])
    page.wait_for_timeout(300)
    book_pct = float(page.locator("#stPct").inner_text().rstrip("%"))
    char_pct = float(page.locator("#stCharPct").inner_text().rstrip("%"))
    check("讀完 5 卷最短書：書卷進度 ≈7.6%", abs(book_pct - 7.6) < 0.3, f"{book_pct}%")
    check("讀完 5 卷最短書：字數進度 <1%", char_pct < 1.0, f"{char_pct}%")
    check("兩條進度條確實拉開差距", book_pct > char_pct * 5,
          f"書卷 {book_pct}% vs 字數 {char_pct}%")

    # 6. 進度寫進 localStorage，重整後還在
    page.reload(wait_until="networkidle"); page.wait_for_timeout(500)
    check("重整後進度保留", page.locator("#stDone").inner_text() == "5/66",
          page.locator("#stDone").inner_text())

    # 7. 推薦功能（無群組時退回原本行為）
    page.click("button:has-text('幫我挑一本現在能完成的')")
    page.wait_for_timeout(300)
    st = page.locator("#suggestText").inner_text()
    check("推薦功能可用", len(st) > 5 and "章" in st, st[:50])

    # 8. 從一年讀經計畫匯入：第268天含「俄巴底亞書＋約拿書1-4」。
    #    注意俄巴底亞書本身就是最短的書卷之一，前面已勾過，所以只會新增約拿書。
    plan = json.loads(open(os.path.join(ROOT, "data", "year_plan.json"), encoding="utf-8").read())
    covered = set(plan["days"][267])
    short_ids = {b["id"] for b in shortest}
    def whole(b):
        keys = [b["full"]] if b["chapters"] == 1 else [b["full"] + str(c) for c in range(1, b["chapters"] + 1)]
        return all(k in covered for k in keys)
    expect_new = [b for b in data["books"] if whole(b) and b["id"] not in short_ids]
    expect_total = len(short_ids) + len(expect_new)

    page.evaluate("localStorage.setItem('year365', JSON.stringify([267]))")
    page.reload(wait_until="networkidle"); page.wait_for_timeout(500)
    dialogs.clear()
    page.click("button:has-text('從一年讀經計畫匯入')")
    page.wait_for_timeout(900)
    msg = dialogs[-1] if dialogs else ""
    check("匯入第268天 → 帶入該天整卷讀完的書",
          all(b["full"] in msg for b in expect_new), msg.replace("\n", " ")[:60])
    check("已勾過的書不會重複匯入（俄巴底亞書）", "俄巴底亞書" not in msg, msg.replace("\n", " ")[:60])
    check(f"匯入後書卷數 {expect_total}/66",
          page.locator("#stDone").inner_text() == f"{expect_total}/66",
          page.locator("#stDone").inner_text())

    # 9. 重複匯入不應重複計算（冪等）
    dialogs.clear()
    page.click("button:has-text('從一年讀經計畫匯入')")
    page.wait_for_timeout(700)
    check("重複匯入不會重複計算",
          page.locator("#stDone").inner_text() == f"{expect_total}/66",
          page.locator("#stDone").inner_text())

    # 10. 取消勾選可以正常反向
    page.evaluate("toggleBook(%d, false)" % shortest[0]["id"])
    page.wait_for_timeout(250)
    check("取消勾選可反向",
          page.locator("#stDone").inner_text() == f"{expect_total - 1}/66",
          page.locator("#stDone").inner_text())

    # 11. 點書名 → 連到經文（index.html?ref=），不會打勾也不展開
    before = page.locator("#stDone").inner_text()
    row = page.locator('[data-book="1"]')
    href = row.locator(".blink").get_attribute("href")
    check("書名連到創世記第1章經文", href == "index.html?ref=" + "%E5%89%B51", href)
    jude = page.locator('[data-book="65"] .blink').get_attribute("href")
    check("單章書連結不帶章號（猶大書）", jude == "index.html?ref=%E7%8C%B6", jude)
    row.locator(".blink").click()
    page.wait_for_timeout(600)
    check("點書名會導到經文頁", "index.html?ref=" in page.url, page.url)
    page.go_back(); page.wait_for_timeout(600)
    check("點書名不會打勾", page.locator("#stDone").inner_text() == before, page.locator("#stDone").inner_text())

    browser.close()

httpd.shutdown()
passed = sum(1 for _, ok, _ in results if ok)
print(f"\n{'='*46}\n通過 {passed}/{len(results)}")
if passed != len(results):
    print("失敗項目：")
    for n, ok, d in results:
        if not ok:
            print(f"  - {n}: {d}")
    raise SystemExit(1)
print("全部通過 ✅")
