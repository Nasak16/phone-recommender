#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ธีมหน้าตาแอป (dark neon + ฟอนต์ไทย Prompt/Orbitron) — อ้างอิงสไตล์จากงานรุ่นพี่ที่ส่ง

ใช้:  from theme import CSS, HERO, card_html, inject
      inject()            # เรียกครั้งเดียวหลัง st.set_page_config
"""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;700&family=Orbitron:wght@700&display=swap');

/* ---------- พื้นหลัง: ดำ-น้ำเงิน + ตารางจาง ๆ ---------- */
.stApp {
    background: #05070f;
    background-image:
        radial-gradient(circle at 18% 12%, rgba(0,160,255,0.14) 0%, transparent 42%),
        radial-gradient(circle at 82% 72%, rgba(0,90,200,0.18) 0%, transparent 42%),
        linear-gradient(rgba(0,160,255,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,160,255,0.05) 1px, transparent 1px);
    background-size: auto, auto, 40px 40px, 40px 40px;
    background-attachment: fixed;
    color: #e6f1ff;
}
[data-testid="stHeader"] { background: transparent; }
html, body, [class*="css"], .stMarkdown, .stCaption { font-family: 'Prompt', sans-serif; }
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px; }
footer { visibility: hidden; }

h1, h2, h3, h4 { font-family: 'Prompt', sans-serif; color: #e6f1ff; letter-spacing: .2px; }
h3 { border-left: 3px solid #00b4ff; padding-left: 12px; }

/* ---------- Hero ---------- */
.hero { text-align: center; padding: 22px 10px 6px 10px; }
.hero h1 {
    font-family: 'Orbitron', 'Prompt', sans-serif;
    font-size: 2.5rem; margin: 0;
    background: linear-gradient(90deg, #00b4ff, #38d0ff, #7fe3ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero p { color: #8fa8c8; letter-spacing: 1px; margin-top: 8px; font-size: .95rem; }

/* ---------- การ์ด (container border) ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0b1220;
    border: 1px solid #1b3a63;
    border-radius: 18px;
    padding: 10px 12px;
    box-shadow: 0 4px 15px rgba(0,120,255,0.10);
    transition: all .3s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-4px);
    border-color: #00b4ff;
    box-shadow: 0 8px 25px rgba(0,180,255,0.28);
}
div[data-testid="stVerticalBlockBorderWrapper"] img {
    border-radius: 12px; border: 1px solid #1b3a63;
}

/* ---------- ปุ่ม ---------- */
.stButton > button, div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #0066ff, #00b4ff);
    color: #ffffff; font-weight: 600; border: none; border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,140,255,0.35); transition: all .2s;
}
.stButton > button:hover, div[data-testid="stDownloadButton"] button:hover {
    filter: brightness(1.12); color: #ffffff;
    box-shadow: 0 6px 18px rgba(0,180,255,0.5);
    border: none;
}
.stButton > button p { color: #ffffff; font-family: 'Prompt', sans-serif; }
div[data-testid="stLinkButton"] a {
    background: linear-gradient(90deg, #0066ff, #00b4ff); color: #ffffff !important;
    font-weight: 600; border: none !important; border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,140,255,0.35); transition: all .2s;
}
div[data-testid="stLinkButton"] a:hover {
    filter: brightness(1.12); color: #ffffff !important;
    box-shadow: 0 6px 18px rgba(0,180,255,0.5);
}
div[data-testid="stLinkButton"] a p { color: #ffffff !important; font-family: 'Prompt', sans-serif; }

/* ---------- ตัวชี้วัด ---------- */
div[data-testid="stMetric"] {
    background: #0b1220; border: 1px solid #1b3a63; border-radius: 14px;
    padding: 12px 14px; box-shadow: 0 4px 14px rgba(0,120,255,0.08);
}
div[data-testid="stMetricLabel"] p { color: #8fa8c8 !important; font-size: .82rem; }
div[data-testid="stMetricValue"] {
    font-family: 'Orbitron', 'Prompt', sans-serif;
    background: linear-gradient(90deg, #00b4ff, #7fe3ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* ---------- Sidebar + เมนู ---------- */
section[data-testid="stSidebar"] {
    background: #070c18; border-right: 1px solid #1b3a63;
}
div[data-testid="stSidebarCollapseButton"],
div[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
div[data-testid="stSidebarHeader"] { display: none; visibility: hidden; }
section[data-testid="stSidebar"] div[data-testid="stMetricLabel"] p {
    font-size: .78rem; line-height: 1.25; word-break: keep-all;
}
section[data-testid="stSidebar"] * { font-family: 'Prompt', sans-serif; }
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    display: block; margin: 3px 8px; padding: 9px 13px !important;
    border-radius: 10px; color: #8fa8c8 !important; font-weight: 500;
    transition: all .2s ease; cursor: pointer;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
    background: #0f1d36;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover * { color: #38d0ff !important; }
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, #0a1a33, #0f2548);
    box-shadow: inset 3px 0 0 #00b4ff;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) * {
    color: #38d0ff !important;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[data-testid="stMetric"] {
    background: #0b1526; border-radius: 12px; padding: 8px 10px; margin-bottom: 6px;
}
section[data-testid="stSidebar"] div[data-testid="stMetricValue"] { font-size: 1.15rem; }
section[data-testid="stSidebar"] h2 {
    font-family: 'Orbitron', 'Prompt', sans-serif; font-size: 1.15rem;
    background: linear-gradient(90deg, #00b4ff, #7fe3ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    border: none; padding: 0;
}

/* ---------- ตาราง / แท็บ / กล่องขยาย ---------- */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    border-radius: 12px; overflow: hidden; border: 1px solid #1b3a63;
}
div[data-testid="stExpander"] details {
    background: #0b1220; border: 1px solid #1b3a63; border-radius: 14px;
}
div[data-testid="stExpander"] summary { color: #cfe3ff; font-weight: 500; }
div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: #0b1220 !important; border-color: #1b3a63 !important; color: #e6f1ff !important;
}
div[data-testid="stAlert"] { border-radius: 14px; }
.stSlider [data-baseweb="slider"] div[role="slider"] { background: #00b4ff; }
.stProgress > div > div > div > div { background: linear-gradient(90deg,#0066ff,#00b4ff); }
hr { border-color: #1b3a63; }

/* ---------- การ์ดลิงก์ในหน้า Index ---------- */
.lcard {
    background: #0b1220; border: 1px solid #1b3a63; border-radius: 18px;
    padding: 18px; height: 225px; display: flex; flex-direction: column;
    justify-content: space-between; overflow: hidden; margin-bottom: 16px;
    box-shadow: 0 4px 15px rgba(0,120,255,0.10); transition: all .3s ease;
}
.lcard > div:first-child { flex: 1 1 auto; min-height: 0; }
.lcard:hover {
    transform: translateY(-6px); border-color: #00b4ff;
    box-shadow: 0 8px 25px rgba(0,180,255,0.30);
}
.lcard .icon { font-size: 1.9rem; }
.lcard h3 {
    color: #e6f1ff !important; margin: 6px 0 4px 0; font-size: 1.02rem; font-weight: 700;
    border: none !important; padding: 0 !important;
}
.lcard p {
    color: #8fa8c8; font-size: .8rem; line-height: 1.45; margin: 0 0 10px 0;
    display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden;
}
.lbtn { flex: 0 0 auto; }
/* ---------- การ์ดหน้าแรก (hub): ใช้ key ของ container (Streamlit 1.6x เพิ่มคลาส st-key-*) ---------- */
div[class*="st-key-card_"] {
    background: #0b1220; border: 1px solid #1b3a63 !important;
    border-radius: 18px; padding: 16px 16px 10px 16px; min-height: 215px;
    box-shadow: 0 4px 15px rgba(0,120,255,0.10); transition: all .3s ease;
}
div[class*="st-key-card_"]:hover {
    transform: translateY(-4px); border-color: #00b4ff !important;
    box-shadow: 0 8px 25px rgba(0,180,255,0.28);
}

.cardicon { font-size: 1.9rem; line-height: 1.1; }
.cardtitle { font-weight: 700; color: #eaf3ff; font-size: 1.02rem; margin: 4px 0 2px 0; }
.carddesc { color: #8fa8c8; font-size: .8rem; line-height: 1.45; min-height: 52px; margin-bottom: 4px; }

.lcard .tagline {
    color: #38d0ff; font-size: .72rem; letter-spacing: .5px; margin-bottom: 6px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.lbtn {
    display: block; text-align: center; text-decoration: none !important;
    padding: 9px; border-radius: 10px; font-weight: 600; color: #ffffff !important;
    background: linear-gradient(90deg, #0066ff, #00b4ff);
    box-shadow: 0 4px 12px rgba(0,140,255,0.35); transition: all .2s;
}
.lbtn:hover { filter: brightness(1.12); box-shadow: 0 6px 18px rgba(0,180,255,0.5); }
</style>
"""

HERO = """
<div class="hero">
    <h1>📱 ระบบแนะนำมือถือ</h1>
    <p>Neo4j (Graph Database) + Streamlit · จัดทำโดย นาย ณศักดิ์ ฉายแสงรัตน์ (Nasak) · รหัส 664245007 · กลุ่ม 66/43<br>
    ข้อมูลของเราเอง พร้อมภาพสินค้าจริง</p>
</div>
"""


def hero_text(stat=None):
    """หัวเรื่องที่มีตัวเลขจริงจากฐานข้อมูล (ไม่ใส่ตัวเลขตอนยังไม่รู้ค่า)"""
    if not stat:
        return HERO
    return f"""
<div class="hero">
    <h1>📱 ระบบแนะนำมือถือ</h1>
    <p>Neo4j (Graph Database) + Streamlit · จัดทำโดย นาย ณศักดิ์ ฉายแสงรัตน์ (Nasak) · รหัส 664245007 · กลุ่ม 66/43<br>
    ข้อมูลของเราเอง {stat.get('users', 0)} คน × {stat.get('phones', 0)} รุ่น × {stat.get('likes', 0)} ความสนใจ
    + {stat.get('ratings', 0)} คะแนนดาว · พร้อมภาพสินค้าจริง</p>
</div>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(text=None):
    st.markdown(text or HERO, unsafe_allow_html=True)


def hub_title(title, subtitle):
    """หัวเรื่องหน้าแรกแบบ hub: จัดกลาง ตัวอักษรไล่สี + คำโปรย"""
    st.markdown(f"""
<div style="text-align:center;margin:6px 0 22px 0">
    <h1 style="font-size:2.35rem;margin:0;font-family:'Orbitron','Prompt',sans-serif;
        background:linear-gradient(90deg,#00b4ff,#7fe3ff);-webkit-background-clip:text;
        -webkit-text-fill-color:transparent">{title}</h1>
    <p style="color:#8fa8c8;letter-spacing:1.5px;margin-top:10px;font-size:.95rem">{subtitle}</p>
</div>""", unsafe_allow_html=True)


def card_html(icon, title, desc, url, label="เปิดแอป →", tagline=None, height=230, new_tab=True):
    """การ์ดลิงก์สไตล์เดียวกับ hub (ใช้ unsafe_allow_html)"""
    tag = f'<div class="tagline">{tagline}</div>' if tagline else ""
    return (f'<div class="lcard" style="height:{height}px">'
            f'<div><div class="icon">{icon}</div>{tag}'
            f'<h3>{title}</h3><p>{desc}</p></div>'
            f'<a class="lbtn" href="{url}"'
            + (' target="_blank" rel="noopener"' if new_tab else '') +
            f'>{label}</a></div>')
