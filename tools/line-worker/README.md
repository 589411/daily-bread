# LINE 讀經進度（Cloudflare Worker）

> **2026-07 起：關鍵字回覆模式（每日主動推播已停用）。** 用 LINE **reply**（`replyToken`），
> **不計入每月訊息額度**，免費方案即可、群組人數再多也零成本。兩種問法：
>
> | 在群組輸入 | bot 回覆 |
> |---|---|
> | 含「**每日靈糧**」的訊息 | 當天的三軌道讀經進度 |
> | 整則就是**經文參照**（`彼前5`／`詩119`／`猶`／`彼得前書5`／`彼前５`） | 那一章：第一遍影片、歷史地圖、原文彩蛋、網站連結（**刻意不標日期**，見下） |
>
> ⚠️ 經文參照的回覆**故意不顯示「這是 X/X 的靈修進度」**：這條路是給人自己讀經用的，
> 讀的人進度不必跟教會同步，標日期會被誤會成「今天該讀這章」。日期只出現在「每日靈糧」那條路。
>
> 經文參照採**嚴格比對**（必須以書卷簡稱／全名開頭、其後只剩數字），所以「我們約3點見面」「今天讀彼前5嗎」不會觸發；
> 單獨的「書」「傳」「可」也不觸發（非單章書一定要帶章號）。已知殘餘風險：單獨傳一則「約3」會被當成約翰福音3章。
> 章數超出會友善提醒（「創世記只有 50 章喔。」）。
>
> **測試不必發 LINE**：部署後開 `https://<worker>/?ref=彼前5` 就能預覽回覆內容；
> 本機用 `npx wrangler dev --local` 再 `curl --get --data-urlencode "ref=彼前5" http://localhost:8787/`。
>
> **為何不再每日主動推播**：LINE 免費方案每月僅 200 則，且**推到群組＝按群組人數計費**（4 群 59 人＝每天 59 則，3~4 天就用罄、之後被 LINE 靜默擋掉）。詳見專案 `CLAUDE.md` §13 的「額度坑」。
>
> **部署**：本資料夾執行 `wrangler deploy`（已含 `wrangler.toml`，`crons = []` 表示不排程；secrets 不受影響）。
> 要恢復每日主動推播：升級 LINE 付費方案後，把 `wrangler.toml` 的 `crons` 改回 `["0 23 * * *"]` 再 deploy。

---

以下為原始「每日自動推播」設定說明，保留供未來付費方案恢復時參考。程式碼在 `worker.js`，**token 與 groupId 不在這裡、也不進 repo**，而是放在 Cloudflare Worker 的加密環境變數。

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
   - ⚠️ **要用「Cron expression」分頁**直接填 `0 23 * * *`。別用「Schedule（Execute Worker every N hours）」模式填 `2300`——那個欄位是「每隔幾小時」、只收 0–23，會報「Hour value must be between 0 and 23」。
   - 設完看「Estimated upcoming events (UTC)」應只剩每天 23:00 一筆；若同時出現 00:00 等多筆，表示有重複 cron，刪到只剩 `0 23 * * *`。
   - cron 只在「設定後的下一個 07:00」首次觸發；當天已過 7 點就明早才發。要立即驗證鏈路用 `/?send=1`。
5. **測試**：開 `https://daily-bread-line.<你的帳號>.workers.dev/` 預覽今天訊息；
   加 `?send=1` 會**實際推一次**到群組，確認沒問題。

## 多群組「邀進去就自動加入」（推薦，免每次手動）

設定一次後，以後要把每日靈糧加到新群組，**只要把官方帳號邀進該群組**即可——Worker 會自動把群組存進名單；官方帳號離開群組則自動移除。

1. **建 KV**：Cloudflare → Storage & Databases → **KV → Create**，命名如 `daily-bread-groups`。
2. **綁定到 Worker**：Worker → Settings → **Bindings → Add → KV namespace**，變數名稱填 **`GROUPS`**，選上面那個 namespace。
3. **加簽章驗證**（防偽造）：Worker Secret 新增 **`LINE_CHANNEL_SECRET`** = LINE channel 的 Channel secret（Basic settings 裡）。
4. **設 Webhook**：LINE Developers → Messaging API → **Webhook URL** 填本 Worker 網址、開啟 **Use webhook**（這次要**保持開啟**，才能收 join/leave 事件）。建議關掉「自動回應訊息」避免雜訊。
5. 完成！把官方帳號邀進任何群組 → 它會回覆「已加入推播」並開始每天推。
   - `GROUP_ID`（主群組）會永遠包含在名單裡，與 KV 名單合併去重。
   - 看目前群組數：開 `https://<worker>.workers.dev/?list=1`。

> 沒有做這段也能跑：不綁 KV、不設 webhook 時，Worker 只會推 `GROUP_ID` 那一個群組（即目前狀態）。

## 注意

- `worker.js` 執行時即時抓 `daily-bread.launchdock.app/data/*.json`，所以永遠跟網站同步，更新排程不用改 Worker。
- `?send=1`／webhook 端點：有設 `LINE_CHANNEL_SECRET` 後，webhook 會驗章，偽造的 POST 會被擋（401）。`?send=1` 仍是公開測試入口，知道網址者可觸發一次推送（只送當天訊息）。
- LINE 免費方案有每月訊息上限，一天一則遠低於上限（額度以 LINE 當前定價為準；群組變多時留意總量）。
- token／channel secret 一律放 Cloudflare Secret，**不要**寫進程式碼或 commit。
