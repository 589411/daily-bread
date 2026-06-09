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

- ❌ **不要**用 `每日靈糧排序.csv` 或 `202*.html` 推算未來進度。
  經查證：教會的讀經次序**每一遍（約 3.3 年）都會重新編排**，舊資料是不同次序的計畫，無法預測現行進度。
  唯一可信來源是**教會當期公佈的月曆表**。
- ✅ 排程一律以**完整日期**為 key（不要用 `MM-DD`，會跨年錯位）。
- ✅ YouTube 鎖定**「陪你讀聖經 第一遍」**：即播放清單標題剛好以「《陪你讀聖經》」結尾者
  （排除「《陪你讀聖經2》」「《陪你讀聖經3》」「特別篇」「週末親近神」等）。
- ✅ 長詩篇分兩天讀，兩天對到同一支影片（key 同為 `詩篇N`）——這是正常的，不是錯誤。

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

## 9. 尚未做（未來）

- 串接 LINE Messaging API 自動推播（目前是手動「複製 LINE 訊息」按鈕）。
- 速讀軌道的歷史驗證（資料累積後再做）。
- 進度排到 2028-05-23 之後的延伸。
