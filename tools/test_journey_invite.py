# -*- coding: utf-8 -*-
"""journey.html 邀請連結（?join=CODE）實測：點連結 →（登入）→ 按一次加入。
沿用 test_journey_groups.py 的假 Firestore。執行：python3 tools/test_journey_invite.py"""
import os, re, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE = re.search(r'FAKE = r"""(.*?)"""',
                 open(os.path.join(ROOT, "tools", "test_journey_groups.py"), encoding="utf-8").read(), re.S).group(1)
PORT = 8914
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
Handler.log_message = lambda *a: None
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

CODE = "ABCD2345"
SEED = """
window.__STORE__['groups/%s']={name:'青年小組',ownerUid:'U9',createdAt:1,memberCount:1,coverage:{b1:['U9']}};
""" % CODE

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  — " + str(detail)) if detail else ""))

def new_page(browser, signed_uid=None, extra=""):
    ctx = browser.new_context()
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/firebasejs/**", lambda r: r.fulfill(status=200, content_type="text/javascript", body=""))
    pg.add_init_script(FAKE)
    pg.add_init_script(SEED + extra)
    pg.add_init_script("window.prompt=(m,d)=>d||'';window.confirm=()=>true;window.alert=()=>{};")
    if signed_uid:
        pg.add_init_script("window.__U__={uid:'%s',email:'%s@x.y',isAnonymous:false};" % (signed_uid, signed_uid))
    return pg, errs

def card(pg):
    c = pg.locator("#joinCard")
    return "" if c.get_attribute("hidden") is not None else c.inner_text()

with sync_playwright() as p:
    browser = p.chromium.launch()
    url = f"http://127.0.0.1:{PORT}/journey.html?join={CODE.lower()}&openExternalBrowser=1"

    # 1. 未登入點連結 → 顯示邀請卡＋「用 Google 登入並加入」，網址參數清掉
    pg, errs = new_page(browser)
    pg.goto(url); pg.wait_for_timeout(600)
    t = card(pg)
    check("未登入：顯示邀請卡", "邀請" in t, t[:30])
    check("未登入：按鈕是「用 Google 登入並加入」", "用 Google 登入並加入" in t)
    check("網址的 join/openExternalBrowser 參數已清掉", "join=" not in pg.url and "openExternal" not in pg.url, pg.url)

    # 2. 重新整理（登入過程可能重載）→ 邀請還在
    pg.goto(f"http://127.0.0.1:{PORT}/journey.html"); pg.wait_for_timeout(600)
    check("重新整理後邀請仍在", "用 Google 登入並加入" in card(pg))

    # 3. 按「登入並加入」→ 登入完成自動加入
    pg.click("text=用 Google 登入並加入")
    pg.evaluate("window.__signIn__('U2','u2@x.y')"); pg.wait_for_timeout(1200)
    st = pg.evaluate("window.__STORE__")
    g = st.get(f"groups/{CODE}", {})
    check("登入後自動加入：memberCount=2", g.get("memberCount") == 2, g.get("memberCount"))
    check("登入後自動加入：myGroups 有群組", CODE in (st.get("users/U2", {}).get("myGroups") or []))
    check("加入後切到該群組", pg.evaluate("CURGROUP") == CODE)
    check("加入後邀請卡收起、pending 清掉",
          card(pg) == "" and pg.evaluate("localStorage.getItem('journeyPendingJoin')") is None)
    check("無 JS 錯誤（情境 1-3）", not errs, errs[:2])
    pg.context.close()

    # 4. 已登入點連結 → 顯示群組名＋「加入群組」，不會自動加入；按了才加入
    pg, errs = new_page(browser, "U3")
    pg.goto(url); pg.wait_for_timeout(900)
    t = card(pg)
    check("已登入：卡片顯示群組名", "青年小組" in t, t[:30])
    check("已登入：不會自動加入", pg.evaluate("window.__STORE__")[f"groups/{CODE}"]["memberCount"] == 1)
    pg.click("#joinCard >> text=加入群組"); pg.wait_for_timeout(900)
    g = pg.evaluate("window.__STORE__")[f"groups/{CODE}"]
    check("按「加入群組」後加入", g["memberCount"] == 2 and pg.evaluate("CURGROUP") == CODE, g["memberCount"])
    check("無 JS 錯誤（情境 4）", not errs, errs[:2])
    pg.context.close()

    # 5. 已經是成員 → 直接切過去，不重複加入
    already = "window.__STORE__['users/U9']={myGroups:['%s']};" % CODE
    pg, errs = new_page(browser, "U9", already)
    pg.goto(url); pg.wait_for_timeout(900)
    g = pg.evaluate("window.__STORE__")[f"groups/{CODE}"]
    check("已是成員：不重複計算人數", g["memberCount"] == 1, g["memberCount"])
    check("已是成員：邀請卡收起", card(pg) == "")
    pg.context.close()

    # 6. 群組不存在（被刪了）→ 清掉邀請、不加入
    pg, errs = new_page(browser, "U4")
    pg.goto(f"http://127.0.0.1:{PORT}/journey.html?join=ZZZZ9999"); pg.wait_for_timeout(900)
    check("失效邀請：卡片收起", card(pg) == "")
    check("失效邀請：沒有寫入 myGroups", not (pg.evaluate("window.__STORE__").get("users/U4", {}).get("myGroups")))
    pg.context.close()

    # 7. 「先不要」→ 清掉
    pg, errs = new_page(browser)
    pg.goto(url); pg.wait_for_timeout(600)
    pg.click("#joinCard >> text=先不要"); pg.wait_for_timeout(200)
    check("先不要：卡片收起且不再出現",
          card(pg) == "" and pg.evaluate("localStorage.getItem('journeyPendingJoin')") is None)

    # 8. 邀請訊息用連結、帶 openExternalBrowser
    link = pg.evaluate("inviteLink('%s')" % CODE)
    check("邀請連結帶 join 與 openExternalBrowser=1",
          link == "https://daily-bread.launchdock.app/journey.html?join=%s&openExternalBrowser=1" % CODE, link)
    pg.context.close()
    browser.close()

httpd.shutdown()
print(f"\n{'='*46}\n通過 {sum(results)}/{len(results)}")
if sum(results) != len(results):
    raise SystemExit(1)
print("全部通過 ✅")
