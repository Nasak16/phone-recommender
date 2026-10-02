# -*- coding: utf-8 -*-
"""รายการงานทั้งหมด — สร้างอัตโนมัติด้วย tools/build_homework_index.py
   (ดึงจากหน้า index: https://nasak16.github.io/homework/) — ห้ามแก้มือ"""
INDEX_URL = "https://nasak16.github.io/homework/"
HOMEWORK = [
    {
        "category": "ฐานข้อมูล",
        "title": "ระบบแนะนำมือถือ (Neo4j + Streamlit)",
        "desc": "งานนี้: ระบบแนะนำมือถือบนฐานข้อมูลกราฟ Neo4j — 12 คน × 23 รุ่น × 38 ความสนใจ + 38 คะแนนดาว (RATED) · เว็บแอป 6 หน้า (Dashboard / Recommendations / Phone Search / Like & Rate / Graph Explorer / Admin & Setup) · 5 วิธีให้คะแนน · แสดงภาพสินค้าจริงในการ์ดทุกใบ · มีโน๊ตบุ๊ก Colab + สไลด์ 16 หน้า",
        "repo": "phone-recommender",
        "date": "2026-10-02",
        "url": "https://github.com/Nasak16/phone-recommender",
        "extra": [
            ("📓 โน๊ตบุ๊ก Colab", "https://colab.research.google.com/gist/Nasak16/8667b219bbff8253335ec78f78b5c79e/PhoneRecommender_Neo4j_007.ipynb"),
            ("📊 สไลด์นำเสนอ (.pptx/.pdf)", "https://github.com/Nasak16/phone-recommender/tree/main/slides"),
        ],
    },
    {
        "category": "ฐานข้อมูล",
        "title": "ระบบแนะนำหนังสือ (Neo4j + Streamlit)",
        "desc": "งานนี้: ระบบแนะนำหนังสือบนฐานข้อมูลกราฟ Neo4j 12 คน × 28 เล่ม แสดงภาพปกจริง มีทั้งโน๊ตบุ๊ก Colab และเว็บแอปสาธิต",
        "repo": "book-recommender",
        "date": "2026-10-01",
        "url": "https://github.com/Nasak16/book-recommender",
        "extra": [
        ],
    },
    {
        "category": "ฐานข้อมูล",
        "title": "GraphBook — ระบบแนะนำหนังสือด้วยกราฟ (งานตัวอย่างในวิชา)",
        "desc": "Streamlit + Neo4j Aura: (Student)-[:BORROWED]->(Book) + เพื่อน/หมวด/คะแนนดาว สูตร hybrid แบบ heuristic",
        "repo": "GrapDB1",
        "date": "2026-09-29",
        "url": "https://github.com/Nasak16/GrapDB1",
        "extra": [
        ],
    },
    {
        "category": "ฐานข้อมูล",
        "title": "Dashboard แสดงข้อมูลด้วย Grafana + InfluxDB",
        "desc": "รวบรวมข้อมูลอนุกรมเวลาและทำแดชบอร์ดติดตามสถานะ",
        "repo": "grafanaDB",
        "date": "2026-09-24",
        "url": "https://github.com/Nasak16/grafanaDB",
        "extra": [
        ],
    },
    {
        "category": "IoT",
        "title": "โปรเจกต์จบ: ระบบรักษาความปลอดภัยบ้าน IoT",
        "desc": "ESP32 + ESP32-CAM + Firebase + Grafana + LINE Notify (repo ส่วนตัว)",
        "repo": "iot-security-dashboard",
        "date": "2026-08-28",
        "url": "https://nasak16.github.io/homework/",
        "extra": [
        ],
    },
    {
        "category": "Machine Learning",
        "title": "Machine Learning: ทำนายผู้รอดชีวิต Titanic",
        "desc": "EDA + โมเดลทำนาย และเว็บแอป Streamlit สำหรับทดลองทำนาย",
        "repo": "titanic-ml-project",
        "date": "2026-08-21",
        "url": "https://github.com/Nasak16/titanic-ml-project",
        "extra": [
        ],
    },
    {
        "category": "Machine Learning",
        "title": "ทำนายผลการเรียนของนักเรียน",
        "desc": "สร้างโมเดลจาก student performance dataset แล้ว deploy ด้วย Streamlit",
        "repo": "web_model",
        "date": "2026-07-30",
        "url": "https://github.com/Nasak16/web_model",
        "extra": [
        ],
    },
    {
        "category": "Machine Learning",
        "title": "Machine Learning: จำแนกประเภทข้อมูลป่า",
        "desc": "ฝึกโมเดลจำแนกประเภทพร้อมวัดผลความแม่นยำ",
        "repo": "forest",
        "date": "2026-07-24",
        "url": "https://github.com/Nasak16/forest",
        "extra": [
        ],
    },
    {
        "category": "Machine Learning",
        "title": "Machine Learning: วิเคราะห์ข้อมูลสุขภาพจิต",
        "desc": "สำรวจข้อมูลและสร้างโมเดลทำนายกลุ่มเสี่ยง",
        "repo": "mental_ML",
        "date": "2026-07-17",
        "url": "https://github.com/Nasak16/mental_ML",
        "extra": [
        ],
    },
    {
        "category": "Machine Learning",
        "title": "Machine Learning: ทำนายราคาบ้าน (Boston Housing)",
        "desc": "งาน Regression พื้นฐานพร้อมกราฟวิเคราะห์",
        "repo": "Boston_ML",
        "date": "2026-07-17",
        "url": "https://github.com/Nasak16/Boston_ML",
        "extra": [
        ],
    },
    {
        "category": "Decision Tree",
        "title": "Decision Tree: ทำนายความเสี่ยงโรคหัวใจ",
        "desc": "สร้างโมเดล Decision Tree และวัดผลด้วย confusion matrix",
        "repo": "DTreeHeart",
        "date": "2026-07-14",
        "url": "https://github.com/Nasak16/DTreeHeart",
        "extra": [
        ],
    },
    {
        "category": "Decision Tree",
        "title": "Decision Tree: จำแนกชนิดไวน์",
        "desc": "ฝึก Decision Tree กับข้อมูลไวน์และเปรียบเทียบผล",
        "repo": "DTwine",
        "date": "2026-07-14",
        "url": "https://github.com/Nasak16/DTwine",
        "extra": [
        ],
    },
    {
        "category": "Decision Tree",
        "title": "Decision Tree (งานที่ 3)",
        "desc": "ฝึกสร้างโมเดลต้นไม้ตัดสินใจและปรับพารามิเตอร์",
        "repo": "DecisionTree_ML3",
        "date": "2026-07-10",
        "url": "https://github.com/Nasak16/DecisionTree_ML3",
        "extra": [
        ],
    },
    {
        "category": "Machine Learning",
        "title": "KNN: จำแนกข้อมูลด้วยเพื่อนบ้านใกล้สุด",
        "desc": "ฝึกอัลกอริทึม K-Nearest Neighbors พร้อมเลือกค่า k ที่เหมาะสม",
        "repo": "KNN",
        "date": "2026-07-07",
        "url": "https://github.com/Nasak16/KNN",
        "extra": [
        ],
    },
]
