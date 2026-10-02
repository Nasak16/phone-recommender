#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ตรวจว่าแอป "บังคับใช้ Neo4j จริง" — ถ้ายังไม่ได้ตั้งค่าจะต้องขึ้นหน้าวิธีตั้งค่า ไม่มีข้อมูลจำลอง

วิธีใช้:
    # 1) ย้าย secrets ออกชั่วคราว (จำลองเครื่องที่ยังไม่ตั้งค่า)
    mv .streamlit/secrets.toml "$TMPDIR/secrets.test.toml"
    # 2) เปิดแอป
    py -3.13 -m streamlit run app.py --server.port 8781
    # 3) ตรวจ
    py -3.13 tools/test_needs_neo4j.py http://127.0.0.1:8781
    # 4) คืนไฟล์
    mv "$TMPDIR/secrets.test.toml" .streamlit/secrets.toml

ผ่านเมื่อ: เห็นข้อความให้ตั้งค่า Neo4j + ปุ่มลองเชื่อมต่อใหม่ และ **ไม่มี** ตัวเลขข้อมูล/
การ์ดคำแนะนำปลอมขึ้นมาในหน้า
"""
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8781"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 1500})
    pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_timeout(15000)
    text = " ".join(pg.inner_text("body").split())
    radios = pg.locator('input[type="radio"]').count()       # ไม่ควรมีเมนูให้ใช้ถ้ายังต่อไม่ได้
    checks = {
        "ขึ้นข้อความว่ายังต่อ Neo4j ไม่ได้": "ยังเชื่อมต่อฐานข้อมูลกราฟ" in text,
        "บอกวิธีตั้งค่าในเครื่อง (secrets.toml)": "secrets.toml" in text and "bolt://127.0.0.1:7687" in text,
        "บอกวิธีตั้งค่าบน Streamlit Cloud (Aura)": "neo4j+s://" in text,
        "มีปุ่มลองเชื่อมต่อใหม่": "ลองเชื่อมต่อใหม่" in text,
        "ไม่มีเมนู/หน้าข้อมูลให้ใช้": radios == 0,
        "ไม่แสดงตัวเลขข้อมูลปลอม (12 ผู้ใช้)": "12 คน × 23 รุ่น" not in text,
    }
    print("เมนูที่พบ:", radios)
    for k, v in checks.items():
        print(("✓ " if v else "✗ ") + k)
    pg.screenshot(path="tools/out/needs_neo4j.png", full_page=True)
    print("บันทึกภาพ: tools/out/needs_neo4j.png")
    b.close()
    sys.exit(0 if all(checks.values()) else 1)
