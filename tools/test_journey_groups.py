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
          deepSet(base,k,applySentinel(deepGet(base,k),patch[k]));
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
    increment:(v)=>({__op:'increment',v:v})
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

    # 10. 退出群組 → 自己的痕跡全部移除，但別人的保留、個人進度不變
    page.evaluate("leaveGroup()")
    page.wait_for_timeout(800)
    store = page.evaluate("window.__STORE__")
    gdoc = store.get(f"groups/{gid}", {})
    cov = gdoc.get("coverage", {})
    mine_left = [k for k, v in cov.items() if isinstance(v, list) and "U1" in v]
    check("退出後自己的點燈全部移除", not mine_left, mine_left)
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
