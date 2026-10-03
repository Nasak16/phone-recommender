#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ตรวจ + ถ่ายภาพทุกหน้าของแอป (ใช้ยืนยันว่าทุกหน้าทำงานจริง)"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "out")
os.makedirs(OUT, exist_ok=True)

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8783"
TAG = sys.argv[2] if len(sys.argv) > 2 else "local"

# ลำดับต้องตรงกับเมนูในแอป (radio index)
PAGES = [("Dashboard", "ภาพรวมระบบ"), ("Recommendations", "แนะนำมือถือ"),
         ("Phone Search", "ค้นหารุ่นมือถือ"), ("Like & Rate", "ถูกใจ / ให้คะแนน"),
         ("Graph Explorer", "สำรวจโครงสร้างกราฟ"), ("Index & Links", "งานทั้งหมด (Index)"),
         ("Admin & Setup", "ผู้ดูแลระบบ")]

CHECK = {
    "Index & Links": ["งานทั้งหมดของเรา", "หน้า index"],
    "Dashboard": ["ภาพรวมระบบ", "ความสนใจ (LIKES)", "คนสนใจ", "โปรไฟล์"],
    "Recommendations": ["คำแนะนำสำหรับ", "Jaccard", "รุ่นที่ระบบแนะนำ"],
    "Phone Search": ["พบ", "รุ่น"],
    "Like & Rate": ["สถานะปัจจุบัน", "ให้คะแนนดาว"],
    "Graph Explorer": ["สำรวจโครงสร้างกราฟ", "อ่านกราฟ", "Cypher", "edge"],
    "Admin & Setup": ["โครงสร้างกราฟ", "schema", "รีโหลดข้อมูลตัวอย่าง", "เดิน 3 hop"],
}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1500, "height": 1350})
        pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(12000)
        ok_all = True
        radios = pg.locator('input[type="radio"]')
        for i, (name, th) in enumerate(PAGES):
            try:
                radios.nth(i).click(force=True, timeout=20000)
            except Exception as e:
                print(f"[{name}] คลิกเมนูไม่ได้: {type(e).__name__}")
                ok_all = False
                continue
            pg.wait_for_timeout(7000)
            txt = " ".join(pg.inner_text("body").split())
            imgs = pg.eval_on_selector_all(
                "img", "e=>[e.filter(x=>x.naturalWidth>60).length, e.length]")
            miss = [k for k in CHECK[name] if k not in txt]
            shot = os.path.join(OUT, f"page6_{TAG}_{name.replace(' ', '').replace('&','')}.png")
            pg.screenshot(path=shot)
            status = "OK " if not miss else "ขาด: " + ", ".join(miss)
            if miss:
                ok_all = False
            print(f"[{name:16s}] ภาพ {imgs[0]}/{imgs[1]} | ข้อความ {len(txt):5d} ตัว | {status} | {shot}")
        b.close()
        print("สรุป:", "ผ่านทุกหน้า" if ok_all else "มีหน้าที่ต้องแก้")


if __name__ == "__main__":
    main()
