"""一個指令跑完整條論文流程：資料分析 → gnuplot 畫圖 → 檢查文獻 → 編出 PDF。

平常不用自己打：跟 AI 說「跑一次 build」，AI 會執行這支。

原料都在 source/（資料、書目、分析程式、gnuplot 腳本、論文本文），成品都寫到 output/：
    output/numbers.tex   內文數字        output/tables/    表（.tex 給 PDF、.csv 給 Excel）
    output/figdata/      畫圖用的資料表  output/figures/   gnuplot 畫好的圖
    output/main.pdf      論文            output/latex-log/ 排版過程的紀錄
output/ 裡的東西每次 build 都會重做，不要手改；要改就改 source/。

用法（在這個資料夾裡；Mac 和 Linux 把 python 換成 python3，Windows 也可以用 py）：
    python build.py          # 產生 output/main.pdf
    python build.py --docx   # 另外產生 output/main.docx（給只收 Word 的期刊或合作者）

每一步失敗就停下來，印出是哪一步、去看哪個檔。最後一行是總結：
    BUILD OK pages=頁數 undefined_cites=找不到的引用 undefined_refs=找不到的圖表編號 refs=文獻篇數
             refs_without_doi=標了 nodoi 的篇數 bib_warnings=書目缺欄位的警告
undefined_cites、undefined_refs 一定是 0（不是 0 就不會 OK）；bib_warnings 不是 0 時，上面會列出缺什麼。
Windows、Mac、Linux 都用同一支；需要 Python 套件（requirements.txt）、gnuplot、TeX（pdflatex 或 xelatex、bibtex）。
用哪個 TeX 引擎看 source/paper/main.tex 第一行 `% !TEX program = pdflatex`；論文或書目有中文就改成 xelatex。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
MAIN_TEX = SRC / "paper" / "main.tex"
REFS = SRC / "refs" / "refs.bib"
OUT = ROOT / "output"
LOGDIR = OUT / "latex-log"
REBUILT = ["numbers.tex", "tables", "figdata", "figures", "latex-log", "main.pdf"]  # 每次重做的東西
TEX_SCRATCH = ["main.tex", "refs.bib", "main.aux", "main.bbl", "main.blg", "main.log", "main.out", "main.spl"]
STD_TYPES = {"article", "book", "booklet", "inbook", "incollection", "inproceedings", "conference", "manual",
             "mastersthesis", "phdthesis", "proceedings", "techreport", "unpublished", "misc", "online"}
ENGINES = {"pdflatex", "xelatex", "lualatex"}
CJK = re.compile(r"[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]")

# 英文版 Windows 的輸出編碼（cp1252）印不出中文：改用 UTF-8，不要整支程式停掉
for _s in (sys.stdout, sys.stderr):
    try:
        "中".encode(_s.encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def step(msg):
    print(f"\n== {msg}", flush=True)


def fail(msg):
    print(f"\nBUILD FAILED: {msg}", flush=True)
    sys.exit(1)


def need(tool, hint):
    if shutil.which(tool) is None:
        fail(f"找不到 {tool}。{hint}")


def run(cmd, cwd, log=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if log:
        Path(log).write_text(r.stdout + r.stderr, encoding="utf-8")
    return r


def engine():
    """看 main.tex 開頭的 % !TEX program = … 決定用哪個引擎（沒寫就用 pdflatex）。"""
    head = MAIN_TEX.read_text(encoding="utf-8").splitlines()[:5]
    for line in head:
        m = re.match(r"\s*%\s*!TEX\s+(?:TS-)?program\s*=\s*(\w+)", line, re.I)
        if m:
            e = m.group(1).lower()
            if e not in ENGINES:
                fail(f"main.tex 第一行寫的引擎 {e} 不支援，請改成 pdflatex 或 xelatex。")
            return e
    return "pdflatex"


def check_tools(docx, eng):
    step("0/5 檢查工具")
    try:
        import numpy, pandas, scipy, statsmodels  # noqa: F401
    except ImportError as e:
        fail(f"缺 Python 套件（{e.name}）。執行：python -m pip install -r requirements.txt（Mac：python3 -m pip …）")
    need("gnuplot", "Windows：winget install -e --id gnuplot.gnuplot，或到 gnuplot 官網下載安裝；裝好要能在終端機打 "
                    "gnuplot --version 看到版本。打了沒反應的話，把 gnuplot 安裝夾裡的 bin 資料夾加進使用者的 PATH，"
                    "再把 Codex／Claude 關掉重開。Mac：brew install gnuplot。")
    need(eng, "要裝 TeX（Windows：MiKTeX；Mac：MacTeX 或 BasicTeX；Linux：TeX Live）。")
    need("bibtex", "TeX 裝好就會有 bibtex。")
    if docx:
        need("pandoc", "做 Word 版要 pandoc（pandoc.org）。")
    print(f"工具都在（TeX 引擎：{eng}）。")


def analysis():
    step("1/5 資料分析（source/scripts/analyze.py → output/numbers.tex、tables/、figdata/）")
    for name in REBUILT:  # 先清掉上一次的成品，免得留下舊的圖表
        target = OUT / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    OUT.mkdir(exist_ok=True)
    r = run([sys.executable, str(SRC / "scripts" / "analyze.py")], ROOT)
    print(r.stdout.strip())
    if r.returncode == 3:  # analyze.py 自己說明了原因（找不到資料、編碼不對）
        fail(r.stderr.strip())
    if r.returncode != 0:
        print(r.stderr)
        fail("資料分析出錯，看上面的錯誤訊息。")


def figures(fmt="latex"):
    if fmt == "latex":
        step("2/5 gnuplot 畫圖（source/gnuplot/*.gp 讀 output/figdata/，畫到 output/figures/）")
    else:
        print("  先用 gnuplot 另外畫一份 PNG 圖給 Word 用", flush=True)
    gps = sorted((SRC / "gnuplot").glob("*.gp"))
    if not gps:
        print("  source/gnuplot/ 還沒有畫圖腳本，這一步先跳過。")
        return
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    for gp in gps:
        cmd = ["gnuplot", "-e", f"fmt='{fmt}'", str(gp)]
        r = run(cmd, OUT)  # 在 output/ 裡執行，腳本裡的路徑都從 output/ 算起
        if r.returncode != 0:
            print(r.stderr)
            fail(f"gnuplot 畫 {gp.name} 失敗。")
        print(f"  {gp.name} ok")


def strip_comments(tex):
    """拿掉 LaTeX 註解（% 到行尾；\\% 是百分比符號，不算）。"""
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in tex.splitlines())


def cite_keys(tex):
    keys = set()
    # \cite、\citep、\citet、\citealp…，可帶一到兩個 [選項]，例如 \citep[e.g.][p.~3]{Key}
    for m in re.finditer(r"\\cite[a-zA-Z]*\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^}]*)\}", tex):
        keys.update(k.strip() for k in m.group(1).split(",") if k.strip())
    return keys


def has_tag(body, tag):
    m = re.search(r"\bkeywords\s*=\s*[{\"](.*?)[}\"]\s*,?\s*$", body, re.I | re.M)
    return bool(m) and tag in re.split(r"[,;\s]+", m.group(1).lower())


def check_refs(eng):
    step("3/5 檢查文獻（每個引用都要在 refs.bib；期刊論文要有 DOI）")
    tex = strip_comments(MAIN_TEX.read_text(encoding="utf-8"))
    bib = REFS.read_text(encoding="utf-8")
    entries = re.findall(r"@(\w[\w-]*)\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@|\Z)", bib, re.S)
    entries = [(t, k, b) for t, k, b in entries if t.lower() not in {"comment", "string", "preamble"}]
    bib_keys = {k for _, k, _ in entries}
    cited = cite_keys(tex)
    missing = sorted(cited - bib_keys)
    odd_types = sorted(f"{k}（@{t}）" for t, k, _ in entries if t.lower() not in STD_TYPES)
    articles_no_doi = [k for t, k, body in entries if t.lower() == "article" and not re.search(r"\bdoi\s*=", body, re.I)]
    tagged = sorted(k for t, k, body in entries if k in articles_no_doi and has_tag(body, "nodoi"))
    no_doi = sorted(k for k in articles_no_doi if k not in tagged)
    unused = sorted(bib_keys - cited)
    print(f"  source/refs/refs.bib {len(entries)} 筆；內文引用 {len(cited)} 篇")
    if unused:
        print(f"  （refs.bib 裡有、但內文沒引用：{'、'.join(unused)}）")
    if odd_types:
        fail(f"這些書目的文章種類（條目類型）排版程式不認得：{'、'.join(odd_types)}。"
             "請在 Zotero 把這篇的項目類型改對（例如期刊文章），再重新匯出；不要直接改 refs.bib。")
    if missing:
        fail(f"內文的引用代號在書目檔 refs.bib 裡找不到：{'、'.join(missing)}。"
             "先把文獻加進 Zotero，讓 refs.bib 自動更新；如果是代號打錯，改 main.tex。")
    if no_doi:
        fail(f"這些期刊論文沒有 DOI：{'、'.join(no_doi)}。先回 Zotero 補上 DOI；"
             "真的沒有（例如有些台灣的中文期刊），就在 Zotero 給這篇加一個標籤 nodoi，再重新匯出。不要自己編 DOI。")
    if tagged:
        print(f"  標了 nodoi、沒有 DOI 的：{'、'.join(tagged)}。這幾篇請老師自己對一次書目。")
    if eng == "pdflatex":
        bodies = {k: body for _, k, body in entries}
        zh_bib = [k for k in cited & bib_keys if CJK.search(bodies[k])]
        if zh_bib or CJK.search(tex):
            where = f"書目 {'、'.join(sorted(zh_bib))}" if zh_bib else "main.tex 本文"
            fail(f"{where} 有中文，pdflatex 編不了中文。"
                 "把 source/paper/main.tex 第一行改成 % !TEX program = xelatex，再跑一次（中文字型那段已經寫好了）。")
    return len(entries), len(tagged)


def tidy():
    """排版的暫存檔收進 output/latex-log/，output/ 只留看得懂的成品。"""
    LOGDIR.mkdir(parents=True, exist_ok=True)
    for name in TEX_SCRATCH:
        if (OUT / name).exists():
            shutil.move(str(OUT / name), str(LOGDIR / name))


def latex(eng):
    step(f"4/5 編譯 PDF（{eng} → bibtex → {eng} ×2，在 output/ 裡排版）")
    shutil.copy(MAIN_TEX, OUT / "main.tex")
    shutil.copy(REFS, OUT / "refs.bib")
    LOGDIR.mkdir(parents=True, exist_ok=True)
    try:
        return compile_pdf(eng)
    finally:
        tidy()


def compile_pdf(eng):
    base = [eng, "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    steps = [base, ["bibtex", "main"], base, base]
    if not cite_keys(strip_comments(MAIN_TEX.read_text(encoding="utf-8"))):
        print("  論文還沒有引用文獻，先跳過 BibTeX。")
        steps = [base, base]
    for i, cmd in enumerate(steps):
        r = run(cmd, OUT, log=LOGDIR / f"build-{i}.log")
        if r.returncode != 0:
            tail = "\n".join((r.stdout + r.stderr).splitlines()[-25:])
            print(tail)
            fail(f"{cmd[0]} 失敗，完整紀錄在 output/latex-log/build-{i}.log。")
    log = (OUT / "main.log").read_text(encoding="utf-8", errors="replace")
    pages = re.search(r"Output written on main\.pdf \((\d+) page", log)
    und_c = sorted(set(re.findall(r"Citation `([^']+)' .*undefined", log)))
    und_r = sorted(set(re.findall(r"Reference `([^']+)' .*undefined", log)))
    if und_c:
        fail(f"PDF 裡有找不到的引用：{'、'.join(und_c)}。看 output/latex-log/main.log。")
    if und_r:
        fail(f"PDF 裡有找不到的圖表編號（\\ref 指到不存在的 \\label）：{'、'.join(und_r)}。")
    if not pages:
        fail("沒有產生 PDF，看 output/latex-log/main.log。")
    missing_chars = re.findall(r"Missing character: There is no (\S+)", log)
    if missing_chars:
        sample = "".join(dict.fromkeys(missing_chars))[:20]
        fail(f"PDF 裡有 {len(missing_chars)} 個字印不出來（例如：{sample}），多半是缺字型。"
             "中文的話，照 WORKFLOW.md 第 5 步確認第一行是 xelatex、電腦上有中文字型。")
    print(f"  output/main.pdf：{pages.group(1)} 頁")
    blg = OUT / "main.blg"
    warns = []
    if blg.exists():
        warns = [w.strip() for w in blg.read_text(encoding="utf-8", errors="replace").splitlines() if w.startswith("Warning--")]
    if warns:
        print("  書目警告（BibTeX）：有些文獻缺欄位，PDF 的參考文獻會少東西。請回 Zotero 補齊：")
        for w in warns:
            print(f"    {w}")
    return int(pages.group(1)), len(warns)


def docx():
    step("5/5 產生 Word 版（pandoc；只有加 --docx 才做）")
    figures("png")
    tex = MAIN_TEX.read_text(encoding="utf-8")
    tex = re.sub(r"\\input\{figures/(fig\d+)\.tex\}", r"\\includegraphics[width=14cm]{figures/\1.png}", tex)
    tmp = OUT / "main-for-word.tex"
    tmp.write_text(tex, encoding="utf-8")
    r = run(["pandoc", tmp.name, "-o", "main.docx", "--citeproc", f"--bibliography={REFS}",
             "--resource-path=.", "-M", "link-citations=true"], OUT)
    tmp.unlink()
    if r.returncode != 0:
        print(r.stderr)
        fail("pandoc 轉 Word 失敗。")
    print("  output/main.docx 完成。注意：每次產生都會蓋掉舊的 main.docx；要在 Word 裡改，先另存到別的資料夾。排版要人工再看一次。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", action="store_true", help="另外產生 Word 版")
    a = ap.parse_args()
    eng = engine()
    check_tools(a.docx, eng)
    try:
        old_docx = OUT / "main.docx"
        if not a.docx and old_docx.exists():  # 沒有要 Word 版，就清掉上次的，免得留著數字是舊的 Word 檔
            old_docx.unlink()
            print("（清掉了上次的 output/main.docx：這次沒有加 --docx，舊的 Word 檔數字會是舊的。）")
        analysis()
        figures()
        n_refs, n_nodoi = check_refs(eng)
        pages, n_warn = latex(eng)
        if a.docx:
            docx()
    except PermissionError as e:  # Windows：Excel、PDF 閱讀器開著 output 裡的檔，就刪不掉也寫不進去
        fail(f"有檔案被別的程式開著，改不了：{e.filename}。先關掉 Excel、Word 或 PDF 閱讀器裡開著的 output 資料夾裡的檔，再跑一次。")
    extra = " docx=output/main.docx" if a.docx else ""
    if "During the preparation of this example" in MAIN_TEX.read_text(encoding="utf-8"):
        print("\n  提醒：論文最後的 AI 使用聲明還是範例原文。寫自己的論文時，要改成你真的做過的事（README〈守住這四件事〉第 4 條）。")
    print(f"\nBUILD OK pages={pages} undefined_cites=0 undefined_refs=0 refs={n_refs} "
          f"refs_without_doi={n_nodoi} bib_warnings={n_warn}{extra}")


if __name__ == "__main__":
    main()
