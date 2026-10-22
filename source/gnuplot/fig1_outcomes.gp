# 圖 1：三個量表在三個時間點的平均 ± 標準差，兩組各一條線
# 讀：output/figdata/fig1_dkas.csv、fig1_adq.csv、fig1_scids.csv（analyze.py 產生的資料表）
# 寫：output/figures/fig1.tex＋fig1.pdf（放進 PDF 論文）或 fig1.png（Word 版用）
# build.py 會在 output/ 資料夾裡執行這支，所以下面的路徑都從 output/ 算起。

set encoding utf8                              # 固定 UTF-8：不寫的話 Windows 會照電腦語系（cp1252、cp950）寫進圖檔，pdflatex 編不過（2026-10-22 msi 實測）
if (!exists("fmt")) fmt = 'latex'
if (fmt eq 'png') {
    set terminal pngcairo size 1500,560 font 'Arial,18'
    set output 'figures/fig1.png'
} else {
    set terminal cairolatex pdf size 12cm,6cm
    set output 'figures/fig1.tex'
}

set datafile separator comma                   # 資料表是 CSV（逗號分隔）
set style line 1 lc rgb '#0072B2' lw 2 pt 7 ps 0.8          # 介入組：藍色實線、實心圓
set style line 2 lc rgb '#D55E00' lw 2 pt 5 ps 0.8 dt 2     # 對照組：橘色虛線、實心方塊
set xrange [-0.35:2.35]
set xtics ('0' 0, '12' 1, '24' 2)               # 0 = 前測、12 = 介入結束、24 = 追蹤
set xlabel 'Week'
set ytics nomirror
set xtics nomirror
set border 3                                   # 只留左邊和下面的框線
set autoscale y                                # y 軸範圍跟著資料走，換資料不會把點切掉
set offsets 0, 0, graph 0.08, graph 0.05       # 上下各留一點空間，點和誤差線不會貼邊
unset key                                      # 圖例最後另外畫（見最下面）
set multiplot layout 1,3 margins 0.1,0.98,0.2,0.74 spacing 0.07,0

set title 'DKAS'
set ylabel 'Mean score (SD)'
plot 'figdata/fig1_dkas.csv' every ::1 using ($1-0.04):2:3 with yerrorlines ls 1, \
     ''                      every ::1 using ($1+0.04):4:5 with yerrorlines ls 2

unset ylabel
set title 'ADQ'
plot 'figdata/fig1_adq.csv' every ::1 using ($1-0.04):2:3 with yerrorlines ls 1, \
     ''                     every ::1 using ($1+0.04):4:5 with yerrorlines ls 2

set title 'SCIDS'
plot 'figdata/fig1_scids.csv' every ::1 using ($1-0.04):2:3 with yerrorlines ls 1, \
     ''                       every ::1 using ($1+0.04):4:5 with yerrorlines ls 2

# 最後一張「看不見的圖」只放圖例：橫跨整張圖寬度，排成一列在最上面
unset title
unset xlabel
unset tics
unset border
set lmargin at screen 0.1
set rmargin at screen 0.98
set tmargin at screen 1.0
set bmargin at screen 0.86
set xrange [0:1]
set yrange [0:1]
set key center center horizontal samplen 2
plot NaN with linespoints ls 1 title 'Intervention', NaN with linespoints ls 2 title 'Control'

unset multiplot
