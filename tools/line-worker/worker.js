// =====================================================================
//  Cloudflare Worker — 每天把「當天讀經進度」推到 LINE 群組
//  部署步驟見同資料夾 README.md。
//  秘密環境變數（在 Worker 設定，不進公開 repo）：
//    LINE_TOKEN  = LINE Messaging API 的 Channel access token
//    GROUP_ID    = 目標群組的 groupId（用 webhook.site 抓，見 README）
//  Cron Trigger 例：「0 23 * * *」(UTC) = 台灣每天早上 07:00
//  測試：部署後用瀏覽器打 https://<worker>.workers.dev/         → 預覽今天訊息
//        打 https://<worker>.workers.dev/?send=1                → 實際推一次
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
  const today = new Date(Date.now()+8*3600*1000).toISOString().slice(0,10); // 台灣日期
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

async function push(env, msg){
  return fetch("https://api.line.me/v2/bot/message/push", {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":"Bearer "+env.LINE_TOKEN },
    body: JSON.stringify({ to: env.GROUP_ID, messages:[{ type:"text", text: msg }] })
  });
}

export default {
  async scheduled(event, env, ctx){
    const msg = await buildMsg();
    if(msg) ctx.waitUntil(push(env, msg));
  },
  async fetch(req, env){
    const msg = await buildMsg();
    if(!msg) return new Response("今天沒有排程資料", {status:200, headers:{"content-type":"text/plain; charset=utf-8"}});
    if(new URL(req.url).searchParams.get("send")==="1"){
      const r = await push(env, msg);
      return new Response("已推送，狀態 "+r.status+"\n\n"+msg, {headers:{"content-type":"text/plain; charset=utf-8"}});
    }
    return new Response("預覽（加 ?send=1 會實際推送）：\n\n"+msg, {headers:{"content-type":"text/plain; charset=utf-8"}});
  }
};
