---
name: youtube-playlist-map
description: >
  用 YouTube Data API（在 Google Colab）把某頻道的播放清單建成「影片標題→videoId」對照表，
  省 API 配額。當使用者要大量對應 YouTube 影片、依系列/播放清單篩選、或解析標題抽出關鍵欄位時使用。
---

# 頻道播放清單 → videoId 對照表（YouTube Data API, Colab）

## 步驟

1. Google Cloud Console 免費申請 **YouTube Data API v3** 金鑰；Colab 左側「祕密」存成 `YOUTUBE_DATA_API_KEY`。
2. **先列播放清單**：`playlists.list(channelId, part=snippet,contentDetails)` 印出每個清單的 id／標題／影片數，找出你要的系列。
3. **抓清單內容用 `playlistItems.list`（part=snippet,contentDetails，maxResults=50）**，逐頁翻 `nextPageToken`。
4. 解析每部影片標題 → 抽出 key（例：書卷＋章），配 `videoId`，輸出 JSON。
5. 用 `channels.list(forHandle=...)` 由 @handle 解析出 channelId。

## 踩過的坑

- **配額**：`search.list` 一次 **100 units**；`playlistItems.list` 一次 **1 unit／50 部**。逐章 search 會爆每日 1 萬額度——**一律走 playlistItems**。整個頻道約 70 units。
- **標題解析的陷阱**：
  - **全形數字**（`羅馬書２`）要先轉半形再 parse。
  - **單章內容**（書名沒帶數字）要特例處理（key 用名稱本身）。
  - 去掉「第／章／篇」與括號附註（如 `(1-53節)`）。
- **依系列篩選**：同一內容可能錄了多遍（標題結尾如《…》《…2》《…3》）。用「標題剛好以某字串結尾」精準鎖定某一遍，排除特別篇等。
- 跑完務必檢查**覆蓋率**（你需要的清單是否都對到），列出缺漏。

## FAQ

- **重跑一次就會有每一筆連結嗎？** 對；它把（你篩選的）播放清單全部影片標題抽出來配 videoId，輸出整張對照表，只收「真的有上片」的項目，並回報缺哪些。
