---
name: line-daily-push
description: >
  用 Cloudflare Worker＋Cron Trigger 每天定時把內容推到 LINE 群組（LINE Messaging API push），
  並支援「把官方帳號邀進群組就自動加入推播名單」。當使用者要做 LINE 定時推播、抓 groupId、
  多群組自動註冊、或排查推播不動時使用。
---

# LINE 每日自動推播（Cloudflare Worker + Cron）

靜態網站沒有伺服器，故用 Worker 的 Cron Trigger 每天呼叫 LINE push API。

## 步驟

1. **LINE Messaging API channel**（LINE Developers）→ 取得 **Channel access token**、**Channel secret**。
2. **Cloudflare 建「Worker」**（不是 Pages）：Workers & Pages → Create → Workers → 「Start with Hello World!」→ 命名 → Deploy → **Edit code** 貼上推播程式 → Deploy。
3. **Secrets**（Worker → Settings → Variables and Secrets，Type 選 Secret）：`LINE_TOKEN`、`LINE_CHANNEL_SECRET`、`GROUP_ID`。
4. **KV（多群組自動註冊）**：建 KV namespace → Worker → **Bindings 分頁**（不在 Settings 裡）→ Add → KV namespace，變數名 **`GROUPS`**。
5. **Cron Trigger**：Settings → Triggers → 加 `0 23 * * *`（UTC）＝台灣 07:00。
6. **Webhook**（要自動註冊才需）：LINE Webhook URL 指到 Worker 網址、開啟 Use webhook。Worker 收 `join` 事件就把 groupId 存進 KV、回覆歡迎；`leave` 則移除。cron 推給「KV 名單 ∪ GROUP_ID」。
7. **測試端點**：`/?` 預覽今天訊息、`/?send=1` 立即推、`/?list=1` 看群組數。

## 取得 groupId（單群組、一次性）

webhook.site 取臨時網址 → 設為 LINE Webhook URL → 把 OA 邀進群組並發一則訊息 → 在 webhook.site 看 `source.groupId`。抄完把 webhook 關掉。**沒有 token 經過 webhook，風險低**；要完全自host 就用第 6 步的 Worker webhook。

## 踩過的坑

- **Worker ≠ Pages**：建立時要在 **Workers** 那邊、選 Hello World；別連 git repo、別加自訂網域。它只用 Cron＋預設 `*.workers.dev`，**不需要 DNS、不會跟現有 Pages/Worker 衝突**（衝突只發生在路由重疊）。
- **改了程式要按 Deploy**：曾把舊版貼上去忘了更新，`?list=1` 不認得而回到預設預覽——換最新碼再 Deploy 即可。
- **「There is nothing here yet」**＝請求沒到你的程式：用錯網址（`xxx` 要換成真實帳號子網域，如 `name.<acct>.workers.dev`）、workers.dev 路由被關、或沒 Deploy。
- **Cron 是 UTC**：台灣時間 − 8 小時。早上 7:00 → `0 23 * * *`。
- **簽章驗證**：設 `LINE_CHANNEL_SECRET` 後，用 HMAC-SHA256 驗 `x-line-signature`，擋偽造 POST。
- token/secret 一律放 Worker Secret，不進 repo。KV 免費額度（10萬讀、各 1千寫/列/刪、1GB）對「一個小清單」綽綽有餘。
