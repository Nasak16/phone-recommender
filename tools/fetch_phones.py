#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างชุดข้อมูลมือถือ + ดาวน์โหลดภาพจริงจาก Wikimedia Commons

    py -3.13 tools/fetch_phones.py

ได้ผลลัพธ์
- data/phones.json        : 24 รุ่น (ยี่ห้อ/ระดับราคา/ไฟล์ภาพ/เครดิตภาพ)
- assets/phones/*.jpg     : ภาพสินค้า (ใช้ทั้งในแอปและโน๊ตบุ๊ก/Colab)
- tools/out/phone_sheet.png : ตารางภาพรวมไว้ตรวจด้วยตาว่าตรงรุ่นทุกภาพ
ข้อมูลรุ่น/ยี่ห้อ/ระดับราคาเป็นการจัดชุดสำหรับการเรียนการสอน (ไม่ใช่สเปกทางการ)
ภาพเป็นผลงานของผู้อัปโหลดใน Wikimedia Commons ตามสัญญาอนุญาตของแต่ละไฟล์ (ดูเครดิตใน phones.json)
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "phones")
os.makedirs(IMG, exist_ok=True)
UA = {"User-Agent": "phone-recommender-coursework/1.0 (educational demo)"}

# (รุ่น, ยี่ห้อ, ระดับราคา, คำค้นใน Commons)
PHONES = [
    ("iPhone 15 Pro Max", "Apple", "เรือธง", "iPhone 15 Pro Max"),
    ("iPhone 15", "Apple", "เรือธง", "iPhone 15 smartphone"),
    ("iPhone 13", "Apple", "ระดับกลาง", "iPhone 13"),
    ("iPhone SE (3rd gen)", "Apple", "ระดับเริ่มต้น", "iPhone SE 3rd generation"),
    ("Galaxy S24 Ultra", "Samsung", "เรือธง", "Samsung Galaxy S24 Ultra"),
    ("Galaxy S23", "Samsung", "เรือธง", "Samsung Galaxy S23"),
    ("Galaxy Z Flip 5", "Samsung", "เรือธง", "Samsung Galaxy Z Flip 5"),
    ("Galaxy A55", "Samsung", "ระดับกลาง", "Samsung Galaxy A55"),
    ("Pixel 8 Pro", "Google", "เรือธง", "Pixel 8 Pro"),
    ("Pixel 7a", "Google", "ระดับกลาง", "Pixel 7a"),
    ("Xiaomi 14", "Xiaomi", "เรือธง", "Xiaomi 14 smartphone"),
    ("Redmi Note 13 Pro", "Xiaomi", "ระดับกลาง", "Redmi Note 13 Pro"),
    ("POCO X6 Pro", "Xiaomi", "ระดับกลาง", "POCO X6 Pro"),
    ("Find X7 Ultra", "OPPO", "เรือธง", "Oppo Find X7 Ultra"),
    ("Reno 11", "OPPO", "ระดับกลาง", "Oppo Reno 11"),
    ("A78", "OPPO", "ระดับเริ่มต้น", "Oppo A78"),
    ("vivo X100 Pro", "vivo", "เรือธง", "Vivo X100 Pro"),
    ("vivo V30", "vivo", "ระดับกลาง", "Vivo V30"),
    ("realme GT5 Pro", "realme", "เรือธง", "Realme GT5 Pro"),
    ("realme 12 Pro+", "realme", "ระดับกลาง", "Realme 12 Pro"),
    ("OnePlus 12", "OnePlus", "เรือธง", "OnePlus 12"),
    ("ROG Phone 8", "ASUS", "เรือธง", "Asus ROG Phone 8"),
    ("Honor Magic6 Pro", "Honor", "เรือธง", "Honor Magic6 Pro"),
    ("Nothing Phone (2)", "Nothing", "ระดับกลาง", "Nothing Phone (2)"),
]

BAD_WORDS = ("logo", "icon", "wordmark", "svg", "diagram", "chart", "map", "screenshot",
             "advert", "poster", "benchmark", "box", "packaging", "banner", "sign",
             "socket", "charger", "cable", "case", "stand", "cpu", "chip", "wallpaper")
GOOD_WORDS = ("front", "back", "photo", "display", "screen")


def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8"))


def fetch(url, tries=4):
    for i in range(tries):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                         timeout=60).read()
            if len(data) > 5000:
                return data
            raise ValueError("too small %d" % len(data))
        except Exception as e:
            print("   retry%d %s: %s" % (i + 1, url[-40:], type(e).__name__))
            time.sleep(2 + 2 * i)
    return None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def search_image(term, model_tokens):
    """หาภาพใน Commons: เลือกภาพที่เป็น 'รูปตัวเครื่อง' มากที่สุด"""
    try:
        d = api({"action": "query", "format": "json", "generator": "search",
                 "gsrsearch": "filetype:bitmap " + term, "gsrnamespace": "6", "gsrlimit": "25",
                 "prop": "imageinfo", "iiprop": "url|extmetadata",
                 "iiurlwidth": "900"})
    except Exception as e:
        print("   search error:", e)
        return None
    pages = list((d.get("query", {}).get("pages") or {}).values())
    best, best_score = None, -99
    for p in pages:
        title = p.get("title", "")
        low = title.lower()
        if any(b in low for b in BAD_WORDS):
            continue
        info = (p.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url or not url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")):
            continue
        score = 0
        score += sum(3 for t in model_tokens if t.lower() in low)
        score += sum(1 for g in GOOD_WORDS if g in low)
        score -= 2 if "logo" in low else 0
        score -= 1 if p.get("width") and p["width"] < 500 else 0
        if score > best_score:
            best, best_score = (title, url, info.get("descriptionurl", "")), score
    return best


def main():
    out, fails = [], []
    for model, brand, tier, term in PHONES:
        tokens = [t for t in re.split(r"[\s()]+", model) if len(t) > 1][:3]
        hit = search_image(term, tokens)
        if not hit:
            fails.append((model, "ไม่พบภาพใน Commons"))
            continue
        title, url, page = hit
        path = os.path.join(IMG, slug(model) + ".jpg")
        data = fetch(url)
        if not data:
            fails.append((model, "ดาวน์โหลดภาพไม่สำเร็จ"))
            continue
        open(path, "wb").write(data)
        out.append({"phone_id": "P%02d" % (len(out) + 1), "model": model, "brand": brand,
                    "tier": tier, "image": "assets/phones/" + os.path.basename(path),
                    "image_title": title, "image_page": page})
        print("OK   %-22s %-9s %-14s %5dKB  %s" % (model, brand, tier, len(data) // 1024,
                                                   title[5:60]))
        time.sleep(0.3)
    json.dump(out, open(os.path.join(ROOT, "data", "phones.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nได้ภาพ %d/%d -> data/phones.json" % (len(out), len(PHONES)))
    for m, why in fails:
        print("FAIL", m, "|", why)
    return 0 if len(out) >= 20 else 1


if __name__ == "__main__":
    sys.exit(main())
