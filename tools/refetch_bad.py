#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""หาภาพสินค้าที่ “ดีกว่า” ให้รุ่นที่การ์ดดูแย่ (ภาพมืด/แบน) แล้วทำตารางเทียบให้ตรวจด้วยตา

    py -3.13 tools/refetch_bad.py            # ดาวน์โหลดผู้สมัคร + ทำตารางเทียบ
    py -3.13 tools/refetch_bad.py --apply P01=2 P02=1 ...   # เลือกผู้สมัครลำดับที่ n

เกณฑ์: ชื่อไฟล์ต้องตรงรุ่น (score >= 4) และภาพต้อง “ไม่แบน” (std ของความสว่าง >= 42)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import inventory  # noqa: E402

CAND = os.path.join(ROOT, "tools", "out", "cand")
os.makedirs(CAND, exist_ok=True)
DATA = os.path.join(ROOT, "data", "phones.json")

# รุ่นที่การ์ดมืด/แบน (std ต่ำ) — ต้องหาภาพใหม่
BAD = {"P01": ("Apple", "iPhone 15 Pro Max"), "P02": ("Apple", "iPhone 15"),
       "P03": ("Apple", "iPhone 13"), "P20": ("OnePlus", "OnePlus 13R"),
       "P18": ("realme", "realme 16 Pro"), "P07": ("Samsung", "Galaxy A55")}

UA = "Nasak16-coursework/1.0 (educational)"


def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    with open(path, "wb") as f:
        f.write(b)
    return path


def brightness_std(path):
    import numpy as np
    im = Image.open(path).convert("RGB")
    w, h = im.size                     # ตัดกลางภาพแบบการ์ด (4:3) แล้ววัดความต่างของแสง
    cw, ch = min(w, int(h * 4 / 3)), min(h, int(w * 3 / 4))
    im = im.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2)).resize((240, 180))
    a = np.asarray(im.convert("L"), dtype=float)
    return float(a.std()), float(a.mean())


def collect(pid, brand, model, limit=12):
    """รวบรวมผู้สมัครจาก Wikipedia (lead image) + Commons แล้วกรองด้วยชื่อ + ความสว่าง"""
    out = []
    wimg, wnote = inventory.wikipedia_lead(brand, model)
    urls = []
    if wimg:
        urls.append((wimg, wnote or "wikipedia"))
    cands, err = inventory.scan(brand, model, limit=limit)
    for c in (cands or []):
        if c["score"] >= 4:
            urls.append((c["url"], c["title"]))
    if err:
        print("   commons error:", err)
    for i, (u, note) in enumerate(urls[:8]):
        ext = ".jpg" if ".jp" in u.lower() or "thumb" not in u else os.path.splitext(u)[1] or ".jpg"
        p = os.path.join(CAND, f"{pid}_{i}{ext}")
        try:
            if not os.path.exists(p):
                fetch(u, p)
            std, mean = brightness_std(p)
        except Exception as e:
            print("   ข้าม:", type(e).__name__, u[:60])
            continue
        out.append({"pid": pid, "i": i, "path": p, "url": u, "note": note[:70],
                    "std": round(std, 1), "mean": round(mean, 1)})
        time.sleep(0.8)
    good = [c for c in out if c["std"] >= 42]
    good.sort(key=lambda c: (-c["std"]))
    return out, good


def montage(items, out_path, cols=4, tile=(260, 200)):
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile[0], rows * (tile[1] + 26)), (16, 22, 38))
    d = ImageDraw.Draw(sheet)
    for k, c in enumerate(items):
        im = Image.open(c["path"]).convert("RGB")
        w, h = im.size
        cw, ch = min(w, int(h * 4 / 3)), min(h, int(w * 3 / 4))
        im = im.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2))
        im = im.resize(tile, Image.LANCZOS)
        x, y = (k % cols) * tile[0], (k // cols) * (tile[1] + 26)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + tile[1] + 6), f"{c['pid']} #{c['i']} std={c['std']}", fill=(240, 245, 255))
    sheet.save(out_path, optimize=True)
    print("ตารางเทียบ:", out_path, sheet.size)


def main():
    picks = {}
    for a in sys.argv[1:]:
        if a.startswith("--apply"):
            continue
        if "=" in a:
            k, v = a.split("=")
            picks[k] = int(v)

    if picks:                          # ---- โหมดเลือกผู้สมัคร
        data = json.load(open(DATA, encoding="utf-8"))
        items = data if isinstance(data, list) else data["phones"]
        table = json.load(open(os.path.join(CAND, "candidates.json"), encoding="utf-8"))
        for pid, n in picks.items():
            c = next(x for x in table[pid] if x["i"] == n)
            rec = next(p for p in items if p["phone_id"] == pid)
            slug = re.sub(r"[^a-z0-9]+", "-", (rec["brand"] + " " + rec["model"]).lower()).strip("-")
            dst = os.path.join(ROOT, "assets", "phones", slug + ".jpg")
            im = Image.open(c["path"]).convert("RGB")
            im.save(dst, quality=90, optimize=True)
            old = os.path.basename(rec["image"])
            rec["image"] = "assets/phones/" + os.path.basename(dst)
            rec["image_title"] = c["note"]
            rec.pop("image_url", None)
            print(f"{pid} {rec['brand']} {rec['model']}: {old} -> {os.path.basename(dst)} "
                  f"(std={c['std']}, {c['note'][:50]})")
        json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("บันทึก data/phones.json แล้ว — อย่าลืมรัน tools/make_cards.py ต่อ")
        return

    table = {}
    for pid, (brand, model) in BAD.items():
        print(f"== {pid} {brand} {model}")
        allc, good = collect(pid, brand, model)
        for c in allc:
            print(f"   #{c['i']} std={c['std']:6} mean={c['mean']:6} {c['note']}")
        table[pid] = allc
    json.dump(table, open(os.path.join(CAND, "candidates.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    for k in range(0, len(BAD), 3):
        group = list(BAD)[k:k + 3]
        items = [c for pid in group for c in table[pid][:4]]
        montage(items, os.path.join(ROOT, "tools", "out", f"cand_sheet_{k // 3 + 1}.png"))
    print("ตรวจตารางเทียบด้วยตา แล้วสั่ง: py -3.13 tools/refetch_bad.py P01=2 P02=1")


if __name__ == "__main__":
    main()
