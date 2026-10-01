#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ระบบแนะนำมือถือ (Phone Recommender System) — Neo4j + Streamlit
รหัส 007 · งาน: พัฒนาระบบแนะนำเป็นระบบของตัวเอง

รัน: streamlit run app.py
"""
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "data"))

st.set_page_config(page_title="ระบบแนะนำมือถือ | Neo4j + Streamlit", page_icon="📱",
                   layout="wide")


def _secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return os.environ.get(key, default)


@st.cache_resource(show_spinner="กำลังเชื่อมต่อฐานข้อมูลกราฟ…")
def get_engine():
    """ใช้ Neo4j ก่อน ถ้าต่อไม่ได้ให้ใช้ backend สำรองในหน่วยความจำ (ข้อมูลชุดเดียวกัน)"""
    from recommender import PhoneRecommender
    from graph_fallback import from_files

    uri = _secret("NEO4J_URI", os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"))
    user = _secret("NEO4J_USER", os.environ.get("NEO4J_USER", "neo4j"))
    pw = _secret("NEO4J_PASSWORD", os.environ.get("NEO4J_PASSWORD", ""))
    db = _secret("NEO4J_DATABASE", os.environ.get("NEO4J_DATABASE", None))
    try:
        eng = PhoneRecommender(uri, user, pw, database=db)
        eng.stats()
        return eng, "neo4j", f"Neo4j ({uri}{' · db ' + db if db else ''})"
    except Exception as e:
        return from_files(), "local", f"โหมดสำรองในหน่วยความจำ (ต่อ Neo4j ไม่ได้: {type(e).__name__})"


@st.cache_resource(show_spinner=False)
def thai_font():
    import graph_view
    return graph_view.thai_font(ROOT)


@st.cache_data(show_spinner=False)
def display_names():
    """ชื่อรุ่นสำหรับแสดงผล + ภาพการ์ดขนาดเท่ากัน (จากข้อมูลชุดเดียวกับกราฟ)"""
    import seed_data
    names, cards = {}, {}
    for p in seed_data.load_phones():
        names[p["phone_id"]] = p["display"]
        card = os.path.join(ROOT, "assets", "cards",
                            os.path.splitext(os.path.basename(p["image"]))[0] + ".jpg")
        cards[p["phone_id"]] = card if os.path.exists(card) else os.path.join(ROOT, p["image"])
    return names, cards


NAMES, CARDS = display_names()


def dname(pid):
    return NAMES.get(pid) or pid


def image_source(row):
    """ภาพการ์ดในโปรเจกต์ก่อน (ออฟไลน์ก็เห็นภาพ) ถ้าไม่มีค่อยใช้ไฟล์ต้นฉบับ"""
    pid = row.get("phone_id")
    if pid and CARDS.get(pid) and os.path.exists(CARDS[pid]):
        return CARDS[pid]
    rel = row.get("image") or ""
    p = os.path.join(ROOT, rel)
    return p if rel and os.path.exists(p) else None


def show_phone(row, width=150):
    src = image_source(row)
    if src:
        st.image(src, width=width)
    else:
        st.info("ไม่มีภาพ")


engine, backend, backend_label = get_engine()
stat = engine.stats()

with st.sidebar:
    st.markdown("## 📱 ระบบแนะนำมือถือ")
    st.caption("Neo4j (กราฟ) + Streamlit · รหัส 007")
    if backend == "neo4j":
        st.success("ฐานข้อมูล: " + backend_label, icon="🗄️")
    else:
        st.warning(backend_label, icon="⚠️")
    st.metric("ผู้ใช้ในระบบ", stat["users"])
    c1, c2, c3 = st.columns(3)
    c1.metric("รุ่นมือถือ", stat["phones"])
    c2.metric("ความสนใจ", stat["likes"])
    c3.metric("ยี่ห้อ", stat["brands"])

    users = engine.users()
    who = st.selectbox("เลือกผู้ใช้ที่จะแนะนำมือถือให้", users,
                       index=users.index("สมชาย") if "สมชาย" in users else 0)
    mode = st.radio("วิธีให้คะแนน", [
        "ถ่วงน้ำหนัก (Jaccard)",
        "นับโหวตเพื่อน",
        "ตามยี่ห้อ/ราคา",
        "ผสม: เพื่อน + ยี่ห้อ",
    ])
    top_n = st.slider("จำนวนที่แนะนำ", 1, 8, 3)
    st.divider()
    st.caption("อัลกอริทึม: Collaborative Filtering บนกราฟ (เดิน 3 hop) + "
               "Content-based ผ่านโหนด Brand/Tier")

MODE = {"ถ่วงน้ำหนัก (Jaccard)": "weighted", "นับโหวตเพื่อน": "votes",
        "ตามยี่ห้อ/ราคา": "content", "ผสม: เพื่อน + ยี่ห้อ": "hybrid"}[mode]

recs = {"weighted": engine.recommend_weighted, "votes": engine.recommend_votes,
        "content": engine.recommend_content, "hybrid": engine.recommend_hybrid}[MODE](who, top_n)

st.title("📱 ระบบแนะนำมือถือ")
st.caption(f"คำแนะนำสำหรับ **{who}** · วิธี: **{mode}** · "
           f"แสดง {len(recs)} รุ่นจาก {stat['phones']} รุ่นในระบบ")

tabs = st.tabs(["🎯 แนะนำมือถือ", "📱 คลังรุ่นทั้งหมด", "🕸️ โครงสร้างกราฟ",
                "🧪 เดโมสด: เพิ่มความสนใจ", "ℹ️ เกี่ยวกับระบบ"])

# ---------------------------------------------------------------- tab 1
with tabs[0]:
    liked = engine.liked_phones(who)
    left, right = st.columns([1.05, 3])
    with left:
        st.markdown("#### สนใจอยู่แล้ว")
        st.caption(f"รุ่นที่ {who} สนใจ — จุดเริ่มของกราฟ ({len(liked)} รุ่น)")
        for p in liked:
            with st.container(border=True):
                cc1, cc2 = st.columns([1, 2.4], vertical_alignment="center")
                with cc1:
                    show_phone(p, width=105)
                with cc2:
                    st.markdown(f"**{dname(p['phone_id'])}**")
                    st.caption(f"ระดับราคา: {p['tier']}")
    with right:
        if not recs:
            st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้ (ข้อมูลน้อยเกินไป — cold start)")
        else:
            st.markdown("#### รุ่นที่ระบบแนะนำ")
            st.caption(f"คัดจาก {stat['phones']} รุ่นที่ {who} ยังไม่เคยสนใจ — "
                       f"เรียงตามคะแนนของวิธี “{mode}”")
            cols = st.columns(3)
            for i, r in enumerate(recs):
                with cols[i % 3]:
                    with st.container(border=True):
                        show_phone(r, width=180)
                        st.markdown(f"**{dname(r['phone_id'])}**")
                        st.caption(f"ระดับราคา: {r.get('tier','')}")
                        if MODE == "votes":
                            st.markdown(f"🔢 **{r['votes']} โหวต** จาก " + ", ".join(r["voters"]))
                        elif MODE == "content":
                            st.markdown(f"🏷️ ยี่ห้อตรง **{r.get('brand','')}** · "
                                        f"ระดับราคาตรง **{r.get('tier','')}**")
                        else:
                            st.markdown(f"⭐ คะแนน **{r['score']}**")
                            if r.get("voters"):
                                st.caption("เพื่อนที่สนใจ: " + ", ".join(r["voters"]))
                        if r.get("via_phones"):
                            st.caption("เพราะคุณสนใจ: " + ", ".join(r["via_phones"]))

    st.divider()
    st.markdown("#### ใครมีรสนิยมใกล้ " + who + " (Jaccard similarity)")
    sims = engine.similar_users(who)
    if sims:
        st.dataframe([{"ผู้ใช้": s["user"], "สนใจร่วมกัน (รุ่น)": s["common_count"],
                       "รุ่นที่สนใจร่วม": ", ".join(dname(pid) for pid in s["common"]),
                       "Jaccard": round(s["jaccard"], 3)} for s in sims],
                     hide_index=True)
    st.caption("Jaccard = |รุ่นที่สนใจร่วมกัน| ÷ |รุ่นทั้งหมดของสองคน| "
               "→ ยิ่งใกล้ 1 ยิ่งรสนิยมเหมือนกัน น้ำหนักโหวตของคนนั้นยิ่งมาก")

# ---------------------------------------------------------------- tab 2
with tabs[1]:
    st.markdown("#### รุ่นมือถือทั้งหมดในระบบ")
    phones = engine.phones()
    brands = sorted({p["brand"] for p in phones})
    c1, c2 = st.columns([2, 2])
    q = c1.text_input("ค้นหา (รุ่น / ยี่ห้อ / ระดับราคา)", "")
    pick = c2.selectbox("กรองตามยี่ห้อ", ["ทั้งหมด"] + brands)
    view = [p for p in phones
            if (pick == "ทั้งหมด" or p["brand"] == pick)
            and (not q or q.lower() in p["model"].lower() or q.lower() in p["brand"].lower()
                 or q.lower() in p["tier"].lower())]
    st.caption(f"พบ {len(view)} รุ่น")
    for i in range(0, len(view), 5):
        cols = st.columns(5)
        for c, p in zip(cols, view[i:i + 5]):
            with c, st.container(border=True):
                show_phone(p, width=150)
                st.markdown(f"**{dname(p['phone_id'])}**")
                st.caption(f"{p['brand']} · {p['tier']}")
                st.caption(f"❤️ {p['likes']} คนสนใจ")
    st.caption("ภาพสินค้าดึงจาก Wikimedia Commons แล้วเก็บไว้ในโปรเจกต์ (assets/phones) "
               "จึงแสดงได้แม้ไม่มีอินเทอร์เน็ต")

# ---------------------------------------------------------------- tab 3
with tabs[2]:
    import graph_view
    import matplotlib.pyplot as plt

    st.markdown("#### กราฟความสัมพันธ์ (ผู้ใช้ ↔ รุ่นมือถือ)")
    st.caption("โหนดส้ม = ผู้ใช้ที่เลือก · ฟ้า = ผู้ใช้รสนิยมใกล้ · เหลือง = รุ่นที่สนใจแล้ว · "
               "เขียว = รุ่นที่ระบบแนะนำ · เส้นประเขียว = เส้นทาง 3 hop")
    fig = graph_view.draw(engine, who, recs, font=thai_font(),
                          title=f"กราฟคำแนะนำสำหรับ {who} · {mode}")
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("##### เส้นทางการตัดสินใจของคำแนะนำอันดับ 1")
    if recs:
        r = recs[0]
        via = r.get("via_phones") or [f"(ยี่ห้อ {r.get('brand')} / ระดับ {r.get('tier')})"]
        voters = r.get("voters") or ["(ตรงกับยี่ห้อ/ระดับราคาที่ชอบ)"]
        st.markdown(f"""
        ```
        {who} ──สนใจ──► {", ".join(via)}
                          │
                          ▼  มีคนสนใจรุ่นเดียวกัน (รสนิยมใกล้กัน)
        {", ".join(voters)}
                          │
                          ▼  คนกลุ่มนี้สนใจรุ่นอื่นที่ {who} ยังไม่สนใจ
        แนะนำ ► {r['brand']} {r['model']}
        ```
        """)

# ---------------------------------------------------------------- tab 4
with tabs[3]:
    st.markdown("#### เดโมสด: เพิ่มรุ่นที่สนใจ แล้วดูว่าคำแนะนำเปลี่ยนทันที")
    st.caption("แก้ข้อมูลในฐานข้อมูลกราฟจริง แล้วคำนวณใหม่ทันที — ไม่ต้องเทรนโมเดลใหม่")
    state = st.session_state.get("before")
    allphones = engine.phones()
    cc1, cc2, cc3 = st.columns([2, 2, 1])
    with cc1:
        pick = st.selectbox("เลือกให้ " + who + " สนใจรุ่นนี้",
                            [f"{p['phone_id']} · {p['brand']} {p['model']}" for p in allphones])
    with cc2:
        st.write("ผลก่อน–หลังจะแสดงด้านล่าง")
    with cc3:
        if st.button("➕ เพิ่มความสนใจ"):
            st.session_state["before"] = {"recs": engine.recommend_weighted(who, top_n)}
            engine.add_like(who, pick.split(" · ")[0])
            st.rerun()
    if state:
        now = engine.recommend_weighted(who, top_n)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**ก่อนเพิ่ม**")
            st.dataframe([{"รุ่น": f"{r['brand']} {r['model']}", "คะแนน": r["score"]}
                          for r in state["recs"]], hide_index=True)
        with c2:
            st.markdown("**หลังเพิ่ม**")
            st.dataframe([{"รุ่น": f"{r['brand']} {r['model']}", "คะแนน": r["score"]}
                          for r in now], hide_index=True)
        changed = [f"{r['brand']} {r['model']}" for r in now
                   if r["phone_id"] not in [x["phone_id"] for x in state["recs"]]]
        st.success("รุ่นที่โผล่ใหม่หลังเพิ่มข้อมูล: " + (", ".join(changed) or "ไม่เปลี่ยน"))
    st.divider()
    st.markdown("##### แก้ข้อมูลตั้งต้นของ " + who)
    for p in engine.liked_phones(who):
        b1, b2 = st.columns([4, 1])
        b1.write(f"❤️ {p['brand']} {p['model']}")
        if b2.button("ลบ", key="del_" + p["phone_id"]):
            engine.remove_like(who, p["phone_id"])
            st.rerun()

# ---------------------------------------------------------------- tab 5
with tabs[4]:
    st.markdown("#### ระบบนี้ทำงานอย่างไร")
    st.markdown(f"""
**สถาปัตยกรรม** — ข้อมูลเก็บใน **Neo4j** (ฐานข้อมูลกราฟ) มี 4 ชนิดโหนด:
`User` ({stat['users']} คน) · `Phone` ({stat['phones']} รุ่น) · `Brand` ({stat['brands']} ยี่ห้อ) ·
`Tier` ({stat['tiers']} ระดับราคา) และ 3 ชนิดความสัมพันธ์: `LIKES` ({stat['likes']} เส้น),
`BY_BRAND`, `IN_TIER`

**การทำงานของระบบแนะนำ (เดิน 3 hop)**
1. `(ผู้ใช้)-[:LIKES]->(รุ่นมือถือ)` — ดูว่าผู้ใช้สนใจรุ่นไหน
2. `(รุ่น)<-[:LIKES]-(คนอื่น)` — หาคนที่สนใจรุ่นเดียวกัน = รสนิยมใกล้กัน
3. `(คนอื่น)-[:LIKES]->(รุ่นใหม่)` — เก็บรุ่นที่ผู้ใช้ยังไม่สนใจ แล้วจัดอันดับ

**สูตรให้คะแนน**
- นับโหวต: `คะแนน = จำนวนคนที่สนใจรุ่นนั้น` (ใช้ `count(DISTINCT other)` → 1 คน = 1 เสียง)
- ถ่วงน้ำหนัก: `คะแนน = Σ Jaccard(เรา, คนนั้น)`, `Jaccard = |สนใจร่วม| ÷ |รุ่นของสองคนรวมกัน|`
- ตามยี่ห้อ/ราคา: นับรุ่นที่เราเคยสนใจซึ่งใช้ **ยี่ห้อ** เดียวกัน และอยู่ **ระดับราคา** เดียวกัน
- ผสม: `0.6 × (คะแนนเพื่อน normalize) + 0.4 × (คะแนนยี่ห้อ/ราคา normalize)`

**ทำไมต้องมีโหนด Brand/Tier** — ช่วยแก้ cold start: ผู้ใช้ใหม่ที่ยังไม่มีความคล้ายกับใคร
ยังได้คำแนะนำจากยี่ห้อและระดับราคาที่ตัวเองสนใจ (เช่น งบระดับกลางก็ไม่ต้องแนะนำเรือธง)
    """)
    st.markdown("##### สถานะการเชื่อมต่อ")
    st.write(f"- backend ที่ใช้อยู่: **({'Neo4j' if backend == 'neo4j' else 'หน่วยความจำสำรอง'})** "
             f"· {backend_label}")
    st.write("- ตรวจว่าสอง backend ให้ผลตรงกัน: `py -3.13 tools/consistency_test.py <uri> "
             "neo4j <password>`")

st.divider()
st.caption("ระบบแนะนำมือถือ · จัดทำโดย รหัส 007 · ภาพสินค้าจาก Wikimedia Commons · "
           "กราฟ: Neo4j · ส่วนติดต่อผู้ใช้: Streamlit")
