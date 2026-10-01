#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สลับรุ่นที่หาภาพจริงใน Commons/Wikipedia ไม่ได้ → ใช้รุ่นที่มีภาพจริง + เก็บภาพใหม่

    py -3.13 tools/apply_picks.py
"""
import io, json, os, re, sys, urllib.parse, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "assets", "phones")
UA = "Nasak16-coursework/1.0 (educational)"
BAD = ["logo", "icon", "map", "chart", "diagram", "poster", "box", "packaging", "teardown",
       "protector", "case", "cover", "bumper", "holder", "shop", "store", "sign", "person",
       "portrait", "people", "broken", "crack", "wildfire", "moon", "concert", "jaguar", "ford"]

# phone_id: (ยี่ห้อใหม่, รุ่นใหม่, ระดับราคา, คำค้น Commons, บังคับว่าชื่อไฟล์ต้องมีคำนี้)
PICKS = {
    "P12": ("Xiaomi", "POCO X3 Pro", "ระดับกลาง", "Xiaomi POCO X3 Pro", "Poco X3 Pro"),
    "P14": ("OPPO", "Find X6 Pro", "เรือธง", "OPPO Find X6 Pro", "Find X6 Pro"),
    "P17": ("vivo", "Y36", "ระดับเริ่มต้น", "vivo Y36", "Y36"),
    "P18": ("realme", "realme 16 Pro", "ระดับกลาง", "realme 16 Pro", "16 Pro"),
    "P19": ("realme", "C35", "ระดับเริ่มต้น", "realme C35", "C35"),
    "P20": ("OnePlus", "OnePlus 13R", "ระดับกลาง", "OnePlus 13R", "13R"),
    "P23": ("Sony", "Xperia 1 V", "เรือธง", "Sony Xperia 1 V", "Xperia 1"),
}


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


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
                req = urllib.request.Request(
                    f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" +
                    urllib.parse.quote(cand.replace(" ", "_")), headers={"User-Agent": UA})
                d = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
            except Exception:
                continue
            img = (d.get("originalimage") or {}).get("source")
            if img and norm(model.split()[0]) in norm(d.get("title", "")):
                return img, f"wikipedia:{lang}:{d.get('title')}"
    return None, None


def commons(term, must_have, limit=12):
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           f"&gsrsearch={urllib.parse.quote(term)}&gsrnamespace=6&gsrlimit={limit}"
           "&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1000")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
    except Exception:
        return []
    out = []
    for pg in (d.get("query", {}).get("pages") or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        t = pg["title"]
        if ii.get("mime", "").startswith("image/svg") or not ii.get("thumburl"):
            continue
        if norm(must_have) not in norm(t):
            continue
        if any(b in norm(t) for b in BAD):
            continue
        if min(ii.get("width", 0), ii.get("height", 0)) < 400:
            continue
        out.append({"title": t, "url": ii["thumburl"], "w": ii["width"], "h": ii["height"]})
    return out


def main():
    phones = json.load(open(os.path.join(ROOT, "data", "phones.json"), encoding="utf-8"))
    for p in phones:
        pid = p["phone_id"]
        if pid not in PICKS:
            continue
        brand, model, tier, term, must = PICKS[pid]
        data = title = page = None
        url, note = wiki_lead(brand, model)
        if url:
            try:
                d = get(url)
                if valid(d):
                    data, title, page = d, note, url
            except Exception:
                pass
        if data is None:
            for c in commons(term, must)[:4]:
                try:
                    d = get(c["url"])
                except Exception:
                    continue
                if valid(d):
                    data, title, page = d, c["title"], c["url"]
                    break
        if data is None:
            print("✗ %s %s: ยังไม่พบภาพ" % (pid, model))
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-") + ".jpg"
        old = os.path.join(ROOT, p["image"])
        target = os.path.join(OUTDIR, slug)
        with open(target, "wb") as f:
            f.write(data)
        if os.path.exists(old) and os.path.abspath(old) != os.path.abspath(target):
            os.remove(old)
        p.update({"brand": brand, "model": model, "tier": tier, "image": "assets/phones/" + slug,
                  "image_title": title, "image_page": page})
        print("✓ %s -> %s %s (%s) | %s" % (pid, brand, model, tier, title[:60]))
    json.dump(phones, open(os.path.join(ROOT, "data", "phones.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    objs = json.load(open(os.path.join(ROOT, "data", "phones.json"), encoding="utf-8"))
    print("สลับแล้ว — รุ่นทั้งหมด %d" % len(objs))


if __name__ == "__main__":
    main()
