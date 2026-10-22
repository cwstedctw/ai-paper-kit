"""開一篇新論文：把現在 source/ 的內容收進 examples/，再換上空白的骨架。不會刪掉任何東西。

用法（在範本資料夾裡；Mac 用 python3）：
    python tools/new_paper.py                     # 範例收進 examples/，source/ 換成空白骨架
    python tools/new_paper.py --refs material/模擬/refs.bib
                                                  # 研究模擬：書目換成這個檔（當成從 Zotero 匯出的）
    python tools/new_paper.py --name 範例論文重算   # 收進 examples/ 的資料夾名字（不寫就用日期）
    python tools/new_paper.py --name 模擬論文 --restore examples/範例論文重算
                                                  # 現在的 source/ 收進 examples/模擬論文，
                                                  # 再把 examples/範例論文重算 那份「複製」回 source/（examples/ 裡那份還在）

研究資料（source/data/ 的資料檔）一律留在 source/data/：不複製進 examples/，也不刪。
examples/ 裡只留一份 data/README.md（欄位說明），因為 examples/ 會跟著資料夾推上 GitHub，
多複製一份資料，就多一個地方可能把資料推出去。.gitignore 也排除了 examples/ 裡的資料檔（第二道保險）。
（--keep-data 是舊的寫法，現在資料本來就會留著；加了也照樣能跑。）

做完以後 source/ 長這樣：
    data/      研究資料，原封不動
    refs/      refs.bib（--refs 指定的檔；不然是空的，等 Zotero 匯出）
    scripts/   analyze.py 骨架：只算人數
    gnuplot/   空的，要畫圖再請 AI 寫
    paper/     main.tex 骨架：各節的標題和說明
原本的 source/（資料檔除外）在 examples/<名字>/source/，隨時可以打開來參考，或用 --restore 複製回來。
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source"
SKEL = Path(__file__).resolve().parent / "skeleton"
BUILD_HINT = "python build.py（Mac：python3 build.py）"

EMPTY_REFS = """% refs.bib：這篇論文的書目。
% 在 Zotero 建這篇論文的文獻集，用 Better BibTeX 匯出、勾「保持更新」，存成這個檔（蓋掉這一份）。
% 不要手改；要加文獻就加進 Zotero。
"""
EMPTY_GNUPLOT = """# source/gnuplot：畫圖腳本

一張圖一個 `.gp` 檔。要畫圖，跟 AI 說要什麼圖；它會在 `source/scripts/analyze.py` 產生小表（`output/figdata/`），再寫一支腳本讀它，畫到 `output/figures/`。
寫法可以參考 `examples/` 裡範例的 `source/gnuplot/`。

每支 `.gp` 開頭都要有這一行：

    set encoding utf8

不寫的話，Windows 版 gnuplot 會照電腦語系把 `\\inputencoding{cp1252}` 之類的設定寫進圖檔，pdflatex 就編不過（2026-10-22 在 Windows 實測）。
"""
EMPTY_DATA = """# source/data：研究資料

把去識別化的研究資料存成「CSV UTF-8（逗號分隔）」放在這裡，並在這份說明寫清楚每一欄是什麼。
放之前先確認符合範本 README〈守住這四件事〉第 1 條的四個條件。AI 只讀、不改這裡的檔。
"""


def copy_without_data(src, dest):
    """把 src（一份 source/）複製到 dest，但 data/ 裡只帶 README.md，資料檔不複製。回傳沒複製的檔名。"""
    data_dir = (src / "data").resolve()

    def ignore(folder, names):
        if Path(folder).resolve() == data_dir:
            return [n for n in names if n != "README.md"]
        return []

    shutil.copytree(src, dest, ignore=ignore)
    if not data_dir.is_dir():
        return []
    return sorted(p.name for p in data_dir.iterdir() if p.name != "README.md")


def restore_from(archive):
    """把 archive（examples/<名字>/source/）複製回 source/。

    data/ 以外的東西整個換成 archive 裡的那份（現在的已經先收進 examples/ 了）。
    data/ 不清空：現在的資料檔留著；archive 的 data/README.md 複製回來；
    archive 裡如果有資料檔（舊版工具收的），只補 source/data/ 沒有的，同名的不蓋掉。回傳沒蓋掉的檔名。"""
    for item in SRC.iterdir():
        if item.name == "data":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()  # 已經收進 examples/
    for item in archive.iterdir():
        if item.name == "data":
            continue
        if item.is_dir():
            shutil.copytree(item, SRC / item.name)
        else:
            shutil.copy2(item, SRC / item.name)
    kept = []
    if (archive / "data").is_dir():
        (SRC / "data").mkdir(exist_ok=True)
        for f in (archive / "data").iterdir():
            target = SRC / "data" / f.name
            if f.name == "README.md" or not target.exists():
                shutil.copytree(f, target, dirs_exist_ok=True) if f.is_dir() else shutil.copy2(f, target)
            else:
                kept.append(f.name)
    return kept


def main():
    ap = argparse.ArgumentParser(description="開一篇新論文：source/ 收進 examples/（資料檔除外），換上空白骨架")
    ap.add_argument("--keep-data", action="store_true", help="舊的寫法：現在研究資料本來就會留在 source/data/")
    ap.add_argument("--refs", help="書目換成這個 .bib 檔（例如 material/模擬/refs.bib）")
    ap.add_argument("--name", help="收進 examples/ 的資料夾名字")
    ap.add_argument("--restore", help="不換骨架，改把這個 examples/ 資料夾裡的 source/ 複製回來（原資料夾保留）")
    a = ap.parse_args()

    restore_src = None
    if a.restore:
        restore_src = (ROOT / a.restore / "source").resolve()
        if not restore_src.is_dir():
            sys.exit(f"找不到 {a.restore}/source/。")

    refs_src = None
    if a.refs:
        refs_src = (ROOT / a.refs).resolve() if not Path(a.refs).is_absolute() else Path(a.refs)
        if not refs_src.exists():
            sys.exit(f"找不到書目檔 {a.refs}。")

    name = a.name or datetime.now().strftime("%Y%m%d-%H%M-舊的source")
    dest = ROOT / "examples" / name
    n = 2
    while dest.exists():
        dest = ROOT / "examples" / f"{name}-{n}"
        n += 1
    skipped = copy_without_data(SRC, dest / "source")
    print(f"原本的 source/ 已收進 {dest.relative_to(ROOT).as_posix()}/source/")
    if skipped:
        print(f"  研究資料沒有一起收：{', '.join(skipped)} 留在 source/data/（沒有複製、也沒有刪），"
              "examples/ 裡只放 data/README.md。")

    if restore_src:
        kept = restore_from(restore_src)
        print(f"已把 {a.restore}/source/ 複製回 source/（{a.restore}/ 那份還在，沒有搬走）。")
        print("  source/data/ 的資料檔照舊留著，只換回那份的 data/README.md。")
        if kept:
            print(f"  {a.restore}/source/data/ 裡的 {', '.join(kept)} 跟 source/data/ 的同名，沒有蓋掉現在的這份。")
        print(f"下一步：跑一次 {BUILD_HINT}。")
        return

    for sub in ["refs", "scripts", "gnuplot", "paper"]:
        shutil.rmtree(SRC / sub, ignore_errors=True)  # 已經收進 examples/，這裡換成骨架
        (SRC / sub).mkdir(parents=True)
    (SRC / "data").mkdir(exist_ok=True)
    if not (SRC / "data" / "README.md").exists():
        (SRC / "data" / "README.md").write_text(EMPTY_DATA, encoding="utf-8")
    if refs_src:
        shutil.copy(refs_src, SRC / "refs" / "refs.bib")
    else:
        (SRC / "refs" / "refs.bib").write_text(EMPTY_REFS, encoding="utf-8")
    shutil.copy(SKEL / "analyze.py", SRC / "scripts" / "analyze.py")
    (SRC / "gnuplot" / "README.md").write_text(EMPTY_GNUPLOT, encoding="utf-8")
    shutil.copy(SKEL / "main.tex", SRC / "paper" / "main.tex")

    print("source/ 換成新論文的骨架：")
    print("  data/     研究資料原封不動（要換成你的資料：放進來，再請 AI 改 analyze.py 上面 DATA 那一行）")
    print(f"  refs/     {'用 ' + a.refs if refs_src else '空的，等 Zotero 匯出'}")
    print("  scripts/  analyze.py 骨架（只算人數）")
    print("  gnuplot/  空的")
    print("  paper/    main.tex 骨架")
    print(f"下一步：跑一次 {BUILD_HINT}，應該會編出一份只有標題和各節標題的 PDF。")


if __name__ == "__main__":
    main()
