#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ยกระดับคุณภาพภาพสินค้า: เลือกภาพที่เป็น "ตัวเครื่อง" มากกว่าภาพหน้าจอ/ป้ายร้าน

    py -3.13 tools/upgrade_images.py P05 P08 P09 ...
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "assets", "phones")
UA = "Nasak16-coursework/1.0 (educational)"

# คำที่บ่งบอกว่าเป็นภาพหน้าจอ/ป้ายร้าน/ชิ้นส่วน (หักคะแนนแรง)
BAD = ["screen", "display", "interface", "settings", "android", "lineage", "ui ", " ui",
       "information", "informazioni", "setup", "review", "hand", "holding", "person",
       "people", "shop", "store", "retail", "price", "sign", "logo", "icon", "map", "chart",
       "diagram", "poster", "broken", "crack", "repair", "teardown", "frame", "part",
       "battery", "box", "packaging", "accessor", "case", "cover", "protector", "moon",
       "concert", "wildfire", "banana", "car"]
# คำที่บ่งบอกว่าเป็นภาพตัวเครื่อง (เพิ่มคะแนน)
GOOD = ["back", "rear", "front", "titanium", "color", "colour", "product", "photo", "series",
        "smartphone", "5g", "phone"]


def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                  timeout=timeout).read()


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
        s -= 6
    s -= 4 * sum(1 for b in BAD if b in t)
    s += 1.0 * sum(1 for g in GOOD if g in t)
    return s


def valid(data):
    try:
        im = Image.open(io.BytesIO(data)); im.load()
        return im.size[0] >= 400 and im.size[1] >= 400 and len(data) > 8000
    except Exception:
        return False


def wiki_lead(brand, model):
    for lang in ("en", "th"):
        for cand in (f"{brand} {model}", model):
            try:
                d = json.loads(get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" +
                                   urllib.parse.quote(cand.replace(" ", "_")), 40).decode())
            except Exception:
                continue
            img = (d.get("originalimage") or {}).get("source")
            if img and norm(model.split()[0]) in norm(d.get("title", "")):
                return img, f"wikipedia:{lang}:{d.get('title')}"
    return None, None


def commons(term, limit=20):
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           f"&gsrsearch={urllib.parse.quote(term)}&gsrnamespace=6&gsrlimit={limit}"
           "&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1000")
    try:
        d = json.loads(get(url, 45).decode())
    except Exception:
        return []
    out = []
    for pg in (d.get("query", {}).get("pages") or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        if ii.get("mime", "").startswith("image/svg") or not ii.get("thumburl"):
            continue
        if min(ii.get("width", 0), ii.get("height", 0)) < 400:
            continue
        out.append({"title": pg["title"], "url": ii["thumburl"]})
    return out


def main():
    want = [a for a in sys.argv[1:] if a.startswith("P")]
    phones = json.load(open(os.path.join(ROOT, "data", "phones.json"), encoding="utf-8"))
    for p in phones:
        if p["phone_id"] not in want:
            continue
        brand, model = p["brand"], p["model"]
        best = None
        url, note = wiki_lead(brand, model)
        if url:
            try:
                d = get(url)
                if valid(d):
                    best = (d, note)
            except Exception:
                pass
        if best is None:
            cands = sorted(commons(f"{brand} {model}"), key=lambda c: -score(c["title"], brand, model))
            for c in cands[:6]:
                if score(c["title"], brand, model) < 3:
                    break
                try:
                    d = get(c["url"])
                except Exception:
                    continue
                if valid(d):
                    best = (d, c["title"])
                    break
        if best is None:
            print("✗ %s %s: ไม่พบภาพใหม่ (คงของเดิม)" % (p["phone_id"], model))
            continue
        data, title = best
        fn = os.path.basename(p["image"])
        with open(os.path.join(OUTDIR, fn), "wb") as f:
            f.write(data)
        im = Image.open(os.path.join(OUTDIR, fn)).convert("RGB")
        if im.width > 900:
            im = im.resize((900, int(im.height * 900 / im.width)), Image.LANCZOS)
        im.save(os.path.join(OUTDIR, fn), "JPEG", quality=86, optimize=True)
        p["image_title"] = title
        print("✓ %s %s | %s" % (p["phone_id"], model, title[:64]))
        time.sleep(0.8)
    json.dump(phones, open(os.path.join(ROOT, "data", "phones.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
