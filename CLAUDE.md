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
- **預測流程**：在 `data/reading_order.json` 找一個已知錨點（例：歷代志下8 在 index 416 ＝ 2026-06-08），
  往後逐日對應 `order[index+offset]`，產生草稿排程；公布後用月曆表驗證、修正，再 commit。
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

- 經文 API：`https://bolls.life/api/CUNP/{書卷編號}/{章}/`，經 `api.allorigins.win` proxy 解決 CORS。和合本＝CUNP。
- 影片縮圖：`https://i.ytimg.com/vi/{videoId}/hqdefault.jpg`。
- 想取某影片標題可用免金鑰的 oEmbed：`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json`。
- 速讀軌道是跨多章的範圍，不對應單一影片；網站只放「開始讀經」連結。
- 深／淺色：`<html data-theme=light|dark>`；字級：`data-fs=''|lg|xl`。兩者存 localStorage（`theme`／`fs`），切換鈕在 header（兩頁都有）。首次進站深淺色跟隨系統。
- 經文抓取走 `fetchJson()`：依序試「直連 → allorigins → corsproxy」，全失敗才顯示「重試」鈕＋BibleGateway 備援連結。
- LINE 分享：`https://line.me/R/share?text=` 深連結（手機直接開 LINE）；另保留「複製訊息」。訊息內容由 `buildMsg()` 產生。

## 9. 尚未做（未來）

- **進度雲端同步**：planner.html 目前進度只存瀏覽器 localStorage（換裝置不通）。待接後端同步（見 §11）。
- **順序預測驗證**：待教會公布 2026 年 7、8 月月曆表後，用 §6 流程比對 `data/reading_order.json` 的預測；
  若持續高命中，即可一次產生整年排程（僅修正局部換書）。
- 串接 LINE Messaging API 自動推播（目前是手動「複製 LINE 訊息」按鈕）。
- 速讀（5章／10章）兩軌道的順序驗證：目前只有 5–6 月圖片資料，待累積後比照靈修軌做同樣的順序重建。

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
