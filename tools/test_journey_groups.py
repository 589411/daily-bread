# -*- coding: utf-8 -*-
"""journey.html 群組邏輯實測：用假的 Firestore 驗證點燈、加入、退出的資料操作。
重點在驗證 update() 的 dotted path + arrayUnion/arrayRemove 語意有沒有用對。"""
import json, os, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

_CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
LAUNCH_KW = {"executable_path": _CH} if os.path.exists(_CH) else {}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo 根目錄
PORT = 8913
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

# 假的 Firebase：刻意複製真實 Firestore 的語意——
#   set(data,{merge:true}) 的 dotted key 是「字面欄位名」，不是路徑
#   update(patch)          的 dotted key 才是路徑
FAKE = r"""
window.__STORE__ = {};
(function(){
  function deepGet(o,p){return p.split('.').reduce((a,k)=>(a==null?a:a[k]),o);}
  function deepSet(o,p,v){const ks=p.split('.');let cur=o;
    for(let i=0;i<ks.length-1;i++){if(typeof cur[ks[i]]!=='object'||cur[ks[i]]==null)cur[ks[i]]={};cur=cur[ks[i]];}
    cur[ks[ks.length-1]]=v;}
  function applySentinel(cur,val){
    if(val&&val.__op==='arrayUnion'){const a=Array.isArray(cur)?cur.slice():[];val.v.forEach(x=>{if(!a.includes(x))a.push(x);});return a;}
    if(val&&val.__op==='arrayRemove'){const a=Array.isArray(cur)?cur.slice():[];return a.filter(x=>!val.v.includes(x));}
    if(val&&val.__op==='delete')return undefined;
    if(val&&val.__op==='increment')return (typeof cur==='number'?cur:0)+val.v;
    return val;
  }
  function docRef(path){
    return {
      _path:path,
      async get(){
        const d=window.__STORE__[path];
        return {exists:d!==undefined, data:()=>JSON.parse(JSON.stringify(d||{}))};
      },
      async set(data,opts){
        const merge=opts&&opts.merge;
        let base=merge?(window.__STORE__[path]||{}):{};
        base=JSON.parse(JSON.stringify(base));
        // 真實 set+merge：key 裡的點是字面欄位名，只做頂層淺合併
        Object.keys(data).forEach(k=>{base[k]=applySentinel(base[k],data[k]);});
        window.__STORE__[path]=base;
      },
      async update(patch){
        if(window.__STORE__[path]===undefined)throw new Error('No document to update: '+path);
        const base=JSON.parse(JSON.stringify(window.__STORE__[path]));
        Object.keys(patch).forEach(k=>{ // update：點 = 路徑
          const nv=applySentinel(deepGet(base,k),patch[k]);
          if(nv===undefined){const ks=k.split('.');const par=ks.length>1?deepGet(base,ks.slice(0,-1).join('.')):base;if(par)delete par[ks[ks.length-1]];}
          else deepSet(base,k,nv);
        });
        window.__STORE__[path]=base;
      },
      async delete(){delete window.__STORE__[path];},
      collection(sub){const parent=path;return {doc(id){return docRef(parent+'/'+sub+'/'+id);}};}
    };
  }
  let authCb=null;
  window.__signIn__=function(uid,email){window.__U__={uid:uid,email:email,isAnonymous:false};if(authCb)authCb(window.__U__);};
  window.__signOut__=function(){window.__U__=null;if(authCb)authCb(null);};
  window.firebase={
    initializeApp(){},
    auth(){return{
      onAuthStateChanged(cb){authCb=cb;setTimeout(()=>cb(window.__U__||null),0);},
      signOut(){window.__signOut__();},
      signInWithPopup(){return Promise.resolve();},
      get currentUser(){return window.__U__||null;}
    };},
    firestore(){return{collection(c){return{doc(id){return docRef(c+'/'+id);}};}};}
  };
  window.firebase.auth.GoogleAuthProvider=function(){};
  window.firebase.firestore.FieldValue={
    arrayUnion:(...v)=>({__op:'arrayUnion',v:v}),
    arrayRemove:(...v)=>({__op:'arrayRemove',v:v}),
    increment:(v)=>({__op:'increment',v:v}),
    delete:()=>({__op:'delete'})
  };
})();
"""

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  — " + str(detail)) if detail else ""))

data = json.load(open(os.path.join(ROOT, "data", "book_journey.json"), encoding="utf-8"))
JONAH = next(b for b in data["books"] if b["full"] == "約拿書")
NAHUM = next(b for b in data["books"] if b["full"] == "那鴻書")
ISAIAH = next(b for b in data["books"] if b["full"] == "以賽亞書")

with sync_playwright() as p:
    browser = p.chromium.launch(**LAUNCH_KW)
    page = browser.new_context().new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    # 有網路時真的 Firebase SDK 會從 CDN 載入並蓋掉假的 window.firebase，所以擋掉
    page.route("**/firebasejs/**", lambda r: r.fulfill(status=200, content_type="text/javascript", body=""))
    page.add_init_script(FAKE)
    page.add_init_script("window.prompt=(m,d)=>window.__PROMPT__||'測試團契';window.confirm=()=>true;window.alert=()=>{};")
    page.goto(f"http://127.0.0.1:{PORT}/journey.html", wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    # 1. 假 Firebase 生效 → 未登入時應顯示 Google 登入提示
    gt = page.locator("#groupBody").inner_text()
    check("未登入顯示 Google 登入提示", "Google 登入" in gt, gt[:40])

    # 2. 登入後、還沒有群組 → 顯示建立群組引導
    page.evaluate("window.__signIn__('U1','joseph@example.com')")
    page.wait_for_timeout(400)
    gt = page.locator("#groupBody").inner_text()
    check("登入後顯示建立群組引導", "建立群組" in gt, gt[:40])

    # 3. 先讀完約拿書（本地＋雲端）
    page.evaluate(f"toggleBook({JONAH['id']}, true)")
    page.wait_for_timeout(400)
    store = page.evaluate("window.__STORE__")
    check("個人進度寫入 users 文件",
          JONAH["id"] in (store.get("users/U1", {}).get("journeyBooks") or []),
          store.get("users/U1", {}).get("journeyBooks"))
    check("不會蓋掉 year.html 的欄位（用 merge）",
          "journeyBooks" in store.get("users/U1", {}), list(store.get("users/U1", {}).keys()))

    # 4. 建立群組 → 已讀的書要立刻回填成點亮
    page.evaluate("window.__PROMPT__='公司團契'")
    page.evaluate("createGroup()")
    page.wait_for_timeout(700)
    store = page.evaluate("window.__STORE__")
    gkey = [k for k in store if k.startswith("groups/") and k.count("/") == 1]
    check("群組文件已建立", len(gkey) == 1, gkey)
    gid = gkey[0].split("/")[1]
    gdoc = store[gkey[0]]
    check("群組名稱正確", gdoc.get("name") == "公司團契", gdoc.get("name"))
    check("建群時回填已讀書卷（約拿書亮起）",
          gdoc.get("coverage", {}).get(f"b{JONAH['id']}") == ["U1"],
          gdoc.get("coverage"))
    check("myGroups 記錄群組", gid in (store.get("users/U1", {}).get("myGroups") or []),
          store.get("users/U1", {}).get("myGroups"))

    # 5. 再讀一卷 → update() 的 dotted path 必須真的寫成巢狀，不能變成字面欄位名
    page.evaluate(f"toggleBook({NAHUM['id']}, true)")
    page.wait_for_timeout(600)
    gdoc = page.evaluate("window.__STORE__")[f"groups/{gid}"]
    check("點燈寫入巢狀 coverage（dotted path 正確）",
          gdoc.get("coverage", {}).get(f"b{NAHUM['id']}") == ["U1"],
          gdoc.get("coverage", {}).get(f"b{NAHUM['id']}"))
    check("沒有產生字面欄位名 'coverage.bN'",
          not any("." in k for k in gdoc.keys()), [k for k in gdoc.keys() if "." in k])

    # 6. 取消勾選 → arrayRemove 要把自己移掉
    page.evaluate(f"toggleBook({NAHUM['id']}, false)")
    page.wait_for_timeout(600)
    gdoc = page.evaluate("window.__STORE__")[f"groups/{gid}"]
    check("取消勾選會從 coverage 移除",
          gdoc.get("coverage", {}).get(f"b{NAHUM['id']}") == [],
          gdoc.get("coverage", {}).get(f"b{NAHUM['id']}"))

    # 7. 模擬另一位成員讀了以賽亞書 → 我沒讀，但地圖要亮，且不該標「群組還沒人讀」
    page.evaluate(f"""
      window.__STORE__['groups/{gid}'].coverage['b{ISAIAH['id']}']=['U2'];
      window.__STORE__['groups/{gid}'].memberCount=2;
    """)
    page.evaluate(f"(async()=>{{await loadGroup('{gid}');renderGroups();render();}})()")
    page.wait_for_timeout(500)
    lit = page.evaluate("[...LIT]")
    check("別人讀的書也會點亮地圖", ISAIAH["id"] in lit, f"lit={sorted(lit)}")
    row = page.locator(f'[data-book="{ISAIAH["id"]}"]').inner_text()
    check("已被別人點亮的書不標『群組還沒人讀』", "群組還沒人讀" not in row, row[:40])
    nrow = page.locator(f'[data-book="{NAHUM["id"]}"]').inner_text()
    check("沒人讀過的書標示『群組還沒人讀』", "群組還沒人讀" in nrow, nrow[:40])

    # 8. 群組看板數字
    gt = page.locator("#groupBody").inner_text()
    check("看板顯示已點亮數與人數", "2" in gt and "一起讀的人" in gt, gt.replace("\n", " ")[:70])
    check("看板不顯示任何成員身分", "U1" not in gt and "U2" not in gt and "example.com" not in gt,
          gt.replace("\n", " ")[:60])

    # 9. 推薦應優先挑「群組還沒人讀」且最短的一卷
    page.evaluate("suggestEasy()")
    page.wait_for_timeout(400)
    st = page.locator("#suggestText").inner_text()
    check("推薦優先補群組空白", "群組還沒有人讀過" in st, st[:60])

    # 9b. 「我正在讀」預約：淺色、不顯示是誰、上限 2 卷、讀完自動清掉、別人的標記影響推薦
    OBAD = next(b for b in data["books"] if b["full"] == "俄巴底亞書")
    J2 = next(b for b in data["books"] if b["full"] == "約翰二書")
    J3 = next(b for b in data["books"] if b["full"] == "約翰三書")
    page.evaluate(f"setReading({NAHUM['id']}, true)")
    page.wait_for_timeout(500)
    store = page.evaluate("window.__STORE__")
    rd = store[f"groups/{gid}"].get("reading", {})
    exp = (rd.get(f"b{NAHUM['id']}") or {}).get("U1")
    check("標記正在讀寫入群組 reading 巢狀欄位", isinstance(exp, (int, float)), rd)
    days = round((exp - page.evaluate("Date.now()")) / 86400000)
    check("期限依長度計算（3章→最少7天）", days == 7, days)
    check("正在讀存在 users.journeyReading 陣列",
          [r["id"] for r in store["users/U1"].get("journeyReading", [])] == [NAHUM["id"]],
          store["users/U1"].get("journeyReading"))
    cls = page.locator(f'.gcell[title^="{NAHUM["full"]}"]').get_attribute("class")
    check("看板該格顯示淺色 reading", "reading" in cls, cls)
    page.evaluate(f"setReading({J2['id']}, true)"); page.wait_for_timeout(400)
    page.evaluate(f"setReading({J3['id']}, true)"); page.wait_for_timeout(400)
    ids = page.evaluate("READING.map(r=>r.id)")
    check("同時最多 2 卷", len(ids) == 2 and J3["id"] not in ids, ids)
    page.evaluate(f"setReading({J2['id']}, false)"); page.wait_for_timeout(500)
    store = page.evaluate("window.__STORE__")
    rd = store[f"groups/{gid}"].get("reading", {})
    check("取消正在讀會刪掉 key（不留空物件的 uid）", "U1" not in (rd.get(f"b{J2['id']}") or {}), rd)
    check("取消後 users.journeyReading 真的移除（陣列不被 merge 合併）",
          J2["id"] not in [r["id"] for r in store["users/U1"].get("journeyReading", [])],
          store["users/U1"].get("journeyReading"))
    page.evaluate(f"toggleBook({NAHUM['id']}, true)"); page.wait_for_timeout(700)
    store = page.evaluate("window.__STORE__")
    check("讀完該卷自動清掉正在讀", NAHUM["id"] not in page.evaluate("READING.map(r=>r.id)")
          and "U1" not in (store[f"groups/{gid}"].get("reading", {}).get(f"b{NAHUM['id']}") or {}),
          store[f"groups/{gid}"].get("reading"))
    page.evaluate(f"toggleBook({NAHUM['id']}, false)"); page.wait_for_timeout(600)
    # 別人正在讀俄巴底亞書（最短的未讀書之一）→ 標「有人在讀」、推薦跳過它；過期的不算
    page.evaluate(f"""
      const g=window.__STORE__['groups/{gid}']; g.reading=g.reading||{{}};
      g.reading['b{OBAD['id']}']={{U2:Date.now()+5*86400000}};
      g.reading['b{J2['id']}']={{U2:Date.now()-1000}};
    """)
    page.evaluate(f"(async()=>{{await loadGroup('{gid}');renderGroups();render();}})()")
    page.wait_for_timeout(400)
    orow = page.locator(f'[data-book="{OBAD["id"]}"]').inner_text()
    check("別人正在讀的書標『有人在讀』且不標『群組還沒人讀』", "有人在讀" in orow and "群組還沒人讀" not in orow, orow[:40])
    j2row = page.locator(f'[data-book="{J2["id"]}"]').inner_text()
    check("過期的正在讀不顯示", "有人在讀" not in j2row, j2row[:40])
    gt = page.locator("#groupBody").inner_text()
    check("正在讀也不顯示成員身分", "U2" not in gt and "example.com" not in gt)
    page.evaluate("suggestEasy()"); page.wait_for_timeout(300)
    st = page.locator("#suggestText").inner_text()
    check("推薦跳過別人正在讀的書", OBAD["full"] not in st, st[:40])
    page.evaluate(f"setReading({J3['id']}, true)"); page.wait_for_timeout(400)

    # 10. 退出群組 → 自己的痕跡全部移除，但別人的保留、個人進度不變
    page.evaluate("leaveGroup()")
    page.wait_for_timeout(800)
    store = page.evaluate("window.__STORE__")
    gdoc = store.get(f"groups/{gid}", {})
    cov = gdoc.get("coverage", {})
    mine_left = [k for k, v in cov.items() if isinstance(v, list) and "U1" in v]
    check("退出後自己的點燈全部移除", not mine_left, mine_left)
    # 步驟 6 取消勾選那鴻書留下的空陣列不算（那是 toggle 路徑）；退出本身不該再製造空陣列
    empties = [k for k, v in cov.items() if v == [] and k != f"b{NAHUM['id']}"]
    check("退出後不留空陣列 key", not empties, empties[:5])
    rd = gdoc.get("reading", {})
    check("退出後自己的正在讀全部移除", not any("U1" in (v or {}) for v in rd.values()), rd)
    check("退出後別人的點燈保留", cov.get(f"b{ISAIAH['id']}") == ["U2"], cov.get(f"b{ISAIAH['id']}"))
    check("退出後 memberCount 減一", gdoc.get("memberCount") == 1, gdoc.get("memberCount"))
    check("退出後個人進度不受影響",
          page.locator("#stDone").inner_text() == "1/66", page.locator("#stDone").inner_text())
    check("退出後 myGroups 已移除", gid not in (store.get("users/U1", {}).get("myGroups") or []),
          store.get("users/U1", {}).get("myGroups"))

    check("全程無 JS 錯誤", not errs, errs[:3])
    browser.close()

httpd.shutdown()
passed = sum(1 for _, ok, _ in results if ok)
print(f"\n{'='*46}\n通過 {passed}/{len(results)}")
if passed != len(results):
    print("失敗項目：")
    for n, ok, d in results:
        if not ok: print(f"  - {n}: {d}")
    raise SystemExit(1)
print("全部通過 ✅")
