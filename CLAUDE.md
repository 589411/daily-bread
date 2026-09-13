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
- LINE 分享：`https://line.me/R/share?text=` 深連結（手機直接開 LINE）；另保留「複製訊息」。訊息內容由 `buildMsg()` 產生。

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

## 13. LINE 每日自動推播（Cloudflare Worker）

GitHub Pages 是靜態網站，無法自己定時發訊息，故用 **Cloudflare Worker ＋ Cron Trigger** 每天呼叫 LINE Messaging API push。

- 程式與部署說明：`tools/line-worker/`（`worker.js`＋`README.md`）。
- **秘密不進 repo**：`LINE_TOKEN`、`GROUP_ID` 放 Cloudflare Worker 的加密環境變數。
- Worker 執行時即時抓 `daily-bread.launchdock.app/data/*.json` 組訊息（用與前端相同的 `parseRef`/`ytKey` 邏輯），所以排程更新後不必改 Worker。
- Cron `0 23 * * *`(UTC) = 台灣 07:00。Cron Trigger 不需要 DNS，不影響網域。
- ⚠️ 設 cron 用 Worker → Settings → Triggers 的 **「Cron expression」分頁**填 `0 23 * * *`；別用「Schedule（every N hours）」填 2300（會報 0–23 錯誤）。cron 只在下一個觸發點才首次跑；要立即測用 `/?send=1`。推播停掉先查：Cron 還在嗎？`schedule.json` 有涵蓋今天嗎（排程到期會靜默不發）？
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

## 15. 讀經名單管理（admin.html，教會統計會友進度用）

背景：教會希望把紙本讀經登記換成線上、榮譽制（不驗證，相信會友自報），且要能快速交出「誰完成了、完成多少」的名單給教會。設計原則：**不做排名/比較給一般使用者看**（避免落後者的社交壓力），名單只給管理者看，個人只看得到自己的資料。

- **`planner.html` 新增「姓名／小組」欄位**（見 `profileBlock`）：使用者自行填寫真實姓名＋選填小組/區，存 `localStorage`（`pfName`/`pfGroup`）＋隨 `cloudPush()` 一起寫回 Firestore，不論走 Google 登入或同步碼都會收集到（同步碼是給長輩用的免登入路徑，特別要涵蓋到）。
- **Firestore 文件新增兩個欄位**（`users/{uid}` 與 `codes/{code}` 共用同一份文件結構）：
  - `profile: {name, group}` —— 使用者自填的姓名/小組。
  - `latestPlan: {planSig, order, cpd, total, done, pct, start, end, updatedAt}` —— 每次 `cloudPush()` 時，從目前的 `plan`／`getDone()` 算出來的**去正規化**進度摘要（管理者名單不必重新展開整份讀經計畫邏輯就能顯示進度）。
  - 這兩者都在 `cloudPush()`／`pullCloud()` 一起讀寫，不影響原本的 `progress[planSig]`（勾選陣列）欄位格式。
- **新增 `admin.html`**：管理者專用頁面，Google 登入後讀取 `users`／`codes` 兩個 collection，彙整成一張表（姓名、小組、進度%、來源、最後更新），可搜尋、可下載 CSV 交給教會。**這個頁面沒有連結在導覽列上**，只有知道網址的人（教會指定管理者）會用到，避免一般會友點進去看到管理介面。
- **✅ Firestore 安全規則已更新並發佈**（2026-09-06，取代 2026-06-10 建立後從未修改的舊版；Firebase Console 保留版本歷史，隨時可回復）。線上現行規則就是下面這版：
  ```
  rules_version = '2';
  service cloud.firestore {
    match /databases/{db}/documents {
      function isAdmin() {
        return request.auth != null && request.auth.uid in [
          "BuVVEegTwEPS50rWyc6cSHwaJzi1"   // 589411@gmail.com（目前唯一管理者）
        ];
      }
      match /users/{uid} {
        allow get, write: if request.auth != null && request.auth.uid == uid;
        allow list: if isAdmin();
      }
      match /codes/{code} {
        allow get, write: if request.auth != null;
        allow list: if isAdmin();
      }
    }
  }
  ```
  - **這順便修掉一個既有漏洞**：舊規則 `codes/{code}` 是 `allow read, write: if request.auth != null`，`read` 在 Firestore 規則裡等於 `get`＋`list`——因為條件不看文件內容、只看有沒有登入（連匿名登入都算），任何人在瀏覽器主控台打 `firebase.firestore().collection('codes').get()` 就能**列出所有同步碼使用者的完整進度**，不需要真的知道那組 6 碼。新規則把 `codes` 拆成 `get`（仍然任何登入可讀「單一」已知文件）＋`list`（只有 `isAdmin()` 能列全部），把這個洞補起來。
  - 要新增管理者：請對方用 Google 登入網站一次（Authentication → 使用者 就會出現他的 UID），把 UID 加進 `isAdmin()` 陣列再發佈即可。或讓他開 `admin.html`，頁面會顯示「你目前還不在管理者名單裡」並秀出自己的 UID。

## 16. 2026-09-06 現況盤點（動任何東西前先看這段）

實際登入 Firebase Console 逐項確認的結果，跟先前文件的假設有出入：

- **後端只有兩塊，而且只有一塊真的在運作**：
  | 服務 | 位置 | 狀態 |
  |---|---|---|
  | 網站託管 | GitHub Pages `589411/daily-bread`，自訂網域 `daily-bread.launchdock.app` | ✅ 運作中 |
  | LINE 推播 | Cloudflare Worker `daily-bread-line` ＋ KV `daily-bread-groups`（只存群組 ID） | ✅ 運作中，唯一真正在跑的後端 |
  | 使用者資料 | Firebase `daily-bread-f88ac`（專案編號 258444297032） | ⚠️ 接好但幾乎沒用 |
  - Cloudflare 帳號下**沒有**任何跟讀經有關的 D1／R2；別再去那邊找進度資料。
- **⚠️ 最重要的發現：Firestore 資料庫是空的。** 連 `users`／`codes` 集合都不存在，一筆資料都沒寫進去過。
  Authentication 原本只有 1 個匿名使用者（2026-07-23），**沒有任何 Google 使用者**。
- **原因已查明並修復**：`daily-bread.launchdock.app` **不在 Firebase 的授權網域清單裡**（清單只有 localhost、
  `*.firebaseapp.com`、`*.web.app`、`589411.github.io`——後者是還沒換自訂網域時加的）。
  Firebase SDK 會用授權網域擋下 OAuth，所以**線上正式網址的 Google 登入從上線以來就沒成功過**，
  只會噴 `auth/unauthorized-domain`。同步碼（匿名登入）不受此限，所以沒人發現。
  → 2026-09-06 已把 `daily-bread.launchdock.app` 加入授權網域，並實測 Google 登入成功
  （產生史上第一個 Google 使用者 `589411@gmail.com`）。**日後若再換網域，記得同步加授權網域。**
- **登入方式**：Google 與匿名都是「已啟用」，這部分一直都沒問題。
- **對讀經名單功能的意義**：雲端同步的實際採用率是 **0**，所以名單功能不是「在既有資料上加報表」，
  而是要從零推動會友養成新習慣，且要連過四道摩擦：開網頁 → 產生計畫 → 填姓名 → 每天回來勾選。
  對照之下 LINE 推播是唯一會友每天真的會碰到的介面，且 Worker 已能回應關鍵字。
  **「進度改從 LINE 收」是尚未決定但值得認真評估的方向**，`admin.html` 的資料結構與匯出邏輯兩條路都用得上。
- ⚠️ **最重要的教訓：動手前先 `git fetch`／`git pull`，不要拿本機 clone 當作 repo 的真實狀態。**
  2026-09-06 這次，本機 clone 停在 `73dcf40`（2026-07），而遠端 `main` 早在 8/3–8/4 就有四個 commit
  （LINE 關鍵字回覆、經文參照回覆、防迴圈、`wrangler.toml`、`data/schedule.json` 新月份等，共 8 檔 1081 行）。
  當時只看本機就下結論「線上 Worker 領先 repo 兩個多月、repo 那份是舊的」——**這句話對本機成立，對 GitHub 不成立**，
  於是白做了一次「從 Cloudflare 反向抓回 worker.js」，那個 commit 事後整個丟棄。
  本機那個 VM 沒有網路也沒有 GitHub 憑證，`git fetch` 跑不動；這種情況下要嘛請使用者先 fetch，
  要嘛用瀏覽器去看 `github.com/589411/daily-bread/commits/main` 確認遠端狀態，**不要憑本機臆測**。
- **尚未上線**：`feature/roster` 分支（`admin.html` ＋ `planner.html` 姓名欄位）已 commit 但**還沒 merge 進 main、沒 push**，
  所以線上還是舊版 `planner.html`，`admin.html` 也還不存在於正式站。
- **待辦／未來擴充**：
  1. 目前只支援單一管理者清單（寫死在規則裡）。長期教會想讓「小組長只看自己組」，需要多加一層——例如另建 `roles/{uid}: {role:'leader', group:'三區'}` 文件，`isAdmin()`/`isLeaderOf(group)` 改成查這個 collection，並讓 `admin.html` 依登入者的 group 過濾名單。這是之後才做，先別為了這個過度設計。
  2. 「一年讀完聖經」的官方進度目前仍要會友自己在 `planner.html` 用「正典順序＋指定完成日」手動產生，`generate()` 用的是**固定每天章數**（`byend` 只是 `ceil(units/days)`），不是先前討論那種「多數書卷整卷收尾、365天剛好讀完」的智慧分配演算法——如果教會要全體統一用同一份「智慧版」年度計畫，需要另外把那個排法做成 `planner.html` 的第三個 order 選項或一份固定 `data/` 排程檔，目前還沒做。

## 17. 一年讀完整本聖經（`year.html` ＋ `data/year_plan.json`）

教會用來鼓勵會友一年讀完一遍聖經的獨立功能。**與 §6 的教會傳統順序無關**，是另一套排程，兩者並存互不影響。

### 排程規則與產生方式（**2026-09-13 改為字數加權**）

- **為什麼不用章數**：「章」不是等量單位。實測和合本（去空白與標點）**詩篇117篇只有 50 字、
  詩篇119篇有 3304 字，差 66 倍**。舊版固定「每天 3 或 4 章」造成每日字數 383–6328 字、
  最重的一天是最輕的 **16.5 倍**；改成字數加權後是 1424–3546 字、**2.7 倍**，標準差從 1053 降到 355。
- **每章字數資料：`data/chapter_chars.json`**（1189 章，取自 bolls.life CUV，去空白與標點）。
  全本共 **931,237 字**，平均每章 783 字，365 天平均**每天 2,551 字**。
  repo 裡原本沒有任何字數資料（`daily_txt.html` 是教會網站導覽頁、`每日靈糧V2.4.1.csv` 是章摘要），
  這份是靠瀏覽器逐章抓 bolls API 產生的；**雲端容器與裝置端 VM 都連不到 bolls.life**，要重抓只能走瀏覽器。
- **規則**：正典順序創→啟，1189 章一章不漏、不跳段；365 天讀完；
  目標是**每天字數接近 2,551**，章數因此浮動；仍盡量讓每卷在某一天整卷讀完。
- **演算法**（`tools/gen_year_plan.py`，執行 0.1 秒）：
  1. 把字數太少的書卷與相鄰書卷併成群組（門檻 0.55×目標），避免出現過輕的一天。
  2. 每組用一次 DP 算出「切成 j 段」的真實最小成本（成本＝Σ(每日字數−目標)²），j = 1..40。
  3. 依**邊際效益**把 365 天分配給各組（多給一天能省最多成本的先拿）。成本對 k 為凸，貪婪即最佳。
  4. 每組依分到的 k 取出 DP 的切法。
  - 試過「過重懲罰」（讓超過目標的日子成本加權 1.5~3 倍），最多只把最重的一天從 3546 降到 3400，
    標準差反而變差——因為重的日子多半是**整卷書**（雅歌 3546 字），瓶頸在「保持書卷完整」不在成本函數。**沒有採用。**
- **產生的結果**：每日章數 1~16 章（中位數 3）。1章×4天、2章×116、3章×138、4章×54、5章×32、6~16章×21天。
  - 只讀 1 章的 4 天都是超長章：民數記7、列王紀上8、**詩篇119（自成一天）**、馬可福音14。
  - 一天讀完一整卷的例子：路得記、雅歌、約珥書、那鴻書、哈巴谷書、西番雅書、瑪拉基書、腓立比書、歌羅西書、帖前、帖後、提前。
  - 章數最多的一天是**詩篇120-135（16 章，共 2589 字）**——上行之詩都很短。
- **驗證**：產生器自我檢查天數 365、章數 1189、與正典順序逐章比對、無重複、每章都對得到 `yt_map` 影片 → `ALL OK`。
  **不要手改 `data/year_plan.json`，要改就改產生器重跑。**
- `data/year_plan.json` 格式：`{name, order, weighted:"chars", totalDays, totalChapters, totalChars,
  targetCharsPerDay, generatedAt, note, days:[[key,...] × 365]}`。
  `key` 與 `yt_map.json` 完全同格式（全名＋章號；單章書卷只有書名）。

### `year.html`（獨立頁面）
- **開啟就看到「今天要讀哪幾章、約幾字」**，不需要設定、不需要登入——這是刻意的，摩擦愈低採用率愈高。
- 一鍵「今天讀完了」；進度條、目前進度、全書完成度、**本週完成 N/N 天**。
- **補讀導向**：落後不用重來，今天的進度照樣讀，週末再把前面補回來。頁面會顯示「有 N 天還沒讀完」，
  清單裡未讀的過去日子標「待補」，可直接勾；另有「只看未讀完」篩選。
  **刻意不做連續天數（streak）**——那會懲罰「平日忙、假日補」的人，與這個計畫的設計目的相反。
- 每天可展開看該章經文（bolls CUV，同 §8）與第一遍影片；有整卷收尾的日子會標「讀完《某某書》」。
- 分享到 LINE、姓名／小組欄位、雲端同步（Google 登入／同步碼），資料結構與 `planner.html` 相同，
  所以 `admin.html`（§15）讀得到，教會可直接匯出名單。
- **起始日**：預設 `OFFICIAL_START = "2027-01-01"`（教會統一進度，第 365 天正好是 2027-12-31 讀完啟示錄）。
  個人想提早開始可自行改，進度會照自己的起始日重算。改起始日要動 `year.html` 裡的這個常數。

### 與 `planner.html` 的關係
- `planner.html` 最上方有「📅 一年讀完整本聖經（教會推薦）」區塊，按「使用這份計畫」會載入同一份 `year_plan.json`。
- **兩頁共用同一個進度鍵 `planSig = "year365_<起始日>"`**（localStorage 與 Firestore 皆是），
  所以在哪一頁勾選都會互通。起始日共用 localStorage 的 `yearStart`。
- 底下原本的自訂規劃功能（§10）完全保留，只是標題改成「或自訂我的讀經計畫」。

### 導覽
`index.html`、`planner.html`、`insight.html` 的導覽列都已加入「一年讀經」連結指向 `year.html`。

