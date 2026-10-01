#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สำรวจว่ามีภาพสินค้ารุ่นไหนใน Wikimedia Commons บ้าง (ไม่ดาวน์โหลด — แค่ประเมิน)

    py -3.13 tools/inventory.py            # สแกนรายการรุ่นที่เตรียมไว้
    py -3.13 tools/inventory.py "OPPO Reno 12"

ทำงานทีละคำขอ (ไม่ยิงพร้อมกัน) เพราะ Commons จำกัดอัตราการเรียก
"""
import json, re, sys, time, urllib.parse, urllib.request

UA = "Nasak16-coursework/1.0 (educational)"
BAD = ["logo", "icon", "map", "chart", "diagram", "poster", "box", "packaging", "teardown",
       "protector", "case", "cover", "shop", "store", "sign", "person", "portrait", "people",
       "beach", "mansion", "festival", "university", "reflection", "fireball", "azulene",
       "banana", "car", "building", "house", "room", "street", "welding", "solder"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def score(title, brand, model):
    t = norm(title)
    toks = [x for x in norm(model).split() if x not in ("the", "gen", "generation")]
    nums = [x for x in toks if x.isdigit()]
    words = [x for x in toks if not x.isdigit() and len(x) > 1]
    s = 2.0 if norm(brand).split()[0] in t else 0.0
    hit = sum(1 for n in nums if n in t.split())
    s += 3 * hit + 1.5 * sum(1 for w in words if w in t)
    if nums and hit < len(nums):
        s -= 4
    s -= 3 * sum(1 for b in BAD if b in t)
    return s, hit, len(nums)


def scan(brand, model, limit=10):
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           f"&gsrsearch={urllib.parse.quote(brand + ' ' + model)}&gsrnamespace=6&gsrlimit={limit}"
           "&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=900")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
    except Exception as e:
        return None, type(e).__name__
    out = []
    for pg in (d.get("query", {}).get("pages") or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        if ii.get("mime", "").startswith("image/svg") or not ii.get("thumburl"):
            continue
        sc, hit, want = score(pg["title"], brand, model)
        out.append({"title": pg["title"], "score": sc, "w": ii.get("width"), "h": ii.get("height"),
                    "url": ii["thumburl"], "num_hit": hit, "num_want": want})
    return sorted(out, key=lambda c: -c["score"]), None


def wikipedia_lead(brand, model):
    for lang in ("en", "th"):
        for cand in (f"{brand} {model}", model):
            try:
                req = urllib.request.Request(
                    f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" +
                    urllib.parse.quote(cand.replace(" ", "_")), headers={"User-Agent": UA})
                d = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
            except Exception:
                continue
            img = (d.get("originalimage") or {}).get("source")
            if img and norm(model.split()[0]) in norm(d.get("title", "")):
                return img, f"{lang}:{d.get('title')}"
    return None, None


if __name__ == "__main__":
    if len(sys.argv) > 2:
        rows = [(sys.argv[1], " ".join(sys.argv[2:]))]
    else:
        import os
        rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "inventory_list.json"), encoding="utf-8"))
    for brand, model in rows:
        wimg, wnote = wikipedia_lead(brand, model)
        cands, err = scan(brand, model)
        best = cands[0] if cands else None
        verdict = "✗ ไม่มี" if not best or best["score"] < 4 else "✓ มี"
        print(f"{verdict} {brand} {model}")
        if wimg:
            print(f"      wikipedia: {wnote} -> {wimg[:88]}")
        if err:
            print("      commons error:", err)
        for c in (cands or [])[:3]:
            print(f"      [{c['score']:5.1f}] {c['title'][5:62]} ({c['w']}x{c['h']})")
        time.sleep(1.2)
