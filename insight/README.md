# 原文彩蛋（Lost in Translation）

聖經翻譯過程中「掉落的彩蛋」：中譯本無法呈現的希伯來文／希臘文精神——
諧音雙關、名字詞源、語義場、離合結構、文法損失……幫助華人讀者聽見原文的聲音。

- 瀏覽頁：`../insight.html`（GitHub Pages 部署後直接可看）
- 目前規模：26 筆（2026-07-05 首批），黃金範例：耶1:11 שקד 諧音雙關

## 設計哲學（承 bible-atlas）

**品質來自規格，而非模型。** 三份文件三層把關：

| 檔案 | 角色 |
|---|---|
| `RULES.md` | 品質憲法：分類法、schema、寫作規則、審核 rubric |
| `HARNESS.md` | 生產線：sub-agent 並行流程、踩坑紀錄、下一批候選 |
| `tools/validate_insights.py` | L1 程式驗證：每個原文字串逐節比對 WLC/TR，和合本引文比對 CUV |
| `data/insights.json` | 條目本體（純資料，與任何前端解耦） |

核心原則：**生成便宜，驗證才是產品。** 每筆條目攜帶可程式驗證的錨點
（原文字串＋經節位置＋Strong's），幻覺過不了驗證器。

## 獨立性與整合介面

本資料夾自成一體，隨時可拆成獨立 repo（只需一併帶走 `insight.html`，
並把 `data/bible_books.json` 複製進來）。

已預留的整合點：
1. **daily-bread 首頁**：以（bookNo, chapter）查 `insights.json`，今日靈修章節有彩蛋
   即顯示卡片（查詢邏輯見 `insight.html` 的 `todayEgg()`，可直接搬）。
2. **LINE 推播**：`tools/line-worker/worker.js` 組訊息時同樣查表，附一行
   「🥚 今日彩蛋：杏樹＝醒著的樹」＋連結。
3. **bible-atlas（聖經像素地圖）**：條目以書卷＋章為 key，時代資料可反查該時代
   經卷的彩蛋清單；insights.json 是純資料，符合 atlas 的引擎/資料分離原則。

## 維護

- 新增條目：照 `HARNESS.md` §1 流程（sub-agent 並行生成 → L1+L2 驗證 → 合併）
- 改完必跑：`python3 insight/tools/validate_insights.py` → `ALL OK` 才 commit
- 驗證快取 `tools/.cache/` 不進 repo
