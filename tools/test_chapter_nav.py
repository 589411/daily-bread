# -*- coding: utf-8 -*-
"""index.html 前一章／後一章按鈕實測（需連得到 bolls.life）。執行：python3 tools/test_chapter_nav.py"""
import os,sys,threading,http.server,socketserver,functools
from playwright.sync_api import sync_playwright
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory=os.path.dirname(os.path.dirname(os.path.abspath(__file__))));H.log_message=lambda *a:None
socketserver.TCPServer.allow_reuse_address=True
s=socketserver.TCPServer(("127.0.0.1",8923),H);threading.Thread(target=s.serve_forever,daemon=True).start()
R=[]
def ck(n,ok,d=""):R.append(ok);print(("PASS " if ok else "FAIL ")+n,d)
def title(pg):return pg.locator("#devTitle").inner_text()
def navtxt(pg):
    # 等經文區換成目前標題那一章（避免讀到上一章殘留）
    pg.wait_for_function("()=>{const t=document.getElementById('devTitle').textContent;const n=document.querySelector('.ch-nav');const r=document.getElementById('bibleArea').dataset.req||'';return n&&t&&r.split('#')[0]===(READ_REF?READ_REF.p.abbr+READ_REF.p.ch:r.split('#')[0])}",timeout=20000)
    pg.wait_for_timeout(200);return pg.locator(".ch-nav").inner_text().replace("\n"," ")
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={"width":400,"height":900});errs=[]
  pg.on("pageerror",lambda e:errs.append(str(e)))
  pg.goto("http://127.0.0.1:8923/index.html?ref=%E5%89%B51");t=navtxt(pg)
  ck("創1 只有後一章",("後一章" in t) and ("前一章" not in t),t)
  pg.click("text=後一章");pg.wait_for_timeout(1500);t=navtxt(pg)
  ck("點後一章 → 創2",("2" in title(pg)) and "創世記 1" in t and "創世記 3" in t, title(pg)+" | "+t)
  ck("網址更新", "ref=%E5%89%B52" in pg.url, pg.url)
  ck("章節選單同步", pg.locator("#jbCh").input_value()=="2")
  pg.click("text=前一章");pg.wait_for_timeout(1500);navtxt(pg)
  ck("點前一章 → 創1", "1" in title(pg) and "2" not in title(pg), title(pg))
  pg.goto("http://127.0.0.1:8923/index.html?ref=%E7%91%AA4");t=navtxt(pg)
  ck("瑪4 後一章跨卷到馬太福音 1","馬太福音 1" in t,t)
  pg.goto("http://127.0.0.1:8923/index.html?ref=%E7%8C%B6");t=navtxt(pg)
  ck("猶大書 前→約翰三書(單章不帶號)、後→啟示錄 1","約翰三書" in t and "啟示錄 1" in t,t)
  pg.goto("http://127.0.0.1:8923/index.html?ref=%E5%95%9F22");t=navtxt(pg)
  ck("啟22 沒有後一章","後一章" not in t,t)
  pg.goto("http://127.0.0.1:8923/index.html");t=navtxt(pg)
  before=title(pg); pg.click("text=後一章");pg.wait_for_timeout(500);navtxt(pg)
  ck("每日進度模式按後一章 → 切到閱讀聖經",pg.locator("#pickerBlock").is_visible() and title(pg)!=before, before+" → "+title(pg))
  ck("無 JS 錯誤",not errs,errs[:2])
  b.close()
print("通過",sum(R),"/",len(R))
if sum(R)!=len(R): raise SystemExit(1)
