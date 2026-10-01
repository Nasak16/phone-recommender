#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ดึงภาพสินค้ามือถือแบบคัดกรองเข้ม (แก้ภาพผิดรุ่น)

ลำดับแหล่งภาพ
 1) Wikipedia REST summary ของรุ่นนั้น (en แล้ว th) → ภาพหลักของบทความ (มักเป็นภาพสินค้าจริง)
 2) Wikimedia Commons search + ให้คะแนนชื่อไฟล์เอง (ต้องมียี่ห้อ+รุ่นครบ) และหักคะแนนคำต้องห้าม

    py -3.13 tools/fix_phones_images.py            # ทุกรุ่น
    py -3.13 tools/fix_phones_images.py P12 P18    # เฉพาะรุ่นที่ระบุ
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "assets", "phones")
UA = "Nasak16-coursework/1.0 (educational; contact: student)"
BAD = ["logo", "icon", "map", "chart", "diagram", "graph", "poster", "advert", "advertisement",
       "box", "packaging", "teardown", "protector", "case", "cover", "bumper", "holder",
       "mount", "stand", "wallet", "earbud", "charger", "cable", "watch", "tablet", "laptop",
       "sign", "shop", "store", "screenshot", "stamp", "coin", "book", "vs ", "comparison",
       "representative", "politician", "portrait", "person", "man", "woman", "beach", "banana"]


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def jget(url, timeout=45):
    return json.loads(get(url, timeout).decode("utf-8"))


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def tokens(model):
    """คำสำคัญของรุ่น เช่น 'iPhone 15 Pro Max' -> ['iphone','15','pro','max']"""
    t = [x for x in norm(model).split() if x not in ("the", "gen", "generation")]
    return t


def score(title, brand, model):
    """ให้คะแนนชื่อไฟล์: ต้องมียี่ห้อ + โทเคนของรุ่น (ตัวเลขสำคัญที่สุด)"""
    t, s = norm(title), 0.0
    toks = tokens(model)
    if norm(brand).split()[0] in t:
        s += 2
    nums = [x for x in toks if x.isdigit()]
    words = [x for x in toks if not x.isdigit()]
    hit = sum(1 for n in nums if n in t.split())
    s += 3 * hit
    s += 1.5 * sum(1 for w in words if len(w) > 2 and w in t)
    if nums and hit < len(nums):
        s -= 4                        # ขาดเลขรุ่น = คนละรุ่น
    s -= 3 * sum(1 for b in BAD if b in t)
    if t.endswith(".svg") or " .svg" in t:
        s -= 5
    return s


def wikipedia_image(brand, model):
    """ภาพหลักของบทความ Wikipedia (ชื่อบทความมักเป็น 'iPhone 15' / 'Samsung Galaxy S24')"""
    for lang in ("en", "th"):
        for cand in (f"{brand} {model}", model):
            slug = urllib.parse.quote(cand.replace(" ", "_"))
            try:
                d = jget(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}")
            except Exception:
                continue
            img = (d.get("originalimage") or d.get("thumbnail") or {}).get("source")
            title = d.get("title", "")
            if img and norm(model.split()[0]) in norm(title):
                return img, "wikipedia:" + lang + ":" + title, 99
    return None


def commons_candidates(brand, model, limit=14):
    q = urllib.parse.quote(f"{brand} {model}")
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           f"&gsrsearch={q}&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo"
           "&iiprop=url|size|mime&iiurlwidth=900")
    try:
        d = jget(url)
    except Exception:
        return []
    out = []
    for page in (d.get("query", {}).get("pages") or {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        if not ii.get("thumburl") or ii.get("mime", "").startswith("image/svg"):
            continue
        out.append({"title": page["title"], "url": ii["thumburl"], "w": ii.get("width", 0),
                    "h": ii.get("height", 0),
                    "score": score(page["title"], brand, model)})
    return sorted(out, key=lambda c: -c["score"])


def valid_image(data):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.load()
        w, h = im.size
        return w >= 300 and h >= 300 and len(data) > 12000
    except Exception:
        return False


def fetch(phone, log):
    brand, model = phone["brand"], phone["model"]
    tried = []
    wi = wikipedia_image(brand, model)
    if wi:
        url, note, _ = wi
        try:
            data = get(url, 60)
            if valid_image(data):
                log.append(f"  ✓ wikipedia {note} ({len(data)//1024} KB)")
                return data, note, url
            log.append("  ✗ ภาพ wikipedia เล็ก/เสีย: " + note)
        except Exception as e:
            log.append(f"  ✗ wikipedia โหลดไม่ได้ ({type(e).__name__})")
    for c in commons_candidates(brand, model):
        tried.append(c["title"])
        if c["score"] < 4:            # ต้องมียี่ห้อ+เลขรุ่นอย่างน้อย
            continue
        if c["w"] < 500 or c["h"] < 500:
            continue
        try:
            data = get(c["url"], 60)
        except Exception:
            continue
        if valid_image(data):
            log.append(f"  ✓ commons {c['title']} (score {c['score']:.1f}, {len(data)//1024} KB)")
            return data, c["title"], c["url"]
    log.append("  ✗ ไม่พบภาพที่ชื่อตรงรุ่น — ผู้สมัครที่มี: " + " | ".join(tried[:8]))
    return None, None, None


def main():
    want = [a for a in sys.argv[1:] if a.startswith("P")]
    phones = json.load(open(os.path.join(ROOT, "data", "phones.json"), encoding="utf-8"))
    os.makedirs(OUTDIR, exist_ok=True)
    changed = 0
    for p in phones:
        if want and p["phone_id"] not in want:
            continue
        log = [f"{p['phone_id']} {p['brand']} {p['model']} (เดิม: {p.get('image_title','')[:40]})"]
        data, title, page = fetch(p, log)
        print("\n".join(log))
        if data:
            fn = os.path.basename(p["image"])
            with open(os.path.join(OUTDIR, fn), "wb") as f:
                f.write(data)
            p["image_title"], p["image_page"] = title, page
            changed += 1
        time.sleep(0.4)
    json.dump(phones, open(os.path.join(ROOT, "data", "phones.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nอัปเดต {changed} รุ่น")


if __name__ == "__main__":
    main()
