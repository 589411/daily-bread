# 每日靈糧（中靈版）— 維護手冊

> 這個檔案會被 Claude 自動讀取。**任何模型（Sonnet / Opus / Haiku）接手前請先讀完本檔**，
> 照流程就能正確更新，不需要重新摸索。

## 1. 這是什麼

中壢靈糧堂（及分堂）的每日讀經進度網站。使用者每天把當天進度＋YouTube 影片分享到 LINE 群組。
網站依「今天的日期」自動顯示三個讀經軌道、經文、第一遍影片，並提供一鍵複製 LINE 訊息。

- 線上網址：https://589411.github.io/daily-bread/ （GitHub Pages，repo `589411/daily-bread`，branch `main`，root）
- 純前端靜態網站，`index.html` 啟動時 `fetch` 讀取 `data/*.json`。**必須用伺服器或 GitHub Pages 開啟，不能用 `file://`**。

## 2. 檔案結構

| 檔案 | 角色 |
|---|---|
| `index.html` | 全部 UI + 邏輯（單檔）。資料來自 `data/`。 |
| `data/schedule.json` | **排程**：日期 → 三軌道。每月需手動新增（見 §4）。 |
| `data/yt_map.json` | **影片對照表**：章節 → YouTube videoId（陪你讀聖經第一遍，全 1189 章）。用 Colab 重建。 |
| `data/summary.json` | 靈修章節 → 摘要（選用）。 |
| `data/reading_order.json` | **教會傳統讀經順序**（一個循環 1239 天，已清理）。用於預測未來月份，見 §6。 |
| `data/bible_books.json` | 全 66 卷：簡稱／全名／編號／章數（共 1189 章）。自訂讀經規劃功能用。 |
| `data/split_days.json` | 長章節分多天讀的對照（如 詩篇119→6天），多天指到**同一部**影片。 |
| `tools/fetch_yt_map.py` | Colab 用：重建 `yt_map.json`。需 YouTube Data API key。 |
| `tools/validate.py` | **驗證器**：改完 `data/` 一定要跑，過了再 commit。 |
| `tools/predict_check.py` | **順序預測／驗證器**：依 `reading_order.json` 預測未來靈修、或比對教會新月曆表。見 §6。 |
| `tools/line-worker/` | LINE 每日自動推播的 Cloudflare Worker（`worker.js`＋部署說明）。見 §13。 |
| `planner.html` | 自訂讀經規劃（獨立分頁），見 §10。 |
| `insight.html`＋`insight/` | **原文彩蛋**：中譯無法呈現的希伯來/希臘文亮點（自成一體的小專案），見 §14。 |
| `manifest.webmanifest`、`sw.js`、`icons/` | PWA：可「加到主畫面」當 App、離線可開，見 §12。 |
| `index_v1_backup.html` | 舊版備份，勿動。 |
| `202*.html`、`每日靈糧*.csv` | **舊計畫的原始檔，已被 .gitignore。是不同的讀經次序，請勿當作排程來源**（見 §6）。 |

## 3. 資料格式（務必照格式）

`data/schedule.json` — key 為完整日期 `YYYY-MM-DD`：
```json
"2026-06-08": { "d": "代下8", "s5": "林後2-林後6", "s10": "結48-但9" }
```
- `d` 靈修進度（單章，一天一章/篇）；`s5` 速讀5章（範圍）；`s10` 速讀10章（範圍）。
- 一律使用 §5 的**書卷簡稱**。詩篇用「篇」，例 `詩119`。單章書卷只寫書名，例 `約貳`。

`data/yt_map.json` — key 為「全名＋章號」（無「第/章/篇」）；單章書卷只用書名：
```json
"歷代志下8": "J84b5aS1MDE",  "詩篇119": "....",  "約翰二書": "...."
```
`data/summary.json` — 同 key 規則：`"歷代志下8": "摘要文字…"`。

## 4. 每月更新流程（最常見的工作）

教會每月公佈一張「月曆表」圖片，四欄：日期 / 靈修進度 / 速讀5章 / 速讀10章。

1. **轉錄**：把該月每一天的三欄，依 §3 格式寫進 `data/schedule.json`（沿用簡稱）。
   - 一天一章的是「靈修進度」；速讀兩欄是範圍（如 `徒27-羅3`）。
   - 仔細核對：靈修通常是連續章節，可用來抓字。
2. **驗證**：`python3 tools/validate.py` → 必須出現 `ALL OK`。它會檢查格式、日數、靈修是否能對到 `yt_map`。
3. **影片**：若新月份出現 `yt_map.json` 裡沒有的章節（validate 會警告「第一遍無影片」），通常是因為當初某書卷第一遍尚未錄；可重跑 Colab（§7）刷新。整本聖經已收錄者不必動。
4. **摘要（選用）**：可從舊檔 `每日靈糧V2.4.1.csv`（key 形如「歷代志下第8章」）補進 `data/summary.json`。
5. **commit & push**：`git add data/ && git commit -m "新增 X 月進度" && git push`。GitHub Pages 自動部署。

## 5. 書卷簡稱對照（轉錄只能用這些）

創出利民申書士得撒上撒下王上王下代上代下拉尼斯伯詩箴傳歌賽耶哀結但何珥摩俄拿彌鴻哈番該亞瑪
太可路約徒羅林前林後加弗腓西帖前帖後提前提後多門來雅彼前彼後約壹約貳約參猶啟
（完整「簡稱→編號→全名」對照寫在 `tools/validate.py` 的 `BOOKS`，那是唯一真實來源。）

## 6. 重要教訓（別重蹈覆轍）

- ✅ `每日靈糧排序.csv` 是使用者手動整理的**教會傳統讀經順序**（一個循環約 1239 天 ≈ 3 年 4 個月）。
  **已驗證**：以此順序對齊「今天＝代下8」可重現 2026 年 5–6 月月曆表 **59/61**
  （唯一差異：5/1–5/2 教會讀雅各書4–5，CSV 為瑪拉基書3–4——皆為某卷最後兩章接在歷代志上1之前）。
  → 順序**大致穩定（約 97%）**，可用來**預測**未來月份；但**偶有局部換書**，故產生的未來進度一律標為「預測」，
  待教會公布該月月曆表後比對、修正局部差異，再併入 `data/schedule.json`。
  清理後的順序存於 `data/reading_order.json`（已修正「瑪垃基書→瑪拉基書」、去除「第/章/篇」、全形數字正規化）。
- **預測流程一律用 `tools/predict_check.py`**（它自動以 schedule.json 最後一天為錨點，無需手算 index）：
  1. 教會公布新月份 → 先轉錄該月三軌道進 `data/schedule.json`（靈修可先用 gen 草稿，見下）。
  2. `python3 tools/predict_check.py verify 2026-07` → 看靈修命中率、列出不符的「局部換書」日，照月曆表修正那幾天。
  3. 想省工：`python3 tools/predict_check.py gen 2026-07-01 2026-07-31` 產生「預測靈修」草稿（d 欄），貼進 schedule.json；s5/s10 仍須照月曆表填。
  4. 最後跑 `tools/validate.py` → `ALL OK` → commit。
  - 直接執行 `python3 tools/predict_check.py`（無參數）會對現有各月做自我檢查，印出命中率。
- ⚠️ 早期 `202*.html`（2020–2024）跨了一個以上的循環，巨觀書序看似不同，多半是循環邊界與局部換書造成；
  以 `每日靈糧排序.csv` 整理出的單一循環順序為準。
- ✅ 排程一律以**完整日期**為 key（不要用 `MM-DD`，會跨年錯位）。
- ✅ YouTube 鎖定**「陪你讀聖經 第一遍」**：即播放清單標題剛好以「《陪你讀聖經》」結尾者
  （排除「《陪你讀聖經2》」「《陪你讀聖經3》」「特別篇」「週末親近神」等）。
- ✅ 一個循環＝整本聖經讀**一遍**（1189 章各一次）。除詩篇外，每卷都是整卷連續讀完再換下一卷。
- ✅ **只有詩篇分段**：拆成 4 段散在循環不同位置（依教會規劃）。其他「看似讀兩遍」的書卷是手動整理或換循環造成的雜訊，重建時已去除。
- ✅ 長章節分多天讀，多天對到**同一部**影片（key 同為該章）。清單在 `data/split_days.json`：
  詩篇78→2天、詩篇119→6天、馬太26→2天、馬太27→2天、約翰6→2天。

## 7. 重建 YouTube 對照表（少做，整本已收錄）

在 Google Colab：
1. Colab 左側「祕密」新增 `YOUTUBE_DATA_API_KEY`（Google Cloud Console 免費申請 YouTube Data API v3）。
2. 貼上 `tools/fetch_yt_map.py`，執行 `build_map()`。它會自動抓所有「第一遍」播放清單、解析標題、輸出 `yt_map.json`，並印出涵蓋率。
3. 把 `yt_map.json` 放回 `data/`，跑 `tools/validate.py`，再 commit。
- 配額：用 playlistItems（1 unit/50 部），整頻道約 70 units，遠低於每日 10,000 額度。**不要**改回逐章 search（100 units/次，會爆配額）。

## 8. 技術備註

- 經文 API：`https://bolls.life/get-text/CUV/{書卷編號}/{章}/`（**和合本＝CUV**，不是 CUNP；端點是 `/get-text/` 不是 `/api/`）。回傳 `[{verse,text}]`。書卷編號＝正典 1–66（與 `bible_books.json` 一致，代下＝14）。前端用 `fetchJson()` 依序試直連→allorigins→corsproxy；和合本字間有多餘空白，渲染時以 `replace(/[\s　]/g,'')` 清除。
- 影片縮圖：`https://i.ytimg.com/vi/{videoId}/hqdefault.jpg`。
- 想取某影片標題可用免金鑰的 oEmbed：`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json`。
- 速讀軌道是跨多章的範圍：除「開始讀經」連結外，`expandRange()` 會依正典書序把範圍（含同卷如 `羅4-8`、跨卷如 `徒27-羅3`）展開成各章，於 `<details>` 內列出每章第一遍影片（需 `bible_books.json` 的章數判斷換卷）。
- 影片可內嵌播放：首頁 `playYT()`、規劃頁 `playPV()` 皆以 `youtube.com/embed/{id}` iframe 就地播放，並保留「↗ 在 YouTube 開啟」。
- 無障礙／觸控：`:focus-visible` 外框、`prefers-reduced-motion` 關動畫、icon 按鈕有 `aria-label`、按鈕與日期格放大點擊區。
- 深／淺色：`<html data-theme=light|dark>`；字級：`data-fs=''|lg|xl`。兩者存 localStorage（`theme`／`fs`），切換鈕在 header（兩頁都有）。首次進站深淺色跟隨系統。
- 經文抓取走 `fetchJson()`：依序試「直連 → allorigins → corsproxy」，全失敗才顯示「重試」鈕＋BibleGateway 備援連結。
- LINE 分享：`https://line.me/R/share?text=` 深連結（手機直接開 LINE）；另保留「複製訊息」。訊息由 `currentMsg()` 依模式挑：
  每日進度用 `buildMsg()`（日期＋靈修＋影片＋地圖＋速讀＋彩蛋）；**「閱讀聖經」任意章用 `buildMsgRef()`**
  （章名＋影片＋地圖＋彩蛋＋回站連結 `index.html?ref=簡稱章`，收訊人點了直接開同一章）。
  模式由全域 `READ_REF` 判斷：`jumpTo()` 設值、`loadDay()` 清成 null。

## 9. Roadmap（已完成／待辦）

**已完成**：完整日期排程、三軌道、第一遍影片對照（1189 章）、經文（bolls CUV）、摘要、
分享到 LINE／複製、回到今天、深淺色、字級、自訂讀經規劃、雲端同步（§11）、PWA（§12）、
無障礙、影片內嵌、速讀各章影片清單、教會傳統順序重建（§6）。

**待辦（依優先序）**：

1. **順序預測驗證**：待教會公布 2026 年 7、8 月月曆表，用 §6 流程比對 `reading_order.json` 的預測；
   若持續高命中（目前 59/61），即可**一次產生整年排程**（只手動修正局部換書），不必每月轉錄。
2. **速讀軌道順序重建**：目前只有 5–6 月速讀資料；累積數月後，比照靈修軌做速讀5/10 的順序考證與預測。
3. **LINE 自動推播**：Worker 已備妥（§13、`tools/line-worker/`），待填 token/groupId 部署即可上線。
4. **離線經文**：經文來自外部 API，目前離線看不到；可考慮把當月靈修章節的經文預先快取進 PWA。
5. **規劃頁長清單優化**：整年計畫上百天時，過去週次可收合／虛擬捲動，進一步提速。

## 10. 自訂讀經規劃（planner.html）

讓使用者排自己的讀經計畫。是獨立分頁，頂部導覽與 `index.html` 互通。

- **輸入**：讀經順序（正典創→啟／教會傳統順序 `reading_order.json`）、勾選書卷（快捷：全選／舊約／新約／福音書）、
  速度（每天幾章 → 算完成日；或 指定完成日 → 算每天幾章）、起始日。
- **產生**：把選取書卷展開成「一章一單位」清單，依每天章數切成多天、配日期。
  - 正典順序：照 `bible_books.json` 的 `id` 1→66，每卷 1→N 章。
  - 教會順序：取 `reading_order.json`，過濾出選取書卷、保留其循環順序。
- **每天可展開**：顯示經文（同 §8 的 bolls API）＋每章的第一遍影片（查 `yt_map.json`，key＝全名＋章號／單章書卷用書名）。
- **進度**：每天可勾選完成，存 `localStorage`（key＝`plan_{順序}_{總章}_{每天章}_{起始日}`），含進度條。**換裝置不會同步**（見 §9）。
- **匯出**：複製計畫文字、下載 CSV。
- 維護：書卷或章數有變動只會動到 `data/bible_books.json`；計畫邏輯純前端，無需後端。
  注意 `BOOKS.find(b=>key.startsWith(b.full))` 依賴沒有書卷全名是另一卷的前綴（目前 66 卷成立）。

## 11. 進度雲端同步（Firebase + Google 登入）

planner.html 內建雲端同步，**未填金鑰時自動降級為只存本機**（功能照常）。設定一次即可：

提供兩種同步方式：**Google 登入**（每人一份，最正規）與**同步碼**（免登入，給長輩；輸入同一組 6 碼即互通）。

1. Firebase Console 建專案 → Authentication → Sign-in method → **啟用 Google** 與 **匿名（Anonymous）**。
   （同步碼用匿名登入在背後撐著，使用者無感；沒啟用匿名，同步碼會無法連線。）
2. 建立 **Firestore Database**。
3. 專案設定 → 新增 **Web 應用** → 複製 `firebaseConfig`（apiKey / authDomain / projectId / appId）。
4. 填進 `planner.html` 的 `FIREBASE_CONFIG`（檔案上方，搜尋「填入」）。
5. Authentication → Settings → **授權網域** 加入 `589411.github.io`（與測試用 `localhost`）。
6. Firestore 安全規則：
   ```
   rules_version = '2';
   service cloud.firestore {
     match /databases/{db}/documents {
       match /users/{uid} {            // Google 登入：只能讀寫自己的
         allow read, write: if request.auth != null && request.auth.uid == uid;
       }
       match /codes/{code} {           // 同步碼：任何（含匿名）登入皆可讀寫
         allow read, write: if request.auth != null;
       }
     }
   }
   ```
- 資料模型：`users/{uid}` 或 `codes/{code}` = `{ planConfig:{order,pace,books,start,cpd,end}, progress:{ [planSig]:[已完成天index] }, ts }`。
- 流程：Google 登入或輸入同步碼後 `pullCloud()` 還原計畫＋進度；產生計畫或勾選完成時 `cloudPush()` 寫回（`merge:true`）。
- 同步衝突採最後寫入為準。
- ⚠️ 同步碼安全性：知道碼的人就能讀寫該筆（碼為隨機 6 碼，純讀經進度，風險低）。Google 路徑才有逐人隔離。
- 未填金鑰時整個雲端區塊自動停用，只存本機，網站照常運作。

## 12. PWA（加到主畫面／離線）

`manifest.webmanifest`＋`sw.js`＋`icons/` 讓網站可「加到主畫面」當 App 開、離線也能載入。

- 兩頁 `<head>` 都有 `<link rel="manifest">`、`theme-color`、`apple-touch-icon`，並註冊 `sw.js`。
- `sw.js` 對**同源檔案**採 network-first：有網路時一律抓最新（更新即時生效，不會卡舊版），離線才回退快取；外部資源（bolls 經文／YouTube／Firebase）不攔截。
- **維護**：若新增了需要離線快取的檔案，加進 `sw.js` 的 `SHELL` 陣列，並把 `CACHE` 版本字串（`daily-bread-v1`）改成 v2…以淘汰舊快取。一般改 HTML／JSON 不必動（network-first 會自動更新）。
- 圖示：`icons/icon-192.png`、`icon-512.png`（用 Pillow 畫的開書圖，要換可重畫同尺寸覆蓋）。

## 13. LINE 讀經進度（Cloudflare Worker）

> **2026-07 起改為「關鍵字回覆」模式，每日主動推播已停用。** 原因見本節末的「⚠️ 額度坑」。
> - **現行有兩種回覆**（皆走 `replyToken`，**不計入 LINE 每月訊息額度**，不管群組多少人、發幾次都零成本）：
>   1. 訊息含「每日靈糧」→ 回覆**當天**三軌道進度（`buildMsg()`）。
>   2. 訊息**整則就是經文參照**（如 `彼前5`／`詩119`／`猶`／`彼得前書5`）→ 回覆**那一章**的進度
>      （`buildRefMsg()`：章名＋第一遍影片＋歷史地圖＋原文彩蛋＋回站連結）。
>      - ⚠️ **刻意不顯示「這是 X/X 的靈修進度」**：這條路是給人自己讀經用的，讀的人進度不必跟教會同步，
>        標日期會被誤會成「今天該讀這章」。日期只出現在「每日靈糧」那條路（`buildMsg()`）。曾做過又拿掉，別再加回去。
>      - 兩關比對：`quickRef()` 只用 worker 內建書卷表判形狀（**不連網**，閒聊訊息零請求就擋掉）；
>        通過才 fetch `bible_books.json` 由 `parseRefStrict()` 驗章數（超出回「創世記只有 50 章喔。」）。
>      - **刻意採嚴格比對**：必須以書卷簡稱／全名開頭、其後只剩數字，所以「我們約3點見面」「今天讀彼前5嗎」都不會觸發；
>        非單章書一定要帶章號（單獨的「書」「傳」「可」不觸發）。**已知殘餘風險：單獨傳一則「約3」會被當成約翰福音3章。**
>      - 支援全形數字（彼前５）、「彼前第5章」、單章書（猶／俄／門／約貳／約參）。
>      - 測試不必發 LINE：`GET /?ref=彼前5` 直接預覽回覆內容；`npx wrangler dev --local` 可本機全流程測。
> - **已停用**：`scheduled()` 每日 push 與 Cron Trigger（`wrangler.toml` 的 `crons = []`）。程式保留，升級付費方案後把 `crons` 改回 `["0 23 * * *"]` 重新 deploy 即可恢復。
> - 部署：`tools/line-worker/` 執行 `wrangler deploy`（已含 `wrangler.toml`；secrets 不動）。

以下為原「每日自動推播」設計，保留供未來付費方案恢復時參考——GitHub Pages 是靜態網站，無法自己定時發訊息，故用 **Cloudflare Worker ＋ Cron Trigger** 每天呼叫 LINE Messaging API push。

- 程式與部署說明：`tools/line-worker/`（`worker.js`＋`README.md`）。
- **秘密不進 repo**：`LINE_TOKEN`、`GROUP_ID` 放 Cloudflare Worker 的加密環境變數。
- Worker 執行時即時抓 `daily-bread.launchdock.app/data/*.json` 組訊息（用與前端相同的 `parseRef`/`ytKey` 邏輯），所以排程更新後不必改 Worker。
- Cron `0 23 * * *`(UTC) = 台灣 07:00。Cron Trigger 不需要 DNS，不影響網域。
- ⚠️ 設 cron 用 Worker → Settings → Triggers 的 **「Cron expression」分頁**填 `0 23 * * *`；別用「Schedule（every N hours）」填 2300（會報 0–23 錯誤）。cron 只在下一個觸發點才首次跑；要立即測用 `/?send=1`。推播停掉先查：Cron 還在嗎？`schedule.json` 有涵蓋今天嗎（排程到期會靜默不發）？
- ⚠️ **額度坑（2026-07 踩爆，導致改用回覆模式的原因）**：LINE 訊息額度是**按「收訊人頭」計費**——推到群組 ＝ 該群組「當下人數」則，**不是每群 1 則**。免費方案每月僅 **200 則**、每月 1 號（JST）重置。4 群共 59 人、每天推一次 ＝ 每天 59 則 → 約 **3.4 天**用罄，之後所有 push 被 LINE 擋（HTTP 429）。而 `scheduled()` 用 `Promise.all` 發完**沒檢查回應**，被擋也**靜默不報錯** → 表面「設定全對卻突然不發」。
  - **查證指令**（需 worker 的 LINE_TOKEN）：`GET /v2/bot/message/quota`（看上限）、`/v2/bot/message/quota/consumption`（看已用）、`/v2/bot/insight/message/delivery?date=YYYYMMDD`（每日按類型：`apiPush` 主動推、`apiReply` 回覆、`broadcast` 後台群發）。
  - **關鍵教訓**：群組主動推播在免費 200 額度下數學上不可行（59 人/天 ×30 ≈ 1680/月）；**reply（`replyToken` 回覆）不計入額度** → 故改「關鍵字回覆」。若要恢復每日主動推播，須升級 LINE 付費方案並開啟「超量訊息」。
- groupId 取得（單群組）：用 webhook.site 抓一次，填進 Secret `GROUP_ID`。
- **多群組自動註冊**（推薦）：綁 KV（變數名 `GROUPS`）＋設 `LINE_CHANNEL_SECRET`＋把 LINE Webhook URL 指到 Worker 並保持開啟。之後把官方帳號邀進新群組就自動加入名單、離開自動移除；cron 推給名單所有群組（含 `GROUP_ID`）。`?list=1` 看群組數。步驟見 README。

## 14. 原文彩蛋（insight.html ＋ insight/）

「聖經翻譯裡藏的小彩蛋」：中譯無法呈現的希伯來文／希臘文現象（諧音雙關、名字詞源、
語義場、離合結構…），獨立小專案，隨時可拆成獨立 repo。

- 資料：`insight/data/insights.json`（26 筆起）。schema、分類法、寫作規則在 `insight/RULES.md`（品質憲法，唯一標準）。
- 生產：sub-agent 並行生成 → 高階模型審核 → 程式驗證。流程與**踩坑清單**在 `insight/HARNESS.md`——新增條目前必讀，
  尤其：cuvQuote 不可憑記憶、和合本括號註、詩篇篇題位移、中希分節位移、match 填實際字形。
- 驗證：改完 `insight/data/` 必跑 `python3 insight/tools/validate_insights.py` → `ALL OK` 才 commit。
  它會抓 bolls（WLC/TR/CUV）逐節比對每個原文錨點與和合本引文，快取在 `insight/tools/.cache/`（已 gitignore）。
- 前端：`insight.html`（比照 planner.html：導覽互通、深淺色/字級同 localStorage key）。
  頁面會讀 `data/schedule.json`，今日靈修章節若有彩蛋自動顯示提示（`todayEgg()`）——
  未來要整合進 index.html 或 LINE 推播，搬同一段查表邏輯即可（key＝bookNo＋chapter）。
