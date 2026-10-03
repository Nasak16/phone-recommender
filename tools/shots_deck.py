#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ถ่ายภาพหน้าจอแอป 6 หน้า (เต็มหน้า) สำหรับใส่สไลด์

    py -3.13 tools/shots_deck.py http://127.0.0.1:8783
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shots")
os.makedirs(OUT, exist_ok=True)
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8783"

# ลำดับต้องตรงกับเมนูในแอป (radio index)
PAGES = [("Home", "หน้าหลัก", "06_home"),
         ("Dashboard", "ภาพรวมระบบ", "07_dashboard"),
         ("Recommendations", "แนะนำมือถือ", "01_hero"),
         ("Phone Search", "ค้นหารุ่นมือถือ", "02_catalog"),
         ("Like & Rate", "ถูกใจ / ให้คะแนน", "04_rate"),
         ("Graph Explorer", "สำรวจโครงสร้างกราฟ", "03_graph"),
         ("Index & Links", "งานทั้งหมด (Index)", "08_index"),
         ("Admin & Setup", "ผู้ดูแลระบบ", "05_admin")]


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1680, "height": 1200})
        pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(12000)
        radios = pg.locator('input[type="radio"]')
        for i, (name, th, out) in enumerate(PAGES):
            radios.nth(i).click(force=True, timeout=20000)
            pg.wait_for_timeout(7500)
            path = os.path.join(OUT, out + ".png")
            pg.screenshot(path=path, full_page=True)
            imgs = pg.eval_on_selector_all(
                "img", "e=>[e.filter(x=>x.naturalWidth>60).length, e.length]")
            print("%-22s ภาพ %s/%s -> %s" % (name, imgs[0], imgs[1], out + ".png"))
        b.close()


if __name__ == "__main__":
    main()
