# WORKFLOW.md：論文流程說明書（給 AI 看的）

> **這份是寫給 AI 助手的。** 老師看的是 `README.md`，老師不用讀這份，也不會自己打指令：老師跟你說話，你照這份去改檔、跑程式，再回報。
> 規矩在 `AGENTS.md`〈論文工作的規矩〉，這份是做法。每一步都寫：老師可能怎麼說、你怎麼做、怎麼驗證、回報什麼。
> **資料夾的分法：原料在 `source/`（data、refs、scripts、gnuplot、paper），成品在 `output/`（numbers.tex、tables、figdata、figures、main.pdf）。** 你只改 `source/`；`output/` 由 build 重做，不手改。範例是用重建的練習資料重算原論文（2021，BMC Geriatrics；書目 Su2021）的結果，`source/data/README.md` 有說明。

## 共通做法

- **指令名稱**：一律用 uv 跑：`uv run build.py`、`uv run tools/<程式>.py`，Windows、Mac 寫法一樣。uv 會照 `pyproject.toml`／`uv.lock` 在這個資料夾的 `.venv/` 裝好 Python 和套件，不動電腦原本的 Python。要加套件：`uv add 套件名`（先問老師），不要用 pip。電腦還沒有 uv：照 README 第三節請老師同意後安裝。
- **跑完整條流程**：`uv run build.py`（要 Word 加 `--docx`）。最後一行是 `BUILD OK pages=… undefined_cites=0 undefined_refs=0 refs=… refs_without_doi=… bib_warnings=…`：頁數、找不到的引用（一定是 0）、找不到的圖表編號（一定是 0）、文獻篇數、標了 `nodoi` 的篇數、書目缺欄位的警告。頁數和文獻數看論文而定，不是錯；`bib_warnings` 不是 0，把上面列出的警告給老師看。失敗時最後一行是 `BUILD FAILED: 原因`。
- **不為了過 build 動手腳**：不改條目類型、不編 DOI、不手改 `output/`、不刪引用。照 `BUILD FAILED` 的訊息做；要改書目，就請老師回 Zotero 改。
- **回報**一律包含：改了哪些檔、build 最後一行、要老師決定的事。
- **紙條與變更報告**：會改檔的工作照 `AGENTS.md` 寫紙條；論文工作的成品是直接改好的工作檔，`workspace/outbox/` 放變更報告（改了哪些檔、為什麼、怎麼驗證）。
- **時間**讀電腦的時間（`date`），不要估。
- **看改了哪些檔**：用 `git -c core.quotepath=off status`。直接打 `git status`，中文檔名會印成 `\347\240\224` 這種八進位碼，老師會以為是亂碼。

## 開一篇新論文（或做研究模擬）

- 老師可能說：「我要開始寫自己的論文」或「我們來做研究模擬」。
- 你怎麼做：先請老師同意，再執行 `uv run tools/new_paper.py`。它把現在的 `source/` 收進 `examples/<名字>/source/`（不刪任何東西），換上骨架：`scripts/analyze.py` 只算人數、`paper/main.tex` 只有各節標題和說明、`gnuplot/` 空的。
  - **研究資料不會被收進 `examples/`**：`source/data/` 的資料檔原地留著，`examples/` 裡只放一份 `data/README.md`（欄位說明）。`examples/` 會跟著推上 GitHub，多一份資料就多一個外流的地方；`.gitignore` 也擋了 `examples/` 裡的資料檔。不要自己把資料複製進 `examples/`。
  - `--refs <檔>`：書目換成這個檔。研究模擬用 `--keep-data --refs material/模擬/refs.bib`（`--keep-data` 是舊寫法，資料本來就會留著，加了也能跑），研究構想在 `material/模擬/研究構想.md`。
  - 想回到舊的那份：`uv run tools/new_paper.py --name <現在這份的名字> --restore examples/<舊的名字>`。這是**複製回** `source/`，`examples/` 裡那份還在；現在這份先收進 `examples/<現在這份的名字>/`；`source/data/` 的資料檔照舊留著。跑完照它的提示 build：`uv run build.py`。
- 骨架也能 build：沒有圖就跳過畫圖，沒有引用就跳過 BibTeX，會編出一頁 PDF。
- 之後照下面第 1–8 步，一節一節做；`examples/` 裡的範例可以參考寫法（分析程式、gnuplot 腳本、表格），但不要把範例的數字或句子搬進新論文。

## ✋ 只有老師能決定的事

研究問題、收哪些文獻、統計方法、資料怎麼解讀、結論說到多強、投哪一本期刊。你每一步都可以提建議，但這些等老師拍板。

---

## 第 0 步：開工

- 老師可能說：「請先讀 AGENTS.md 和 WORKFLOW.md，再跟我報到。」
- 你怎麼做：讀 `AGENTS.md`、這份、`team.md`；有接 GitHub 就先 `git pull`。
- 回報：第一行「領隊 · 」接資料夾完整路徑；這次用什麼模式。

## 第 1 步：找文獻

- 老師可能說：「幫我找＿＿的文獻。」
- 你怎麼做：有付費文獻工具（例如 Scite、Consensus）接在你身上就用；沒有就用免費的 PubMed、Crossref、OpenAlex、Semantic Scholar。**只收查得到的真文獻**：期刊論文附 DOI；台灣的中文期刊、政府報告、書這類沒有 DOI 的，附可以查證的來源（期刊網站、出版單位網頁）。讀不到摘要或原文的，不寫它說了什麼，標 ⚠️。
- 回報：一張表，每篇寫：題目、年份、DOI、為什麼收、摘要裡支持這個理由的那一句。請老師挑。
- 不要做：自己把文獻寫進 refs.bib。老師挑好後加進 Zotero（第 2 步）。

## 第 2 步：Zotero 管書目 → source/refs/refs.bib

三種接法，老師挑一種：

| | 做法 | 你的角色 |
|---|---|---|
| **A. 自動匯出（推薦）** | 老師先把 Zotero 更新到最新版，到 Better BibTeX 官網（retorque.re/zotero-better-bibtex）下載 `.xpi` 檔（用 Firefox 下載要按右鍵另存），在 Zotero 選「工具 → 外掛（Tools → Plugins）」→ 齒輪 →「從檔案安裝（Install Plugin From File）」。之後文獻集按右鍵「匯出文獻集（Export Collection）」→ 格式選 Better BibTeX、勾「保持更新（Keep updated）」→ 存成 `source/refs/refs.bib`。老師在 Zotero 加文獻，refs.bib 自己更新。 | 檢查 refs.bib：筆數、cite key、缺 DOI 的 |
| **B. 你操作 Zotero** | 老師同意後，先裝 uv，再裝 zotero-mcp（`uv tool install zotero-mcp-server`），照它的說明接上。之後你可以搜老師的文獻庫。用 DOI 把文獻加進文獻集（例如 `zotero_add_by_doi`）是**寫入**：要 Zotero 開著，而且要照 zotero-mcp 的說明另外授權（新版 Zotero 例如 `zotero-mcp authorize-local`；舊版要 Zotero 網頁的 API key）。版本與設定以 zotero-mcp 官方說明為準。 | 加文獻前先列給老師看 |
| **C. 不裝外掛** | Zotero 開著，執行 `uv run tools/zotero_export.py "文獻集名稱"`，直接跟電腦上開著的 Zotero 拿書目，存成 refs.bib（超過 100 筆會自動分頁拿完）。 | 執行、回報匯出幾筆 |

B 和 C 都要老師先在 Zotero：設定 → 進階，勾「允許此電腦上的其他應用程式與 Zotero 通訊（Allow other applications on this computer to communicate with Zotero）」。

- **三種接法產生的 cite key（引用代號）格式不一樣。** 換接法之後，main.tex 裡的引用要跟著改；跑 build 會列出找不到的代號。
- **沒有 DOI 的文獻**（例如有些台灣的中文期刊）：請老師在 Zotero 給那一篇加一個標籤 `nodoi`，重新匯出後 build 才會放行，並在結果裡列出來請老師自己對一次。不要自己補 DOI。

- 老師可能說：「我已經把文獻集匯出成 refs.bib，幫我看一下。」
- 回報：幾筆、每筆的 cite key、哪幾筆缺 DOI。工具的書目也會錯（作者漏列、條目類型怪），提醒老師用 DOI 抽查。
- **`bib_warnings=0` 只代表欄位不缺，不代表書目對。** 打開 PDF 的參考文獻看一次，常見的錯：
  - 題目裡的專有名詞被排成小寫（期刊格式會把題目改成句首大寫）：DKAS、SCIDS 這種量表縮寫、人名、地名，在 refs.bib 要用大括號包起來，例如 `({DKAS})`。refs.bib 不手改：請老師在 Zotero 修正（在 Zotero 怎麼標記、匯出才會有大括號，照 Better BibTeX 的說明做），重新匯出後打開 refs.bib 確認大括號在。
  - BMC 這類線上期刊沒有頁碼，用「文章編號」（例如 *BMC Geriatrics* 17:168 的 168）；缺了就請老師在 Zotero 的頁碼欄（Pages）補上。
  - 作者名字、縮寫跟原文不同：用 DOI 查 Crossref（`https://api.crossref.org/works/<DOI>`）對一次。

## 第 3 步：分析資料

- 老師可能說：「我把資料放在 source/data/＿＿，請改分析程式。」
- 你怎麼做：
  1. 先確認老師說過資料符合 `source/data/README.md` 的四個條件；沒說過就先問。
  2. 讀資料和 `source/data/README.md` 的欄位說明。資料讀不進來、說不是 UTF-8：請老師用 Excel 另存新檔，存檔類型選「CSV UTF-8（逗號分隔）」；不要自己轉檔蓋掉 `source/data/` 的檔。
  3. **先提分析計畫，等老師同意**：要做哪些統計、為什麼、會產生哪些數字（巨集名稱）和表格。報告效果量和 95% 信賴區間，不只報 p 值。
     - 先問研究設計：分組是不是隨機的、以個人還是以機構為單位分組、量了幾次。統計方法要跟設計相符；不確定就請老師先問統計顧問，不要照抄範例（範例只做 t 檢定、卡方、Fisher 精確檢定、效果量，因為練習資料只能重現論文的摘要數字）。
     - 排除受試者（寫在 `analyze.py` 上面的 `EXCLUDE_IDS`）、處理離群值、只看某個子群，都由老師決定，並寫進 Methods。不為了顯著換方法。
  4. 同意後改 `source/scripts/analyze.py`：每個結果數字寫成 `output/numbers.tex` 裡的巨集（名字只能用英文字母，例如 `\DKASIntTOneMean`，不能有數字），表格寫成 `output/tables/tableN.tex`，同時寫一份 `tableN.csv` 讓老師用 Excel 核對。數字一律用程式裡的 `fmt()` 四捨五入（跟 SPSS、Excel 一樣，81.25 → 81.3）；p 值用 `pfmt()`（四捨五入到三位是 0.000 才寫 `<0.001`）。
     - **類別變項的 Fisher 精確檢定，用 `analyze.py` 裡寫好的完整列舉函式，不要用 scipy 的 `stats.fisher_exact`**：超過 2×2 的表（例如婚姻狀況四類 × 兩組），scipy 預設用亂數模擬，每次 build 的 p 值都不一樣，build 也不會報錯。兩支 `analyze.py` 裡的函式名稱不一樣：骨架（`tools/skeleton/analyze.py`，開新論文時會放進 `source/scripts/`）叫 `fisher_exact()`，收任何列數 × 欄數的人數表；範例的 `source/scripts/analyze.py` 叫 `fisher_exact_2col()`，只收「類別 × 兩組」的表（每列兩個數）。
     - 表裡縮排的子項目寫 `\quad{}` 接標籤，不要寫 `\quad` 加空白：轉 Word 時 pandoc 會把後面的數字吃掉（「3-6 h」變「-6 h」）。
  5. 跑 build。
- 怎麼驗證：
  - 挑幾個數字，用另一種方法從 `source/data/` 重算，跟 `output/` 對。
  - **連跑兩次 build，`output/numbers.tex` 要一模一樣**（例如先複製一份，再用 `fc`（Windows）或 `cmp`（Mac）比）。不一樣，就是程式裡有亂數，找出來改掉。
- 不要做：改 `source/data/` 的原始檔；清理資料一律寫進程式。
- 數字變了（換資料、排除受試者），把用到這些數字的句子列給老師重讀：數字會自動更新，句子的解讀不會。

## 第 3.5 步：老師用 Excel 做好的表

- 老師可能說：「我在 source/tables/ 放了 my_table.csv，請把它放進論文。」
- build 會把 `source/tables/*.csv`（Excel 另存的「CSV UTF-8」，第一列是欄名）自動轉成 `output/tables/同名.tex`（booktabs 表格），也複製一份 `.csv` 到 `output/tables/`。
- 你怎麼做：在 `source/paper/main.tex` 該放的位置加 table 環境，`\caption`（照老師給的標題）、`\label`、`\input{tables/同名.tex}`，內文用 `\ref` 提到它；跑 build。**不手改 `output/tables/` 裡轉出來的檔，也不改老師的 CSV**；內容要改，請老師改 Excel 重存。
- build 停下來的三種情況照它說的做：表裡有中文 → 改用 xelatex（`main.tex` 第一行）；不是 UTF-8 → 請老師用 Excel 另存成「CSV UTF-8」；跟分析程式產生的表同名 → 請老師改檔名。
- 數字是老師手打進 Excel 的，跟 `analyze.py` 算出來的不一樣：在回報裡提醒老師「這張表的數字是手打的，沒有從資料自動算；資料改了它不會跟著變」。

## 第 4 步：gnuplot 畫圖

- 老師可能說：「加一張圖：＿＿。」
- 你怎麼做：
  1. `source/scripts/analyze.py` 產生這張圖要的資料表 `output/figdata/figN_….csv`（CSV，第一列是欄名；老師也能用 Excel 打開）。**老師自己用 Excel 做好的畫圖資料**放在 `source/figdata/*.csv`，build 會原樣複製到 `output/figdata/`，腳本一樣讀 `figdata/檔名.csv`；這種不用改 analyze.py，也不要改老師的 CSV。
  2. 複製一個現有的 `source/gnuplot/*.gp` 改成新的。build 在 `output/` 裡執行腳本，所以路徑從 `output/` 算起：讀 `figdata/…csv`（加 `set datafile separator comma`，用 `every ::1` 跳過欄名那一列），**輸出檔名一定是 `figures/figN.tex`（PNG 版是 `figures/figN.png`）**，N 是數字；Word 版靠這個名字換圖。保留開頭那段 `fmt` 判斷。圖寬不超過 12 公分（論文版面的寬度）。
     - **每支 `.gp` 開頭都要有 `set encoding utf8`。** 不寫的話，Windows 版 gnuplot 會照電腦語系在圖檔寫進 `\inputencoding{cp1252}`，pdflatex 就編不過（2026-10-22 Windows 實測）。
  3. y 軸用 `set autoscale y` 加 `set offsets`，不要寫死範圍，換資料才不會把點切掉。
     - 例外：**長條圖的 y 軸要從 0 開始**，寫 `set yrange [0:*]`（0 起、上限跟著資料走）。刻度太密就改 `set ytics 10`（或 20）。
  4. `source/paper/main.tex` 用 `\input{figures/figN.tex}` 放進 figure 環境，加 `\caption` 和 `\label`，內文用 `\ref` 提到它。
  5. **老師給的現成圖片**（流程圖、照片）放在 `source/images/`，build 原樣複製到 `output/images/`。不用寫 `.gp`，在 figure 環境裡寫 `\includegraphics[width=\linewidth]{images/檔名}`，一樣加 `\caption`、`\label`、內文 `\ref`。不改、不轉檔老師的圖；檔名有空白或中文，build 會停下來，請老師自己改名。
  6. 跑 build。
- 為什麼用 gnuplot：`cairolatex` 輸出時，圖上的字交給 LaTeX 排，跟內文同一套字型；配色用色盲也分得出的藍（#0072B2）和橘（#D55E00）。
- 怎麼驗證：打開 PDF 看：點和誤差線沒有被切掉、圖例沒蓋到資料、數字跟表格對得上。

## 第 5 步：寫 LaTeX

- 老師可能說：「幫我起草＿＿這一節。」
- 你怎麼做：在 `source/paper/main.tex` 寫。結果數字用巨集（例如 `\DKASTOneD{}`），表格用 `\input{tables/table1.tex}`，引用用 refs.bib 的 key。`main.tex` 裡 `\input` 的路徑都是 `output/` 裡的檔（build 會把 main.tex 複製到 output/ 再排版）。每一句講到文獻的，只寫該篇摘要或原文真的有寫的。
- **新表要放在最後一張表後面**：LaTeX 依表在 `main.tex` 出現的順序編號。新表插在前面，會變成表 2、原本的表 2 變表 3，跟 `tableN` 檔名和內文對不上。
- **寫到文獻的句子，自己逐句對摘要再交**：AI 很容易寫得比摘要多（例如把作者的結論寫成受訪者說的話、替「上面這些研究」做摘要沒寫的總結、沒引用的轉折句讀起來像結論）。`undefined_cites=0` 抓不到這種錯。
- 回報：列出每一句講到文獻的：根據哪一篇、**摘要裡支持它的那一句原文**（照抄、不改字）；找不到支持的句子就改寫或刪掉，讀不到摘要的標 ⚠️。最後附 build 最後一行。
- 換期刊：先讀 `material/` 裡的投稿須知，照它的章節規定（例如 BMC 研究論文要有 Declarations 底下那幾個小標、AI 使用要寫在 Methods）改。期刊有自己的 LaTeX 範本時，請老師從官網下載，把 `.cls`、`.bst` 放進 `source/paper/`（build 會自動帶去排版；官方範本檔不改，有授權條款），再改 `\documentclass`；`\bibliographystyle` 看範本：有的範本自己設好了（範例的 sn-jnl 用 `sn-vancouver-num` 選項，main.tex 裡就不能再寫 `\bibliographystyle`，也不能另外載入 hyperref、natbib）。`\input{numbers.tex}`、`\input{tables/...}`、`\input{figures/...}` 不用動。改之前先列給老師看；換完跑 build，再跑一次 `--docx` 確認 Word 版的摘要、作者、各小標都還在（build.py 的 `for_pandoc()` 只認得 Springer Nature 範本的寫法，別的範本有自訂指令要補進去）。
- 範例論文用的是 *BMC Geriatrics* 投稿須知建議的 Springer Nature LaTeX 範本（2024 年 12 月版，`sn-jnl.cls`＋`sn-vancouver-num.bst`，LPPL 授權）；開新論文的骨架（`tools/skeleton/main.tex`）用的是通用的 elsarticle。
- **有中文**（中文論文，或英文論文引用了中文文獻）：把 `main.tex` 第一行改成 `% !TEX program = xelatex` 就好。中文字型那段（`\ifXeTeX` 開頭）已經寫好：依序找 Noto Serif CJK TC（Linux、GitHub 雲端）、新細明體 PMingLiU、微軟正黑體（Windows）、宋體-繁 Songti TC（Mac）；都找不到時改用 TeX 內附的 Fandol 字型（常用繁體字大多有）。有字印不出來，build 會停下來列出是哪幾個字，再請老師裝字型或改成電腦上有的中文字型。

## 第 6 步：編出 PDF

- 老師可能說：「跑一次 build。」
- 你怎麼做：`uv run build.py`。它依序：0 檢查工具 → 1 分析 → 2 畫圖 → 3 檢查文獻 → 4 編 PDF。
- 失敗時照 `BUILD FAILED` 後面的原因處理：

| 訊息 | 處理 |
|---|---|
| 缺 Python 套件 | 確認是用 `uv run build.py` 跑的；還是缺就 `uv sync`（先問老師）。不要用 pip |
| 找不到 gnuplot／pdflatex／xelatex／bibtex | 照 README 第三節請老師同意後安裝；Windows 裝好 gnuplot 還是找不到，多半是沒加進 PATH |
| 找不到資料 | 還在練習：執行 `uv run tools/make_practice_data.py`。**已經放了真資料**（檔名不同）：改 `source/scripts/analyze.py` 的 `DATA` 那一行，不要產生練習資料 |
| 資料不是 UTF-8 | 請老師用 Excel 另存成「CSV UTF-8（逗號分隔）」 |
| 引用代號在 refs.bib 裡找不到 | 請老師把文獻加進 Zotero；代號打錯就改 main.tex。不要自己寫進 refs.bib |
| 期刊論文沒有 DOI | 請老師回 Zotero 補；真的沒有，請老師在 Zotero 加標籤 `nodoi` |
| 文章種類（條目類型）不認得 | 請老師在 Zotero 把項目類型改對再匯出；不要直接改 refs.bib |
| 有中文，pdflatex 編不了 | 照第 5 步把第一行改成 xelatex |
| 字印不出來（缺字型） | 照第 5 步的中文字型說明處理 |
| pdflatex／xelatex／bibtex 失敗 | 看它指的 `output/latex-log/build-N.log` 最後幾十行，修 `source/paper/main.tex` |
| BUILD OK 但 bib_warnings 不是 0 | 把警告（例如 `empty journal in …`）列給老師，請老師回 Zotero 補欄位 |

## 第 7 步：Word 版

- 老師可能說：「期刊只收 Word。」
- 你怎麼做：
  1. 資料夾裡還是範例資料的話，先提醒：「這是練習資料，不是原始資料，不能投稿。」
  2. `uv run build.py --docx`，產生 `output/main.docx`（圖換成 PNG，引用由 pandoc 排）。
  3. 打開 docx 跟 PDF 對照，列出要人工檢查的地方：引用格式、表格、圖說編號、標題頁、行距字型。
- 提醒老師：每次產生都會蓋掉舊的 `main.docx`，要在 Word 裡改先另存新檔名；正式稿以 PDF 為準。

## 第 8 步：交給老師前的檢查清單

- [ ] build 最後一行是 `BUILD OK`，而且 `bib_warnings=0`
- [ ] 連跑兩次 build，`output/numbers.tex` 一模一樣（分析裡沒有亂數）
- [ ] 待補的紅字、`To be written`、`placeholder` 都清掉了（build 不會擋這些；在 `main.tex` 搜一次）
- [ ] 結果數字都是巨集，沒有手打的
- [ ] 每篇文獻的描述沒有超過摘要或原文；提醒老師用 DOI 抽查；標了 `nodoi` 的，請老師自己對書目
- [ ] PDF 的參考文獻看過：專有名詞（DKAS、SCIDS 這類）沒有變小寫、BMC 這類期刊有文章編號
- [ ] 沒有為了過 build 改條目類型、補 DOI、改 `output/`
- [ ] 圖是這次 build 重畫的，打開看過
- [ ] AI 使用聲明照期刊規定寫了：寫出工具名稱和用途；聲明裡每一句都是真的做過的事
- [ ] 統計方法跟研究設計相符（不確定的有沒有問過統計顧問）
- [ ] 數字更新過的段落，句子的解讀重讀過
- [ ] 範例資料已經換成真資料（要投稿的話）
- [ ] 回報寫清楚：改了什麼、哪些要老師決定

要投稿、期刊要 LaTeX 原始檔時：很多期刊要求所有檔案放同一層，並附上 `.bbl`。先列給老師看，另外建一個投稿資料夾打包，不改原本的資料夾結構。

## 第 9 步：存一版、推上 GitHub

- 老師可能說：「存一版、推上去。」
- 你怎麼做：列出要推的檔，特別標出 `source/data/`、`material/` 裡新放的；老師同意後 commit、push。`output/` 不推，`examples/` 裡的資料檔也不推（.gitignore 都已經排除）。列檔案用 `git -c core.quotepath=off status`，中文檔名才看得懂。資料不符合 `source/data/README.md` 的條件就不推資料（那裡有只在本機跑的做法）。
- 回報：GitHub 會用 `.github/workflows/build-paper.yml` 在雲端自動跑一次 build，到儲存庫的 Actions 頁面下載 paper-pdf。提醒老師：資料也會在 GitHub 的雲端機器上被讀取。
