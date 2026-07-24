# STATUS — 每日靈糧

> 單一真相。每次離開前更新（全域憲法收尾鐵律）。
**最後更新：** 2026-07-24
**整體狀態：** 🔵 維護中

## 一句話現況
讀經進度 PWA。**2026-07 進度已上線**（schedule.json 92 天、validate ALL OK）。
LINE **每日自動推播已停用**（免費額度 200 則/月、群組按人數計費撐不住，7/3 燒完額度靜默中斷）；
**改為關鍵字回覆**：群組輸入「每日靈糧」→ bot 回覆當天進度（reply 免費、不計額度）。已部署、cron 已移除。

## 下一個具體動作 ⭐
1. **驗證關鍵字回覆**：在有邀官方帳號的群組輸入「每日靈糧」，確認 bot 回當天進度。
   （前置：LINE Developers → Messaging API → Webhook URL = worker 網址、Use webhook 開；OA 後台「自動回應訊息」可關避免干擾。）
2. 等教會公布 **2026-8 月曆頁**（blccjl.org.tw/2026-8）→ 照 §4 轉錄三軌道進 schedule.json。
   - 靈修 d：**逐日照月曆頁轉錄**（預測已不可信，見已知坑）。
   - 速讀5 s5：正典固定表；速讀10 s10：正典連續循環每日 +10。
   - 收尾：`python3 tools/validate.py` → ALL OK → commit & push。

## 怎麼驗證這一步成功
讀經資料 JSON 通過 `tools/validate.py`（ALL OK）、本地預覽 PWA、推播測試發送成功。

## 卡點 / 待你決定
- 5–6 月的 s10 仍是舊「連續循環」演算法（未對齊任何固定表）；7 月起才改用循環規則。要不要回頭統一 5–6 月 s10？（目前不影響顯示，暫擱置。）

## 進度脈絡（新的在上）
- 2026-07-24 查修「7/3 後推播停」：根因＝LINE 免費 200 則/月額度用罄（群組 push 按人數計費，4 群 59 人→每天 59 則，7/1~7/4 燒完 200）。改方向：停用每日推播（移除 cron）、改「群組輸入『每日靈糧』自動回覆」（reply 免費不計額度）。worker.js + wrangler.toml 已改並部署。
- 2026-06-27 新增 2026-07 進度（靈修照教會月曆頁）；修正 5–6 月速讀5章對齊正典固定表；釐清三軌道演算法
- 2026-06-19 起草此 STATUS
- 2026-06-11 記錄 LINE cron 設定坑（Cron expression 分頁）
- 2026-06-10 LINE 自動推播上線，技能工具包索引改通用版

## 已知坑
- ⚠️ **LINE 免費方案訊息額度按「收訊人頭」計費**：推到群組 ＝ 該群組「當下人數」則（不是每群 1 則）。免費 200 則/月，4 群 59 人每天推一次＝59 則，約 3.4 天就用罄，之後 push 被 LINE 擋（回 429）。**worker 的 scheduled() 沒檢查 LINE 回應→靜默中斷、不報錯**。每月 1 號（JST）重置。→ 教訓：群組主動推播在免費方案不可行；**reply（replyToken 回覆）不計額度**，故改用關鍵字回覆。查證工具：LINE `GET /v2/bot/message/quota`、`/quota/consumption`、`/insight/message/delivery?date=YYYYMMDD`（apiPush/apiReply 分項）。
- LINE cron 的 Cron expression 要在對的分頁設定（已踩過）。
- ⚠️ **靈修順序預測（reading_order.json）7 月起失效**：2026 實測命中 5月29/31、6月30/30、但**7月僅 6/31**（教會讀完代下後跳路加福音1-24，預測卻是詩篇107+）。§6／Roadmap#1「可一次產生整年排程」的假設**不成立**，往後每月仍須照教會月曆頁逐日轉錄。
- ⚠️ **legacy Pages 連續推送會互相取消部署**：短時間內推兩個 commit，後者會把前者還在跑的 deploy 取消，卡成 `status: errored`、線上沒更新（build 其實成功）。對策：**改動併成單一 commit 再推**，或推完等部署綠燈再推下一個；已卡住時用 `gh api --method POST repos/589411/daily-bread/pages/builds` 觸發乾淨重建，再 `curl .../data/schedule.json` 驗證上線。
