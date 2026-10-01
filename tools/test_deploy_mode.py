#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ทดสอบโหมด deploy: ไม่มี Neo4j ให้ใช้ → ต้องสลับไป backend สำรองและยังแสดงภาพครบ

    py -3.13 tools/test_deploy_mode.py            # รันแอปพอร์ต 8781 แล้วตรวจเอง
เปิดแอปด้วยตัวเอง (แบบไม่มี secrets.toml และชี้ URI ไปพอร์ตที่ไม่มีอะไรฟัง) แล้วเรียกสคริปต์นี้
"""
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8781"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 1600})
    pg.goto(URL, wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(12000)
    text = pg.inner_text("body")
    imgs = pg.eval_on_selector_all("img", "els => els.filter(e => e.naturalWidth > 60).length")
    checks = {
        "แสดงข้อความโหมดสาธิต": ("โหมดสาธิต" in text or "โหมดสำรอง" in text),
        "มีชื่อผู้ใช้ในระบบ (สมชาย)": "สมชาย" in text,
        "มีการ์ดแนะนำ (คะแนน)": "คะแนน" in text,
        "ภาพที่โหลดได้จริง > 10 ภาพ": imgs > 10,
    }
    print("ภาพที่โหลดได้:", imgs)
    for k, v in checks.items():
        print(("✓ " if v else "✗ ") + k)
    pg.screenshot(path="tools/out/deploy_mode.png", full_page=True)
    print("บันทึกภาพ: tools/out/deploy_mode.png")
    b.close()
    sys.exit(0 if all(checks.values()) else 1)
