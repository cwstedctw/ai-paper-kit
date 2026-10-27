# output：成品（程式產生，不要手改）

這裡的東西都是 `uv run build.py` 從 `source/` 做出來的。整個資料夾刪掉也沒關係，下次 build 會全部重做；手改的地方也會被蓋掉。這個資料夾不推上 GitHub（這份說明除外）。

| 檔案或資料夾 | 是什麼 | 誰做的 |
|---|---|---|
| `main.pdf` | **論文**，你要看的就是這個 | LaTeX 排版 |
| `main.docx` | Word 版（加 `--docx` 才有） | pandoc |
| `numbers.tex` | 內文用的數字，一個數字一個代號，例如 `\NTotal` | `source/scripts/analyze.py` |
| `tables/` | 論文的表：`.tex` 放進 PDF，`.csv` 可以用 Excel 打開核對 | `analyze.py` |
| `figdata/` | 畫圖用的資料表（CSV，也能用 Excel 打開） | `analyze.py` |
| `figures/` | 畫好的圖（PDF 版和 PNG 版） | `source/gnuplot/*.gp` |
| `images/` | 你放的圖片檔（流程圖、照片），從 `source/images/` 原樣複製 | `build.py` |
| `latex-log/` | 排版過程的紀錄；出錯時 AI 會來這裡看 | LaTeX |

要在 Word 裡改 `main.docx`，先另存到別的資料夾（例如桌面），因為下次產生 Word 版會蓋掉這一份。
