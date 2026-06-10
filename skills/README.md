# Web 專案技能工具包

一組可重複使用的技能，涵蓋「把純前端網站做起來、上線、加上雲端與自動化」常見任務，每個都附**踩過的坑**與常見問題。皆為通用版（使用前把佔位符如 `<your-domain>`、`<user>.github.io`、`@handle` 換成你的）。在「設定 → Capabilities」安裝後用 `/名稱` 啟動。

| 技能 | 用途 | 何時用 |
|---|---|---|
| `static-site-deploy` | 靜態網站上 GitHub Pages＋自訂網域（Cloudflare DNS／HTTPS） | 部署純前端網站、綁網域時 |
| `pwa-offline` | 把靜態網站變成可「加到主畫面」＋離線可開的 PWA | 想讓網站像 App、培養每日開啟習慣時 |
| `firebase-web-sync` | 純前端 App 加雲端同步（Google 登入＋同步碼） | 要跨裝置同步、又沒有後端時 |
| `line-daily-push` | LINE 每日自動推播（Cloudflare Worker＋Cron） | 每天定時把內容推到 LINE 群組時 |
| `youtube-playlist-map` | 用 YouTube Data API 把播放清單建成「標題→videoId」對照表 | 大量對應影片、且要省 API 配額時 |
| `cyclic-schedule-reconstruct` | 從雜亂歷史資料重建並驗證「週期性排程／順序」 | 有不乾淨的歷史排程、想找規律並預測未來時 |

每份 SKILL.md 都含：何時用、步驟、**踩過的坑**、FAQ。

> 註：本 repo 另有一個「專案專屬維護技能」（位於 `../skill/`），它會帶該專案自己的（公開）網址，僅供維護該專案用，不屬於這個通用工具包。
