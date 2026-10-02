#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ดึงรายการงานทั้งหมดจากหน้า index ของเรา (homework/index.html) มาเป็นข้อมูลให้แอป

    py -3.13 tools/build_homework_index.py            # อ่าน ../homework/index.html
    py -3.13 tools/build_homework_index.py <path>

ผลลัพธ์: data/homework_index.py (ใช้แสดงในหน้า “งานทั้งหมด (Index)” ของแอป)
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "homework",
                                                        "index.html")
OUT = os.path.join(ROOT, "data", "homework_index.py")
INDEX_URL = "https://nasak16.github.io/homework/"

CARD = re.compile(r'<article class="card" data-cat="(?P<cat>[^"]+)">(?P<body>.*?)</article>', re.S)
TAG = re.compile(r'<div class="tag"[^>]*>(?P<tag>.*?)</div>', re.S)
H3 = re.compile(r"<h3>(?P<t>.*?)</h3>", re.S)
P = re.compile(r"<p>(?P<t>.*?)</p>", re.S)
META = re.compile(r'<div class="meta">(?P<t>.*?)</div>', re.S)
CODE = re.compile(r"<code>(?P<t>.*?)</code>", re.S)
LINKS = re.compile(r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<label>.*?)</a>', re.S)
DATE = re.compile(r"อัปเดต\s+(?P<d>\d{4}-\d{2}-\d{2})")


def clean(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or ""))).strip()


def main():
    if not os.path.exists(SRC):
        raise SystemExit("ไม่พบไฟล์ index: %s" % SRC)
    src = open(SRC, encoding="utf-8").read()

    items = []
    for m in CARD.finditer(src):
        body = m.group("body")
        title = clean(H3.search(body).group("t")) if H3.search(body) else ""
        desc = clean(P.search(body).group("t")) if P.search(body) else ""
        repo = clean(CODE.search(body).group("t")) if CODE.search(body) else ""
        date = (DATE.search(body) or [None, ""])
        date = DATE.search(body).group("d") if DATE.search(body) else ""
        repo_url = INDEX_URL
        extra = []
        for a in LINKS.finditer(body):
            href, label = a.group("href"), clean(a.group("label"))
            if "github.com/Nasak16/" in href and href.rstrip("/").endswith(repo) and repo:
                repo_url = href
            elif href.startswith("http") and "target" in a.group(0):
                extra.append((label, href))
        items.append({"category": m.group("cat"), "title": title, "desc": desc,
                      "repo": repo, "date": date, "url": repo_url, "extra": extra})

    lines = ['# -*- coding: utf-8 -*-',
             '"""รายการงานทั้งหมด — สร้างอัตโนมัติด้วย tools/build_homework_index.py',
             '   (ดึงจากหน้า index: %s) — ห้ามแก้มือ"""' % INDEX_URL,
             'INDEX_URL = "%s"' % INDEX_URL,
             'HOMEWORK = [']
    for it in items:
        lines.append("    {")
        for k in ("category", "title", "desc", "repo", "date", "url"):
            lines.append('        "%s": %s,' % (k, as_repr(it[k])))
        lines.append('        "extra": [')
        for label, href in it["extra"]:
            lines.append('            (%s, %s),' % (as_repr(label), as_repr(href)))
        lines.append("        ],")
        lines.append("    },")
    lines.append("]")
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    cats = {}
    for it in items:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    print("ดึงได้ %d งาน -> %s" % (len(items), OUT))
    for c, n in sorted(cats.items(), key=lambda kv: -kv[1]):
        print("   %-18s %d งาน" % (c, n))


def as_repr(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


if __name__ == "__main__":
    main()
