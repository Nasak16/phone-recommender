#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างโน๊ตบุ๊ก .ipynb สำหรับส่ง (Colab + Neo4j) จากข้อมูลชุดเดียวกับแอป

    py -3.13 tools/build_notebook.py            # ตัวส่งจริง (Neo4j Aura + getpass)
    py -3.13 tools/build_notebook.py --test     # สำเนาทดสอบ (ต่อ Neo4j ในเครื่อง)

ห้ามมี docstring สามชั้นในข้อความเซลล์ (จะพังตอนประกอบ) — ใช้ # แทน
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "data"))
import seed_data  # noqa: E402

TEST = "--test" in sys.argv
REPO = "Nasak16/phone-recommender"
IMAGE_BASE = f"https://cdn.jsdelivr.net/gh/{REPO}@main/assets/phones/"
OUT = os.path.join(ROOT, "notebooks" if not TEST else os.path.join("tools", "out"),
                   "PhoneRecommender_Neo4j_007.ipynb")

users, phones, likes = seed_data.graph_data()
for p in phones:
    p["img"] = os.path.basename(p["image"])

PHONES_PY = "[\n" + "".join(
    "    {\"phone_id\": \"%s\", \"model\": \"%s\", \"brand\": \"%s\", \"tier\": \"%s\", "
    "\"img\": \"%s\"},\n"
    % (p["phone_id"], p["model"].replace('"', "'"), p["brand"], p["tier"], p["img"])
    for p in phones) + "]"
USERS_PY = "[\n" + "".join(
    "    {\"user\": \"%s\", \"age\": %s, \"group\": \"%s\"},\n" % (u["user"], u["age"], u["group"])
    for u in users) + "]"
LIKES_PY = "[\n" + "".join(
    "    (\"%s\", \"%s\"),\n" % (u, p) for u, p in likes) + "]"
ratings = seed_data.ratings_data(phones)
RATINGS_PY = "[\n" + "".join(
    "    (\"%s\", \"%s\", %s),\n" % (u, p, s) for u, p, s in ratings) + "]"

MD, PY = {}, {}

# ------------------------------------------------------------------ 0-1
MD[0] = """[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/gist/Nasak16/8667b219bbff8253335ec78f78b5c79e/PhoneRecommender_Neo4j_007.ipynb)

# 📱 ระบบแนะนำมือถือด้วย Graph Database (Neo4j)

**ผู้จัดทำ:** นาย ณศักดิ์ ฉายแสงรัตน์ (Nasak) · **รหัส 664245007** · **กลุ่ม 66/43** · **งาน:** พัฒนาระบบแนะนำเป็นระบบของตัวเอง

ระบบนี้เป็น **ระบบแนะนำมือถือ** ที่สร้างข้อมูลขึ้นเองทั้งชุด (ไม่ใช้ dataset สำเร็จรูป)
{NU} คน × {NP} รุ่น × {NL} ความสนใจ — และ **แสดงภาพสินค้าจริง** ในผลการแนะนำ

**แนวคิด** ผู้ใช้สนใจรุ่นอะไร → หาคนอื่นที่สนใจรุ่นเดียวกัน (รสนิยมใกล้กัน) →
ดูว่าเขาสนใจรุ่นอะไรอีกที่เรายังไม่สนใจ → เรียงตามคะแนน = คำแนะนำ

เลือกใช้ **ฐานข้อมูลกราฟ (Neo4j)** เพราะข้อมูลแบบ "ใครสนใจรุ่นไหน" เป็นเรื่องของความสัมพันธ์
เขียนคำถามได้สั้นมาก และอธิบายย้อนหลังได้ว่าเพราะใคร/เพราะรุ่นไหนจึงแนะนำรุ่นนั้น"""

PY[1] = """!pip -q install neo4j pandas

import getpass
import pandas as pd
from neo4j import GraphDatabase
from IPython.display import HTML, display

# ---- ข้อมูลการเชื่อมต่อ (เวอร์ชันส่งจริงใช้ Neo4j Aura ของเราเอง) ----
URI = "neo4j+s://<รหัส-instance>.databases.neo4j.io"
USER = "neo4j"
PASSWORD = getpass.getpass("Neo4j password: ")
DATABASE = "neo4j"

def connect(uri=None, user=None, password=None, database=None):
    driver = GraphDatabase.driver(uri or URI, auth=(user or USER, password or PASSWORD))
    driver.verify_connectivity()
    return driver

def run(driver, query, **params):
    with driver.session(database=DATABASE) as s:
        return [r.data() for r in s.run(query, **params)]

driver = connect()
print("เชื่อมต่อสำเร็จ:", driver.get_server_info().agent)"""

# ------------------------------------------------------------------ data
MD[2] = """## 👥 ข้อมูลชุดของเรา (เก็บเอง ไม่ใช่ dataset สำเร็จรูป)

| องค์ประกอบ | จำนวน | รายละเอียด |
|---|---|---|
| ผู้ใช้ | {NU} คน | สอบถามเพื่อนในห้องว่า "สนใจมือถือรุ่นไหน" (ข้อมูลผู้ใช้เป็นชุดสมมติเพื่อสาธิต) |
| มือถือ | {NP} รุ่น | ครอบคลุม 10 ยี่ห้อ และ 3 ระดับราคา (เรือธง / ระดับกลาง / ระดับเริ่มต้น) |
| ความสนใจ | {NL} เส้น | ความสัมพันธ์ `LIKES` หนึ่งเส้น = "คนนี้สนใจรุ่นนี้" |

**ภาพสินค้า** ดึงจาก Wikimedia Commons (ฟรี ต้องให้เครดิต — เก็บรายชื่อไฟล์ต้นทางไว้ใน
`data/phones.json`) แล้วเก็บไฟล์ไว้ในโปรเจกต์ GitHub จึงแสดงในผลการแนะนำได้ทุกที่

> หมายเหตุตรงไปตรงมา: รายชื่อรุ่น/ยี่ห้อ/ระดับราคาเป็นการจัดชุดสำหรับการเรียนการสอน
> ไม่ใช่สเปกหรือราคาทางการ ส่วนภาพเป็นภาพจริงของผู้ใช้ใน Commons"""

PY[3] = """IMAGE_BASE = "%s"

USERS = %s

PHONES = %s

LIKES = %s

# คะแนนดาว 1.0-5.0 ที่ผู้ใช้ให้รุ่นที่ตัวเองสนใจ (ใช้เป็นสัญญาณที่ 5 ของระบบ)
RATINGS = %s
""" % (IMAGE_BASE, USERS_PY, PHONES_PY, LIKES_PY, RATINGS_PY) + """
PHONE = {p["phone_id"]: p for p in PHONES}
BRANDS = sorted({p["brand"] for p in PHONES})
TIERS = ["เรือธง", "ระดับกลาง", "ระดับเริ่มต้น"]

def image_url(phone_id):
    return IMAGE_BASE + PHONE[phone_id]["img"]

def show_cards(rows, title=None, height=190):
    # แสดงผลเป็น "การ์ดมือถือ" พร้อมภาพสินค้า — ใช้ HTML ให้ Colab เรนเดอร์รูปได้
    css_box = "display:flex;gap:12px;flex-wrap:wrap;margin:6px 0 14px 0"
    css_card = ("width:158px;background:#172136;border:1px solid #2B3A5C;border-radius:10px;"
                "padding:8px;color:#E9EFFA;font-family:sans-serif")
    html = []
    if title:
        html.append("<h4 style='color:#E9EFFA;font-family:sans-serif'>" + title + "</h4>")
    html.append("<div style='" + css_box + "'>")
    for r in rows:
        pid = r["phone_id"]
        p = PHONE[pid]
        badge = ""
        if r.get("score") is not None:
            badge = "<div style='color:#FBBF24'>คะแนน " + str(r["score"]) + "</div>"
        elif r.get("votes"):
            badge = ("<div style='color:#FBBF24'>" + str(r["votes"]) + " โหวต จาก " +
                     ", ".join(r.get("voters", [])) + "</div>")
        elif r.get("content_score") is not None:
            badge = ("<div style='color:#38BDF8'>ยี่ห้อตรง " + str(r.get("brand_matches", 0)) +
                     " · ระดับราคาตรง " + str(r.get("tier_matches", 0)) + "</div>")
        if r.get("avg_stars"):
            badge += ("<div style='color:#FDE68A'>🌟 ดาวจากเพื่อน " + str(r["avg_stars"]) +
                      "</div>")
        elif r.get("phone_id") and avg_stars(r["phone_id"]):
            badge += ("<div style='color:#FDE68A'>🌟 ดาวเฉลี่ย " +
                      str(avg_stars(r["phone_id"])) + "</div>")
        why = ""
        if r.get("via_phones"):
            why = ("<div style='color:#9FB0CB;font-size:11px'>เพราะคุณสนใจ: " +
                   ", ".join(r["via_phones"]) + "</div>")
        html.append(
            "<div style='" + css_card + "'>"
            "<img src='" + image_url(pid) + "' style='width:100%;height:" + str(height) +
            "px;object-fit:cover;border-radius:6px'>"
            "<div style='font-weight:600;margin-top:6px'>" + p["brand"] + " " + p["model"] +
            "</div>" + "<div style='color:#9FB0CB;font-size:12px'>ระดับราคา: " + p["tier"] +
            "</div>" + badge + why + "</div>")
    html.append("</div>")
    display(HTML("".join(html)))

RATING_OF = {}
for _u, _p, _s in RATINGS:
    RATING_OF.setdefault(_p, []).append(_s)


def avg_stars(phone_id):
    # ดาวเฉลี่ยของรุ่นนั้น (None = ยังไม่มีใครให้คะแนน)
    v = RATING_OF.get(phone_id) or []
    return round(sum(v) / len(v), 2) if v else None


print("ผู้ใช้", len(USERS), "คน | มือถือ", len(PHONES), "รุ่น | ความสนใจ", len(LIKES),
      "เส้น | คะแนนดาว", len(RATINGS), "รายการ")
show_cards([{"phone_id": p["phone_id"]} for p in PHONES[:6]],
           title="ตัวอย่างรุ่นมือถือในระบบ (ภาพจริงจาก Wikimedia Commons)")"""

# ------------------------------------------------------------------ schema
MD[4] = """## 🧩 โครงสร้างกราฟที่ใช้ในงานนี้

| องค์ประกอบ | รายละเอียด |
|---|---|
| โหนด `User` | {NU} โหนด (ชื่อผู้ใช้, อายุ, กลุ่มรสนิยม) |
| โหนด `Phone` | {NP} โหนด (รุ่น, ยี่ห้อ, ระดับราคา) |
| โหนด `Brand` | {NB} โหนด (ยี่ห้อ) |
| โหนด `Tier` | {NT} โหนด (เรือธง / ระดับกลาง / ระดับเริ่มต้น) |
| ความสัมพันธ์ | `LIKES` (ผู้ใช้→รุ่น), `BY_BRAND` (รุ่น→ยี่ห้อ), `IN_TIER` (รุ่น→ระดับราคา) |

การเดิน 3 hop เพื่อหาคำแนะนำ

```
                 สมชาย (คนที่เราจะแนะนำ)
                        ↓ [:LIKES]
        Galaxy S24 Ultra · Xiaomi 14 · OnePlus 12 · Honor Magic6 Pro
                        ↓ ใครสนใจรุ่นพวกนี้เหมือนกัน
              คนรสนิยมใกล้กัน (นรินทร์ · อนุชา · ธนกร)
                        ↓ รุ่นอื่นที่คนกลุ่มนี้สนใจ
              Pixel 8 Pro · Pixel 7a · Galaxy S23 · ROG Phone 8 ...
                        ↓ นับคะแนน (และดูยี่ห้อ/ระดับราคาประกอบ)
                  คำแนะนำสำหรับสมชาย
```

เริ่มจากล้างฐานข้อมูลเดิม แล้วสร้าง constraint ให้คีย์ไม่ซ้ำ"""

PY[5] = """Q_RESET = "MATCH (n) DETACH DELETE n"

Q_CONSTRAINTS = [
    "CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.user IS UNIQUE",
    "CREATE CONSTRAINT phone_id IF NOT EXISTS FOR (p:Phone) REQUIRE p.phone_id IS UNIQUE",
    "CREATE CONSTRAINT brand_name IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
    "CREATE CONSTRAINT tier_name IF NOT EXISTS FOR (t:Tier) REQUIRE t.name IS UNIQUE",
]

Q_LOAD_USERS = '''
UNWIND $rows AS row
MERGE (u:User {user: row.user})
SET u.age = row.age, u.group = row.group, u.node_type = 'user'
RETURN count(u) AS users
'''

Q_LOAD_PHONES = '''
UNWIND $rows AS row
MERGE (p:Phone {phone_id: row.phone_id})
SET p.model = row.model, p.brand = row.brand, p.tier = row.tier,
    p.image = row.image, p.node_type = 'phone'
MERGE (b:Brand {name: row.brand})  MERGE (p)-[:BY_BRAND]->(b)
MERGE (t:Tier {name: row.tier})    MERGE (p)-[:IN_TIER]->(t)
RETURN count(p) AS phones
'''

Q_LOAD_LIKES = '''
UNWIND $rows AS row
MATCH (u:User {user: row.user})
MATCH (p:Phone {phone_id: row.phone_id})
MERGE (u)-[:LIKES]->(p)
RETURN count(*) AS likes
'''

Q_LOAD_RATINGS = '''
UNWIND $rows AS row
MATCH (u:User {user: row.user})
MATCH (p:Phone {phone_id: row.phone_id})
MERGE (u)-[rt:RATED]->(p) SET rt.stars = row.stars
RETURN count(rt) AS ratings
'''

run(driver, Q_RESET)
for q in Q_CONSTRAINTS:
    run(driver, q)
print("สร้างผู้ใช้:", run(driver, Q_LOAD_USERS, rows=USERS))
print("สร้างรุ่นมือถือ:", run(driver, Q_LOAD_PHONES, rows=PHONES))
print("สร้างความสนใจ:", run(driver, Q_LOAD_LIKES,
                           rows=[{"user": u, "phone_id": p} for u, p in LIKES]))
print("สร้างคะแนนดาว:", run(driver, Q_LOAD_RATINGS,
                          rows=[{"user": u, "phone_id": p, "stars": s}
                                for u, p, s in RATINGS]))"""

MD[6] = """## ✅ ตรวจสอบว่าข้อมูลเข้าครบตามที่ออกแบบไว้

ถ้าตัวเลขตรงกับตารางข้างบน แปลว่าข้อมูลชุดเดียวกันถูกโหลดเข้า Neo4j แล้วจริง"""

PY[7] = """Q_STATS = '''
RETURN COUNT { MATCH (u:User) } AS users,
       COUNT { MATCH (p:Phone) } AS phones,
       COUNT { MATCH ()-[r:LIKES]->() } AS likes,
       COUNT { MATCH ()-[rt:RATED]->() } AS ratings,
       COUNT { MATCH (b:Brand) } AS brands,
       COUNT { MATCH (t:Tier) } AS tiers
'''
# หมายเหตุ: ใช้ COUNT { } เพราะแบบ MATCH ... WITH count() จะได้ 0 แถวถ้าฐานข้อมูลว่าง

stats = run(driver, Q_STATS)[0]
print("สรุปฐานข้อมูล:", stats)

rows = run(driver, '''
    MATCH (p:Phone) OPTIONAL MATCH (p)<-[:LIKES]-(u:User)
    RETURN p.brand AS ยี่ห้อ, p.tier AS ระดับราคา, count(DISTINCT p) AS จำนวนรุ่น,
           count(u) AS ความสนใจรวม
    ORDER BY ความสนใจรวม DESC''')
display(pd.DataFrame(rows))"""

# ------------------------------------------------------------------ Q1
MD[8] = """## ❓ คำถามข้อ 1: ผู้ใช้คนนี้สนใจมือถือรุ่นอะไรบ้าง?

Neighbor ของโหนดผู้ใช้ = รุ่นที่เขาเชื่อมด้วย `[:LIKES]`
เขียนเป็น Cypher ได้สั้น ๆ ว่า `MATCH (u)-[:LIKES]->(p)` แล้วคืน `p` ทั้งหมด"""

PY[9] = """Q_LIKED = '''
MATCH (u:User {user: $user})-[:LIKES]->(p:Phone)
OPTIONAL MATCH (p)-[:BY_BRAND]->(b:Brand)
OPTIONAL MATCH (p)-[:IN_TIER]->(t:Tier)
RETURN p.phone_id AS phone_id, p.model AS model, p.brand AS brand, p.tier AS tier,
       collect(DISTINCT b.name) AS brands, collect(DISTINCT t.name) AS tiers
ORDER BY p.model
'''

TARGET = "สมชาย"
liked = run(driver, Q_LIKED, user=TARGET)
display(pd.DataFrame(liked)[["phone_id", "model", "brand", "tier"]])
show_cards(liked, title="รุ่นที่ " + TARGET + " สนใจอยู่แล้ว (" + str(len(liked)) + " รุ่น)")"""

# ------------------------------------------------------------------ Q2
MD[10] = """## ❓ คำถามข้อ 2: ใครมีรสนิยมใกล้ "สมชาย" และใกล้แค่ไหน?

วิธีคิด: หารุ่นที่ทั้งสองคนสนใจร่วมกัน แล้วเทียบสัดส่วนด้วย **Jaccard similarity**

```
Jaccard(เรา, เขา) = |รุ่นที่สนใจร่วมกัน| / |รุ่นของสองคนรวมกัน (ไม่ซ้ำ)|
```

- 0 = ไม่มีรุ่นไหนเหมือนกันเลย
- 1 = สนใจเหมือนกันทุกรุ่น
"""

PY[11] = """Q_SIMILAR = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Phone)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.phone_id) AS common
MATCH (me)-[:LIKES]->(mine:Phone)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Phone)
WITH other, common, n_mine, count(DISTINCT theirs) AS n_theirs
RETURN other.user AS user, size(common) AS common_count, common AS common_phones,
       n_mine, n_theirs,
       toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard
ORDER BY jaccard DESC, user
'''

sims = run(driver, Q_SIMILAR, user=TARGET)
display(pd.DataFrame([{**s, "jaccard": round(s["jaccard"], 3)} for s in sims]))
print("อ่านผล: คนที่ได้ Jaccard สูงสุดคือคนที่รสนิยมใกล้เราที่สุด — "
      "น้ำหนักโหวตของเขาจะมากกว่าคนที่สนใจบังเอิญตรงกันรุ่นเดียว")"""

# ------------------------------------------------------------------ v1
MD[12] = """## 🎯 เริ่มสร้างระบบ Recommendation (เวอร์ชัน 1: นับโหวต)

ลำดับการทำงานบนกราฟ (3 hop) เขียนเป็น Cypher ได้ในคำสั่งเดียว

```
MATCH (me)-[:LIKES]->(shared:Phone)<-[:LIKES]-(other)-[:LIKES]->(rec:Phone)
```

> 💡 **จุดสังเกตสำคัญ** — ถ้าเขียนด้วยลูปใน Python (แบบที่ฝึกในคลาส) จะนับซ้ำได้ง่าย
> เช่นเพื่อนที่สนใจตรงกับเราหลายรุ่นจะออกเสียงหลายครั้ง แต่ใน Cypher เราใช้
> `count(DISTINCT other)` ทำให้ **1 คน = 1 เสียง ต่อ 1 รุ่น** อย่างอัตโนมัติ
> และ `WHERE NOT (me)-[:LIKES]->(rec)` กันไม่ให้แนะนำรุ่นที่เราสนใจอยู่แล้ว"""

PY[13] = """Q_RECO_VOTES = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Phone)<-[:LIKES]-(other:User)-[:LIKES]->(rec:Phone)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.phone_id AS phone_id, rec.model AS model, rec.brand AS brand, rec.tier AS tier,
       count(DISTINCT other) AS votes,
       collect(DISTINCT other.user) AS voters,
       collect(DISTINCT shared.model) AS via_phones
ORDER BY votes DESC, model
'''

votes = run(driver, Q_RECO_VOTES, user=TARGET)
display(pd.DataFrame(votes)[["model", "brand", "votes", "voters"]])
show_cards(votes[:4], title="คำแนะนำจากเพื่อน (นับโหวต) — " + str(len(votes)) + " รุ่นที่เข้าเกณฑ์")

top = votes[0]
print("อันดับ 1 คือ", top["brand"], top["model"], "ได้", top["votes"], "โหวต จาก",
      ", ".join(top["voters"]))
print("เหตุผล: คุณสนใจ", ", ".join(top["via_phones"]), "ซึ่งเพื่อนกลุ่มนี้ก็สนใจเหมือนกัน")"""

# ------------------------------------------------------------------ v2
MD[14] = """## ⭐ เวอร์ชัน 2: ถ่วงน้ำหนักด้วยความคล้าย (Jaccard)

เวอร์ชันนับโหวตให้ทุกคนน้ำหนักเท่ากัน ปัญหาคือ "เพื่อนที่สนใจตรงกันรุ่นเดียว" มีเสียงเท่ากับ
"เพื่อนที่รสนิยมเหมือนเราเกือบทั้งหมด" — เวอร์ชันนี้จึงคูณน้ำหนักด้วย Jaccard

```
คะแนน(รุ่น) = Σ Jaccard(เรา, คนที่สนใจรุ่นนั้น)
```
"""

PY[15] = """Q_RECO_WEIGHTED = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Phone)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.phone_id) AS common
MATCH (me)-[:LIKES]->(mine:Phone)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Phone)
WITH me, other, common, n_mine, count(DISTINCT theirs) AS n_theirs
WITH me, other, toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard, common
MATCH (other)-[:LIKES]->(rec:Phone)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.phone_id AS phone_id, rec.model AS model, rec.brand AS brand, rec.tier AS tier,
       round(sum(jaccard) * 1000) / 1000.0 AS score,
       count(DISTINCT other) AS votes, collect(DISTINCT other.user) AS voters
ORDER BY score DESC, model
'''

weighted = run(driver, Q_RECO_WEIGHTED, user=TARGET)
display(pd.DataFrame(weighted)[["model", "brand", "score", "votes", "voters"]])
show_cards(weighted[:3], title="3 อันดับแรก: คำแนะนำแบบถ่วงน้ำหนัก (Jaccard)")
print("เทียบกับเวอร์ชันนับโหวต: อันดับอาจสลับกัน เพราะรุ่นที่คนรสนิยมใกล้เราสุดสนใจ "
      "จะได้คะแนนสูงกว่า")"""

# ------------------------------------------------------------------ content + hybrid
MD[16] = """## 🏷️ เพิ่มอีกสัญญาณ: ยี่ห้อ และระดับราคา (Content-based) แล้วผสมกับสัญญาณเพื่อน

Collaborative Filtering มีจุดอ่อนเรื่อง **cold start** — คนใหม่ที่ยังไม่มีความสนใจร่วมกับใครเลย
จะไม่ได้คำแนะนำอะไร ระบบนี้จึงใช้โหนด `Brand` และ `Tier` เป็นสัญญาณที่สอง
(มือถือเป็นสินค้าที่คนมักยึดติดยี่ห้อและจำกัดด้วยงบประมาณ)

- **สายยี่ห้อ/ราคา** นับรุ่นที่เราเคยสนใจซึ่งใช้ยี่ห้อเดียวกัน + อยู่ระดับราคาเดียวกัน
- **ผสม** `คะแนน = 0.6 × (คะแนนเพื่อน normalize) + 0.4 × (คะแนนยี่ห้อ/ราคา normalize)`
"""

PY[17] = """Q_RECO_CONTENT = '''
MATCH (me:User {user: $user})-[:LIKES]->(liked:Phone)-[:BY_BRAND]->(b:Brand)<-[:BY_BRAND]-(rec:Phone)
WHERE NOT (me)-[:LIKES]->(rec)
WITH rec, count(DISTINCT liked) AS brand_matches, collect(DISTINCT b.name) AS brands
OPTIONAL MATCH (me)-[:LIKES]->(liked2:Phone)-[:IN_TIER]->(t:Tier)<-[:IN_TIER]-(rec)
WITH rec, brand_matches, brands, count(DISTINCT liked2) AS tier_matches,
     collect(DISTINCT t.name) AS tiers
RETURN rec.phone_id AS phone_id, rec.model AS model, rec.brand AS brand, rec.tier AS tier,
       brand_matches, brands, tier_matches, tiers,
       brand_matches + tier_matches AS content_score
ORDER BY content_score DESC, brand_matches DESC, model
'''

content = run(driver, Q_RECO_CONTENT, user=TARGET)
display(pd.DataFrame(content)[["model", "brand", "tier", "brand_matches", "tier_matches",
                              "content_score"]])
show_cards(content[:3], title="คำแนะนำจากยี่ห้อ/ระดับราคาที่ " + TARGET + " สนใจ")

def hybrid(user, top_n=5, weight_collab=0.6):
    # รวมสองสัญญาณหลัง normalize ให้คะแนนอยู่ช่วง 0-1 เท่ากัน
    recs = {r["phone_id"]: r for r in run(driver, Q_RECO_WEIGHTED, user=user)}
    gens = {r["phone_id"]: r for r in run(driver, Q_RECO_CONTENT, user=user)}
    max_s = max([r["score"] for r in recs.values()] or [0]) or 1
    max_g = max([r["content_score"] for r in gens.values()] or [0]) or 1
    out = {}
    for pid in set(recs) | set(gens):
        c, g = recs.get(pid), gens.get(pid)
        base = c or g
        out[pid] = {"phone_id": pid, "model": base["model"], "brand": base["brand"],
                    "tier": base.get("tier"),
                    "score": round(weight_collab * (c["score"] if c else 0) / max_s
                                   + (1 - weight_collab) * (g["content_score"] if g else 0) / max_g, 3),
                    "because": ("เพื่อนที่รสนิยมใกล้ + ยี่ห้อ/ราคาที่สนใจ" if c and g else
                                "เพื่อนที่รสนิยมใกล้สนใจ" if c else "ยี่ห้อ/ระดับราคาที่สนใจ"),
                    "voters": (c or {}).get("voters", []),
                    "via_phones": (c or {}).get("via_phones", []),
                    "brand_matches": (g or {}).get("brand_matches", 0),
                    "tier_matches": (g or {}).get("tier_matches", 0)}
    return sorted(out.values(), key=lambda r: (-r["score"], r["model"]))[:top_n]

mixed = hybrid(TARGET)
display(pd.DataFrame(mixed))
show_cards(mixed, title="คำแนะนำแบบผสม (เพื่อน 60% + ยี่ห้อ/ราคา 40%)")"""

# ------------------------------------------------------------------ signal 5
MD[17.5] = """## ⭐ สัญญาณที่ 5: เพื่อนถ่วงด้วย “คะแนนดาว”

ข้อมูลจริงไม่ได้มีแค่ “สนใจ/ไม่สนใจ” — บางคนชอบรุ่นนั้นมาก บางคนแค่เฉย ๆ
ระบบจึงเก็บ **คะแนนดาว 1.0–5.0** ไว้เป็นความสัมพันธ์อีกชนิด

```
(User)-[:RATED {stars: 1.0-5.0}]->(Phone)
```

สูตร: `คะแนน = Σ ( Jaccard(เรา, เพื่อน) × ดาวที่เพื่อนให้รุ่นนั้น ÷ 5 )`

ต่างจากวิธี “ถ่วงน้ำหนัก” ที่นับแค่ว่าเพื่อนสนใจหรือไม่ — วิธีนี้เอา **ระดับความชอบ** มาคูณ
คนที่ให้ 5 ดาวจึงมีน้ำหนักมากกว่าคนที่ให้ 2 ดาว แม้ Jaccard เท่ากัน"""

# ------------------------------------------------------------------ all users
MD[18] = """## 📊 คำแนะนำของทุกคนในระบบ + เทียบกับ baseline

ระบบที่ใช้ได้จริงต้องตอบได้ว่า "ทุกคนได้อะไร" และมี **baseline** ให้เทียบว่า
คำแนะนำเฉพาะบุคคลดีกว่าการแนะนำของยอดนิยม (Popular) อย่างไร"""

PY[17.7] = """Q_RECO_RATED = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Phone)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.phone_id) AS common,
     collect(DISTINCT shared.model) AS via_models
MATCH (me)-[:LIKES]->(mine:Phone)
WITH me, other, common, via_models, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Phone)
WITH me, other, common, via_models, n_mine, count(DISTINCT theirs) AS n_theirs
WITH me, other, via_models,
     toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard
MATCH (other)-[rt:RATED]->(rec:Phone)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.phone_id AS phone_id, rec.model AS model, rec.brand AS brand, rec.tier AS tier,
       round(sum(jaccard * rt.stars / 5.0) * 1000) / 1000.0 AS score,
       count(DISTINCT other) AS votes, collect(DISTINCT other.user) AS voters,
       reduce(acc = [], x IN collect(DISTINCT via_models) | acc + x) AS via_phones,
       round(avg(rt.stars) * 100) / 100.0 AS avg_stars
ORDER BY score DESC, model
'''

rated = run(driver, Q_RECO_RATED, user=TARGET)
display(pd.DataFrame(rated)[["model", "brand", "tier", "score", "votes", "avg_stars"]])
show_cards(rated[:3], title="คำแนะนำที่ถ่วงด้วยคะแนนดาว (สัญญาณที่ 5) — " + TARGET)

# เทียบทั้ง 5 วิธีในตารางเดียว: อันดับ 1-3 ของแต่ละวิธี
compare = {
    "นับโหวตเพื่อน": run(driver, Q_RECO_VOTES, user=TARGET),
    "ถ่วงน้ำหนัก (Jaccard)": run(driver, Q_RECO_WEIGHTED, user=TARGET),
    "ตามยี่ห้อ/ระดับราคา": run(driver, Q_RECO_CONTENT, user=TARGET),
    "ผสม (เพื่อน+ยี่ห้อ/ราคา)": mixed,
    "ถ่วงด้วยคะแนนดาว": rated,
}
rows_cmp = []
for name, lst in compare.items():
    top = (lst or [])[:3]
    rows_cmp.append({"วิธีให้คะแนน": name,
                     "อันดับ 1": top[0]["model"] if len(top) > 0 else "-",
                     "อันดับ 2": top[1]["model"] if len(top) > 1 else "-",
                     "อันดับ 3": top[2]["model"] if len(top) > 2 else "-"})
display(pd.DataFrame(rows_cmp))
print("แต่ละวิธีให้ผลต่างกัน — เลือกวิธีที่เหมาะกับโจทย์ เช่น ระบบที่ต้องอธิบายเหตุผลได้ "
      "ใช้ถ่วงน้ำหนัก/ผสม, ระบบที่มีคะแนนดาวใช้วิธีที่ 5")"""


PY[19] = """rows = []
for u in USERS:
    top = run(driver, Q_RECO_WEIGHTED, user=u["user"])[:3]
    rows.append({"ผู้ใช้": u["user"], "กลุ่มรสนิยม": u["group"],
                 "คำแนะนำ 3 อันดับ": " | ".join(r["brand"] + " " + r["model"][:18] +
                                                " (" + str(r["score"]) + ")" for r in top)})
display(pd.DataFrame(rows))

Q_POPULAR = '''
MATCH (p:Phone)<-[:LIKES]-(u:User)
RETURN p.phone_id AS phone_id, p.model AS model, p.brand AS brand, count(u) AS likes
ORDER BY likes DESC, model LIMIT 5
'''
popular = run(driver, Q_POPULAR)
show_cards(popular, title="Baseline: 5 รุ่นยอดนิยมในระบบ (แนะนำแบบไม่ดูว่าใครเป็นใคร)")
print("ทุกคนจะได้ลิสต์เดียวกัน = ไม่เฉพาะบุคคล ระบบของเราจึงดูที่ความคล้ายของแต่ละคนแทน")"""

# ------------------------------------------------------------------ cold start
MD[20] = """## 🧊 Cold start: ผู้ใช้ใหม่ที่สนใจรุ่นเดียว (ที่ยังไม่มีใครสนใจ)

เพิ่มผู้ใช้ใหม่ที่สนใจแค่รุ่นเดียว **และรุ่นนั้นยังไม่มีใครในระบบสนใจเลย**
กรณีนี้สัญญาณจาก "เพื่อน" (collaborative filtering) จะว่างเปล่า แต่ระบบของเรายังแนะนำได้
เพราะใช้ **ยี่ห้อและระดับราคา** (โหนด `Brand` / `Tier`) เป็นสัญญาณสำรอง"""

PY[21] = """NEW_USER = "ผู้ใช้ใหม่"
NEW_PHONE = "P99"

run(driver, "MERGE (u:User {user: $user}) SET u.age = 18, u.group = 'ทดลอง', u.node_type = 'user'",
    user=NEW_USER)
run(driver, '''
    MERGE (p:Phone {phone_id: $phone_id})
    SET p.model = $model, p.brand = $brand, p.tier = $tier, p.image = $image,
        p.node_type = 'phone'
    WITH p MERGE (b:Brand {name: $brand}) MERGE (p)-[:BY_BRAND]->(b)
    WITH p MERGE (t:Tier {name: $tier})   MERGE (p)-[:IN_TIER]->(t)
''', phone_id=NEW_PHONE, model="Galaxy S25 (รุ่นใหม่)", brand="Samsung", tier="เรือธง",
     image="phones/galaxy-s25.jpg")
run(driver, '''
    MATCH (u:User {user: $user}) MATCH (p:Phone {phone_id: $phone_id})
    MERGE (u)-[:LIKES]->(p)
''', user=NEW_USER, phone_id=NEW_PHONE)

cold_votes = run(driver, Q_RECO_VOTES, user=NEW_USER)
cold_content = run(driver, Q_RECO_CONTENT, user=NEW_USER)
print("ผู้ใช้ใหม่สนใจแค่ 1 รุ่น: Samsung Galaxy S25 (เรือธง) และยังไม่มีใครอื่นสนใจรุ่นนี้")
print("คำแนะนำจากสัญญาณเพื่อน   :", [r["model"] for r in cold_votes] or "ว่างเปล่า (cold start จริง)")
print("คำแนะนำจากยี่ห้อ/ราคา    :", [r["brand"] + " " + r["model"] for r in cold_content][:4])
show_cards(cold_content[:3],
           title="ระบบยังแนะนำได้ เพราะใช้โหนด Brand (Samsung) และ Tier (เรือธง) แทน")"""

# ------------------------------------------------------------------ summary
MD[22] = """## 🧠 สรุป

**สิ่งที่ทำในงานนี้**
1. ออกแบบข้อมูลชุดของตัวเอง: {NU} ผู้ใช้ × {NP} รุ่นมือถือ ({NB} ยี่ห้อ / {NT} ระดับราคา) × {NL} ความสนใจ + ภาพสินค้าจริง
2. ออกแบบโครงสร้างกราฟ `(User)-[:LIKES]->(Phone)`, `-[:RATED {stars}]->(Phone)`, `-[:BY_BRAND]->(Brand)`, `-[:IN_TIER]->(Tier)` และโหลดเข้า Neo4j
3. สร้างระบบแนะนำ **5 วิธี** (นับโหวต · ถ่วงน้ำหนัก Jaccard · ยี่ห้อ/ราคา · ผสม · ถ่วงด้วยคะแนนดาว)
   และ **แสดงภาพสินค้าจริงในการ์ดคำแนะนำทุกใบ**
4. ทดสอบ cold start, เทียบกับ baseline ยอดนิยม และยืนยันว่าคำแนะนำอธิบายย้อนหลังได้

**ข้อดีของวิธีนี้**
- ทำงานได้แม้ไม่มีคะแนนดาว (ใช้แค่ "ใครสนใจรุ่นไหน") และถ้ามีคะแนนดาวก็ใช้เป็นสัญญาณที่ 5 เพิ่มความแม่นได้
- อธิบายย้อนหลังได้ทุกคำแนะนำ (อ้างชื่อเพื่อนและรุ่นที่สนใจร่วมกัน)
- เพิ่มผู้ใช้/รุ่นใหม่แล้วได้คำแนะนำใหม่ทันที ไม่ต้องเทรนโมเดลใหม่ (ดูเซลล์ cold start)
- Cypher จัดการเรื่องนับซ้ำให้เองด้วย `count(DISTINCT ...)`

**ข้อจำกัด**
- ข้อมูล {NL} ความสนใจยังน้อย (ปัญหา sparsity) ถ้าเก็บจากผู้ใช้จริงจะแม่นขึ้น
- ไม่ได้ใช้สเปกเครื่อง (RAM/กล้อง/แบตเตอรี่) เป็นสัญญาณ จึงยังไม่ตอบโจทย์ "รุ่นไหนกล้องดีสุด"
- ระดับราคาแบ่งหยาบเพียง 3 ระดับ ถ้าเพิ่มช่วงงบเป็นตัวเลขจริงจะแนะนำได้ตรงใจกว่า

**ตัวระบบจริง (สาธิตการใช้งาน)**
แอป **Streamlit** ต่อ Neo4j มี **6 หน้า** (โครงเดียวกับงานตัวอย่างในวิชา แต่เป็นโดเมนมือถือ):
**Dashboard** ภาพรวม + กราฟสถิติ · **Recommendations** การ์ดคำแนะนำมีภาพสินค้าจริง +
ตาราง Jaccard · **Phone Search** ค้นหา/กรองตามยี่ห้อและระดับราคา · **Like & Rate**
เพิ่ม/ลบความสนใจและให้คะแนนดาว แล้วเห็นคำแนะนำเปลี่ยนทันที (ก่อน–หลัง) ·
**Graph Explorer** วาดกราฟ + ดูตาราง edge + รัน Cypher เองได้ · **Admin & Setup**
โครงสร้างกราฟ + ปุ่มรีโหลดข้อมูลแบบ idempotent + ดาวน์โหลด CSV

รันด้วยคำสั่ง `streamlit run app.py` — โค้ดอยู่ใน GitHub: https://github.com/Nasak16/phone-recommender"""

PY[23] = """# เก็บกวาดข้อมูลทดลอง แล้วตรวจว่าฐานข้อมูลกลับสู่สภาพเดิม
run(driver, "MATCH (p:Phone {phone_id: $phone_id}) DETACH DELETE p", phone_id=NEW_PHONE)
run(driver, "MATCH (u:User {user: $user}) DETACH DELETE u", user=NEW_USER)

final = (run(driver, Q_STATS) or [{}])[0]
print("ลบผู้ใช้และรุ่นทดลองแล้ว — สถานะสุดท้าย:", final)
assert (final["users"], final["phones"], final["likes"], final["ratings"]) == \
       ({NU}, {NP}, {NL}, {NR}), "ข้อมูลไม่กลับสู่สภาพเดิม"
print("ตรวจแล้ว: กลับมาครบ {NU} ผู้ใช้ / {NP} รุ่น / {NL} ความสนใจ / {NR} คะแนนดาว"
      " เหมือนก่อนทดลอง cold start")
driver.close()
print("ปิดการเชื่อมต่อเรียบร้อย")"""


PLACEHOLDERS = {"{NU}": len(users), "{NP}": len(phones), "{NL}": len(likes),
                "{NR}": len(ratings),
                "{NB}": len({p["brand"] for p in phones}),
                "{NT}": len({p["tier"] for p in phones})}


def R(txt):
    for k, v in PLACEHOLDERS.items():
        txt = txt.replace(k, str(v))
    return txt


def build():
    cells = []
    for i in sorted(set(MD) | set(PY)):
        if i in MD:
            cells.append({"cell_type": "markdown", "metadata": {},
                          "source": R(MD[i]).splitlines(keepends=True)})
        if i in PY:
            txt = R(PY[i])
            assert '"""' not in txt, "cell %d contains triple quotes" % i
            if TEST and i == 1:
                txt = (txt.replace('URI = "neo4j+s://<รหัส-instance>.databases.neo4j.io"',
                                   'URI = "bolt://127.0.0.1:7687"')
                          .replace('PASSWORD = getpass.getpass("Neo4j password: ")',
                                   'PASSWORD = "bookrec007"   # สำเนาทดสอบในเครื่อง')
                          .replace('DATABASE = "neo4j"', 'DATABASE = "phones"'))
            cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                          "outputs": [], "source": txt.splitlines(keepends=True)})
    nb = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("wrote %s (%d cells)" % (OUT, len(cells)))


if __name__ == "__main__":
    build()