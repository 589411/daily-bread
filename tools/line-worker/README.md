# LINE 每日自動推播（Cloudflare Worker）

每天定時把當天讀經進度推到 LINE 群組。程式碼在 `worker.js`，**token 與 groupId 不在這裡、也不進 repo**，而是放在 Cloudflare Worker 的加密環境變數。

## 前置：取得 groupId（一次性）

1. 開 https://webhook.site 取得臨時網址。
2. LINE Developers → Messaging API channel → Webhook URL 填該網址、開啟 Use webhook。
3. LINE Official Account Manager → 回應設定 → 允許「加入群組／多人聊天」。
4. 把官方帳號邀進目標群組，在群組發一則訊息。
5. 回 webhook.site 看 POST 內容，找 `"source":{"type":"group","groupId":"Cxxxx..."}`，抄下 `Cxxxx...`。
6. 之後日常推播不需要 webhook，可關掉。

## 部署 Worker（Cloudflare 主控台，免裝工具）

1. Cloudflare Dashboard → **Workers & Pages → Create → Worker**，命名如 `daily-bread-line`，Deploy。
2. **Edit code**：把 `worker.js` 全部貼上 → **Deploy**。
3. **Settings → Variables and Secrets**：新增兩個 **Secret**（加密）：
   - `LINE_TOKEN` = LINE Channel access token
   - `GROUP_ID`   = 上面抓到的 groupId
4. **Settings → Triggers → Cron Triggers**：新增 `0 23 * * *`（UTC）＝ 台灣每天早上 **07:00**。
   （要別的時間就換算：台灣時間 − 8 小時 = UTC。）
5. **測試**：開 `https://daily-bread-line.<你的帳號>.workers.dev/` 預覽今天訊息；
   加 `?send=1` 會**實際推一次**到群組，確認沒問題。

## 注意

- `worker.js` 執行時即時抓 `daily-bread.launchdock.app/data/*.json`，所以永遠跟網站同步，更新排程不用改 Worker。
- 測試用的 `?send=1` 端點任何人知道網址都能觸發推送（只會送當天那則固定訊息）。確認可用後，可把 `worker.js` 裡的 `fetch(...)` handler 整段刪掉，只留 `scheduled`，就只剩 cron 會推。
- LINE 免費方案有每月訊息上限，一天一則遠低於上限（額度以 LINE 當前定價為準）。
- token 一律放 Cloudflare Secret，**不要**寫進程式碼或 commit。
