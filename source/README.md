# source：原料（你和 AI 只改這裡）

論文裡的每一個數字、每一張表、每一張圖，都從這裡的檔案做出來。`python build.py` 會讀這裡，把成品寫到 `output/`。

| 資料夾 | 放什麼 | 誰改 |
|---|---|---|
| `data/` | 研究資料（CSV）和欄位說明。範例是重建的練習資料，加上從論文抄下來對照用的數字 | 你放進來；AI 只讀不改 |
| `refs/` | 書目 `refs.bib`，由 Zotero 自動匯出 | Zotero；不手改 |
| `scripts/` | 分析程式 `analyze.py`：算數字、做表、做畫圖用的資料表 | AI 改，你決定統計方法 |
| `gnuplot/` | 畫圖腳本，一張圖一個 `.gp` 檔 | AI 改，你決定要什麼圖 |
| `paper/` | 論文本文 `main.tex` | AI 寫、改；你看 `output/main.pdf` |

**原則**：要改結果，就改這裡，再跑一次 build。不要去改 `output/` 裡的東西，下次 build 會被蓋掉。
