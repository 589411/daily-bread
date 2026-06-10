---
name: pwa-offline
description: >
  把靜態網站變成可「加到主畫面」當 App 開、離線也能載入的 PWA。當使用者要做 manifest、
  service worker、App 圖示，或處理「iPhone 找不到加入主畫面」「更新後卡舊版」等問題時使用。
---

# 靜態網站 PWA 化（可安裝＋離線）

## 步驟

1. **manifest.webmanifest**：`name`、`short_name`、`start_url:"./index.html"`、`display:"standalone"`、`theme_color`、`icons`（192／512，含一個 `purpose:"maskable"`）。
2. **圖示**：可用 Python Pillow 直接「畫」一個（純幾何圖形免字型），輸出 192／512 PNG。
3. **service worker（sw.js）**：對**同源檔案**用 **network-first**（有網路抓最新→更新即時生效；離線才回退快取）；外部 API 不攔截。安裝時 `cache.addAll(SHELL)` 預快取。
4. **掛上**：兩個頁面 `<head>` 加 `<link rel="manifest">`、`theme-color`、`apple-touch-icon`，並 `navigator.serviceWorker.register('sw.js')`。

## 踩過的坑

- **iPhone Safari 不會自動跳「加入主畫面」**（那是 Android Chrome 行為）。iOS 一律手動：**分享鈕 ⬆️ → 往下滑 → 加入主畫面**。
- **最常見：從 LINE/FB 點連結開的是「App 內建瀏覽器」，沒有加入主畫面選項**。要先「用 Safari 開啟」。
- **別用 cache-first**：會讓使用者卡在舊版。network-first 才能 push 後立即更新、又保有離線能力。
- 新增需離線快取的檔案時：加進 `sw.js` 的 `SHELL` 陣列，並把 `CACHE` 版本字串升版（v1→v2）以淘汰舊快取。

## FAQ

- **PWA 需要什麼條件？** HTTPS（GitHub Pages／自訂網域都有）、manifest、註冊的 service worker。
