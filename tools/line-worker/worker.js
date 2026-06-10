// =====================================================================
//  Cloudflare Worker — 每天把「當天讀經進度」推到 LINE 群組
//  ★ 支援多群組自動註冊：把官方帳號邀進群組 → 自動加入推播名單（存 KV）；
//    官方帳號離開群組 → 自動移除。詳見同資料夾 README.md。
//
//  必要環境變數（Worker Secret，不進 repo）：
//    LINE_TOKEN           = Channel access token（push/reply 用）
//  建議環境變數：
//    LINE_CHANNEL_SECRET  = Channel secret（驗證 webhook 簽章，防偽造）
//    GROUP_ID             = 主群組 groupId（沒綁 KV 或想固定保留一個時用）
//  必要繫結（Binding）：
//    GROUPS               = KV Namespace（存自動註冊的群組清單）。沒綁也能跑，只會推 GROUP_ID。
//
//  Cron Trigger：「0 23 * * *」(UTC) = 台灣 07:00
//  LINE Webhook URL 設成本 Worker 網址，並開啟 Use webhook（才能自動註冊群組）。
// =====================================================================
const SITE = "https://daily-bread.launchdock.app";
const BGN = {"創":"創世記","出":"出埃及記","利":"利未記","民":"民數記","申":"申命記","書":"約書亞記","士":"士師記","得":"路得記","撒上":"撒母耳記上","撒下":"撒母耳記下","王上":"列王紀上","王下":"列王紀下","代上":"歷代志上","代下":"歷代志下","拉":"以斯拉記","尼":"尼希米記","斯":"以斯帖記","伯":"約伯記","詩":"詩篇","箴":"箴言","傳":"傳道書","歌":"雅歌","賽":"以賽亞書","耶":"耶利米書","哀":"耶利米哀歌","結":"以西結書","但":"但以理書","何":"何西阿書","珥":"約珥書","摩":"阿摩司書","俄":"俄巴底亞書","拿":"約拿書","彌":"彌迦書","鴻":"那鴻書","哈":"哈巴谷書","番":"西番雅書","該":"哈該書","亞":"撒迦利亞書","瑪":"瑪拉基書","太":"馬太福音","可":"馬可福音","路":"路加福音","約":"約翰福音","徒":"使徒行傳","羅":"羅馬書","林前":"哥林多前書","林後":"哥林多後書","加":"加拉太書","弗":"以弗所書","腓":"腓立比書","西":"歌羅西書","帖前":"帖撒羅尼迦前書","帖後":"帖撒羅尼迦後書","提前":"提摩太前書","提後":"提摩太後書","多":"提多書","門":"腓利門書","來":"希伯來書","雅":"雅各書","彼前":"彼得前書","彼後":"彼得後書","約壹":"約翰一書","約貳":"約翰二書","約參":"約翰三書","猶":"猶大書","啟":"啟示錄"};
const ABBR = Object.keys(BGN).sort((a,b)=>b.length-a.length);
const SINGLE = {"俄":1,"門":1,"約貳":1,"約參":1,"猶":1};

function parseRef(s){
  s=(s||"").replace(/[（(][^）)]*[）)]/,"").trim();
  for(const k of ABBR){ if(s.startsWith(k)){ const ch=parseInt(s.slice(k.length).replace(/[章篇]/g,""))||1; return {abbr:k,full:BGN[k],ch,single:!!SINGLE[k]}; } }
  return null;
}
const ytKey = p => p.full + (p.single?"":p.ch);
const label = p => p.full + (p.single?"":p.ch + (p.abbr==="詩"?"篇":"章"));

async function buildMsg(){
  const today = new Date(Date.now()+8*3600*1000).toISOString().slice(0,10);
  const sched = await (await fetch(SITE+"/data/schedule.json")).json();
  const yt    = await (await fetch(SITE+"/data/yt_map.json")).json();
  const d = sched[today];
  if(!d) return null;
  const p = parseRef(d.d), lab = p?label(p):d.d, vid = p?yt[ytKey(p)]:"";
  const md = `${parseInt(today.slice(5,7))}/${parseInt(today.slice(8,10))}`;
  let msg = `📖 ${md} 每日靈糧\n靈修進度：${lab}`;
  if(vid) msg += `\n📺 https://youtu.be/${vid}`;
  msg += `\n（速讀5章：${d.s5}　速讀10章：${d.s10}）\n🔗 ${SITE}/`;
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
        const gid = ev.source && ev.source.groupId; if(!gid) continue;
        if(ev.type === "join"){
          if(!kv.includes(gid)){ kv.push(gid); changed = true; }
          if(ev.replyToken) ctx.waitUntil(linePost(env, "reply", {replyToken:ev.replyToken, messages:[{type:"text", text:"✅ 已加入「每日靈糧」每日推播，明早 7:00 起每天會送上當天讀經進度。"}]}));
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
