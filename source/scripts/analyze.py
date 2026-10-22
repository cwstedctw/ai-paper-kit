"""分析程式：讀 source/data/ 的資料，算出論文要用的數字、表格、畫圖用的資料表，全部寫進 output/。

範例：用重建的練習資料，重算原論文（2021，BMC Geriatrics；書目 Su2021）的表 1、表 2、表 4，並跟論文印的數字對照。

讀（source/data/，原料，不改）：
- study_data.csv        每人一列：組別、基本資料、三個量表在三個時間點的分數
- published_values.csv  從論文抄下來的數字（拿來對照）

寫（output/，成品，每次 build 重做，不要手改）：
- numbers.tex                     內文用的數字，一個數字一個代號（巨集），例如 \\NTotal
- tables/table1.tex、table1.csv …  論文的表：.tex 放進 PDF，.csv 可以用 Excel 打開看
- figdata/fig1_dkas.csv …          畫圖用的資料表，gnuplot 讀它

統計：組間比較用 Student t 檢定（連續變項）、Fisher 精確檢定與概似比卡方（類別變項，照原論文表 1 每一列的檢定）；
效果量用 Cohen's d（合併標準差），95% 信賴區間用 Hedges 與 Olkin 的大樣本變異數。
四捨五入跟 SPSS、Excel 一樣（0.125 → 0.13）。
"""
import csv
import sys
from decimal import ROUND_HALF_UP, Decimal
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]

# ===== 設定：老師決定，AI 照著改 =====
DATA = ROOT / "source" / "data" / "study_data.csv"
PUBLISHED = ROOT / "source" / "data" / "published_values.csv"
EXCLUDE_IDS = []  # 要排除的受試者代號，例如 ["I001"]；排除的理由要寫進論文的 Methods
# =====================================

OUT = ROOT / "output"
GROUPS = [("intervention", "Int"), ("control", "Ctl")]
SCALES = ["DKAS", "ADQ", "SCIDS"]
TIMES = [("T0", "TZero", "Baseline"), ("T1", "TOne", "Week 12"), ("T2", "TTwo", "Week 24")]


def fmt(x, d=1):
    q = Decimal(1).scaleb(-d)
    return str(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))


def pfmt(p):
    # 印到小數三位；四捨五入後是 0.000 才寫 <0.001（0.0006 印成 0.001，跟一般期刊的寫法一樣）
    if p > 0.9995:
        return ">0.999"
    return "<0.001" if p < 0.0005 else fmt(p, 3)


def tex(s):
    """把 <、> 這類符號變成 LaTeX 寫法。"""
    return s.replace("<", "\\ensuremath{<}").replace(">", "\\ensuremath{>}")


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(3)


# ---------- 讀資料 ----------
if not DATA.exists():
    fail(f"找不到資料 {DATA.relative_to(ROOT)}。還在練習的話，先執行 uv run tools/make_practice_data.py；"
         "已經放了自己的資料（檔名不同）的話，請改這支程式上面 DATA 那一行的檔名，不要產生練習資料。")
try:
    df_all = pd.read_csv(DATA)
except UnicodeDecodeError:
    fail(f"{DATA.relative_to(ROOT)} 不是 UTF-8 編碼。用 Excel 另存新檔，存檔類型選「CSV UTF-8（逗號分隔）」，再放回來。")
pub = pd.read_csv(PUBLISHED, dtype=str, keep_default_na=False)


def published(table, variable, level, group, stat):
    hit = pub[(pub.table == table) & (pub.variable == variable) & (pub.level == level)
              & (pub.group == group) & (pub.stat == stat)]
    return hit.value.iloc[0] if len(hit) else ""


unknown = sorted(set(EXCLUDE_IDS) - set(df_all.id))
if unknown:
    fail(f"EXCLUDE_IDS 裡的代號在資料裡找不到：{'、'.join(unknown)}。")
df = df_all[~df_all.id.isin(EXCLUDE_IDS)]
grp = {g: df[df.group == g] for g, _ in GROUPS}
n = {g: len(grp[g]) for g, _ in GROUPS}
macros = {
    "NTotal": str(len(df)), "NInt": str(n["intervention"]), "NCtl": str(n["control"]),
    "NExcluded": str(len(EXCLUDE_IDS)), "NFemale": str(int((df.sex == "female").sum())),
    # 排除了人，論文就印出代號並提醒要補理由（理由要老師自己寫進 main.tex）
    "ExcludedSentence": "No participants were excluded." if not EXCLUDE_IDS else
        f"{len(EXCLUDE_IDS)} participant{'s' if len(EXCLUDE_IDS) > 1 else ''} ({', '.join(EXCLUDE_IDS)}) "
        f"{'were' if len(EXCLUDE_IDS) > 1 else 'was'} excluded \\textbf{{[state the reason here]}}.",
    "AgeMean": fmt(df.age.mean()), "AgeSD": fmt(df.age.std(ddof=1)),
}
OUT.joinpath("tables").mkdir(parents=True, exist_ok=True)
OUT.joinpath("figdata").mkdir(parents=True, exist_ok=True)


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig：Excel 打開中文、符號不會亂碼
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def msd(s, d):
    return f"{fmt(s.mean(), d)} ({fmt(s.std(ddof=1), d)})"


def fisher_exact_2col(table):
    """Fisher 精確檢定（超過 2×2 用 Freeman–Halton 延伸）：類別 × 兩組的表。
    把邊際總數相同的表全部列出來，p ＝ 機率不大於觀察到的表的機率總和。用整數算，每次結果都一樣。
    （不用 scipy 的 fisher_exact：超過 2×2 時它預設用亂數模擬，每次 build 的 p 值會不一樣。）"""
    rows = [int(a) + int(b) for a, b in table]
    c1 = int(sum(a for a, _ in table))
    suffix = [sum(rows[i:]) for i in range(len(rows))] + [0]
    observed = 1
    for r, (a, _) in zip(rows, table):
        observed *= comb(r, int(a))
    total = 0

    def walk(i, remaining, acc):
        nonlocal total
        if i == len(rows) - 1:
            v = acc * comb(rows[i], remaining)
            if v <= observed:
                total += v
            return
        for x in range(max(0, remaining - suffix[i + 1]), min(rows[i], remaining) + 1):
            walk(i + 1, remaining - x, acc * comb(rows[i], x))

    walk(0, c1, 1)
    return total / comb(sum(rows), c1)


# ---------- 表 1：基本資料 ----------
# 原論文表 1 印了 8 個 p 值，這裡 8 個都重算：年齡、年資用 t 檢定；性別、婚姻、工作型態、在職訓練用 Fisher 精確檢定；
# 教育、失智症訓練用概似比卡方（論文寫「卡方或 Fisher 精確檢定，視情況使用」）。
T1_ROWS = [("age", "Age, years, mean (SD)", "t"),
           ("sex", "Sex, n (\\%)", "fisher"),
           ("marital", "Marital status, n (\\%)", "fisher"),
           ("education", "Education, n (\\%)", "lr"),
           ("job", "Job, n (\\%)", "fisher"),
           ("years_worked", "Years worked, mean (SD)", "t"),
           ("training", "In-service training, n (\\%)", "fisher"),
           ("dementia_training", "Dementia training, n (\\%)", "lr")]
PUB_NAME = {"years_worked": "years"}
t1_tex, t1_csv, t1_match, t1_total = [], [], 0, 0
for var, label, test in T1_ROWS:
    p_pub = published("T1", PUB_NAME.get(var, var), "", "", "p")
    if test == "t":
        p = stats.ttest_ind(grp["intervention"][var], grp["control"][var]).pvalue
        row = [label, msd(grp["intervention"][var], 1), msd(grp["control"][var], 1), p_pub, pfmt(p)]
        t1_tex.append(row)
        t1_csv.append(row)
    else:
        levels = list(pub[(pub.table == "T1") & (pub.variable == var) & (pub.group == "intervention")].level)
        table = [[int((grp[g][var] == lvl).sum()) for g, _ in GROUPS] for lvl in levels]
        if test == "fisher":
            p = fisher_exact_2col(table)
            note = "Fisher exact"
        else:
            p = stats.chi2_contingency(np.array(table), correction=False, lambda_="log-likelihood")[1]
            p_pearson = stats.chi2_contingency(np.array(table), correction=False)[1]
            key = {"education": "Edu", "dementia_training": "Dem"}[var]
            macros[f"{key}PearsonP"] = tex(pfmt(p_pearson))
            macros[f"{key}LRP"] = tex(pfmt(p))
            macros[f"{key}PubP"] = tex(p_pub)
            note = f"likelihood-ratio chi-square (Pearson {pfmt(p_pearson)})"
        t1_tex.append([label, "", "", p_pub, pfmt(p)])
        t1_csv.append([label.replace("\\%", "%"), "", "", p_pub, f"{pfmt(p)} ({note})"])
        for lvl, counts in zip(levels, table):
            cells = [f"{c} ({fmt(100 * c / n[g], 1)})" for c, (g, _) in zip(counts, GROUPS)]
            # \quad{} 後面接標籤：寫成 "\quad 3-6 h" 的話，pandoc 轉 Word 會把 3 吃掉
            t1_tex.append(["\\quad{}" + lvl.replace("senior high or vocational", "senior high/vocational"), *cells, "", ""])
            t1_csv.append(["  " + lvl, *cells, "", ""])
    t1_total += 1
    t1_match += pfmt(p) == p_pub
macros["TOneMatch"], macros["TOneTotal"] = str(t1_match), str(t1_total)
macros["TOnePrinted"] = str(int(((pub.table == "T1") & (pub.stat == "p")).sum()))

with open(OUT / "tables" / "table1.tex", "w", encoding="utf-8") as f:
    f.write("% 由 source/scripts/analyze.py 產生，不要手改\n\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{lcccc}\n\\toprule\n")
    f.write(f" & Intervention & Control & \\multicolumn{{2}}{{c}}{{$p$}} \\\\\n"
            f"Characteristic & ($n={n['intervention']}$) & ($n={n['control']}$) & Published & Reproduced \\\\\n\\midrule\n")
    for r in t1_tex:
        f.write(" & ".join(tex(c) if i else c.replace("<", "$<$").replace(">", "$>$") for i, c in enumerate(r)) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
write_csv(OUT / "tables" / "table1.csv",
          ["Characteristic", f"Intervention (n={n['intervention']})", f"Control (n={n['control']})", "p published", "p reproduced"],
          t1_csv)

# ---------- 表 2：三個量表在三個時間點；表 3：效果量 ----------
t2_tex, t2_csv, t3_tex, t3_csv, fig2 = [], [], [], [], []
p_match = d_match = 0
d_diffs, ci_diffs, p_diffs = [], [], []
for scale in SCALES:
    t2_tex.append(("HEAD", scale))
    figrows = []
    for t, tname, tlabel in TIMES:
        col = f"{scale.lower()}_{t.lower()}"
        a, b = grp["intervention"][col], grp["control"][col]
        p = stats.ttest_ind(a, b).pvalue
        p_pub = published("T2", scale, t, "", "p")
        if pfmt(p) == p_pub:
            p_match += 1
        else:
            p_diffs.append(f"{scale} at {tlabel.lower()} (reproduced {fmt(p, 4)}, published {p_pub})")
        for (g, gk), s in [(("intervention", "Int"), a), (("control", "Ctl"), b)]:
            macros[f"{scale}{gk}{tname}Mean"] = fmt(s.mean(), 2)
            macros[f"{scale}{gk}{tname}SD"] = fmt(s.std(ddof=1), 2)
        macros[f"{scale}{tname}Pstat"] = "\\ensuremath{p<0.001}" if pfmt(p) == "<0.001" else f"\\ensuremath{{p={pfmt(p)}}}"
        t2_tex.append(("ROW", tlabel, msd(a, 2), msd(b, 2), p_pub, pfmt(p)))
        t2_csv.append([scale, tlabel,
                       published("T2", scale, t, "intervention", "mean"), published("T2", scale, t, "intervention", "sd"),
                       fmt(a.mean(), 2), fmt(a.std(ddof=1), 2),
                       published("T2", scale, t, "control", "mean"), published("T2", scale, t, "control", "sd"),
                       fmt(b.mean(), 2), fmt(b.std(ddof=1), 2), p_pub, pfmt(p)])
        figrows.append([TIMES.index((t, tname, tlabel)), fmt(a.mean(), 3), fmt(a.std(ddof=1), 3),
                        fmt(b.mean(), 3), fmt(b.std(ddof=1), 3)])
        if t == "T0":
            continue
        n1, n2 = len(a), len(b)
        sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
        d = (a.mean() - b.mean()) / sp
        se = np.sqrt((n1 + n2) / (n1 * n2) + d * d / (2 * (n1 + n2)))
        lo, hi = d - 1.96 * se, d + 1.96 * se
        pd_, pl, ph = (float(published("T4", scale, t, "", k)) for k in ("d", "d_low", "d_high"))
        d_match += fmt(d, 2) == f"{pd_:.2f}"
        d_diffs.append(abs(float(fmt(d, 2)) - pd_))
        ci_diffs += [abs(float(fmt(lo, 2)) - pl), abs(float(fmt(hi, 2)) - ph)]
        macros[f"{scale}{tname}D"] = fmt(d, 2)
        t3_tex.append([f"{scale}, {tlabel.lower()}", f"{pd_:.2f} ({pl:.2f}, {ph:.2f})", f"{fmt(d, 2)} ({fmt(lo, 2)}, {fmt(hi, 2)})"])
        t3_csv.append([scale, tlabel, f"{pd_:.2f}", f"{pl:.2f}", f"{ph:.2f}", fmt(d, 2), fmt(lo, 2), fmt(hi, 2)])
        fig2.append([len(fig2) + 1, f"{scale} {tlabel.lower()}", f"{pd_:.2f}", f"{pl:.2f}", f"{ph:.2f}",
                     fmt(d, 3), fmt(lo, 3), fmt(hi, 3)])
    write_csv(OUT / "figdata" / f"fig1_{scale.lower()}.csv", ["time", "int_mean", "int_sd", "ctl_mean", "ctl_sd"], figrows)
macros.update({"PMatch": str(p_match), "PTotal": str(len(SCALES) * len(TIMES)),
               # 全部相同時這句是空的；有不同（例如排除了某人）才列出來
               "PDiffSentence": tex(f" In this analysis, values that differ from the published ones: {'; '.join(p_diffs)}.") if p_diffs else "",
               "DMatch": str(d_match), "DTotal": str(len(d_diffs)),
               "DMaxDiff": fmt(max(d_diffs), 2), "CIMaxDiff": fmt(max(ci_diffs), 2)})

with open(OUT / "tables" / "table2.tex", "w", encoding="utf-8") as f:
    f.write("% 由 source/scripts/analyze.py 產生，不要手改\n\\begin{tabular}{lcccc}\n\\toprule\n")
    f.write(f" & Intervention & Control & \\multicolumn{{2}}{{c}}{{$p$}} \\\\\n"
            f"Scale and time & ($n={n['intervention']}$) & ($n={n['control']}$) & Published & Reproduced \\\\\n\\midrule\n")
    for r in t2_tex:
        if r[0] == "HEAD":
            if r[1] != SCALES[0]:
                f.write("\\midrule\n")
            f.write(f"\\multicolumn{{5}}{{l}}{{\\textit{{{r[1]}}}, mean (SD)}} \\\\\n")
        else:
            f.write("\\quad " + " & ".join([r[1], r[2], r[3], tex(r[4]), tex(r[5])]) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
write_csv(OUT / "tables" / "table2.csv",
          ["Scale", "Time", "Int mean published", "Int SD published", "Int mean reproduced", "Int SD reproduced",
           "Ctl mean published", "Ctl SD published", "Ctl mean reproduced", "Ctl SD reproduced",
           "p published", "p reproduced"], t2_csv)

with open(OUT / "tables" / "table3.tex", "w", encoding="utf-8") as f:
    f.write("% 由 source/scripts/analyze.py 產生，不要手改\n\\begin{tabular}{lcc}\n\\toprule\n")
    f.write("Scale and time & Published & Reproduced \\\\\n\\midrule\n")
    for r in t3_tex:
        f.write(" & ".join(c.replace("-", "$-$") if i else c for i, c in enumerate(r)) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
write_csv(OUT / "tables" / "table3.csv",
          ["Scale", "Time", "d published", "CI low published", "CI high published",
           "d reproduced", "CI low reproduced", "CI high reproduced"], t3_csv)
write_csv(OUT / "figdata" / "fig2_effects.csv",
          ["row", "label", "pub_d", "pub_low", "pub_high", "rep_d", "rep_low", "rep_high"], fig2)

# ---------- 內文數字 ----------
with open(OUT / "numbers.tex", "w", encoding="utf-8") as f:
    f.write("% 由 source/scripts/analyze.py 產生，不要手改\n")
    for k, v in macros.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

print(f"analysis done: N={len(df)} (excluded {len(EXCLUDE_IDS)}); "
      f"Table 2 p matched {p_match}/{macros['PTotal']}; Cohen's d matched {d_match}/{len(d_diffs)} "
      f"(max difference {macros['DMaxDiff']})")
