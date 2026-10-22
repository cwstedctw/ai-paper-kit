# 圖 2：效果量（Cohen's d 與 95% 信賴區間），論文印的（空心）和重算的（實心）並排
# 讀：output/figdata/fig2_effects.csv（analyze.py 產生的資料表）
# 寫：output/figures/fig2.tex＋fig2.pdf（放進 PDF 論文）或 fig2.png（Word 版用）
# build.py 會在 output/ 資料夾裡執行這支，所以下面的路徑都從 output/ 算起。

set encoding utf8                              # 固定 UTF-8：不寫的話 Windows 會照電腦語系（cp1252、cp950）寫進圖檔，pdflatex 編不過（2026-10-22 msi 實測）
if (!exists("fmt")) fmt = 'latex'
if (fmt eq 'png') {
    set terminal pngcairo size 1000,620 font 'Arial,18'
    set output 'figures/fig2.png'
    set xlabel "Cohen's d (95% CI)"
} else {
    set terminal cairolatex pdf size 11cm,6.8cm
    set output 'figures/fig2.tex'
    set xlabel "Cohen's $d$ (95\\% CI)"
}

set datafile separator comma
set style line 1 lc rgb '#0072B2' lw 2 pt 7 ps 0.9          # 重算：藍色實心圓
set style line 2 lc rgb '#555555' lw 2 pt 6 ps 0.9          # 論文：灰色空心圓
set yrange [6.6:0.4]                           # 第 1 列在最上面
set xrange [-0.3:1.5]
set xtics 0.25 nomirror
set ytics nomirror scale 0
set border 1                                   # 只留下面的框線
set arrow 1 from 0, graph 0 to 0, graph 1 nohead dt 3 lc rgb '#888888'   # d = 0 的參考線
set key bottom right
plot 'figdata/fig2_effects.csv' every ::1 using 3:($1-0.15):4:5:ytic(2) with xerrorbars ls 2 title 'Published', \
     ''                         every ::1 using 6:($1+0.15):7:8 with xerrorbars ls 1 title 'Reproduced'
