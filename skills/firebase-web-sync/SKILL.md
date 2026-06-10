---
name: firebase-web-sync
description: >
  為純前端（無自建後端）的網站加上雲端同步：Google 登入＋免登入「同步碼」兩種方式，
  用 Firebase Auth＋Firestore。當使用者要跨裝置同步使用者資料、設定 Firebase、寫安全規則時使用。
---

# 前端 App 雲端同步（Firebase：Google 登入＋同步碼）

## 步驟

1. Firebase Console 建專案 → Authentication → Sign-in method → **啟用 Google 與 匿名（Anonymous）**。
   （同步碼用匿名登入在背後撐著；沒啟用匿名，同步碼會連不上。）
2. 建立 **Firestore Database**，啟動時選 **「正式版模式」**（見下方坑）。
3. 專案設定 → 新增 **Web 應用** → 複製 `firebaseConfig`（apiKey/authDomain/projectId/appId）→ 填進前端。
4. Authentication → Settings → **授權網域** 加入你的網域（與測試用 `localhost`）。
5. Firestore 安全規則：
   ```
   match /users/{uid} { allow read, write: if request.auth != null && request.auth.uid == uid; }
   match /codes/{code} { allow read, write: if request.auth != null; }   // 同步碼
   ```
6. 前端：Google 登入或輸入同步碼 → `pullCloud()` 還原；資料變動 → `cloudPush()`（`merge:true`）。資料模型 `users/{uid}` 或 `codes/{code}`。

## 踩過的坑

- **Firestore 一定選「正式版模式」**：測試模式會讓資料 30 天內**完全公開**，且 30 天後規則自動關閉、同步突然失效。正式版預設全鎖，再貼上面規則精準開放。
- **firebaseConfig 放前端是正常且安全的**：apiKey 本來就會出現在前端，安全靠 Firestore 規則把關，不用藏。你只需要那個 config 物件的值，**不必**貼 Firebase 給的初始化 `<script>`（前端已自帶 init）。
- **同步碼安全性**：知道碼的人就能讀寫該筆（用隨機 6 碼、純低敏資料降低風險）；要逐人隔離請用 Google 登入路徑。
- 未填金鑰時讓整個雲端區塊**自動降級為只存本機**，網站照常運作。

## FAQ

- **npm 那頁要做嗎？** 不用，用 `<script>` 版 SDK＋程式內 `initializeApp` 即可，npm/CDN 設定頁直接跳過。
- **支援電子郵件 ≠ 授權網域**：Google 登入設定頁要的是 OAuth 同意畫面的聯絡信箱；授權網域在 Authentication → Settings 另設。
