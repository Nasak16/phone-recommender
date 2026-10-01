#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ทำ contact sheet รวมภาพมือถือทุกภาพ (ไว้ตรวจด้วยตาว่าภาพตรงรุ่น/ไม่ใช่ภาพเปล่า)

    py -3.13 tools/contact_sheet.py         # -> tools/out/contact_sheet.png
"""
import json, os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "out"); os.makedirs(OUT, exist_ok=True)
COLS, CW, CH, PAD, LBL = 6, 230, 250, 12, 34
phones = json.load(open(os.path.join(ROOT, "data", "phones.json"), encoding="utf-8"))
rows = (len(phones) + COLS - 1) // COLS
W = COLS * (CW + PAD) + PAD
H = rows * (CH + LBL + PAD) + PAD
sheet = Image.new("RGB", (W, H), (14, 22, 38))
d = ImageDraw.Draw(sheet)

for i, p in enumerate(phones):
    x = PAD + (i % COLS) * (CW + PAD)
    y = PAD + (i // COLS) * (CH + LBL + PAD)
    path = os.path.join(ROOT, p["image"])
    try:
        im = Image.open(path).convert("RGB")
        im.thumbnail((CW, CH))
        sheet.paste(im, (x + (CW - im.width) // 2, y + (CH - im.height) // 2))
    except Exception as e:
        d.text((x + 10, y + 10), "ไม่มีภาพ: %s" % type(e).__name__, fill=(248, 113, 113))
    d.rectangle([x, y, x + CW, y + CH], outline=(43, 58, 92))
    d.text((x + 4, y + CH + 4), "%s %s" % (p["phone_id"], p["brand"]), fill=(233, 239, 250))
    d.text((x + 4, y + CH + 17), p["model"][:30], fill=(159, 176, 203))

sheet.save(os.path.join(OUT, "contact_sheet.png"))
print("wrote", os.path.join(OUT, "contact_sheet.png"), sheet.size, "%d รุ่น" % len(phones))
