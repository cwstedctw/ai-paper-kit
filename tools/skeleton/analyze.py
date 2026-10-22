"""分析程式（新論文的骨架）：讀 source/data/ 的資料，算出論文要用的數字、表格、畫圖用的小表，全部寫進 output/。

現在只算了人數。請 AI 依老師同意的分析計畫補上：
- 每個結果數字一個代號（巨集），寫進 output/numbers.tex；代號只能用英文字母，例如 \\NTotal
- 每張表寫 output/tables/tableN.tex（放進 PDF）和 tableN.csv（用 Excel 核對）；可以用下面的 write_table()
- 每張圖要的數字寫成小表 output/figdata/figN_….csv（gnuplot 讀它）
寫法可以參考 examples/ 裡範例的 source/scripts/analyze.py。
四捨五入一律用下面的 fmt()，跟 SPSS、Excel 一樣（0.125 → 0.13）；p 值用 pfmt()。
類別變項（例如性別 × 組別）要做 Fisher 精確檢定，一律用下面的 fisher_exact()，不要用 scipy 的 stats.fisher_exact：
超過 2×2 的表，scipy（1.15 以上）預設用亂數模擬，每次 build 算出來的 p 值都不一樣（2026-10-22 實測婚姻狀況連跑三次：
0.6254、0.6281、0.6167；完整列舉是 0.624）。改完跑兩次 build，output/numbers.tex 要一模一樣。
"""
import csv
import sys
from decimal import ROUND_HALF_UP, Decimal
from math import comb
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

# ===== 設定：老師決定，AI 照著改 =====
DATA = ROOT / "source" / "data" / "study_data.csv"  # 換成你的資料檔名
EXCLUDE_IDS = []  # 要排除的受試者代號；排除的理由要寫進論文的 Methods
# =====================================

OUT = ROOT / "output"


def fmt(x, d=1):
    q = Decimal(1).scaleb(-d)
    return str(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))


def pfmt(p):
    """p 值印到小數三位。四捨五入到三位會變成 0.000 的（p < 0.0005），才寫 <0.001。
    例如 p = 0.00057 印成 0.001，不是 <0.001，跟 SPSS、論文的印法一樣。"""
    return "<0.001" if p < 0.0005 else fmt(p, 3)


def tex(s):
    """把 <、>、% 這類符號變成 LaTeX 寫法。"""
    return s.replace("%", "\\%").replace("<", "\\ensuremath{<}").replace(">", "\\ensuremath{>}")


def fisher_exact(table):
    """Fisher 精確檢定（2×2 以上用 Freeman–Halton 延伸），雙尾 p 值。table 是 r 列 × c 欄的人數，例如
    [[69, 69], [1, 1]]（列＝類別，欄＝組別）。做法：把列總和、欄總和都一樣的表全部列出來，
    p ＝ 機率不大於觀察到的那張表的機率總和。全部用整數算，同一份資料每次結果都一樣。
    類別多、人數多時會算比較久（類別 × 兩組、一兩百人，一秒內算完）。"""
    rows = [int(sum(r)) for r in table]
    cols = [int(sum(r[j] for r in table)) for j in range(len(table[0]))]
    if any(x < 0 for r in table for x in r):
        raise ValueError("人數不能是負的")
    table = [[int(x) for x in r] for r in table]

    def weight(r, parts):  # 一列分到各欄的方法數（多項係數），整數
        w = 1
        for x in parts:
            w *= comb(r, x)
            r -= x
        return w

    observed = 1
    for r, parts in zip(rows, table):
        observed *= weight(r, parts)
    total = 0

    def splits(r, caps):  # 把 r 個人分到各欄、每欄不超過 caps 的所有分法
        if len(caps) == 1:
            if r <= caps[0]:
                yield (r,)
            return
        for x in range(max(0, r - sum(caps[1:])), min(r, caps[0]) + 1):
            for rest in splits(r - x, caps[1:]):
                yield (x,) + rest

    def walk(i, remaining, acc):
        nonlocal total
        if i == len(rows) - 1:  # 最後一列只剩一種填法
            v = acc * weight(rows[i], remaining)
            if v <= observed:
                total += v
            return
        for parts in splits(rows[i], remaining):
            walk(i + 1, [c - x for c, x in zip(remaining, parts)], acc * weight(rows[i], parts))

    walk(0, cols, 1)
    return total / weight(sum(rows), cols)


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig：Excel 打開不會亂碼
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_table(path, colspec, header_lines, rows):
    """寫一張 LaTeX 表（booktabs 樣式）。rows 每一項是一列，用 & 分欄。
    縮排的子項目（例如類別的各個級距）在 LaTeX 裡寫成 \\quad{} 接標籤（下面有例子），不要寫 \\quad 加空白：
    轉 Word 時 pandoc 會把 \\quad 後面的數字吃掉（「3-6 h」變成「-6 h」，2026-10-22 實測）。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write("% 由 source/scripts/analyze.py 產生，不要手改\n")
        f.write(f"\\begin{{tabular}}{{{colspec}}}\n\\toprule\n")
        for h in header_lines:
            f.write(h + " \\\\\n")
        f.write("\\midrule\n")
        for r in rows:
            f.write(r + "\n" if r.startswith("\\midrule") else r + " \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(3)


# ---------- 讀資料 ----------
if not DATA.exists():
    fail(f"找不到資料 {DATA.relative_to(ROOT)}。請把資料放進 source/data/，再改這支程式上面 DATA 那一行的檔名。")
try:
    df_all = pd.read_csv(DATA)
except UnicodeDecodeError:
    fail(f"{DATA.relative_to(ROOT)} 不是 UTF-8 編碼。用 Excel 另存新檔，存檔類型選「CSV UTF-8（逗號分隔）」，再放回來。")
df = df_all[~df_all["id"].isin(EXCLUDE_IDS)] if "id" in df_all.columns else df_all
OUT.joinpath("tables").mkdir(parents=True, exist_ok=True)
OUT.joinpath("figdata").mkdir(parents=True, exist_ok=True)

macros = {"NTotal": str(len(df)), "NExcluded": str(len(df_all) - len(df))}

# ---------- 依分析計畫補在這裡：表、圖的小表、內文數字 ----------
# 例：類別變項 × 組別的 Fisher 精確檢定（欄位名稱照你的資料改）
#   counts = pd.crosstab(df["sex"], df["group"])
#   p = fisher_exact(counts.values.tolist())
#   rows.append(f"Sex, n (\\%) & & & {tex(pfmt(p))}")
#   for level, (a, b) in counts.iterrows():
#       rows.append(f"\\quad{{}}{tex(str(level))} & {a} & {b} &")

# ---------- 內文數字 ----------
with open(OUT / "numbers.tex", "w", encoding="utf-8") as f:
    f.write("% 由 source/scripts/analyze.py 產生，不要手改\n")
    for k, v in macros.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

print(f"analysis done: N={len(df)}（骨架：還沒有做統計）")
