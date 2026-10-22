"""重建練習資料：照一篇已發表論文（2021，BMC Geriatrics，CC BY 4.0）公開的表 1、表 2，產生 140 位「虛構」居服員的資料。

這不是原始研究資料。原始資料沒有公開；這份是用論文印出來的人數、平均、標準差反推的練習資料：
- 每組 70 人；表 1 的類別人數（性別、婚姻、教育、工作型態、在職訓練時數、失智症訓練時數）完全照論文。
  訓練時數的級距寫成 none、<10 h、10-20 h、>20 h（在職訓練），none、<2 h、3-6 h、7-12 h、>12 h（失智症訓練）；
  加「 h」是為了不讓 Excel 把 3-6 這種寫法顯示成日期。級距文字從 published_values.csv 讀，這支程式不改它。
- 年齡、年資、三個量表在三個時間點的平均與標準差，四捨五入後跟論文一樣（年資記到小數一位）。
- 年齡、年資的組間 t 檢定 p 值，四捨五入後也跟論文一樣。
- 同一個人三個時間點的分數彼此相關，但相關多大論文沒寫，這裡假設 0.5。
所以平均、標準差、t 檢定、效果量可以拿來對照論文；要用到個人層次資料的分析（例如論文的 GEE）對不上。

來源（完整書目見 source/refs/refs.bib 的 Su2021）：BMC Geriatrics 2021;21:126.
https://doi.org/10.1186/s12877-021-02075-3（CC BY 4.0）

用法（在範本資料夾裡）：uv run tools/make_practice_data.py
會讀 source/data/published_values.csv，寫出 source/data/study_data.csv。
範本已經附上產好的 study_data.csv，平常不用重跑；只有檔案不見了才需要。

會不會每台電腦都一樣（照實說）：
- 亂數種子是固定的。三個時間點的相關，原本用 numpy 的 multivariate_normal 產生，它在不同 CPU 上會挑不同的分解，
  產生的檔案就不一樣；現在改成把分解直接寫成公式、只用加減乘（雲端 commit ac27234f）。
- 2026-10-22 實測：雲端六種 OpenBLAS 核心產生的檔案都相同（當時級距還沒加「 h」）；
  msi（Windows，numpy 2.4.2）四種核心（Haswell、Zen、Sandybridge、Prescott）產生的檔案，跟範本現在附的那份逐位元相同。
- 但 numpy 不保證換大版本後亂數序列還一樣，Mac（Apple Silicon）也還沒實測。重跑後如果跟附的那份不同，用附的那份就好。
"""
import csv
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "source" / "data" / "published_values.csv"
OUT = ROOT / "source" / "data" / "study_data.csv"
SEED = 20210216
N = 70
GROUPS = ["intervention", "control"]
SCALES = {"DKAS": (0, 50), "ADQ": (19, 95), "SCIDS": (17, 68)}
TIMES = ["T0", "T1", "T2"]
RHO = 0.5  # 同一個人三個時間點的相關（假設值）
CATEGORIES = ["sex", "marital", "education", "job", "training", "dementia_training"]

rng = np.random.default_rng(SEED)


def load_published():
    with open(PUB, encoding="utf-8") as f:
        return list(csv.DictReader(f))


PUBLISHED = load_published()


def pub(table, variable, level, group, stat):
    for r in PUBLISHED:
        if (r["table"], r["variable"], r["level"], r["group"], r["stat"]) == (table, variable, level, group, stat):
            return r["value"]
    raise KeyError((table, variable, level, group, stat))


def sums_for(mean, decimals, unit=1):
    """總和 S（以 unit 為單位的整數）要讓 S×unit/N 四捨五入後剛好等於論文的平均。"""
    lo, hi = (mean - 0.5 * 10 ** -decimals) * N / unit, (mean + 0.5 * 10 ** -decimals) * N / unit
    return [s for s in range(int(np.floor(lo)), int(np.ceil(hi)) + 1)
            if round(s * unit / N + 1e-12, decimals) == round(mean, decimals)]


def fit(z, total, sd, lo, hi, tol):
    """把連續值 z 變成整數：總和剛好是 total，標準差跟 sd 差不到 tol，都在 lo～hi 之間。"""
    x0 = total / N + sd * (z - z.mean()) / z.std(ddof=1)
    x = np.clip(np.rint(x0), lo, hi).astype(int)
    while x.sum() != total:  # 先調總和
        resid = x0 - x
        if x.sum() < total:
            cand = np.where(x < hi)[0]
            x[cand[np.argmax(resid[cand])]] += 1
        else:
            cand = np.where(x > lo)[0]
            x[cand[np.argmin(resid[cand])]] -= 1
    target_ss = sd ** 2 * (N - 1)
    for _ in range(5000):  # 再調標準差：一人 +1、一人 -1，總和不變，平方和變 2(xi - xj) + 2
        if abs(x.std(ddof=1) - sd) < tol:
            return x
        need = target_ss - ((x - x.mean()) ** 2).sum()
        delta = 2 * (x[:, None] - x[None, :]) + 2
        ok = (x[:, None] < hi) & (x[None, :] > lo) & ~np.eye(N, dtype=bool)
        cost = np.where(ok, np.abs(need - delta), np.inf)
        best = np.flatnonzero(cost == cost.min())
        i, j = np.unravel_index(rng.choice(best), cost.shape)
        x[i] += 1
        x[j] -= 1
    sys.exit(f"調不到標準差 {sd}（總和 {total}）")


def two_group_continuous(variable, lo, hi, unit=1):
    """年齡、年資：找兩組的總和與標準差，讓平均、標準差、全體、t 檢定 p 值都對得上論文。
    unit 是資料的最小單位（年齡 1 歲；年資 0.1 年）。"""
    m = {g: float(pub("T1", variable, "", g, "mean")) for g in GROUPS}
    s = {g: float(pub("T1", variable, "", g, "sd")) for g in GROUPS}
    m_all, s_all = float(pub("T1", variable, "", "all", "mean")), float(pub("T1", variable, "", "all", "sd"))
    p_pub = float(pub("T1", variable, "", "", "p"))
    grid = np.round(np.arange(-0.04, 0.045, 0.01), 2)
    a, b = np.meshgrid(s["intervention"] + grid, s["control"] + grid)  # 兩組標準差的所有組合
    a, b = a.ravel(), b.ravel()
    best = None
    for s1 in sums_for(m["intervention"], 1, unit):
        for s2 in sums_for(m["control"], 1, unit):
            m1, m2 = s1 * unit / N, s2 * unit / N
            mean_all = (m1 + m2) / 2
            if round(mean_all, 1) != m_all:
                continue
            t = (m1 - m2) / np.sqrt((a * a + b * b) / N)  # 兩組人數相同時的 t 值
            p = 2 * stats.t.sf(np.abs(t), 2 * N - 2)
            sd_all = np.sqrt(((N - 1) * (a * a + b * b) + N * ((m1 - mean_all) ** 2 + (m2 - mean_all) ** 2)) / (2 * N - 1))
            ok = (np.round(p, 3) == p_pub) & (np.round(sd_all, 1) == s_all)
            for k in np.flatnonzero(ok):
                margin = 0.0005 - abs(p[k] - p_pub)
                if best is None or margin > best[0]:
                    best = (margin, s1, s2, a[k], b[k])
    if best is None:
        sys.exit(f"{variable}：找不到同時符合論文平均、標準差、p 值的組合")
    _, s1, s2, a, b = best
    out = {}
    for g, total, sd in [("intervention", s1, a), ("control", s2, b)]:
        x = fit(rng.standard_normal(N), total, sd / unit, round(lo / unit), round(hi / unit), tol=0.002 / unit)
        out[g] = np.round(x * unit, 1) if unit < 1 else x
    return out


def categorical(variable):
    out = {}
    for g in GROUPS:
        levels = [(r["level"], int(r["value"])) for r in PUBLISHED
                  if r["table"] == "T1" and r["variable"] == variable and r["group"] == g and r["stat"] == "n"]
        values = [lvl for lvl, n in levels for _ in range(n)]
        if len(values) != N:
            sys.exit(f"{variable}（{g}）人數加起來是 {len(values)}，不是 {N}")
        out[g] = rng.permutation(values)
    return out


def main():
    cols = {}
    cols["age"] = two_group_continuous("age", 20, 65)
    cols["years_worked"] = two_group_continuous("years", 0.3, 35, unit=0.1)
    for c in CATEGORIES:
        cols[c] = categorical(c)
    # 把三個獨立的常態亂數，變成「兩兩相關都是 RHO」的三個時間點。不用 rng.multivariate_normal：
    # 這個相關矩陣的特徵值有重根（1 - RHO 出現兩次），它內部的 SVD 分解不唯一，
    # 不同 CPU 上的數學函式庫會挑不同的分解，產生的資料就不一樣（2026-10-22 查到）。
    # 這裡把分解直接寫出來，只用加減乘，每台電腦算出來都一樣。
    a, b = np.sqrt((1 + 2 * RHO) / 3), np.sqrt(1 - RHO)
    mix = np.array([[-a, 0.0, b * 2 / np.sqrt(6)],
                    [-a, -b / np.sqrt(2), -b / np.sqrt(6)],
                    [-a, b / np.sqrt(2), -b / np.sqrt(6)]])
    for scale, (lo, hi) in SCALES.items():
        for g in GROUPS:
            e = rng.standard_normal((N, 3))
            z = e[:, [0]] * mix[:, 0] + e[:, [1]] * mix[:, 1] + e[:, [2]] * mix[:, 2]
            for k, t in enumerate(TIMES):
                mean = float(pub("T2", scale, t, g, "mean"))
                sd = float(pub("T2", scale, t, g, "sd"))
                cols.setdefault(f"{scale.lower()}_{t.lower()}", {})[g] = fit(z[:, k], sums_for(mean, 2)[0], sd, lo, hi, tol=0.003)

    # 自我檢查：重建出來的資料，四捨五入後一定要跟論文一樣
    problems = []
    for scale in SCALES:
        for t in TIMES:
            col = cols[f"{scale.lower()}_{t.lower()}"]
            for g in GROUPS:
                for stat, got in [("mean", col[g].mean()), ("sd", col[g].std(ddof=1))]:
                    want = float(pub("T2", scale, t, g, stat))
                    if round(got, 2) != want:
                        problems.append(f"{scale} {t} {g} {stat}: {got:.4f} vs {want}")
    for variable, col in [("age", cols["age"]), ("years", cols["years_worked"])]:
        p = stats.ttest_ind(col["intervention"], col["control"]).pvalue
        if round(p, 3) != float(pub("T1", variable, "", "", "p")):
            problems.append(f"{variable} p: {p:.4f}")
    if problems:
        sys.exit("重建結果跟論文對不上：\n" + "\n".join(problems))

    header = ["id", "group", "age", "sex", "marital", "education", "job", "years_worked", "training",
              "dementia_training"] + [f"{s.lower()}_{t.lower()}" for s in SCALES for t in TIMES]
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")  # 換行固定 LF：預設是 CRLF，在 Mac 重產後 git 會顯示整檔修改（10/22 mbp 實測）
        w.writerow(header)
        for g, prefix in [("intervention", "I"), ("control", "C")]:
            for i in range(N):
                row = [f"{prefix}{i + 1:03d}", g] + [cols[h][g][i] for h in header[2:]]
                w.writerow([v.item() if hasattr(v, "item") else v for v in row])
    print(f"wrote {OUT.relative_to(ROOT)} ({2 * N} rows, reconstructed practice data, not the original data)")


if __name__ == "__main__":
    main()
