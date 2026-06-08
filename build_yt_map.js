// ====================================================
// 用法：
// 1. 填入 YouTube Data API v3 key（Google Cloud Console 免費申請）
// 2. 在瀏覽器 console 或 Node.js 執行
// 3. 複製輸出的 JSON 貼到 index.html 的 YT_MAP 變數
// ====================================================

const API_KEY = "填入你的API_KEY";
const CHANNEL_ID = "UCV_iUJtaJA62vnM9hM_opRw";

// 所有要查的章節（從讀經進度表）
const CHAPTERS = [
  "哥林多後書第12章","哥林多後書第13章",
  ...Array.from({length:48},(_,i)=>`以西結書第${i+1}章`),
  ...Array.from({length:12},(_,i)=>`但以理書第${i+1}章`),
  ...Array.from({length:6},(_,i)=>`加拉太書第${i+1}章`),
  ...Array.from({length:6},(_,i)=>`以弗所書第${i+1}章`),
  ...Array.from({length:4},(_,i)=>`腓立比書第${i+1}章`),
  ...Array.from({length:4},(_,i)=>`歌羅西書第${i+1}章`),
  ...Array.from({length:5},(_,i)=>`帖撒羅尼迦前書第${i+1}章`),
  ...Array.from({length:3},(_,i)=>`帖撒羅尼迦後書第${i+1}章`),
  ...Array.from({length:6},(_,i)=>`提摩太前書第${i+1}章`),
  ...Array.from({length:4},(_,i)=>`提摩太後書第${i+1}章`),
  ...Array.from({length:3},(_,i)=>`提多書第${i+1}章`),
  "腓利門書第1章",
  ...Array.from({length:13},(_,i)=>`希伯來書第${i+1}章`),
  ...Array.from({length:5},(_,i)=>`雅各書第${i+1}章`),
  ...Array.from({length:29},(_,i)=>`歷代志上第${i+1}章`),
  ...Array.from({length:30},(_,i)=>`歷代志下第${i+1}章`),
];

async function searchVideo(chapterName) {
  const q = encodeURIComponent(chapterName + " JAM陪你讀聖經");
  const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=${CHANNEL_ID}&q=${q}&maxResults=1&type=video&key=${API_KEY}`;
  const r = await fetch(url);
  const d = await r.json();
  const item = d.items?.[0];
  return item ? { id: item.id.videoId, title: item.snippet.title } : null;
}

async function buildMap() {
  const map = {};
  for (const ch of CHAPTERS) {
    const result = await searchVideo(ch);
    if (result) {
      map[ch] = result.id;
      console.log(`✓ ${ch} → ${result.id} (${result.title})`);
    } else {
      console.log(`✗ ${ch} → 找不到`);
    }
    await new Promise(r => setTimeout(r, 200)); // 避免過快
  }
  console.log("\n=== 完成，複製下面這段 ===\n");
  console.log("const YT_MAP = " + JSON.stringify(map, null, 2) + ";");
}

buildMap();
