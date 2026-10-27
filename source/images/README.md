# source/images：現成的圖片檔（選用）

流程圖、照片這類**不是程式畫的圖**放這裡。build 會原樣複製到 `output/images/`，論文用 `\includegraphics{images/檔名}` 放進去（AI 會寫，你不用打）。

- 格式：**PNG 或 JPG**。PDF 也可以，但 Word 版放不進去。
- 檔名只用英文、數字、`-`、`_`，例如 `flowchart.png`；有空白或中文，build 會停下來請你改名。
- 照片裡有人臉、病歷、姓名，先去識別化再放。
- 放好之後跟 AI 說：「我在 source/images/ 放了 flowchart.png，請照 WORKFLOW.md 第 4 步放進論文的 Methods，圖說寫＿＿，內文提到它，跑一次 build。」

程式算出來的圖不放這裡：那種用 gnuplot 畫（看 `source/gnuplot/`）。
