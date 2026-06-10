# 每日靈糧（中靈版）

中壢靈糧堂（及分堂）的每日讀經進度網站。依「今天的日期」自動顯示三個讀經軌道、經文、與「陪你讀聖經 第一遍」影片，並提供一鍵分享到 LINE。另有「自訂讀經規劃」功能。

- **線上網址**：https://daily-bread.launchdock.app/ （亦可用 https://589411.github.io/daily-bread/）
- **技術**：純前端靜態網站（GitHub Pages），無自建後端；雲端同步用 Firebase。
- **維護細節看 [`CLAUDE.md`](./CLAUDE.md)**（任何 AI 模型接手前請先讀那份）。

---

## 功能總覽

**每日進度（`index.html`）**
- 依今日日期自動顯示：靈修進度（一天一章）、速讀5章、速讀10章。
- 靈修章節：和合本經文（bolls.life）＋ 第一遍 YouTube 影片（可就地內嵌播放）＋ 章節摘要。
- 速讀軌道：顯示範圍，並可展開「各章第一遍影片」清單。
- 一鍵「分享到 LINE」與「複製訊息」；月份條帶切換、「回到今天」。

**自訂讀經規劃（`planner.html`）**
- 自選書卷（全選／舊約／新約／福音書）、順序（正典創→啟／教會傳統順序）。
- 速度：每天幾章 → 算完成日，或 指定完成日 → 算每天幾章。
- 逐日清單，可展開經文＋每章第一遍影片；勾選完成、進度條、今天高亮、跳到今天/未讀。
- 進度雲端同步（Google 登入 或 同步碼），匯出/複製計畫。

**全站**
- 深／淺色切換、字級（標準/大/特大），記憶設定、首次跟隨系統。
- PWA：可「加到主畫面」當 App、離線可開。
- 無障礙：鍵盤焦點、aria-label、支援減少動態效果、放大點擊區。

---

## 檔案結構（重點）

| 檔案 | 用途 |
|---|---|
| `index.html` / `planner.html` | 每日進度頁 / 自訂規劃頁 |
| `data/schedule.json` | 每月排程（日期→三軌道），**每月手動新增** |
| `data/reading_order.json` | 教會傳統讀經順序（1189 章一循環，創世記起） |
| `data/yt_map.json` | 章節→第一遍 YouTube videoId（全 1189 章） |
| `data/bible_books.json` | 66 卷書名/編號/章數 |
| `data/summary.json` / `data/split_days.json` | 章節摘要 / 長章節分多天 |
| `tools/validate.py` | 資料驗證器（改完 `data/` 必跑） |
| `tools/fetch_yt_map.py` | Colab 用：重建影片對照表 |
| `manifest.webmanifest` / `sw.js` / `icons/` | PWA |

---

## 每月更新（最常做）

1. 取得教會當月「月曆表」圖片（四欄：日期/靈修/速讀5/速讀10）。
2. 依 `CLAUDE.md` §3 格式，把每天三欄寫進 `data/schedule.json`（用書卷簡稱）。
3. 跑 `python3 tools/validate.py`，看到 `ALL OK` 才 commit。
4. `git add -A && git commit -m "新增 X 月進度" && git push`。GitHub Pages 自動部署。

> 教會的讀經次序**每一遍會重新編排**，故 `reading_order.json` 的未來進度僅為「預測」，
> 一律以教會當期月曆表為準（見 `CLAUDE.md` §6）。

---

## 部署與設定

- **GitHub Pages**：repo `589411/daily-bread`，branch `main`，root。`CNAME` 綁定自訂網域。
- **自訂網域**：Cloudflare DNS `daily-bread` CNAME → `589411.github.io`（DNS only）。
- **Firebase（雲端同步）**：啟用 Google＋匿名登入、建 Firestore、填 `planner.html` 的 `FIREBASE_CONFIG`、加授權網域。完整步驟見 `CLAUDE.md` §11。

---

## 開發歷程與關鍵決策（記錄）

依時間順序，留給未來協作者理解「為什麼這樣設計」：

1. **接手既有初版**：原 `index.html` 用 `MM-DD` 當排程 key、YouTube 靠 RSS 比對最近影片——兩者都不可靠。
2. **改用完整日期排程**：`MM-DD` 跨年會錯位，改為 `YYYY-MM-DD`。5–6 月排程由教會月曆表圖片轉錄而來。
3. **YouTube 對照表**：頻道 @jam2939「陪你讀聖經」已錄三遍；鎖定**第一遍**（播放清單標題剛好以《陪你讀聖經》結尾）。用 Colab + YouTube Data API 的 playlistItems 一次建全 1189 章對照表（省配額）。
4. **讀經順序考證**：先誤判「每遍順序全變、無法預測」；後用第一性原則對齊驗證，發現 CSV 的教會傳統順序對齊「今天=代下8」可重現 5–6 月月曆 **59/61**（約 97% 穩定，僅偶有局部換書）。重建為乾淨的 `reading_order.json`（1189 章、創世記起、段內順排；只有詩篇分段、長章節分多天對同一影片）。
5. **經文 API 修正**：bolls.life 正確端點是 `/get-text/CUV/`（和合本＝CUV，非 CUNP）；前端用 `fetchJson()` 直連→allorigins→corsproxy 依序備援。
6. **自訂讀經規劃**：以 `bible_books.json`（全 1189 章）為基礎，支援自選書卷、兩種順序、兩種速度；進度雲端同步（Firebase Google 登入＋同步碼）。
7. **體驗強化**：深淺色、字級、PWA、無障礙、影片內嵌播放、速讀各章影片清單、分享到 LINE、回到今天。

> 完整 commit 歷史見 `git log`。維護規範與踩過的雷整理在 `CLAUDE.md`。
