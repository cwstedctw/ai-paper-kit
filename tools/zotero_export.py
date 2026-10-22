"""從 Zotero 本機介面把一個文獻集匯出成 source/refs/refs.bib（不用裝外掛的接法）。

用法：
    uv run tools/zotero_export.py "文獻集名稱"           # 存到 source/refs/refs.bib
    uv run tools/zotero_export.py "文獻集名稱" 別的路徑.bib

先決條件：Zotero 開著，而且在 Zotero 設定 → 進階 勾了
「允許此電腦上的其他應用程式與 Zotero 通訊」。
Windows、Mac 都能用，只用到 Python 內建的模組。
一次最多拿 100 筆，會自動分頁拿完（文獻集清單也是）。
文獻集裡的獨立筆記、獨立 PDF 不會變成書目，所以匯出的筆數可能比 Zotero 顯示的少。
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:23119/api/users/0"
HEADERS = {"Zotero-Allowed-Request": "true"}
PAGE = 100


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8"), r.headers


def pages(path, params):
    """分頁拿完。有 Total-Results 就照它；沒有就拿到空白頁為止。
    不能用「這一頁不滿 100 筆」判斷結束：獨立筆記、PDF 會占名額，卻不會變成書目。"""
    start = 0
    while start < 100000:
        q = urllib.parse.urlencode({**params, "limit": PAGE, "start": start})
        body, headers = get(f"{BASE}/{path}?{q}")
        total = headers.get("Total-Results")
        yield body
        start += PAGE
        if total is not None and total.strip().isdigit():
            if start >= int(total):
                return
        elif not body.strip() or body.strip() == "[]":
            return


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    name = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "source" / "refs" / "refs.bib"
    try:
        cols = [c for body in pages("collections", {}) for c in json.loads(body)]
    except urllib.error.URLError as e:
        sys.exit(f"連不到 Zotero（{e}）。Zotero 有開著嗎？有勾「允許其他應用程式通訊」嗎？")
    keys = [c["key"] for c in cols if c.get("data", {}).get("name") == name]
    if not keys:
        names = "、".join(c.get("data", {}).get("name", "") for c in cols)
        sys.exit(f"找不到文獻集「{name}」。現有的文獻集：{names}")
    if len(keys) > 1:
        sys.exit(f"有 {len(keys)} 個文獻集都叫「{name}」。請先在 Zotero 把其中一個改名，再匯出。")
    key = keys[0]
    parts = [body.strip() for body in pages(f"collections/{key}/items/top", {"format": "bibtex"})]
    text = "\n\n".join(p for p in parts if p) + "\n"
    count = text.count("\n@") + (1 if text.startswith("@") else 0)
    if count == 0:
        sys.exit("匯出了 0 筆。文獻集是空的嗎？")
    out.write_text(text, encoding="utf-8")
    print(f"匯出 {count} 筆 → {out}")


if __name__ == "__main__":
    main()
