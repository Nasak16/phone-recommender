#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ระบบแนะนำมือถือ (Phone Recommender System) — Neo4j + Streamlit
รหัส 007 · งาน: พัฒนาระบบแนะนำเป็นระบบของตัวเอง

เมนู 6 หน้า (โครงเดียวกับงานตัวอย่างในวิชา — ทำเป็นโดเมนมือถือและเพิ่มของที่มากกว่า)
  Dashboard / Recommendations / Phone Search / Like & Rate / Graph Explorer / Admin & Setup

รัน: streamlit run app.py   (ไม่ตั้งค่า Neo4j ก็รันได้ → โหมดสาธิตในหน่วยความจำ)
"""
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
import theme  # noqa: E402  (ธีม dark neon + ฟอนต์ไทย)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "data"))

st.set_page_config(page_title="ระบบแนะนำมือถือ | Neo4j + Streamlit", page_icon="📱",
                   layout="wide")
theme.inject()

PAGES = ["Dashboard", "Recommendations", "Phone Search", "Like & Rate",
         "Graph Explorer", "Index & Links", "Admin & Setup"]
PAGE_TH = {"Dashboard": "ภาพรวมระบบ", "Recommendations": "แนะนำมือถือ",
           "Phone Search": "ค้นหารุ่นมือถือ", "Like & Rate": "ถูกใจ / ให้คะแนน",
           "Graph Explorer": "สำรวจโครงสร้างกราฟ", "Index & Links": "งานทั้งหมด (Index)",
           "Admin & Setup": "ผู้ดูแลระบบ"}
METHODS = {
    "ถ่วงน้ำหนัก (Jaccard)": "weighted",
    "นับโหวตเพื่อน": "votes",
    "ตามยี่ห้อ/ระดับราคา": "content",
    "เพื่อน + ยี่ห้อ/ราคา (ผสม)": "hybrid",
    "ถ่วงด้วยคะแนนดาว": "rated",
}


def _secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return os.environ.get(key, default)


def get_engine():
    """เลือก backend อัตโนมัติ

    1) ถ้ามีการตั้งค่า Neo4j (secrets/env) → ต่อ Neo4j จริง
    2) ถ้าไม่มี/ต่อไม่ได้ → โหมดสาธิตในหน่วยความจำ **แยกต่อผู้เข้าชม 1 คน**
    """
    uri = _secret("NEO4J_URI", os.environ.get("NEO4J_URI", "")) or ""
    user = _secret("NEO4J_USER", os.environ.get("NEO4J_USER", "neo4j"))
    pw = _secret("NEO4J_PASSWORD", os.environ.get("NEO4J_PASSWORD", "")) or ""
    db = _secret("NEO4J_DATABASE", os.environ.get("NEO4J_DATABASE", None))

    if uri and pw:
        from recommender import PhoneRecommender
        try:
            with st.spinner("กำลังเชื่อมต่อฐานข้อมูลกราฟ Neo4j…"):
                eng = PhoneRecommender(uri, user, pw, database=db)
                eng.stats()
            return eng, "neo4j", f"Neo4j ({uri}{' · db ' + db if db else ''})"
        except Exception as e:
            st.session_state["neo4j_error"] = type(e).__name__
    elif uri:
        st.session_state["neo4j_error"] = "ไม่มีรหัสผ่าน NEO4J_PASSWORD"

    from graph_fallback import from_files
    if "engine" not in st.session_state:
        st.session_state["engine"] = from_files()
    err = st.session_state.get("neo4j_error")
    note = ("โหมดสาธิตออนไลน์ · ข้อมูลชุดเดียวกับที่โหลดเข้า Neo4j "
            "(ในหน่วยความจำของเซสชันคุณ" + (" · ต่อ Neo4j ไม่ได้: " + err if err else "") + ")")
    return st.session_state["engine"], "local", note


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


@st.cache_resource(show_spinner=False)
def thai_font():
    import graph_view
    return graph_view.thai_font(ROOT)


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


def stars_text(rating_map, pid):
    s = rating_map.get(pid)
    return f"⭐ {s['avg_stars']:.2f} ({s['n_raters']} คน)" if s else "⭐ ยังไม่มีคะแนน"


def card(row, img_w=170, ratings=None, lines=None):
    """การ์ดมือถือ: ภาพสินค้าจริง + ชื่อรุ่น + ระดับราคา + ดาว + เหตุผลของคำแนะนำ"""
    with st.container(border=True):
        show_phone(row, width=img_w)
        st.markdown(f"**{dname(row['phone_id'])}**")
        st.caption(f"{row.get('tier','')} · {stars_text(ratings or {}, row['phone_id'])}")
        for ln in (lines or []):
            st.markdown(ln)


engine, backend, backend_label = get_engine()
stat = engine.stats()
RATINGS = engine.rating_stats()

USERS = engine.users()
DEFAULT_USER = "สมชาย" if "สมชาย" in USERS else (USERS[0] if USERS else "")

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("## 📱 Phone Recommender")
    st.caption("Neo4j (Graph DB) + Streamlit · รหัส 007")
    st.markdown(
        """<div style="display:flex;gap:10px;align-items:center;margin:6px 0 10px 0">
        <div style="width:46px;height:46px;border-radius:50%;background:#FF8833;color:#0E1626;
        display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px">
        N</div><div><b>Nasak16</b><br><span style="color:#9FB0CB;font-size:12px">
        ผู้ดูแลระบบ</span></div></div>""", unsafe_allow_html=True)
    page = st.radio("เมนู", PAGES, format_func=lambda p: f"{p} · {PAGE_TH[p]}")
    st.divider()
    if backend == "neo4j":
        st.success("ฐานข้อมูล: " + backend_label, icon="🗄️")
    else:
        st.info(backend_label, icon="🧪")
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("ผู้ใช้", stat["users"])
    r1c2.metric("รุ่นมือถือ", stat["phones"])
    r2c1, r2c2 = st.columns(2)
    r2c1.metric("ความสนใจ (LIKES)", stat["likes"])
    r2c2.metric("คะแนนดาว (RATED)", stat.get("ratings", 0))
    r3c1, r3c2 = st.columns(2)
    r3c1.metric("ยี่ห้อ", stat["brands"])
    r3c2.metric("ระดับราคา", stat["tiers"])
    st.divider()
    st.caption("ข้อมูลของเราเอง 12 คน × 23 รุ่น พร้อมภาพสินค้าจริง "
               "(ไม่ใช้ dataset สำเร็จรูป)")

theme.hero()

# ------------------------------------------------------------------ 1. Dashboard
if page == "Dashboard":
    st.subheader("📊 ภาพรวมระบบ (Dashboard)")
    cols = st.columns(6)
    for col, (v, l) in zip(cols, [(stat["users"], "ผู้ใช้"), (stat["phones"], "รุ่นมือถือ"),
                                  (stat["likes"], "ความสนใจ (LIKES)"),
                                  (stat.get("ratings", 0), "คะแนนดาว (RATED)"),
                                  (stat["brands"], "ยี่ห้อ"), (stat["tiers"], "ระดับราคา")]):
        col.metric(l, v)
    st.divider()

    left, right = st.columns([1.1, 1])
    with left:
        who = st.selectbox("ดูโปรไฟล์ผู้ใช้", USERS, index=USERS.index(DEFAULT_USER),
                           key="dash_user")
        import seed_data
        prof = next((u for u in seed_data.USERS if u["user"] == who), {})
        liked = engine.liked_phones(who)
        sims = engine.similar_users(who)
        st.markdown(f"### โปรไฟล์: {who}")
        st.write(f"**กลุ่มรสนิยม:** {prof.get('group','-')} · **อายุ:** {prof.get('age','-')} ปี")
        st.write(f"**สนใจแล้ว {len(liked)} รุ่น** · **คนรสนิยมใกล้ {len(sims)} คน**")
        rows = [{"รุ่น": dname(p["phone_id"]), "ระดับราคา": p["tier"],
                 "ดาวที่ให้": RATINGS.get(p["phone_id"], {}).get("avg_stars", "-")}
                for p in liked]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
    with right:
        st.markdown("### 10 รุ่นที่มีคนสนใจมากสุด")
        df = pd.DataFrame([{"รุ่น": dname(p["phone_id"]), "คนสนใจ": p["likes"]}
                           for p in engine.phones()[:10]])
        st.bar_chart(df.set_index("รุ่น"), height=280, color="#FF8833")
        st.markdown("### จำนวนรุ่นในแต่ละระดับราคา")
        tiers = pd.DataFrame(engine.phones())
        st.bar_chart(tiers.groupby("tier")["phone_id"].count(), height=200, color="#4CC9F0")

    st.divider()
    st.markdown(f"### คำแนะนำล่าสุดของ {who} (วิธีผสม)")
    cols = st.columns(4)
    for i, r in enumerate(engine.recommend_hybrid(who, 4)):
        with cols[i % 4]:
            card(r, img_w=170, ratings=RATINGS, lines=[f"⭐ คะแนน **{r.get('score')}**"])

# ------------------------------------------------------------------ 2. Recommendations
elif page == "Recommendations":
    st.subheader("✨ คำแนะนำมือถือ (Recommendations)")
    c1, c2, c3 = st.columns([1.3, 1.5, 1])
    with c1:
        who = st.selectbox("เลือกผู้ใช้", USERS, index=USERS.index(DEFAULT_USER), key="rec_user")
    with c2:
        mode = st.selectbox("วิธีให้คะแนน (เทียบได้ 5 วิธี)", list(METHODS))
    with c3:
        top_n = st.slider("จำนวนคำแนะนำ", 3, 8, 3)

    fn = {"weighted": engine.recommend_weighted, "votes": engine.recommend_votes,
          "content": engine.recommend_content, "hybrid": engine.recommend_hybrid,
          "rated": engine.recommend_rated}[METHODS[mode]]
    recs = fn(who, top_n)
    st.caption(f"คำแนะนำสำหรับ **{who}** · วิธี **{mode}** · {len(recs)} รุ่นจาก "
               f"{stat['phones']} รุ่นที่ระบบยังไม่เคยแนะนำให้คนนี้")

    left, right = st.columns([1, 2.7])
    with left:
        st.markdown("#### สนใจอยู่แล้ว")
        for p in engine.liked_phones(who):
            with st.container(border=True):
                cc1, cc2 = st.columns([1, 2.2], vertical_alignment="center")
                with cc1:
                    show_phone(p, width=100)
                with cc2:
                    st.markdown(f"**{dname(p['phone_id'])}**")
                    st.caption(f"{p['tier']} · {stars_text(RATINGS, p['phone_id'])}")
    with right:
        if not recs:
            st.info("ยังไม่มีคำแนะนำจากวิธีนี้ (ลองวิธีอื่น หรือเพิ่มความสนใจในหน้า Like & Rate)")
        else:
            st.markdown("#### รุ่นที่ระบบแนะนำ")
            for i in range(0, len(recs), 3):
                cols = st.columns(3)
                for col, r in zip(cols, recs[i:i + 3]):
                    lines = []
                    if r.get("score") is not None:
                        lines.append(f"⭐ คะแนน **{r['score']}**")
                    if r.get("votes"):
                        lines.append(f"🔢 {r['votes']} คนสนใจ")
                    if r.get("avg_stars"):
                        lines.append(f"🌟 ดาวจากคนที่สนใจ **{r['avg_stars']}**")
                    if r.get("brand_matches") is not None:
                        lines.append(f"🏷️ ยี่ห้อตรง **{r.get('brand_matches')}** · "
                                     f"ระดับราคาตรง **{r.get('tier_matches')}**")
                    if r.get("voters"):
                        lines.append("👥 " + ", ".join(r["voters"]))
                    if r.get("via_phones"):
                        lines.append("❤️ เพราะสนใจ " + ", ".join(r["via_phones"][:2]))
                    with col:
                        card(r, img_w=170, ratings=RATINGS, lines=lines)

    st.divider()
    st.markdown(f"#### ใครมีรสนิยมใกล้ {who} (Jaccard similarity)")
    sims = engine.similar_users(who)
    if sims:
        st.dataframe(pd.DataFrame([{"ผู้ใช้": s["user"], "สนใจร่วมกัน (รุ่น)": s["common_count"],
                                    "รุ่นที่สนใจร่วม": ", ".join(dname(p) for p in s["common"]),
                                    "Jaccard": round(s["jaccard"], 3)} for s in sims]),
                     hide_index=True)
    st.caption("Jaccard = |รุ่นที่สนใจร่วมกัน| ÷ |รุ่นของสองคนรวมกัน| → ยิ่งใกล้ 1 "
               "รสนิยมยิ่งเหมือน น้ำหนักโหวตของคนนั้นยิ่งมาก")

# ------------------------------------------------------------------ 3. Phone Search
elif page == "Phone Search":
    st.subheader("🔎 ค้นหารุ่นมือถือ (Phone Search)")
    phones = engine.phones()
    brands = ["ทั้งหมด"] + sorted({p["brand"] for p in phones})
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    q = c1.text_input("คำค้น (รุ่น / ยี่ห้อ)", placeholder="เช่น Galaxy, Xperia, Pixel, iPhone")
    b = c2.selectbox("ยี่ห้อ", brands)
    t = c3.selectbox("ระดับราคา", ["ทั้งหมด", "เรือธง", "ระดับกลาง", "ระดับเริ่มต้น"])
    sort_by = c4.selectbox("เรียงตาม", ["คนสนใจ", "ดาวเฉลี่ย", "ชื่อรุ่น"])

    view = [p for p in phones
            if (b == "ทั้งหมด" or p["brand"] == b)
            and (t == "ทั้งหมด" or p["tier"] == t)
            and (not q or q.lower() in dname(p["phone_id"]).lower()
                 or q.lower() in p["brand"].lower())]
    if sort_by == "ดาวเฉลี่ย":
        view.sort(key=lambda p: -RATINGS.get(p["phone_id"], {}).get("avg_stars", 0))
    elif sort_by == "ชื่อรุ่น":
        view.sort(key=lambda p: dname(p["phone_id"]))
    st.write(f"พบ **{len(view)}** รุ่น จากทั้งหมด {len(phones)} รุ่น")
    if not view:
        st.info("ไม่พบรุ่นที่ตรงเงื่อนไข — ลองล้างคำค้นหรือเลือกยี่ห้อ “ทั้งหมด”")
    for i in range(0, len(view), 5):
        cols = st.columns(5)
        for col, p in zip(cols, view[i:i + 5]):
            with col:
                card(p, img_w=150, ratings=RATINGS, lines=[f"❤️ **{p['likes']}** คนสนใจ"])
    st.caption("ภาพสินค้าดึงจาก Wikimedia Commons แล้วเก็บไว้ในโปรเจกต์ (assets/) "
               "จึงแสดงได้แม้ไม่มีอินเทอร์เน็ต")

# ------------------------------------------------------------------ 4. Like & Rate
elif page == "Like & Rate":
    st.subheader("📝 บันทึกความสนใจ / ให้คะแนน (Like & Rate)")
    st.caption("แก้ข้อมูลในฐานข้อมูลกราฟจริง (หรือข้อมูลในหน่วยความจำของเซสชันนี้) "
               "แล้วคำแนะนำเปลี่ยนทันที — ไม่ต้องเทรนโมเดลใหม่")
    who = st.selectbox("เลือกผู้ใช้", USERS, index=USERS.index(DEFAULT_USER), key="rate_user")
    liked = engine.liked_phones(who)
    liked_ids = {p["phone_id"] for p in liked}
    fresh = [p for p in engine.phones() if p["phone_id"] not in liked_ids]

    c1, c2 = st.columns([2, 1])
    with c1:
        pick = st.selectbox("รุ่นมือถือ (แสดงรุ่นที่ยังไม่สนใจก่อน)",
                            [f"{p['phone_id']} · {dname(p['phone_id'])}" for p in fresh])
        pid = pick.split(" · ")[0]
        stars = st.slider("ให้คะแนนดาว (ใช้เป็นสัญญาณที่ 5 ของระบบ)", 1.0, 5.0, 4.0, 0.5)
        b1, b2, b3 = st.columns(3)
        if b1.button("❤️ เพิ่มความสนใจ + ดาว", type="primary", use_container_width=True):
            st.session_state["rate_before"] = engine.recommend_weighted(who, 3)
            engine.add_like(who, pid)
            engine.add_rating(who, pid, stars)
            st.rerun()
        if b2.button("⭐ ให้คะแนนรุ่นนี้", use_container_width=True):
            engine.add_rating(who, pid, stars)
            st.success(f"บันทึกความสัมพันธ์ RATED {{stars: {stars}}} แล้ว")
        if b3.button("♻️ รีเฟรชผล", use_container_width=True):
            st.rerun()
    with c2:
        st.markdown("**สถานะปัจจุบัน**")
        st.write(f"- สนใจแล้ว **{len(liked)}** รุ่น")
        st.write(f"- ให้คะแนนแล้ว **{len([1 for p in liked if p['phone_id'] in RATINGS])}** รุ่น")
        st.write(f"- รุ่นที่ยังไม่สนใจในระบบ **{len(fresh)}** รุ่น")

    before = st.session_state.get("rate_before")
    if before is not None:
        now = engine.recommend_weighted(who, 3)
        b1, b2 = st.columns(2)
        with b1:
            st.markdown("**ก่อนเพิ่มความสนใจ**")
            st.dataframe(pd.DataFrame([{"รุ่น": dname(r["phone_id"]), "คะแนน": r["score"]}
                                       for r in before]), hide_index=True)
        with b2:
            st.markdown("**หลังเพิ่มความสนใจ**")
            st.dataframe(pd.DataFrame([{"รุ่น": dname(r["phone_id"]), "คะแนน": r["score"]}
                                       for r in now]), hide_index=True)
        new = [dname(r["phone_id"]) for r in now
               if r["phone_id"] not in [x["phone_id"] for x in before]]
        st.success("รุ่นที่โผล่ใหม่หลังเพิ่มข้อมูล: " + (", ".join(new) or "ไม่เปลี่ยน"))

    st.divider()
    st.markdown(f"#### รุ่นที่ {who} สนใจ — ลบได้")
    for i in range(0, len(liked), 4):
        cols = st.columns(4)
        for col, p in zip(cols, liked[i:i + 4]):
            with col:
                with st.container(border=True):
                    show_phone(p, width=140)
                    st.markdown(f"**{dname(p['phone_id'])}**")
                    st.caption(f"{p['tier']} · {stars_text(RATINGS, p['phone_id'])}")
                    if st.button("🗑️ ลบความสนใจ", key="del_" + p["phone_id"],
                                 use_container_width=True):
                        engine.remove_like(who, p["phone_id"])
                        st.rerun()

# ------------------------------------------------------------------ 5. Graph Explorer
elif page == "Graph Explorer":
    import matplotlib.pyplot as plt
    import graph_view

    st.subheader("🕸️ สำรวจโครงสร้างกราฟ (Graph Explorer)")
    c1, c2 = st.columns([1, 2])
    who = c1.selectbox("โฟกัสที่ผู้ใช้", USERS, index=USERS.index(DEFAULT_USER), key="gx_user")
    mode = c2.radio("วิธีให้คะแนนที่ใช้ไฮไลต์",
                    ["ถ่วงน้ำหนัก (Jaccard)", "เพื่อน + ยี่ห้อ/ราคา (ผสม)"], horizontal=True)
    fn = engine.recommend_weighted if mode.startswith("ถ่วง") else engine.recommend_hybrid
    recs = fn(who, 3)

    left, right = st.columns([2.4, 1])
    with left:
        fig = graph_view.draw(engine, who, recs, font=thai_font(),
                              title=f"กราฟคำแนะนำสำหรับ {who} · {mode}")
        st.pyplot(fig)
        plt.close(fig)
        if recs:
            r = recs[0]
            via = r.get("via_phones") or [f"(ยี่ห้อ {r.get('brand')})"]
            voters = r.get("voters") or ["(ตรงกับยี่ห้อ/ระดับราคาที่ชอบ)"]
            st.markdown("##### เส้นทางการตัดสินใจของคำแนะนำอันดับ 1")
            st.code(f"""{who} ──สนใจ──► {", ".join(via)}
                  │
                  ▼  มีคนสนใจรุ่นเดียวกัน (รสนิยมใกล้กัน)
{", ".join(voters)}
                  │
                  ▼  คนกลุ่มนี้สนใจรุ่นอื่นที่ {who} ยังไม่สนใจ
แนะนำ ► {r['brand']} {r['model']}""", language="text")
    with right:
        st.markdown("**อ่านกราฟ**")
        st.write("- 🟠 ผู้ใช้ที่เลือก · 🔵 ผู้ใช้รสนิยมใกล้")
        st.write("- 🟡 รุ่นที่สนใจแล้ว · 🟢 รุ่นที่ระบบแนะนำ")
        st.write("- เส้นประเขียว = เส้นทาง 3 hop")
        st.divider()
        st.markdown("**ขนาดกราฟในระบบ**")
        st.write(f"- โหนด: {stat['users']} ผู้ใช้ · {stat['phones']} รุ่น · "
                 f"{stat['brands']} ยี่ห้อ · {stat['tiers']} ระดับราคา")
        st.write(f"- ความสัมพันธ์: {stat['likes']} LIKES · {stat.get('ratings',0)} RATED · "
                 f"{stat['phones'] * 2} BY_BRAND/IN_TIER")

    with st.expander("ดูข้อมูล edge ทั้งหมดในฐานข้อมูล (ความสัมพันธ์)"):
        df = pd.DataFrame(engine.graph_edges())
        st.write(f"รวม {len(df)} ความสัมพันธ์")
        st.dataframe(df, hide_index=True)

    st.divider()
    st.markdown("#### รันคำสั่ง Cypher เอง (อ่านข้อมูลเท่านั้น)")
    st.caption("ระบบบล็อกคำสั่งที่เขียนข้อมูล (CREATE / MERGE / DELETE / SET) — "
               "ใช้สาธิตการ query กราฟได้อย่างปลอดภัย")
    ex = {
        "ผู้ใช้ที่สนใจรุ่นนี้": "MATCH (u:User)-[:LIKES]->(p:Phone {phone_id:'P05'}) "
                              "RETURN u.user AS ผู้ใช้, p.model AS รุ่น ORDER BY u.user",
        "รุ่น + ดาวเฉลี่ย": "MATCH (p:Phone)<-[r:RATED]-() "
                          "RETURN p.model AS รุ่น, round(avg(r.stars)*100)/100.0 AS ดาวเฉลี่ย, "
                          "count(r) AS จำนวนคน ORDER BY ดาวเฉลี่ย DESC LIMIT 8",
        "ยี่ห้อที่มีคนสนใจรวมมากสุด": "MATCH (b:Brand)<-[:BY_BRAND]-(p:Phone)<-[:LIKES]-(u:User) "
                                 "RETURN b.name AS ยี่ห้อ, count(DISTINCT u) AS คน, "
                                 "count(DISTINCT p) AS รุ่น ORDER BY คน DESC LIMIT 5",
    }
    sel = st.selectbox("เลือกคำสั่งตัวอย่าง", list(ex))
    query = st.text_area("คำสั่ง Cypher", value=ex[sel], height=110)
    if st.button("▶️ รันคำสั่ง", type="primary"):
        if backend == "neo4j":
            try:
                rows = engine.run_readonly(query)
                st.success(f"ได้ {len(rows)} แถว")
                st.dataframe(pd.DataFrame(rows), hide_index=True)
            except Exception as e:
                st.error(f"รันไม่สำเร็จ: {e}")
        else:
            st.warning("โหมดสาธิต (ไม่มีเซิร์ฟเวอร์ Neo4j) ไม่สามารถรัน Cypher อิสระได้ — "
                       "คำสั่งนี้จะทำงานเมื่อตั้งค่า Neo4j ใน secrets "
                       "(ดู docs/deploy-streamlit-cloud.md)")

# ------------------------------------------------------------------ 6. Index (งานทั้งหมด)
elif page == "Index & Links":
    import homework_index as HW

    st.subheader("📚 งานทั้งหมดของเรา (Index)")
    st.caption("รวมทุกงานที่ส่งไว้บน GitHub — หน้า index หลักอยู่ที่ "
               f"[{HW.INDEX_URL}]({HW.INDEX_URL})")

    cats = {}
    for it in HW.HOMEWORK:
        cats.setdefault(it["category"], []).append(it)

    c1, c2, c3 = st.columns(3)
    c1.metric("งานทั้งหมด", len(HW.HOMEWORK))
    c2.metric("หมวดวิชา", len(cats))
    c3.metric("งานในวิชานี้ (ฐานข้อมูล)", len(cats.get("ฐานข้อมูล", [])))

    st.markdown("#### ⭐ งานล่าสุด: ระบบแนะนำมือถือ (ชิ้นนี้)")
    hub = [("📱", "ระบบแนะนำมือถือ (ชิ้นนี้)", "โค้ดทั้งหมดบน GitHub: Neo4j + Streamlit 7 หน้า",
            "https://github.com/Nasak16/phone-recommender", "เปิดโค้ด →",
            "phone-recommender · อัปเดต " + (HW.HOMEWORK[0]["date"] if HW.HOMEWORK else "")),
           ("📓", "โน๊ตบุ๊ก Colab", "อธิบายวิธีทำทีละขั้น + ผลลัพธ์จริงทุกเซลล์ (26 เซลล์)",
            "https://colab.research.google.com/gist/Nasak16/8667b219bbff8253335ec78f78b5c79e/PhoneRecommender_Neo4j_007.ipynb",
            "เปิดโน๊ตบุ๊ก →", "Colab · getpass"),
           ("📊", "สไลด์นำเสนอ 16 หน้า", "PowerPoint + PDF + PNG (อยู่ใน GitHub ตามโจทย์ข้อ 2)",
            "https://github.com/Nasak16/phone-recommender/tree/main/slides",
            "เปิดสไลด์ →", "slides/*.pptx · *.pdf"),
           ("🌐", "หน้า index รวมทุกงาน", "รวมงานทุกชิ้นที่ส่งไว้ (14 งาน) พร้อมลิงก์",
            HW.INDEX_URL, "เปิดหน้า index →", "nasak16.github.io/homework")]
    for i in range(0, len(hub), 4):
        cols = st.columns(4)
        for col, (ic, t, d, u, lb, tag) in zip(cols, hub[i:i + 4]):
            with col:
                st.markdown(theme.card_html(ic, t, d, u, lb, tag, height=210),
                            unsafe_allow_html=True)

    st.markdown("#### 🗂️ งานในวิชานี้ (ฐานข้อมูล)")
    db = cats.get("ฐานข้อมูล", [])
    for i in range(0, len(db), 2):
        cols = st.columns(2)
        for col, it in zip(cols, db[i:i + 3]):
            with col:
                url = it["extra"][0][1] if it["extra"] else it["url"]
                label = ("เปิด" + it["extra"][0][0].replace("📓 ", " ") + " →") if it["extra"] \
                    else "เปิดโค้ด →"
                st.markdown(theme.card_html(
                    "📘" if "book" in it["repo"] else ("🧪" if it["repo"] == "GrapDB1" else
                                                       ("📈" if it["repo"] == "grafanaDB" else "📱")),
                    it["title"], it["desc"], url, label,
                    f"{it['repo']} · อัปเดต {it['date']}" + (f" · +{len(it['extra'])} ลิงก์" if it["extra"] else ""),
                    height=250), unsafe_allow_html=True)

    st.markdown("#### 📚 งานหมวดอื่น")
    for cat, items in sorted(cats.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if cat == "ฐานข้อมูล":
            continue
        with st.expander(f"{cat} — {len(items)} งาน"):
            for it in items:
                st.markdown(f"- [{it['title']}]({it['url']}) · `{it['repo']}` · {it['date']}")
                if it["desc"]:
                    st.caption(it["desc"])

# ------------------------------------------------------------------ 7. Admin & Setup
else:
    import seed_data

    st.subheader("⚙️ ผู้ดูแลระบบ: ตรวจสอบและตั้งค่าข้อมูล (Admin & Setup)")
    st.write(f"**backend ที่ใช้อยู่:** {'Neo4j (ฐานข้อมูลกราฟจริง)' if backend == 'neo4j' else 'โหมดสาธิตในหน่วยความจำ'}"
             f" · {backend_label}")

    st.markdown("#### โครงสร้างกราฟ (schema)")
    st.code("""(User {user, age, group})
   │ [:LIKES]             → ความสนใจ (1 เส้น = 1 รุ่นที่สนใจ)
   │ [:RATED {stars}]     → คะแนนดาว 1.0–5.0
   ▼
(Phone {phone_id, model, brand, tier, image})
   │ [:BY_BRAND] → (Brand {name})
   │ [:IN_TIER]  → (Tier  {name})""", language="text")
    st.write(f"จำนวนปัจจุบัน: ผู้ใช้ {stat['users']} · รุ่น {stat['phones']} · "
             f"LIKES {stat['likes']} · RATED {stat.get('ratings',0)} · "
             f"ยี่ห้อ {stat['brands']} · ระดับราคา {stat['tiers']}")

    st.divider()
    st.markdown("#### สร้าง / รีเฟรชข้อมูลตัวอย่าง (idempotent — กดซ้ำได้)")
    st.caption("คำสั่งใช้ MERGE ทั้งหมด จึงรันซ้ำได้อย่างปลอดภัย เหมาะกับตอนสาธิตหน้าห้อง")
    c1, c2, c3 = st.columns(3)
    if c1.button("🔄 รีโหลดข้อมูลตัวอย่าง", type="primary", use_container_width=True):
        u, p, l = seed_data.graph_data()
        r = seed_data.ratings_data(p)
        try:
            if hasattr(engine, "ensure_constraints"):
                engine.ensure_constraints()
            engine.import_data(u, p, l, r)
            st.success(f"โหลดข้อมูลแล้ว: {len(u)} ผู้ใช้ / {len(p)} รุ่น / {len(l)} ความสนใจ / "
                       f"{len(r)} คะแนนดาว")
        except Exception as e:
            st.error(f"โหลดไม่สำเร็จ: {type(e).__name__}: {e}")
    if c2.button("🧹 ล้างโหนดที่ไม่มีเส้นเชื่อม", use_container_width=True):
        try:
            engine._run("MATCH (u:User) WHERE NOT (u)--() DELETE u")
            engine._run("MATCH (p:Phone) WHERE NOT (p)--() DETACH DELETE p")
            st.success("ลบโหนดที่ไม่มีเส้นเชื่อมแล้ว")
        except Exception as e:
            st.warning(f"โหมดสาธิตไม่รองรับการล้างข้อมูลด้วย Cypher ({type(e).__name__}) — "
                       f"ใช้ปุ่มรีเฟรชแทนได้")
    c3.download_button("⬇️ ดาวน์โหลดข้อมูลเป็น CSV",
                       data=pd.DataFrame([{"phone_id": p["phone_id"], "model": p["model"],
                                           "brand": p["brand"], "tier": p["tier"],
                                           "likes": p["likes"]}
                                          for p in engine.phones()]).to_csv(index=False),
                       file_name="phones_007.csv", mime="text/csv",
                       use_container_width=True)

    st.divider()
    st.markdown("#### ระบบนี้ทำงานอย่างไร (สำหรับผู้ตรวจ)")
    st.markdown(f"""
**เดิน 3 hop** — `(ผู้ใช้)-[:LIKES]->(รุ่น) <-[:LIKES]- (คนอื่น) -[:LIKES]-> (รุ่นใหม่)`

**วิธีให้คะแนน 5 วิธี**
1. **นับโหวต** — `count(DISTINCT other)` → 1 คน = 1 เสียง
2. **ถ่วงน้ำหนัก** — `Σ Jaccard(เรา, คนนั้น)` โดย `Jaccard = |สนใจร่วม| ÷ |รุ่นของสองคนรวมกัน|`
3. **ตามยี่ห้อ/ระดับราคา** — นับรุ่นที่เราเคยสนใจซึ่งยี่ห้อเดียวกัน + ระดับราคาเดียวกัน
   (ช่วยแก้ cold start)
4. **ผสม** — `0.6 × (คะแนนเพื่อน normalize) + 0.4 × (คะแนนยี่ห้อ/ราคา normalize)`
5. **ถ่วงด้วยคะแนนดาว** — `Σ (Jaccard × ดาวที่เพื่อนให้ ÷ 5)` ใช้ความสัมพันธ์ `RATED {{stars}}`

**การตรวจสอบที่ทำไว้**
- เทียบผล **2 backend** (Cypher จริง vs หน่วยความจำ) ทุกผู้ใช้ × 6 การตรวจ → ตรงกันทุกข้อ
  (`py -3.13 tools/consistency_test.py <uri> neo4j <password>`)
- โน๊ตบุ๊กบน Colab รันจริงทุกเซลล์ มี assertion และเก็บกวาดข้อมูลทดลอง
- ทดสอบโหมดไม่มี Neo4j แล้วว่ายังแสดงภาพสินค้าครบ
    """)
    st.markdown("#### หมายเหตุของเดโมออนไลน์")
    st.write("- เดโมนี้ **ไม่ต้องมีเซิร์ฟเวอร์ Neo4j** — ใช้ข้อมูลชุดเดียวกับที่โหลดเข้า Neo4j "
             "และผลตรงกันผ่านการทดสอบแล้ว")
    st.write("- การเพิ่ม/ลบความสนใจในหน้า Like & Rate **แยกต่อผู้เข้าชม 1 คน** "
             "ข้อมูลของคนอื่นไม่เปลี่ยน")
    st.write("- ต่อ Neo4j จริง: ตั้งค่า `NEO4J_URI` / `NEO4J_PASSWORD` / `NEO4J_DATABASE` "
             "ใน secrets ของแอป (ดู docs/deploy-streamlit-cloud.md)")

st.divider()
st.caption("ระบบแนะนำมือถือ · จัดทำโดย รหัส 007 · ภาพสินค้าจาก Wikimedia Commons · "
           "ฐานข้อมูลกราฟ: Neo4j · ส่วนติดต่อผู้ใช้: Streamlit")
