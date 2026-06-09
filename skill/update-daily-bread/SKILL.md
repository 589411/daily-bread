---
name: update-daily-bread
description: >
  更新「每日靈糧（中靈版）」讀經網站。當使用者要新增某月份的讀經進度、
  從教會月曆表（圖片）轉錄排程、刷新 YouTube 第一遍影片對照表、或部署到
  GitHub Pages 時使用。涉及 repo 589411/daily-bread 的 data/schedule.json、
  data/yt_map.json、data/summary.json。
---

# 更新每日靈糧網站

本技能用於維護中壢靈糧堂「每日靈糧（中靈版）」讀經網站。

## 先讀

開始前先讀 repo 根目錄的 **`CLAUDE.md`**——那是完整維護手冊與資料格式的唯一真實來源。
本檔只是流程提醒。

## 最常見任務：新增一個月的進度

1. 取得教會公佈的月曆表（四欄：日期／靈修進度／速讀5章／速讀10章）。
2. 依 `CLAUDE.md` §3 格式，把每天三欄寫進 `data/schedule.json`，key 為 `YYYY-MM-DD`，
   一律用 §5 的書卷簡稱。
3. **執行 `python3 tools/validate.py`，必須看到 `ALL OK` 才能繼續。**
4. 若 validate 警告某靈修章節「第一遍無影片」，依 `CLAUDE.md` §7 用 Colab 重建 `yt_map.json`。
5. （選用）從 `每日靈糧V2.4.1.csv` 補摘要到 `data/summary.json`。
6. `git add data/ && git commit -m "新增 X 月進度" && git push`（GitHub Pages 自動部署）。

## 鐵則（來自踩過的雷）

- 只用教會「當期月曆表」當排程來源；**絕不**用 `每日靈糧排序.csv` 或 `202*.html` 推算
  （讀經次序每遍重編，舊資料是不同計畫）。
- 排程 key 用完整日期，不用 `MM-DD`。
- YouTube 只收「《陪你讀聖經》」結尾的播放清單（第一遍），排除 2／3／特別篇。
- 改完 `data/` 一定先跑 `tools/validate.py` 再 commit。

## 驗收

- `tools/validate.py` 顯示 `ALL OK`。
- 開 https://589411.github.io/daily-bread/ ，確認當天日期顯示正確章節、影片縮圖、經文載入、複製鍵可用。
