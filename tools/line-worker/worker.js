// =====================================================================
//  Cloudflare Worker — LINE「每日靈糧」讀經進度
//
//  ★ 主要模式：關鍵字自動回覆（reply）——在群組/聊天輸入含「每日靈糧」的訊息，
//    bot 就回覆當天讀經進度。reply 訊息「不計入」LINE 每月訊息額度 → 完全免費、
//    不管群組人數多少、發幾次都零成本。這是本 Worker 目前的主力功能。
//
//  ⚠️ 每日「主動推播」(scheduled push) 已停用：LINE 免費方案每月僅 200 則，
//    且「推到群組＝按群組人數計費」（4 群 59 人 → 每天 59 則，3~4 天就用罄、之後靜默被擋）。
//    故已移除 Cron Trigger。scheduled() 與 ?send=1 程式保留，僅供升級付費方案後手動/重新啟用。
//    詳見同資料夾 README.md 與專案 CLAUDE.md §13。
//
//  必要環境變數（Worker Secret，不進 repo）：
//    LINE_TOKEN           = Channel access token（push/reply 用）
//  建議環境變數：
//    LINE_CHANNEL_SECRET  = Channel secret（驗證 webhook 簽章，防偽造）
//    GROUP_ID             = 主群組 groupId（沒綁 KV 或想固定保留一個時用）
//  必要繫結（Binding）：
//    GROUPS               = KV Namespace（存自動註冊的群組清單）。沒綁也能跑。
//
//  LINE Webhook URL 設成本 Worker 網址、開啟 Use webhook（收關鍵字訊息與 join/leave）。
// =====================================================================
const SITE = "https://daily-bread.launchdock.app";
const BGN = {"創":"創世記","出":"出埃及記","利":"利未記","民":"民數記","申":"申命記","書":"約書亞記","士":"士師記","得":"路得記","撒上":"撒母耳記上","撒下":"撒母耳記下","王上":"列王紀上","王下":"列王紀下","代上":"歷代志上","代下":"歷代志下","拉":"以斯拉記","尼":"尼希米記","斯":"以斯帖記","伯":"約伯記","詩":"詩篇","箴":"箴言","傳":"傳道書","歌":"雅歌","賽":"以賽亞書","耶":"耶利米書","哀":"耶利米哀歌","結":"以西結書","但":"但以理書","何":"何西阿書","珥":"約珥書","摩":"阿摩司書","俄":"俄巴底亞書","拿":"約拿書","彌":"彌迦書","鴻":"那鴻書","哈":"哈巴谷書","番":"西番雅書","該":"哈該書","亞":"撒迦利亞書","瑪":"瑪拉基書","太":"馬太福音","可":"馬可福音","路":"路加福音","約":"約翰福音","徒":"使徒行傳","羅":"羅馬書","林前":"哥林多前書","林後":"哥林多後書","加":"加拉太書","弗":"以弗所書","腓":"腓立比書","西":"歌羅西書","帖前":"帖撒羅尼迦前書","帖後":"帖撒羅尼迦後書","提前":"提摩太前書","提後":"提摩太後書","多":"提多書","門":"腓利門書","來":"希伯來書","雅":"雅各書","彼前":"彼得前書","彼後":"彼得後書","約壹":"約翰一書","約貳":"約翰二書","約參":"約翰三書","猶":"猶大書","啟":"啟示錄"};
const ABBR = Object.keys(BGN).sort((a,b)=>b.length-a.length);
const SINGLE = {"俄":1,"門":1,"約貳":1,"約參":1,"猶":1};

function parseRef(s){
  s=(s||"").trim();
  let verses=""; const pv=s.match(/[（(]([^）)]*)[）)]/);
  if(pv){ verses=pv[1]; s=s.replace(/[（(][^）)]*[）)]/,"").trim(); }
  for(const k of ABBR){ if(s.startsWith(k)){ const ch=parseInt(s.slice(k.length).replace(/[章篇]/g,""))||1; return {abbr:k,full:BGN[k],ch,verses,single:!!SINGLE[k]}; } }
  return null;
}
const ytKey = p => p.full + (p.single?"":p.ch);
const label = p => p.full + (p.single?"":p.ch + (p.abbr==="詩"?"篇":"章")) + (p.verses?`（${p.verses}）`:"");

// 站上 JSON 取用（Cloudflare 邊緣快取 10 分鐘，避免每則回覆都回源、確保 1 分鐘內回得完）
const getJSON = path => fetch(SITE+path, {cf:{cacheTtl:600, cacheEverything:true}}).then(r=>r.json());
const today8 = () => new Date(Date.now()+8*3600*1000).toISOString().slice(0,10);   // 台北日期
const mdOf = k => `${parseInt(k.slice(5,7))}/${parseInt(k.slice(8,10))}`;

async function buildMsg(){
  const today = today8();
  const sched = await getJSON("/data/schedule.json");
  const yt    = await getJSON("/data/yt_map.json");
  const d = sched[today];
  if(!d) return null;
  const p = parseRef(d.d), lab = p?label(p):d.d, vid = p?yt[ytKey(p)]:"";
  const md = mdOf(today);
  let msg = `📖 ${md} 每日靈糧\n靈修進度：${lab}`;
  if(vid) msg += `\n📺 https://youtu.be/${vid}`;
  msg += `\n🗺️ 歷史地圖 https://atlas.launchdock.app/engine/?ref=${encodeURIComponent(d.d)}`;
  msg += `\n（速讀5章：${d.s5}　速讀10章：${d.s10}）\n🔗 ${SITE}/`;
  return msg;
}

/* ===== 經文參照查詢：輸入「彼前5」→ 回覆該章讀經進度 =====================
   刻意採「整則訊息就是參照」的嚴格比對：訊息必須以書卷簡稱／全名開頭、其後只剩數字。
   所以「我們約3點見面」「今天讀彼前5嗎」都不會觸發，只有單獨傳「約3」才可能誤中（已知殘餘風險）。
   非單章書一定要帶章號：單獨一個「書」「傳」「可」不觸發，避免日常用字被當成經文。 */
const toHalf = s => s.replace(/[０-９]/g, c=>String.fromCharCode(c.charCodeAt(0)-0xFEE0));

// 第一關：只靠 worker 內建的書卷表判形狀，**不連網**。閒聊訊息在這裡就被擋掉，不浪費請求。
// 回 {abbr,full,ch,single} 或 null。
const REF_KEYS = Object.entries(BGN)
  .flatMap(([abbr, full]) => [[full, abbr], [abbr, abbr]])
  .sort((a,b) => b[0].length - a[0].length);   // 長的先比，避免「約」吃掉「約壹」、「詩」吃掉「詩篇」
function quickRef(text){
  let s = toHalf(String(text||"")).replace(/[\s　]/g,"");
  if(!s || s.length > 14) return null;
  s = s.replace(/^第/,"").replace(/[章篇]$/,"");
  for(const [k, abbr] of REF_KEYS){
    if(!s.startsWith(k)) continue;
    const rest = s.slice(k.length).replace(/^第/,"").replace(/[章篇]$/,"");
    const single = !!SINGLE[abbr];
    if(rest === "") return single ? {abbr, full:BGN[abbr], ch:1, single} : null;  // 單獨一個「書」「傳」不觸發
    if(!/^\d+$/.test(rest)) return null;        // 「約3點見面」→ rest 不是純數字 → 不理
    return {abbr, full:BGN[abbr], ch:parseInt(rest), single};
  }
  return null;
}
// 第二關：用 bible_books.json 驗章數。回 {…} 或 {err:"…"}；形狀就不對則回 null。
function parseRefStrict(text, books){
  const p = quickRef(text); if(!p) return null;
  const b = (books||[]).find(x => x.abbr === p.abbr); if(!b) return p;
  if(p.single) return p.ch === 1 ? p : {err:`${b.full}只有一章喔。`};
  if(p.ch < 1 || p.ch > b.chapters) return {err:`${b.full}只有 ${b.chapters} 章喔。`};
  return p;
}

// 這一章在排程裡是哪幾天的靈修進度（詩119 之類會分多天）
function schedDays(sched, books, p){
  const bid = (books.find(b=>b.abbr===p.abbr)||{}).id;
  const out = [];
  for(const k of Object.keys(sched)){
    const q = parseRef(sched[k].d);
    if(!q) continue;
    const qid = (books.find(b=>b.abbr===q.abbr)||{}).id;
    if(qid === bid && (p.single || q.ch === p.ch)) out.push(k);
  }
  return out.sort();
}

async function buildRefMsg(p){
  const [yt, sched, books, eggs] = await Promise.all([
    getJSON("/data/yt_map.json"),
    getJSON("/data/schedule.json"),
    getJSON("/data/bible_books.json"),
    getJSON("/insight/data/insights.json").catch(()=>[]),
  ]);
  const ref = p.abbr + (p.single ? "" : p.ch);
  let msg = `📖 ${p.full}${p.single?"":p.ch + (p.abbr==="詩"?"篇":"章")}`;

  const days = schedDays(sched, books, p);
  if(days.length){
    const today = today8();
    const future = days.filter(k => k >= today);
    const pick = future[0] || days[days.length-1];
    const many = days.length > 1 ? `（分 ${days.length} 天）` : "";
    msg += future.length ? `\n🗓 ${mdOf(pick)} 的靈修進度${many}`
                         : `\n🗓 ${mdOf(pick)} 已讀過${many}`;
  }
  const vid = yt[p.full + (p.single?"":p.ch)];
  if(vid) msg += `\n📺 https://youtu.be/${vid}`;
  msg += `\n🗺️ 歷史地圖 https://atlas.launchdock.app/engine/?ref=${encodeURIComponent(ref)}`;
  const bid = (books.find(b=>b.abbr===p.abbr)||{}).id;
  const egg = (eggs||[]).find(e => e.ref && e.ref.bookNo===bid && e.ref.chapter===p.ch);
  if(egg) msg += `\n🥚 原文彩蛋：${egg.title}\n${SITE}/insight.html#${egg.id}`;
  msg += `\n🔗 ${SITE}/index.html?ref=${encodeURIComponent(ref)}`;
  return msg;
}

// 推播名單＝KV 清單 ∪ 固定的 GROUP_ID（去重）
async function listGroups(env){
  let ids = [];
  if(env.GROUPS){ const v = await env.GROUPS.get("ids"); if(v) ids = JSON.parse(v); }
  if(env.GROUP_ID) ids.push(env.GROUP_ID);
  return [...new Set(ids)];
}
async function saveKV(env, ids){ if(env.GROUPS) await env.GROUPS.put("ids", JSON.stringify([...new Set(ids)])); }

function linePost(env, path, payload){
  return fetch("https://api.line.me/v2/bot/message/"+path, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":"Bearer "+env.LINE_TOKEN },
    body: JSON.stringify(payload)
  });
}

// 驗證 LINE webhook 簽章（HMAC-SHA256，需 LINE_CHANNEL_SECRET）
async function verifySig(env, sig, bodyText){
  if(!env.LINE_CHANNEL_SECRET) return true; // 未設則略過（強烈建議設）
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(env.LINE_CHANNEL_SECRET), {name:"HMAC",hash:"SHA-256"}, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(bodyText));
  const b64 = btoa(String.fromCharCode(...new Uint8Array(mac)));
  return b64 === sig;
}

export default {
  async scheduled(event, env, ctx){
    const msg = await buildMsg(); if(!msg) return;
    const groups = await listGroups(env);
    ctx.waitUntil(Promise.all(groups.map(g => linePost(env, "push", {to:g, messages:[{type:"text", text:msg}]}))));
  },

  async fetch(req, env, ctx){
    const url = new URL(req.url);

    // ── LINE webhook：自動註冊／移除群組 ──
    if(req.method === "POST"){
      const body = await req.text();
      if(!(await verifySig(env, req.headers.get("x-line-signature")||"", body)))
        return new Response("bad signature", {status:401});
      let data; try{ data = JSON.parse(body); }catch(e){ return new Response("ok"); }
      let kv = []; if(env.GROUPS){ const v = await env.GROUPS.get("ids"); if(v) kv = JSON.parse(v); }
      let changed = false;
      for(const ev of (data.events||[])){
        // ── 關鍵字自動回覆：輸入含「每日靈糧」→ 回覆當天進度（reply 免費、不計額度）──
        if(ev.type === "message" && ev.message && ev.message.type === "text" && ev.replyToken){
          const text = ev.message.text || "";
          if(text.includes("每日靈糧")){
            const msg = await buildMsg();
            ctx.waitUntil(linePost(env, "reply", {replyToken:ev.replyToken, messages:[{type:"text", text: msg || "今天沒有排程資料。"}]}));
          }else if(quickRef(text)){
            // ── 經文參照查詢：整則訊息就是「彼前5」這種參照才回，其餘一律安靜 ──
            // quickRef 已在本地擋掉閒聊，走到這裡才連網驗章數。
            const books = await getJSON("/data/bible_books.json").catch(()=>[]);
            const p = parseRefStrict(text, books);
            if(p){
              const msg = p.err ? p.err : await buildRefMsg(p);
              ctx.waitUntil(linePost(env, "reply", {replyToken:ev.replyToken, messages:[{type:"text", text:msg}]}));
            }
          }
          continue;
        }
        // ── 群組加入／離開：維護 KV 名單（保留備用；目前不主動推播，無害）──
        const gid = ev.source && ev.source.groupId; if(!gid) continue;
        if(ev.type === "join"){
          if(!kv.includes(gid)){ kv.push(gid); changed = true; }
          if(ev.replyToken) ctx.waitUntil(linePost(env, "reply", {replyToken:ev.replyToken, messages:[{type:"text", text:"✅ 已加入「每日靈糧」。\n・輸入「每日靈糧」→ 回覆當天讀經進度\n・輸入「彼前5」這種經文參照 → 回覆那一章的進度與影片"}]}));
        }else if(ev.type === "leave"){
          const i = kv.indexOf(gid); if(i>=0){ kv.splice(i,1); changed = true; }
        }
      }
      if(changed) await saveKV(env, kv);
      return new Response("ok");
    }

    // ── GET：預覽 / 測試 / 看名單 ──
    if(url.searchParams.get("list") === "1"){
      const g = await listGroups(env);
      return new Response("目前推播群組數："+g.length, {headers:{"content-type":"text/plain; charset=utf-8"}});
    }
    // ?ref=彼前5 → 預覽「經文參照查詢」會回什麼（不發 LINE，純測試用）
    const q = url.searchParams.get("ref");
    if(q !== null){
      const books = await getJSON("/data/bible_books.json");
      const p = parseRefStrict(q, books);
      const body = !p ? `「${q}」不會觸發回覆（不是經文參照）` : (p.err || await buildRefMsg(p));
      return new Response(body, {headers:{"content-type":"text/plain; charset=utf-8"}});
    }
    const msg = await buildMsg();
    if(!msg) return new Response("今天沒有排程資料", {headers:{"content-type":"text/plain; charset=utf-8"}});
    if(url.searchParams.get("send") === "1"){
      const groups = await listGroups(env);
      await Promise.all(groups.map(g => linePost(env, "push", {to:g, messages:[{type:"text", text:msg}]})));
      return new Response(`已推送到 ${groups.length} 個群組：\n\n`+msg, {headers:{"content-type":"text/plain; charset=utf-8"}});
    }
    return new Response("預覽（?send=1 推送、?list=1 看群組數）：\n\n"+msg, {headers:{"content-type":"text/plain; charset=utf-8"}});
  }
};
