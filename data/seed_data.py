#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ข้อมูลตั้งต้นของระบบแนะนำมือถือ — ชุดของเราเอง

Single source of truth: ทั้งแอป Streamlit, โน๊ตบุ๊ก และสไลด์ อ่านไฟล์นี้ที่เดียว
- รายชื่อรุ่น/ยี่ห้อ/ระดับราคา/ภาพ  อ่านจาก data/phones.json (สร้างโดย tools/fetch_phones.py)
- ผู้ใช้และความสนใจของแต่ละคน ประกาศไว้ด้านล่าง (อ้าง "ชื่อรุ่น" ไม่ใช่รหัส → สลับรุ่นได้ไม่พัง)

หมายเหตุตรงไปตรงมา: ชุดข้อมูลนี้จัดทำเพื่อการเรียนการสอน (ผู้ใช้/ความสนใจเป็นข้อมูลสมมติ
จากการสอบถามเพื่อนในห้อง) ส่วนภาพสินค้าเป็นภาพจริงจาก Wikimedia Commons
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
PHONES_JSON = os.path.join(_HERE, "phones.json")

# ---------------------------------------------------------------- ผู้ใช้
USERS = [
    {"user": "สมชาย", "age": 21, "group": "สาย Android เรือธง"},
    {"user": "นรินทร์", "age": 22, "group": "สาย Android เดิม ๆ (stock)"},
    {"user": "มะลิ", "age": 20, "group": "สาย Apple"},
    {"user": "ปวีณา", "age": 23, "group": "สาย Apple + Samsung"},
    {"user": "อนุชา", "age": 22, "group": "สาย Samsung"},
    {"user": "พลอย", "age": 21, "group": "สายถ่ายรูป (กล้องดี)"},
    {"user": "กัญญา", "age": 20, "group": "สายคุ้มค่า (งบจำกัด)"},
    {"user": "เฟิร์น", "age": 22, "group": "สายดีไซน์ + กล้อง"},
    {"user": "ชัย", "age": 21, "group": "สายเกมมิ่ง"},
    {"user": "ธนกร", "age": 23, "group": "สายสเปกแรง"},
    {"user": "แบม", "age": 20, "group": "สายแบตอึด งบประหยัด"},
    {"user": "มินต์", "age": 21, "group": "สายดีไซน์ไม่เหมือนใคร"},
]

# ---------------------------------------------------------------- ความสนใจ
# รูปแบบ: "ชื่อผู้ใช้": ["ชื่อรุ่น", ...]  — หนึ่งรายการ = หนึ่งความสัมพันธ์ LIKES
LIKES_BY_USER = {
    # สาย Android เรือธง — สนใจแต่รุ่นเรือธง แต่ยี่ห้อกระจาย
    "สมชาย": ["Galaxy S24 Ultra", "Xiaomi 14", "Honor Magic6 Pro", "Xperia 1 V"],
    # สาย Android เดิม ๆ — ชอบ Pixel และ Android ที่ไม่ปรับแต่งเยอะ
    "นรินทร์": ["Pixel 8 Pro", "Pixel 7a", "Xiaomi 14", "OnePlus 13R"],
    # สาย Apple — ชอบทุกระดับราคาของ Apple
    "มะลิ": ["iPhone 15 Pro Max", "iPhone 15", "iPhone 13", "iPhone SE (3rd gen)"],
    # สาย Apple + Samsung — มี iPhone ไว้ถ่ายรูป แต่ก็สนใจ Android เรือธง
    "ปวีณา": ["iPhone 15 Pro Max", "Galaxy S24 Ultra", "Galaxy S23"],
    # สาย Samsung — ครอบคลุมทั้งเรือธงและรุ่นกลาง
    "อนุชา": ["Galaxy S24 Ultra", "Galaxy S23", "Galaxy A55"],
    # สายถ่ายรูป — เน้นกล้องของ OPPO และ vivo
    "พลอย": ["Find X7 Ultra", "Find X6 Pro", "vivo X200 Pro"],
    # สายคุ้มค่า — งบจำกัด เลือก Xiaomi/POCO/OPPO รุ่นกลาง-เริ่มต้น
    "กัญญา": ["Redmi Note 14 Pro+", "POCO X3 Pro", "A78"],
    # สายดีไซน์ + กล้อง — ชอบ realme และ Sony
    "เฟิร์น": ["realme 16 Pro", "C35", "Xperia 1 V"],
    # สายเกมมิ่ง — เน้นชิปแรงและจอรีเฟรชสูง
    "ชัย": ["ROG Phone 6", "POCO X3 Pro", "Xiaomi 14"],
    # สายสเปกแรง — ใกล้เคียงสายเกมมิ่ง แต่ก็ดูเรือธงทั่วไปด้วย
    "ธนกร": ["ROG Phone 6", "realme 16 Pro", "Xiaomi 14"],
    # สายแบตอึด งบประหยัด
    "แบม": ["A78", "Galaxy A55", "Y36"],
    # สายดีไซน์ไม่เหมือนใคร
    "มินต์": ["Xperia 1 V", "C35"],
}


def display_name(phone):
    """ชื่อรุ่นสำหรับแสดงผล — กันชื่อยี่ห้อซ้ำ (เช่น brand 'vivo' + model 'vivo X100 Pro')"""
    model, brand = phone["model"], phone.get("brand", "")
    if model.lower().startswith(brand.lower()):
        return model
    return f"{brand} {model}"


def load_phones():
    with open(PHONES_JSON, encoding="utf-8") as f:
        phones = json.load(f)
    for p in phones:
        p["display"] = display_name(p)
        p.setdefault("image", "assets/phones/%s.jpg" % p["phone_id"])
    return phones


def graph_data():
    """คืน (users, phones, likes) — likes เป็นคู่ (ชื่อผู้ใช้, phone_id)"""
    phones = load_phones()
    by_model = {p["model"]: p for p in phones}
    likes, missing = [], []
    for user, models in LIKES_BY_USER.items():
        for m in models:
            if m not in by_model:
                missing.append(m)
                continue
            likes.append((user, by_model[m]["phone_id"]))
    if missing:
        raise KeyError("ชื่อรุ่นใน LIKES_BY_USER ไม่มีใน phones.json: %s" % sorted(set(missing)))
    return USERS, phones, likes


if __name__ == "__main__":
    u, p, l = graph_data()
    print("ผู้ใช้ %d คน | มือถือ %d รุ่น | ความสนใจ %d เส้น" % (len(u), len(p), len(l)))
    print("ยี่ห้อ:", ", ".join(sorted({x['brand'] for x in p})))
    print("ระดับราคา:", ", ".join(sorted({x['tier'] for x in p})))
    for ph in p:
        n = sum(1 for _, pid in l if pid == ph["phone_id"])
        print("  %s %-28s %-12s สนใจ %d คน" % (ph["phone_id"], ph["display"], ph["tier"], n))
