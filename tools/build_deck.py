#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างสไลด์นำเสนอระบบแนะนำมือถือ (16 สไลด์) ด้วย python-pptx

    python tools/build_deck.py     # interpreter ที่มี python-pptx + pywin32 คือ `python` (3.11)
"""
import os
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches as In, Pt
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "deck_assets")
OUT = os.path.join(ROOT, "slides"); os.makedirs(OUT, exist_ok=True)
BE = os.path.join(ROOT, "deck_assets")   # ภาพประกอบสไลด์ (จาก prep_images.py)
PPTX = os.path.join(OUT, "นำเสนอระบบแนะนำมือถือ_007.pptx")
IMGS = os.path.join(ROOT, "assets", "phones")

SW, SH = 13.333, 7.5
BG, CARD, CARD2, BORDER = "#0E1626", "#172136", "#1E2A45", "#2B3A5C"
ORANGE, CYAN, GREEN, YELLOW, RED = "#FF8833", "#38BDF8", "#34D399", "#FBBF24", "#F87171"
TEXT, MUTED = "#E9EFFA", "#9FB0CB"
FONT = "Leelawadee UI"
GID = "8667b219bbff8253335ec78f78b5c79e"
COLAB = f"https://colab.research.google.com/gist/Nasak16/{GID}/PhoneRecommender_Neo4j_007.ipynb"


def hexc(h):
    return RGBColor.from_string(h.lstrip("#"))


prs = Presentation()
prs.slide_width, prs.slide_height = In(SW), In(SH)
BLANK = prs.slide_layouts[6]


def slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = hexc(BG)
    return s


def rect(s, x, y, w, h, fill=CARD, line=None, radius=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, In(x), In(y), In(w), In(h))
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = hexc(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = hexc(line); sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius if radius is not None else 0.06
    sh.text_frame.text = ""
    return sh


def tb(s, x, y, w, h, runs, size=14, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
       space_after=4, line_spacing=1.06, anchor=MSO_ANCHOR.TOP):
    """runs: str หรือ list ของ (ข้อความ, size, color, bold) หรือ list ของ list (ย่อหน้า)"""
    box = s.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) and runs and isinstance(runs[0], list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        items = para if isinstance(para, list) else [para]
        for it in items:
            if isinstance(it, tuple):
                text, sz, col, bd = (list(it) + [size, color, bold])[:4]
            else:
                text, sz, col, bd = it, size, color, bold
            r = p.add_run(); r.text = text
            r.font.size = Pt(sz); r.font.color.rgb = hexc(col)
            r.font.bold = bd; r.font.name = FONT
    return box


def header(s, kicker, title, num=None):
    rect(s, 0.62, 0.46, 0.075, 0.62, ORANGE, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 0.82, 0.34, 10.8, 0.3, kicker, 11.5, ORANGE, True)
    tb(s, 0.82, 0.6, 11.4, 0.55, title, 27, TEXT, True)
    footer(s, num)


def footer(s, num=None):
    rect(s, 0, SH - 0.34, SW, 0.34, CARD2, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 0.62, SH - 0.31, 9.5, 0.26, "ระบบแนะนำมือถือ · Neo4j + Streamlit · จัดทำโดย รหัส 007",
       9, MUTED)
    if num:
        tb(s, SW - 1.15, SH - 0.31, 0.55, 0.26, str(num), 9.5, ORANGE, True, PP_ALIGN.RIGHT)


def pic_cover(s, path, x, y, w, h, border=True):
    """วางภาพแบบ cover-fit (ตัดขอบให้เต็มกรอบ ไม่ยืด)"""
    iw, ih = Image.open(path).size
    box_ar, img_ar = w / h, iw / ih
    pic = s.shapes.add_picture(path, In(x), In(y), In(w), In(h))
    if img_ar > box_ar:                      # ภาพกว้างเกิน → ตัดซ้าย/ขวา
        crop = (1 - box_ar / img_ar) / 2
        pic.crop_left = pic.crop_right = crop
    else:                                    # ภาพสูงเกิน → ตัดบน/ล่าง
        crop = (1 - img_ar / box_ar) / 2
        pic.crop_top = pic.crop_bottom = crop
    if border:
        pic.line.color.rgb = hexc(BORDER); pic.line.width = Pt(1)
    return pic


def pic_fit(s, path, x, y, w, h):
    """วางภาพแบบ contain (เห็นครบทั้งภาพ)"""
    iw, ih = Image.open(path).size
    ar = iw / ih
    if ar > w / h:
        ww, hh = w, w / ar
    else:
        hh, ww = h, h * ar
    return s.shapes.add_picture(path, In(x + (w - ww) / 2), In(y + (h - hh) / 2),
                                In(ww), In(hh))


def code_box(s, x, y, w, h, lines, size=11.5, title=None):
    rect(s, x, y, w, h, "#0B1220", BORDER, radius=0.04)
    yy = y + 0.12
    if title:
        tb(s, x + 0.2, yy, w - 0.4, 0.24, title, 10.5, CYAN, True)
        yy += 0.3
    tb(s, x + 0.2, yy, w - 0.4, h - (yy - y) - 0.15,
       [[(l, size, "#C9E4FF", False)] for l in lines], space_after=1, line_spacing=1.0)


def bullet_list(s, x, y, w, items, size=14, gap=0.06, dot=ORANGE):
    yy = y
    for it in items:
        rect(s, x, yy + 0.1, 0.085, 0.085, dot, shape=MSO_SHAPE.OVAL)
        box = tb(s, x + 0.26, yy, w - 0.26, 0.4, it, size, TEXT, space_after=2)
        lines = max(1, int((len(it) * size * 0.52) / (w * 96)) + 1)
        yy += 0.24 * lines + gap + 0.1
    return yy


def metric(s, x, y, w, h, value, label, color=ORANGE):
    rect(s, x, y, w, h, CARD, BORDER)
    tb(s, x, y + 0.16, w, 0.5, value, 26, color, True, PP_ALIGN.CENTER)
    tb(s, x, y + 0.72, w, 0.4, label, 10.5, MUTED, False, PP_ALIGN.CENTER)

# ---------------------------------------------------------------- ข้อมูลจริงจาก engine
import sys
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "data"))
from graph_fallback import from_files
import seed_data

ENG = from_files()
ST = ENG.stats()
TARGET = "สมชาย"
LIKED = ENG.liked_phones(TARGET)
REC_W = ENG.recommend_weighted(TARGET, 3)
REC_V = ENG.recommend_votes(TARGET, 6)
REC_C = ENG.recommend_content(TARGET, 3)
REC_H = ENG.recommend_hybrid(TARGET, 3)
SIMS = ENG.similar_users(TARGET)
PH = {p["phone_id"]: p for p in seed_data.load_phones()}
BRANDS = sorted({p["brand"] for p in PH.values()})
TIERS = ["เรือธง", "ระดับกลาง", "ระดับเริ่มต้น"]


def pname(pid):
    return PH[pid]["display"]


def pimg(pid):
    return os.path.join(ROOT, PH[pid]["image"])


def card_phone(s, x, y, w, h, pid, lines, title=None, fit_h=1.45):
    """การ์ดมือถือ: ภาพสินค้า + ชื่อรุ่น + บรรทัดคะแนน"""
    rect(s, x, y, w, h, CARD, BORDER)
    pic_fit(s, pimg(pid), x + 0.12, y + 0.12, w - 0.24, fit_h)
    yy = y + fit_h + 0.18
    tb(s, x + 0.14, yy, w - 0.28, 0.3, title or pname(pid), 11, TEXT, True, PP_ALIGN.CENTER)
    yy += 0.32
    for t, col in lines:
        tb(s, x + 0.14, yy, w - 0.28, 0.26, t, 9.5, col, False, PP_ALIGN.CENTER)
        yy += 0.24


# ---------------------------------------------------------------- 1 ปก
s = slide()
rect(s, 0.9, 1.0, 0.1, 1.6, ORANGE, shape=MSO_SHAPE.RECTANGLE)
tb(s, 1.25, 0.95, 11.4, 0.4, "งาน: พัฒนาระบบแนะนำเป็นระบบของตัวเอง · รหัส 007", 14, CYAN, True)
tb(s, 1.25, 1.35, 11.4, 1.2, "ระบบแนะนำมือถือ", 50, TEXT, True)
tb(s, 1.25, 2.45, 11.4, 0.5, "PHONE RECOMMENDER SYSTEM · Neo4j (Graph DB) + Streamlit", 19, ORANGE, True)
tb(s, 1.25, 3.2, 11.4, 1.2,
   [[("ข้อมูลของเราเอง %d คน × %d รุ่น × %d ความสนใจ (ไม่ใช้ dataset สำเร็จรูป)" %
      (ST["users"], ST["phones"], ST["likes"]), 14.5, TEXT, False)],
    [("ผลการแนะนำแสดง “ภาพสินค้าจริง” ทุกครั้ง + บอกเหตุผลได้ว่าเพราะใคร/เพราะรุ่นไหน", 14.5, TEXT, False)],
    [("งานแนวเดียวกับตัวอย่างในวิชา แต่เปลี่ยนโดเมนเป็นมือถือ และใช้สัญญาณ “ยี่ห้อ + ระดับราคา”",
      14.5, TEXT, False)]], space_after=5)
for i, (v, l, c) in enumerate([(str(ST["users"]), "ผู้ใช้ในระบบ", CYAN),
                               (str(ST["phones"]), "รุ่นมือถือ (%d ยี่ห้อ)" % ST["brands"], YELLOW),
                               (str(ST["likes"]), "ความสนใจ (LIKES)", GREEN),
                               ("4", "วิธีให้คะแนน + ผสม", ORANGE)]):
    metric(s, 1.25 + i * 2.6, 4.9, 2.3, 1.3, v, l, c)
tb(s, 1.25, 6.5, 11.4, 0.5,
   "สาธิตการใช้งาน: เว็บแอป Streamlit 6 หน้า (Dashboard → Admin) · ข้อมูลบน Neo4j · โค้ด/สไลด์/โน๊ตบุ๊กอยู่บน GitHub",
   12, MUTED)

# ---------------------------------------------------------------- 2 สารบัญ
s = slide(); header(s, "AGENDA", "หัวข้อที่จะนำเสนอ", 2)
agenda = [("01", "โจทย์และสิ่งที่ส่ง", "งาน 4 ข้อของอาจารย์ → ส่งครบอะไรบ้าง"),
          ("02", "แนวคิดระบบแนะนำบนกราฟ", "ทำไมข้อมูล “ใครสนใจรุ่นไหน” ต้องใช้กราฟ + การเดิน 3 hop"),
          ("03", "ข้อมูลและสถาปัตยกรรม", "ข้อมูลชุดของเรา + Neo4j + Streamlit + GitHub"),
          ("04", "ระบบทำงานจริง", "ผลการแนะนำ 5 วิธี + ภาพสินค้าจริง + อธิบายเหตุผลย้อนหลังได้"),
          ("05", "สาธิตการใช้งาน (Like & Rate)", "เพิ่มความสนใจ/ให้ดาว แล้วคำแนะนำเปลี่ยนทันที ไม่ต้องเทรนใหม่"),
          ("06", "การทดสอบและลิงก์งาน", "ผลตรวจสอบจริง + Colab + GitHub + หน้า index")]
for i, (n, t, d) in enumerate(agenda):
    y = 1.45 + i * 0.92
    rect(s, 0.82, y, 11.7, 0.78, CARD, BORDER)
    tb(s, 1.0, y + 0.14, 0.8, 0.4, n, 22, ORANGE, True)
    tb(s, 1.85, y + 0.09, 5.2, 0.35, t, 15.5, TEXT, True)
    tb(s, 1.85, y + 0.42, 10.4, 0.3, d, 11.5, MUTED)

# ---------------------------------------------------------------- 3 โจทย์
s = slide(); header(s, "โจทย์ & สิ่งที่ส่ง", "งานที่อาจารย์สั่ง 4 ข้อ — ส่งครบทุกข้อ", 3)
items = [("1", "Present ด้วย PowerPoint + สาธิตการใช้งานระบบ",
          "สไลด์ 16 หน้า (ไฟล์นี้) + เดโมสดในแอป Streamlit + ระบบแสดง “ภาพมือถือจริง” ในผลการแนะนำ"),
         ("2", "ข้อมูล PowerPoint ไว้ใน GitHub",
          "ใส่ทั้ง .pptx และ .pdf ไว้ในโฟลเดอร์ slides/ ของ repo (ดูได้โดยไม่ต้องติดตั้งอะไร)"),
         ("3", "เอาการบ้านทุกอันไว้ใน GitHub",
          "ทุกชิ้นงานมี repo ของตัวเอง และมี repo กลาง homework รวมทุกงานไว้ที่เดียว"),
         ("4", "จัดหน้า index ให้ลิงก์กับงานทุกอัน",
          "หน้าเว็บ GitHub Pages ลิงก์ทุก repo พร้อมคำอธิบายและวันที่อัปเดตล่าสุด")]
for i, (n, t, d) in enumerate(items):
    y = 1.45 + i * 1.28
    rect(s, 0.82, y, 11.7, 1.1, CARD, BORDER)
    rect(s, 0.82, y, 0.075, 1.1, ORANGE, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 1.05, y + 0.18, 0.5, 0.5, n, 24, ORANGE, True)
    tb(s, 1.75, y + 0.14, 10.5, 0.4, t, 16, TEXT, True)
    tb(s, 1.75, y + 0.58, 10.5, 0.5, d, 11.5, MUTED)

# ---------------------------------------------------------------- 4 แนวคิด
s = slide(); header(s, "แนวคิด", "ทำไมงานนี้ต้องใช้ฐานข้อมูลกราฟ?", 4)
tb(s, 0.82, 1.3, 6.1, 0.8,
   "ข้อมูล “ใครสนใจมือถือรุ่นไหน” คือข้อมูลความสัมพันธ์ล้วน ๆ ถ้าเก็บเป็นตารางต้อง JOIN "
   "หลายชั้นกว่าจะตอบได้ แต่ในกราฟเขียนครั้งเดียวจบ", 12.5, TEXT)
code_box(s, 0.82, 2.2, 6.1, 2.5,
         ["MATCH (me:User {user: 'สมชาย'})-[:LIKES]->",
          "      (shared:Phone)<-[:LIKES]-(other:User)",
          "MATCH (other)-[:LIKES]->(rec:Phone)",
          "WHERE NOT (me)-[:LIKES]->(rec)",
          "RETURN rec.model, count(DISTINCT other) AS votes",
          "ORDER BY votes DESC"],
         title="คำแนะนำทั้งระบบเขียนด้วย Cypher ไม่กี่บรรทัด")
tb(s, 0.82, 4.85, 6.1, 0.4, "ขั้นตอนการเดิน 3 hop", 13, ORANGE, True)
tb(s, 0.82, 5.2, 6.1, 1.8,
   [[("1. ดูรุ่นที่ผู้ใช้สนใจ (" + str(len(LIKED)) + " รุ่นของ " + TARGET + ")", 12, TEXT, False)],
    [("2. หาคนอื่นที่สนใจรุ่นเดียวกัน = รสนิยมใกล้กัน", 12, TEXT, False)],
    [("3. เก็บรุ่นที่คนกลุ่มนั้นสนใจ แต่ผู้ใช้ยังไม่สนใจ", 12, TEXT, False)],
    [("4. ให้คะแนน → เรียงอันดับ → แสดงภาพสินค้า", 12, TEXT, False)]], space_after=3)
rect(s, 7.2, 1.3, 5.32, 5.7, CARD, BORDER)
tb(s, 7.45, 1.45, 4.9, 0.4, "ทำไมไม่ใช้ตาราง (SQL) เฉย ๆ?", 14, ORANGE, True)
yy = bullet_list(s, 7.45, 1.9, 4.9, [
    "กราฟเดินความสัมพันธ์ได้ลึกไม่จำกัดชั้น โดยไม่ต้อง JOIN เพิ่มทุกชั้น",
    "ถามแบบ “เพื่อนของเพื่อนสนใจอะไร” ได้ทันที (เส้นทาง 3 hop)",
    "นับซ้ำให้เองด้วย count(DISTINCT …) — 1 คน = 1 เสียง",
    "เพิ่มผู้ใช้/รุ่นใหม่แล้วแนะนำได้ทันที ไม่ต้องเทรนโมเดลใหม่",
    "อธิบายย้อนหลังได้ว่าคำแนะนำมาจากใครและรุ่นไหน"], size=11.5, gap=0.12)
tb(s, 7.45, yy + 0.1, 4.9, 0.9,
   "ข้อแลกเปลี่ยน: ถ้าข้อมูลความสนใจมีหลักล้านเส้น การนับด้วย Cypher ทุกครั้งจะช้ากว่า "
   "การ precompute — งานนี้ข้อมูลเล็ก (38 เส้น) จึงตอบได้ทันที", 10.5, MUTED)

# ---------------------------------------------------------------- 5 ข้อมูลชุดของเรา
s = slide(); header(s, "ข้อมูลชุดของเรา", "เก็บข้อมูลเองทั้งหมด — ไม่ใช้ dataset สำเร็จรูป", 5)
for i, (v, l, c) in enumerate([(str(ST["users"]), "ผู้ใช้ (User)", CYAN),
                               (str(ST["phones"]), "รุ่นมือถือ (Phone)", YELLOW),
                               (str(ST["likes"]), "ความสนใจ (LIKES)", GREEN),
                               (str(ST["brands"]), "ยี่ห้อ (Brand)", ORANGE)]):
    metric(s, 0.82 + i * 1.62, 1.35, 1.5, 1.15, v, l, c)
tb(s, 7.4, 1.35, 5.12, 1.35,
   [[("3 ระดับราคา: " + " · ".join(TIERS), 12, TEXT, True)],
    [("ยี่ห้อ: " + ", ".join(BRANDS), 11, MUTED, False)],
    [("คะแนนดาว (RATED {stars}) " + str(ST.get("ratings", 0)) + " เส้น · ดาวเฉลี่ยต่อรุ่นใช้เป็นสัญญาณที่ 5",
      10.5, YELLOW, False)]], space_after=3)
rect(s, 0.82, 2.7, 5.9, 4.15, CARD, BORDER)
tb(s, 1.05, 2.85, 5.5, 0.35, "12 ผู้ใช้ แบ่งตามกลุ่มรสนิยม", 14, ORANGE, True)
yy = 3.3
for u in seed_data.USERS:
    tb(s, 1.05, yy, 2.3, 0.3, u["user"], 11.5, TEXT, True)
    tb(s, 3.3, yy, 3.3, 0.3, u["group"], 10.5, MUTED)
    yy += 0.29
rect(s, 7.0, 2.7, 5.52, 4.15, CARD, BORDER)
tb(s, 7.25, 2.85, 5.0, 0.35, "ทำไมออกแบบข้อมูลแบบนี้", 14, ORANGE, True)
bullet_list(s, 7.25, 3.3, 5.0, [
    "แต่ละคนสนใจ 2–4 รุ่น → มีทั้งคนที่รสนิยมซ้ำกันและคนที่ต่างกันสุดขั้ว",
    "มีกลุ่ม “สายยี่ห้อ” (Apple/Samsung) และ “สายงบ” (รุ่นกลาง) เพื่อทดสอบสัญญาณ Brand/Tier",
    "ทุกรุ่นมีคนสนใจอย่างน้อย 1 คน → ไม่มีโหนดร้างในกราฟ",
    "ภาพสินค้าดึงจาก Wikimedia Commons แล้วเก็บไว้ในโปรเจกต์ (แสดงได้แม้ไม่มีเน็ต)"],
    size=11, gap=0.1)

# ---------------------------------------------------------------- 6 ภาพในระบบ
s = slide(); header(s, "ภาพในระบบแนะนำ", "ทุกรุ่นในการ์ดมีภาพสินค้าจริง (ตามโจทย์ข้อ 1)", 6)
sheet = os.path.join(BE, "phone_sheet.png")
if os.path.exists(sheet):
    pic_fit(s, sheet, 0.82, 1.3, 8.1, 5.5)
else:
    rect(s, 0.82, 1.3, 8.1, 5.5, CARD, BORDER)
    tb(s, 1.0, 1.5, 7.8, 0.4, "(ยังไม่มี contact sheet — รัน tools/contact_sheet.py)", 12, MUTED)
rect(s, 9.15, 1.3, 3.37, 5.5, CARD, BORDER)
tb(s, 9.38, 1.45, 2.9, 0.4, "ภาพถูกใช้ 2 ที่", 14, ORANGE, True)
yy = bullet_list(s, 9.38, 1.95, 2.9, [
    "ในแอป: การ์ดผลการแนะนำ + คลังรุ่นทั้งหมด",
    "ในโน๊ตบุ๊ก: เซลล์แสดงผลลัพธ์พร้อมภาพทุกครั้ง",
    "ในสไลด์: หน้าสาธิตผลการแนะนำ"], size=11, gap=0.12)
tb(s, 9.38, yy + 0.15, 2.9, 2.2,
   "ที่มา: Wikimedia Commons (สัญญาอนุญาตเสรี) เก็บชื่อไฟล์ต้นทางใน data/phones.json "
   "เพื่อให้เครดิตได้ครบ — ตรวจทีละภาพว่าไม่ผิดรุ่น ไม่ใช่โลโก้ และไม่ใช่ภาพเปล่า",
   10.5, MUTED)

# ---------------------------------------------------------------- 7 โครงสร้างกราฟ
s = slide(); header(s, "สถาปัตยกรรม", "โครงสร้างกราฟและจำนวนข้อมูลจริงใน Neo4j", 7)
code_box(s, 0.82, 1.3, 6.0, 2.15,
         ["(User {user, age, group})",
          "      │ [:LIKES]  " + str(ST["likes"]) + " เส้น",
          "      ▼",
          "(Phone {phone_id, model, brand, tier, image})",
          "      │ [:BY_BRAND] → (Brand {name})   " + str(ST["brands"]) + " โหนด",
          "      │ [:IN_TIER]  → (Tier {name})     3 โหนด"],
         title="Schema ที่โหลดเข้า Neo4j จริง")
rect(s, 7.1, 1.3, 5.42, 2.15, CARD, BORDER)
tb(s, 7.35, 1.45, 5.0, 0.35, "ทำไมแยก Brand/Tier เป็นโหนด?", 13.5, ORANGE, True)
bullet_list(s, 7.35, 1.9, 5.0, [
    "Brand/Tier ใช้เป็นสัญญาณที่สอง (content-based) ไม่ต้องพึ่งเพื่อน",
    "ช่วยแก้ cold start ของผู้ใช้ใหม่",
    "คำนวณ “ยี่ห้อเดียวกันกี่รุ่น” ได้ด้วยการเดินกราฟ ไม่ต้องเขียนโค้ดนับเอง"],
    size=11, gap=0.08)
tb(s, 0.82, 3.6, 11.7, 0.4, "คำถามหลัก 3 hop ที่ระบบใช้จริง (ผลจากข้อมูลชุดนี้)", 13.5, ORANGE, True)
code_box(s, 0.82, 4.05, 5.8, 2.8,
         ["MATCH (me:User {user: '" + TARGET + "'})-[:LIKES]->(shared)",
          "MATCH (shared)<-[:LIKES]-(other:User)",
          "MATCH (other)-[:LIKES]->(rec:Phone)",
          "WHERE NOT (me)-[:LIKES]->(rec)",
          "RETURN rec.model, count(DISTINCT other) AS votes",
          "ORDER BY votes DESC"],
         title="Hop 1-2-3 → รุ่นที่เพื่อนรสนิยมใกล้สนใจ")
rows = [[(pname(r["phone_id"]), 12, TEXT, True),
         ("  " + str(r["votes"]) + " คน: " + ", ".join(r["voters"]), 11, MUTED, False)]
        for r in REC_V[:5]]
rect(s, 6.85, 4.05, 5.67, 2.8, CARD, BORDER)
tb(s, 7.05, 4.2, 5.3, 0.35, "ผลจริงจากกราฟ (เรียงตามจำนวนคน)", 12.5, CYAN, True)
tb(s, 7.05, 4.6, 5.3, 2.1, rows, 11, space_after=6)

# ---------------------------------------------------------------- 8 สูตรให้คะแนน
s = slide(); header(s, "ระบบให้คะแนน", "5 วิธี (เลือกเทียบกันได้ในแอป)", 8)
blocks = [("1) นับโหวตเพื่อน", ["คะแนน = จำนวนคนที่สนใจรุ่นนั้น",
                             "count(DISTINCT other) → 1 คน = 1 เสียง",
                             "ข้อดี: เข้าใจง่าย | ข้อเสีย: ทุกคนน้ำหนักเท่ากัน"], CYAN),
          ("2) ถ่วงน้ำหนัก (Jaccard)", ["คะแนน = Σ Jaccard(เรา, คนนั้น)",
                                     "Jaccard = |สนใจร่วม| ÷ |รุ่นของสองคนรวมกัน|",
                                     "คนรสนิยมใกล้เราสุดมีเสียงมากสุด"], GREEN),
          ("3) ตามยี่ห้อ/ระดับราคา", ["นับรุ่นที่เราเคยสนใจซึ่งใช้ยี่ห้อเดียวกัน",
                                 "+ อยู่ระดับราคาเดียวกัน",
                                 "ใช้ได้กับผู้ใช้ใหม่ (cold start)"], YELLOW),
          ("4) ผสมสองสัญญาณ", ["0.6 × (คะแนนเพื่อน normalize)",
                              "+ 0.4 × (คะแนนยี่ห้อ/ราคา normalize)",
                              "กันปัญหา “แนะนำของนอกงบ” เช่นงบกลางแต่ได้เรือธง"], ORANGE)]
for i, (t, ls, col) in enumerate(blocks):
    x = 0.82 + (i % 2) * 6.03
    y = 1.3 + (i // 2) * 2.75
    rect(s, x, y, 5.85, 2.55, CARD, BORDER)
    rect(s, x, y, 0.075, 2.55, col, shape=MSO_SHAPE.RECTANGLE)
    tb(s, x + 0.22, y + 0.16, 5.4, 0.35, t, 14.5, col, True)
    tb(s, x + 0.22, y + 0.62, 5.4, 1.8, [[(l, 11.5, TEXT, False)] for l in ls], space_after=5)
rect(s, 0.82, 6.52, 11.7, 0.74, CARD2, BORDER)
tb(s, 1.05, 6.6, 11.2, 0.6,
   [[("5) ถ่วงด้วยคะแนนดาว — ", 11.5, ORANGE, True),
     ("คะแนน = Σ ( Jaccard(เรา, เพื่อน) × ดาวที่เพื่อนให้รุ่นนั้น ÷ 5 ) ใช้ความสัมพันธ์ "
      "RATED {stars} → คนที่ให้ 5 ดาวมีน้ำหนักมากกว่าคนที่ให้ 2 ดาว (ทุกวิธีถูกตรวจเทียบกันแล้ว "
      "— ดูหน้าผลการทดสอบ)", 11, TEXT, False)]], space_after=3)

# ---------------------------------------------------------------- 9 สาธิต: ภาพรวมแอป
s = slide(); header(s, "สาธิตการใช้งาน", "เว็บแอป Streamlit ต่อ Neo4j — เมนู 6 หน้า + หน้ารวมงาน", 9)
pages = [("Dashboard", "ภาพรวมระบบ 6 ตัวชี้วัด + กราฟ + โปรไฟล์ผู้ใช้"),
         ("Recommendations", "การ์ดคำแนะนำมีภาพสินค้า + คะแนน + เหตุผล (5 วิธี)"),
         ("Phone Search", "ค้นหา/กรอง 23 รุ่น พร้อมภาพสินค้าจริง"),
         ("Like & Rate", "เพิ่ม/ลบความสนใจ + ให้ดาว แล้วเห็นผลก่อน–หลัง"),
         ("Graph Explorer", "กราฟความสัมพันธ์ + ตาราง edge + รัน Cypher เอง"),
         ("Admin & Setup", "schema + รีโหลดข้อมูล idempotent + ดาวน์โหลด CSV"),
         ("Index & Links", "หัวข้อรวมงานทุกชิ้นบน GitHub + ลิงก์หน้า index")]
yy = 1.26
for i, (nm, d) in enumerate(pages):
    rect(s, 0.82, yy, 5.6, 0.66, CARD, BORDER)
    rect(s, 0.82, yy, 0.055, 0.66, [ORANGE, GREEN, CYAN, YELLOW, ORANGE, GREEN, CYAN][i],
         shape=MSO_SHAPE.RECTANGLE)
    tb(s, 1.0, yy + 0.04, 2.5, 0.28, nm, 11.5, TEXT, True)
    tb(s, 1.0, yy + 0.32, 5.25, 0.28, d, 9.5, MUTED)
    yy += 0.72
p = os.path.join(BE, "app_reco.png")
if os.path.exists(p):
    pic_fit(s, p, 6.65, 1.3, 5.87, 5.45)
else:
    rect(s, 6.65, 1.3, 5.87, 5.45, CARD, BORDER)
    tb(s, 6.85, 1.5, 5.5, 0.4, "(ยังไม่มีภาพหน้าจอ — รัน tools/shots_deck.py)", 12, MUTED)

# ---------------------------------------------------------------- 10 สาธิต: ผลแนะนำ
s = slide(); header(s, "สาธิตการใช้งาน", "ผลจริง: คำแนะนำสำหรับ " + TARGET + " (พร้อมภาพสินค้า)", 10)
tb(s, 0.82, 1.22, 5.6, 0.35, "รุ่นที่ " + TARGET + " สนใจอยู่แล้ว " + str(len(LIKED)) + " รุ่น",
   12.5, CYAN, True)
for i, r in enumerate(LIKED[:4]):
    card_phone(s, 0.82 + i * 1.42, 1.65, 1.32, 2.65, r["phone_id"],
               [(r["tier"], MUTED)], fit_h=1.3)
tb(s, 6.65, 1.22, 5.9, 0.35, "ระบบแนะนำ (ถ่วงน้ำหนัก + ผสม)", 12.5, GREEN, True)
for i, r in enumerate(REC_H[:3]):
    card_phone(s, 6.65 + i * 2.0, 1.65, 1.86, 3.35, r["phone_id"],
               [("คะแนน " + str(r["score"]), YELLOW),
                (("เพื่อน: " + ", ".join(r["voters"])) if r["voters"] else "ตรงยี่ห้อ/ราคา", MUTED),
                (r["because"][:26], MUTED)], fit_h=1.5)
rect(s, 0.82, 4.5, 11.7, 2.35, CARD, BORDER)
tb(s, 1.05, 4.62, 11.2, 0.35, "ทำไมได้รุ่นนี้ — อธิบายย้อนหลังได้ทุกคำแนะนำ", 13.5, ORANGE, True)
rows = []
for r in REC_H:
    via = ", ".join(r["via_phones"]) if r["via_phones"] else "—"
    rows.append([(pname(r["phone_id"]), 11.5, TEXT, True),
                 ("   คะแนน " + str(r["score"]) + "  |  เพื่อน " +
                  (", ".join(r["voters"]) if r["voters"] else "—") + "  |  เพราะสนใจ " + via, 10.5, MUTED, False)])
tb(s, 1.05, 5.02, 11.2, 1.7, rows, space_after=7)
tb(s, 1.05, 6.35, 11.2, 0.35,
   "คะแนนผสม = 0.6 × เพื่อน (Jaccard) + 0.4 × ยี่ห้อ/ระดับราคา — ตัวเลขจริงจากข้อมูลชุดนี้", 10, MUTED)

# ---------------------------------------------------------------- 11 สาธิต: Jaccard
s = slide(); header(s, "สาธิตการใช้งาน", "ใครรสนิยมใกล้ " + TARGET + " (ตารางจริงจาก Cypher)", 11)
tb(s, 0.82, 1.25, 11.7, 0.4,
   "Jaccard = |รุ่นที่สนใจร่วมกัน| ÷ |รุ่นของสองคนรวมกัน| — ยิ่งใกล้ 1 ยิ่งเหมือนกัน "
   "และยิ่งมีน้ำหนักโหวตมาก", 12, TEXT)
rect(s, 0.82, 1.85, 11.7, 3.6, CARD, BORDER)
tb(s, 1.05, 1.98, 11.2, 0.35, "ผู้ใช้ · รุ่นที่สนใจร่วม · ค่า Jaccard", 12.5, CYAN, True)
yy = 2.42
for s_ in SIMS[:5]:
    tb(s, 1.1, yy, 2.0, 0.3, s_["user"], 12, TEXT, True)
    tb(s, 3.1, yy, 5.6, 0.3, ", ".join(pname(pid) for pid in s_["common"]), 10.5, MUTED)
    tb(s, 9.0, yy, 3.2, 0.3, "Jaccard " + str(round(s_["jaccard"], 3)) +
       "   (" + str(s_["common_count"]) + " รุ่น)", 11, YELLOW)
    yy += 0.36
tb(s, 1.05, 4.5, 11.2, 0.8,
   [[("ข้อสังเกต: มี " + str(len(SIMS)) + " คนที่มีรุ่นสนใจร่วมกับ " + TARGET +
      " — น้ำหนักโหวตของแต่ละคนไม่เท่ากันตามค่านี้", 11.5, TEXT, False)]], space_after=4)
rect(s, 0.82, 5.6, 11.7, 1.3, CARD2, BORDER)
tb(s, 1.05, 5.75, 11.2, 1.0,
   [[("ทำไมต้อง K จุดนี้: ถ้าใช้แค่ “นับโหวต” คนที่สนใจตรงกันเพียงรุ่นเดียวจะมีเสียงเท่ากับ "
      "คนที่รสนิยมเหมือนเราเกือบทั้งหมด — การถ่วงด้วย Jaccard แก้ปัญหานี้",
      11.5, TEXT, False)]], space_after=3)

# ---------------------------------------------------------------- 12 สาธิต: กราฟ
s = slide(); header(s, "สาธิตการใช้งาน", "เห็นภาพความสัมพันธ์: กราฟผู้ใช้ ↔ รุ่นมือถือ", 12)
p = os.path.join(BE, "graph_somchai.png")
if os.path.exists(p):
    pic_fit(s, p, 0.82, 1.25, 8.5, 5.55)
else:
    rect(s, 0.82, 1.25, 8.5, 5.55, CARD, BORDER)
rect(s, 9.55, 1.25, 2.97, 5.55, CARD, BORDER)
tb(s, 9.75, 1.4, 2.6, 0.35, "อ่านกราฟ", 13.5, ORANGE, True)
yy = bullet_list(s, 9.75, 1.9, 2.6, [
    "จุดส้ม = ผู้ใช้ที่เลือก",
    "จุดฟ้า = คนรสนิยมใกล้",
    "จุดเหลือง = รุ่นที่สนใจแล้ว",
    "จุดเขียว = รุ่นที่ระบบแนะนำ",
    "เส้นประเขียว = ทางเดิน 3 hop"], size=10.5, gap=0.08)
tb(s, 9.75, yy + 0.15, 2.6, 1.6,
   "กราฟสร้างในตัวแอป (ไม่ใช่ภาพนิ่ง) — เปลี่ยนผู้ใช้/วิธีให้คะแนนแล้ววาดใหม่ทันที",
   10, MUTED)

# ---------------------------------------------------------------- 13 สาธิต: เดโมสด + cold start
s = slide(); header(s, "สาธิตการใช้งาน", "Like & Rate: แก้ข้อมูลแล้วคำแนะนำเปลี่ยนทันที", 13)
rect(s, 0.82, 1.3, 6.0, 4.0, CARD, BORDER)
tb(s, 1.05, 1.42, 5.6, 0.35, "กดเพิ่มความสนใจ 1 รุ่น แล้วดูผลก่อน–หลัง", 13, ORANGE, True)
code_box(s, 1.05, 1.9, 5.55, 3.2,
         ["// เพิ่มความสนใจใหม่ลงกราฟ",
          "MATCH (u:User {user: 'สมชาย'}), (p:Phone {phone_id: 'P01'})",
          "MERGE (u)-[:LIKES]->(p)",
          "",
          "// ให้คะแนนดาวกับรุ่นนั้นด้วย (สัญญาณที่ 5)",
          "MERGE (u)-[r:RATED]->(p) SET r.stars = 4.5",
          "",
          "// แล้วถามคำแนะนำเดิมซ้ำทันที",
          "// ไม่ต้องเทรนโมเดลใหม่ ไม่ต้องรอ batch",
          "// เพราะคำแนะนำคำนวณสดจากการเดินกราฟ"],
         title="สิ่งที่แอปทำตอนกดปุ่ม “เพิ่มความสนใจ”")
NEW_PHONE = "P99"
rect(s, 7.0, 1.3, 5.52, 4.0, CARD, BORDER)
tb(s, 7.25, 1.42, 5.0, 0.35, "Cold start: ผู้ใช้ใหม่ที่ยังไม่มีเพื่อนรสนิยม", 12.5, GREEN, True)
tp = {"phone_id": "P07"}
cold = ENG.recommend_content(TARGET, 3)
tb(s, 7.25, 1.9, 5.0, 1.1,
   [[("เพิ่มผู้ใช้ใหม่ที่สนใจ Samsung Galaxy S25 (รุ่นที่ยังไม่มีใครสนใจ) → สัญญาณ “เพื่อน” "
      "ว่างเปล่า แต่ระบบยังแนะนำได้จากโหนด Brand (Samsung) และ Tier (เรือธง)", 11, TEXT, False)]],
   space_after=4)
tb(s, 7.25, 3.0, 5.0, 0.3, "ตัวอย่างผลจากสัญญาณยี่ห้อ/ราคา (ผู้ใช้จริง " + TARGET + ")", 11, CYAN, True)
yy = 3.35
for r in cold:
    tb(s, 7.3, yy, 4.9, 0.3, pname(r["phone_id"]), 11, TEXT, True)
    tb(s, 9.6, yy, 2.6, 0.3, "ยี่ห้อตรง " + str(r["brand_matches"]) + " · ราคาตรง " +
       str(r["tier_matches"]), 10, MUTED)
    yy += 0.3
rect(s, 0.82, 5.5, 11.7, 1.4, CARD2, BORDER)
tb(s, 1.05, 5.62, 11.2, 1.1,
   [[("สะพานเชื่อมกับของเดิม: ระบบนี้ใช้ซ้ำไอเดีย “เพื่อนของเพื่อน” ที่ฝึกในคลาส แต่ย้ายมาคิดบน "
      "กราฟทั้งหมด → เขียนสั้นกว่า อ่านง่ายกว่า และเพิ่มสัญญาณยี่ห้อ/ราคาเข้ามาแก้จุดอ่อน "
      "เรื่องผู้ใช้ใหม่ได้", 11.5, TEXT, False)]], space_after=4)

# ---------------------------------------------------------------- 14 การทดสอบ
s = slide(); header(s, "การทดสอบ", "ตรวจสอบด้วยข้อมูลจริง ไม่ใช่แค่ “รันผ่าน”", 14)
tests = [("1", "สอง backend ให้ผลตรงกัน", "เทียบ Cypher (Neo4j) กับ backend สำรองในหน่วยความจำ "
          "ของผู้ใช้ทั้ง " + str(ST["users"]) + " คน × 6 การตรวจ (รวมวิธีถ่วงด้วยคะแนนดาว) "
          "— ผลตรงกันครบทุกคน", GREEN),
         ("2", "โน๊ตบุ๊กรันได้จริงทุกเซลล์", "สร้างโน๊ตบุ๊กใหม่จากข้อมูลชุดเดียวกัน รันทุกเซลล์บน "
          "Neo4j ในเครื่อง มี output จริงฝังในไฟล์ และมี assertion ท้ายไฟล์ยืนยันข้อมูลกลับสู่สภาพเดิม", CYAN),
         ("3", "โหมดไม่มี Neo4j ต้องไม่พัง", "ปิดการเชื่อมต่อฐานข้อมูลแล้วเปิดแอปใหม่ — "
          "สลับไปใช้ backend สำรองอัตโนมัติ และภาพสินค้าแสดงครบ", YELLOW),
         ("4", "ภาพต้องถูกต้อง", "ตรวจด้วยตา 2 รอบ: รอบแรกพบภาพ iPhone 3 รุ่นมืดเกินไป → "
          "หาภาพใหม่จาก Commons แล้วตรวจซ้ำ " + str(ST["phones"]) + "/" + str(ST["phones"]) +
          " ภาพเป็นตัวเครื่องจริง", ORANGE)]
for i, (n, t, d, col) in enumerate(tests):
    y = 1.35 + i * 1.32
    rect(s, 0.82, y, 11.7, 1.15, CARD, BORDER)
    rect(s, 0.82, y, 0.075, 1.15, col, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 1.05, y + 0.16, 0.5, 0.4, n, 20, col, True)
    tb(s, 1.7, y + 0.13, 10.6, 0.35, t, 14.5, TEXT, True)
    tb(s, 1.7, y + 0.53, 10.6, 0.55, d, 11, MUTED)

# ---------------------------------------------------------------- 15 ข้อจำกัด
s = slide(); header(s, "ข้อจำกัด & ต่อยอด", "งานนี้ทำอะไรได้ และยังขาดอะไร", 15)
rect(s, 0.82, 1.3, 5.85, 5.5, CARD, BORDER)
tb(s, 1.05, 1.45, 5.4, 0.35, "ข้อจำกัดที่ควรพูดตอนนำเสนอ", 14, RED, True)
bullet_list(s, 1.05, 1.95, 5.4, [
    "ข้อมูลความสนใจมี " + str(ST["likes"]) + " เส้น — น้อย (sparsity) ถ้าเก็บจากผู้ใช้จริงจะแม่นขึ้น",
    "ยังไม่ใช้สเปกเครื่อง (RAM/กล้อง/แบตเตอรี่) เป็นสัญญาณ จึงตอบ “รุ่นไหนกล้องดีสุด” ไม่ได้",
    "ระดับราคาแบ่งหยาบ 3 ระดับ ถ้าใช้ช่วงงบเป็นตัวเลขจริงจะแนะนำตรงใจกว่า",
    "ผู้ใช้/ความสนใจเป็นข้อมูลสมมติจากการจัดชุดเพื่อการเรียนการสอน",
    "คะแนนไม่ได้บอกความมั่นใจ (confidence) ของคำแนะนำ"], size=11, gap=0.1)
rect(s, 7.0, 1.3, 5.52, 5.5, CARD, BORDER)
tb(s, 7.25, 1.45, 5.0, 0.35, "ต่อยอดได้", 14, GREEN, True)
bullet_list(s, 7.25, 1.95, 5.0, [
    "เก็บข้อมูลจริงด้วยแบบสอบถามในห้องเรียน แล้วโหลดเข้าฐานข้อมูลเดิมได้ทันที",
    "เพิ่มโหนดสเปก (Camera, Battery, Chipset) แล้วเป็นระบบแนะนำแบบหลายเกณฑ์",
    "เพิ่มน้ำหนักตามความสำคัญที่ผู้ใช้ให้ (เช่น เน้นกล้องมากกว่าราคา)",
    "เก็บประวัติการกดดู/เทียบรุ่น แล้วเปลี่ยนจาก “ความสนใจ” เป็นพฤติกรรมจริง",
    "deploy บน Neo4j Aura + Streamlit Community Cloud ให้เปิดลิงก์เดโมได้จากที่ไหนก็ได้"],
    size=11, gap=0.1)

# ---------------------------------------------------------------- 16 สรุป
s = slide(); header(s, "สรุป", "ส่งครบ 4 ข้อของโจทย์", 16)
links = [("1", "สไลด์นำเสนอ (ไฟล์นี้)", "slides/นำเสนอระบบแนะนำมือถือ_007.pptx + .pdf"),
         ("2", "โน๊ตบุ๊กอธิบายวิธีทำ (รันบน Colab)", COLAB),
         ("3", "โค้ดระบบทั้งหมดบน GitHub", "https://github.com/Nasak16/phone-recommender"),
         ("4", "หน้า index รวมงานทุกชิ้น", "https://nasak16.github.io/homework/")]
yy = 1.35
for n, t, d in links:
    rect(s, 0.82, yy, 11.7, 0.92, CARD, BORDER)
    tb(s, 1.0, yy + 0.12, 0.5, 0.4, n, 18, ORANGE, True)
    tb(s, 1.6, yy + 0.1, 5.0, 0.35, t, 13, TEXT, True)
    tb(s, 1.6, yy + 0.46, 10.6, 0.35, d, 10.5, CYAN)
    yy += 1.05
rect(s, 0.82, 5.7, 11.7, 1.2, CARD2, BORDER)
tb(s, 1.05, 5.82, 11.2, 1.0,
   [[("ระบบนี้เป็นของเราเองทั้งหมด: ออกแบบข้อมูลเอง (" + str(ST["users"]) + " คน × " +
      str(ST["phones"]) + " รุ่น × " + str(ST["likes"]) + " ความสนใจ) ออกแบบโครงสร้างกราฟเอง "
      "เขียนสูตรให้คะแนน 5 วิธีเอง และแสดงภาพสินค้าจริงในผลการแนะนำ (แอปมี 6 หน้า)", 12, TEXT, False)],
    [("ขอบคุณครับ — ยินดีสาธิตสดในแอปและตอบคำถาม", 12, ORANGE, True)]], space_after=5)

prs.save(PPTX)
print("บันทึกสไลด์:", PPTX, "| จำนวนสไลด์:", len(prs.slides.__iter__.__self__._sldIdLst))
