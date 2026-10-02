#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ทดสอบโหมด deploy (เหมือน Streamlit Cloud): ไม่มี Neo4j / ไม่มี secrets.toml

วิธีใช้ (เปิดแอปเองก่อน แบบไม่มี secrets.toml และชี้ URI ไปพอร์ตที่ไม่มีอะไรฟัง):
    export NEO4J_URI="bolt://127.0.0.1:9999" NEO4J_PASSWORD="wrong-on-purpose"
    py -3.13 -m streamlit run app.py --server.port 8781
    py -3.13 tools/test_deploy_mode.py http://127.0.0.1:8781

ตรวจทีละหน้าจนครบ 7 หน้า แล้วสรุปว่าภาพ/CDN + backend สำรอง + ข้อความโหมดสาธิต ทำงานครบ
"""
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8781"
PAGES = ["Dashboard", "Recommendations", "Phone Search", "Like & Rate",
         "Graph Explorer", "Index & Links", "Admin & Setup"]

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 1500})
    pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_timeout(18000)
    radios = pg.locator('input[type="radio"]')
    total_imgs = 0
    rows, texts = [], []
    for i, name in enumerate(PAGES):
        radios.nth(i).click(force=True, timeout=30000)
        pg.wait_for_timeout(9000)
        imgs = pg.eval_on_selector_all(
            "img", "els => [els.filter(e => e.naturalWidth > 60).length, els.length]")
        total_imgs += imgs[0]
        txt = pg.inner_text("body")
        rows.append((name, imgs[0], imgs[1], len(txt)))
        texts.append(txt)
        print("[%-16s] ภาพ %d/%d | ข้อความ %d ตัว" % (name, imgs[0], imgs[1], len(txt)))
    body = " ".join(texts) + " " + pg.inner_text("body")
    checks = {
        "แอปโหลดได้ครบ 7 หน้า (มีข้อความทุกหน้า)": all(r[3] > 300 for r in rows),
        "แสดงโหมดสาธิต (ไม่มี Neo4j ก็ใช้ได้)": ("โหมดสาธิต" in body or "โหมดสำรอง" in body),
        "มีข้อมูลผู้ใช้ของเรา (สมชาย)": "สมชาย" in body,
        "การ์ดแนะนำมีคะแนนอธิบายได้": "คะแนน" in body,
        "ภาพจาก CDN โหลดได้รวม > 10 ภาพ": total_imgs > 10,
    }
    print("ภาพที่โหลดได้รวมทุกหน้า:", total_imgs)
    for k, v in checks.items():
        print(("✓ " if v else "✗ ") + k)
    pg.screenshot(path="tools/out/deploy_mode.png", full_page=True)
    print("บันทึกภาพ: tools/out/deploy_mode.png")
    b.close()
    sys.exit(0 if all(checks.values()) else 1)
