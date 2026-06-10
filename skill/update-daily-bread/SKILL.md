---
name: update-daily-bread
description: >
  維護與擴充「每日靈糧（中靈版）」讀經網站（repo 589411/daily-bread，線上
  https://daily-bread.launchdock.app）。當使用者要新增某月份讀經進度、從教會月曆表圖片
  轉錄排程、刷新 YouTube 第一遍影片對照表、調整自訂讀經規劃、設定 Firebase 雲端同步、
  處理 PWA／網域／部署，或修改 index.html／planner.html／data/*.json 時使用。
---

# 維護每日靈糧網站

中壢靈糧堂每日讀經網站的維護技能。**先讀 repo 根目錄的 `CLAUDE.md`**——那是資料格式與規範的唯一真實來源；本檔是流程地圖。

## 鐵則（先記住，別踩雷）

- 排程一律以**完整日期** `YYYY-MM-DD` 為 key（不要用 `MM-DD`，跨年會錯位）。
- 教會讀經次序**每一遍會重新編排**，`reading_order.json` 的未來進度只是「預測」；**唯一可信來源是教會當期公佈的月曆表**。別用舊 CSV/HTML 推算當作定案。
- YouTube 只收「第一遍」：播放清單標題剛好以《陪你讀聖經》結尾（排除 2／3 遍、特別篇、週末親近神）。
- 經文 API：`https://bolls.life/get-text/CUV/{書卷編號}/{章}/`（和合本＝CUV，不是 CUNP；端點 `/get-text/` 不是 `/api/`）。
- **改完 `data/` 一定先跑 `python3 tools/validate.py`，看到 `ALL OK` 才 commit。**

## 任務地圖

**A. 新增一個月進度（最常見）**
1. （可選，省工）先 `python3 tools/predict_check.py gen 2026-07-01 2026-07-31` 產生「預測靈修」草稿貼進 `data/schedule.json`。
2. 教會月曆表（四欄：日期／靈修／速讀5／速讀10）→ 依 `CLAUDE.md` §3 補齊三軌道（靈修核對草稿、s5/s10 照表填）。
3. `python3 tools/predict_check.py verify 2026-07` → 確認靈修命中率、照月曆表修正列出的「局部換書」日。
4. `python3 tools/validate.py` → `ALL OK`。validate 若警告某靈修章節「第一遍無影片」→ 見任務 B。
5. （選用）從 `每日靈糧V2.4.1.csv` 補摘要到 `data/summary.json`。
6. `git add -A && git commit -m "新增 X 月進度" && git push`。

**B. 刷新 YouTube 第一遍對照表**（少做，整本已收錄）
- 在 Google Colab 跑 `tools/fetch_yt_map.py`（Colab 祕密放 `YOUTUBE_DATA_API_KEY`），它自動抓所有第一遍播放清單→輸出 `yt_map.json`。放回 `data/`，跑 validate，commit。詳見 `CLAUDE.md` §7。

**C. 自訂讀經規劃（planner.html）**
- 書卷／章數有變只動 `data/bible_books.json`。計畫邏輯純前端。詳見 `CLAUDE.md` §10。

**D. 雲端同步（Firebase）**
- Google 登入＋同步碼。設定金鑰與安全規則見 `CLAUDE.md` §11。未填金鑰時自動降級為只存本機。

**E. PWA／離線**
- 新增需離線快取的檔案時，加進 `sw.js` 的 `SHELL` 並升 `CACHE` 版本號。詳見 `CLAUDE.md` §12。

**F. 部署／網域**
- GitHub Pages（main/root）＋ `CNAME`（daily-bread.launchdock.app）＋ Cloudflare DNS。改網域要同步更新 Firebase 授權網域。

## 驗收

- `tools/validate.py` 顯示 `ALL OK`。
- 開 https://daily-bread.launchdock.app/ ：當天日期顯示正確章節、經文載入、影片可播、複製/分享 LINE 可用；planner 可產生計畫並同步。
