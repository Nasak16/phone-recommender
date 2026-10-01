#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างภาพการ์ดขนาดเท่ากันทุกใบ (4:3) สำหรับแสดงในแอป/สไลด์

    py -3.13 tools/make_cards.py       # -> assets/cards/
"""
import glob, json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "cards"); os.makedirs(OUT, exist_ok=True)
W, H, BG = 720, 540, (14, 22, 38)

phones = json.load(open(os.path.join(ROOT, "data", "phones.json"), encoding="utf-8"))
for p in phones:
    src = os.path.join(ROOT, p["image"])
    im = Image.open(src).convert("RGB")
    ar_box, ar_img = W / H, im.width / im.height
    if ar_img > ar_box:                       # ภาพกว้างเกิน → ตัดซ้าย-ขวา
        w = int(im.height * ar_box)
        im = im.crop(((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height))
    else:                                     # ภาพสูงเกิน → ตัดบน-ล่าง
        h = int(im.width / ar_box)
        im = im.crop((0, (im.height - h) // 2, im.width, (im.height - h) // 2 + h))
    im = im.resize((W, H), Image.LANCZOS)
    name = os.path.splitext(os.path.basename(p["image"]))[0] + ".jpg"
    im.save(os.path.join(OUT, name), "JPEG", quality=88, optimize=True)
print("การ์ด %d ไฟล์ -> %s" % (len(glob.glob(os.path.join(OUT, "*.jpg"))), OUT))
