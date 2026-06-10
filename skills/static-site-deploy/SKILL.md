---
name: static-site-deploy
description: >
  把純前端靜態網站部署到 GitHub Pages，並綁定 Cloudflare 上的自訂（子）網域與 HTTPS。
  當使用者要上線一個 HTML/JS 網站、設定 CNAME 自訂網域、處理 GitHub Pages 與 Cloudflare DNS、
  或遇到 git push 被拒、git lock 檔卡住時使用。
---

# 靜態網站部署（GitHub Pages + Cloudflare 自訂網域）

## 步驟

1. **GitHub Pages**：repo → Settings → Pages → Source「Deploy from a branch」→ 選 `main` / `(root)`。
2. **自訂網域**：在 repo 根目錄放一個 `CNAME` 檔，內容就是網域（例 `sub.example.com`，單獨一行）。push 後 Pages 會認得。
3. **Cloudflare DNS**：在該網域的 zone 新增 **CNAME**：名稱＝子網域、目標＝`<user>.github.io`，**Proxy 狀態設「DNS only（灰雲）」**。
4. 等 GitHub Pages 簽好 SSL 後，勾 **Enforce HTTPS**。
5. 網站若用 `fetch()` 讀本地 JSON，**必須用伺服器或 Pages 開啟，不能 `file://`**（CORS 會擋）。

## 踩過的坑

- **灰雲很重要**：CNAME 若開 Cloudflare 代理（橘雲），會與 GitHub 的 SSL 憑證打架。先用 DNS only，讓 GitHub 自己簽憑證；要 CDN 之後再說。
- **push 被拒「fetch first / 遠端有你沒有的提交」**：常是你在 Pages UI 設自訂網域時，**GitHub 自動 commit 了一個 CNAME 到遠端**，與你本機新建的 CNAME 衝突。解法：
  ```
  git pull --rebase origin main
  # 若 CNAME 衝突（add/add）：
  printf 'sub.example.com\n' > CNAME && git add CNAME && git rebase --continue
  git push origin main
  ```
- **git lock：「Unable to create '.git/HEAD.lock' / index.lock」**：殘留鎖檔。`rm -f .git/HEAD.lock .git/index.lock` 後重試。
- **子網域數量限制**：Cloudflare 免費 zone 的 DNS 記錄上限（2024-09 後新建為 200 筆、之前 1000 筆）；**GitHub Pages 一個 repo 只能綁一個自訂網域**，多個子網域＝多個 repo，且網域全 GitHub 唯一。

## FAQ

- **用子網域會影響後台數據嗎？** 不會。換網址只需把新網域加進相關服務的「授權網域」（如 Firebase）；資料本身與網域無關。換網址後使用者要在新 origin 重新登入，但雲端資料保留。
- **開源 repo 安全嗎？** 程式公開沒問題，**機密（token 等）絕不進 repo**，放部署平台的加密環境變數。
