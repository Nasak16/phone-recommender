#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""แกนของระบบแนะนำมือถือ (Phone Recommender Engine) — คุยกับ Neo4j ด้วย Cypher

ใช้ร่วมกันทั้ง Streamlit app และสคริปต์ทดสอบ เพื่อให้ผลลัพธ์ตรงกันเสมอ
รูปแบบกราฟ:  (User)-[:LIKES]->(Phone)-[:BY_BRAND]->(Brand)
                            (Phone)-[:IN_TIER]->(Tier)
"""
from collections import OrderedDict

from neo4j import GraphDatabase

Q_STATS = """
MATCH (u:User) WITH count(u) AS users
MATCH (p:Phone) WITH users, count(p) AS phones
MATCH ()-[r:LIKES]->() WITH users, phones, count(r) AS likes
MATCH ()-[rt:RATED]->() WITH users, phones, likes, count(rt) AS ratings
MATCH (b:Brand) WITH users, phones, likes, ratings, count(b) AS brands
MATCH (t:Tier) RETURN users, phones, likes, ratings, brands, count(t) AS tiers
"""

Q_RESET = "MATCH (n) DETACH DELETE n"

Q_CONSTRAINTS = [
    "CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.user IS UNIQUE",
    "CREATE CONSTRAINT phone_id IF NOT EXISTS FOR (p:Phone) REQUIRE p.phone_id IS UNIQUE",
    "CREATE CONSTRAINT brand_name IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
    "CREATE CONSTRAINT tier_name IF NOT EXISTS FOR (t:Tier) REQUIRE t.name IS UNIQUE",
]

Q_LOAD_USERS = """
UNWIND $rows AS row
MERGE (u:User {user: row.user})
SET u.age = row.age, u.group = row.group, u.node_type = 'user'
RETURN count(u) AS users
"""

Q_LOAD_PHONES = """
UNWIND $rows AS row
MERGE (p:Phone {phone_id: row.phone_id})
SET p.model = row.model, p.brand = row.brand, p.tier = row.tier,
    p.image = row.image, p.image_title = row.image_title,
    p.node_type = 'phone'
MERGE (b:Brand {name: row.brand})   MERGE (p)-[:BY_BRAND]->(b)
MERGE (t:Tier {name: row.tier})     MERGE (p)-[:IN_TIER]->(t)
RETURN count(p) AS phones
"""

Q_LOAD_LIKES = """
UNWIND $rows AS row
MATCH (u:User {user: row.user})
MATCH (p:Phone {phone_id: row.phone_id})
MERGE (u)-[:LIKES]->(p)
RETURN count(*) AS likes
"""

Q_LOAD_RATINGS = """
UNWIND $rows AS row
MATCH (u:User {user: row.user})
MATCH (p:Phone {phone_id: row.phone_id})
MERGE (u)-[rt:RATED]->(p) SET rt.stars = row.stars
RETURN count(rt) AS ratings
"""

Q_RATINGS = """
MATCH (p:Phone)<-[rt:RATED]-(:User)
RETURN p.phone_id AS phone_id, round(avg(rt.stars) * 100) / 100.0 AS avg_stars,
       count(rt) AS n_raters
ORDER BY avg_stars DESC, phone_id
"""

Q_LIKED = """
MATCH (u:User {user: $user})-[:LIKES]->(p:Phone)
OPTIONAL MATCH (p)-[:BY_BRAND]->(b:Brand)
OPTIONAL MATCH (p)-[:IN_TIER]->(t:Tier)
RETURN p.phone_id AS phone_id, p.model AS model, p.brand AS brand, p.tier AS tier,
       p.image AS image, collect(DISTINCT b.name) AS brands, collect(DISTINCT t.name) AS tiers
ORDER BY p.model
"""

Q_SIMILAR = """
MATCH (me:User {user: $user})-[:LIKES]->(shared:Phone)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.phone_id) AS common
MATCH (me)-[:LIKES]->(mine:Phone)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Phone)
WITH other, common, n_mine, count(DISTINCT theirs) AS n_theirs
RETURN other.user AS user, size(common) AS common_count, common,
       n_mine, n_theirs,
       toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard
ORDER BY jaccard DESC, user
"""

# 1 เสียง/คน/รุ่น (Cypher รวมผลแบบ DISTINCT ให้เอง จึงไม่นับซ้ำ)
Q_RECO_VOTES = """
MATCH (me:User {user: $user})-[:LIKES]->(shared:Phone)<-[:LIKES]-(other:User)-[:LIKES]->(rec:Phone)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.phone_id AS phone_id, rec.model AS model, rec.brand AS brand, rec.tier AS tier,
       rec.image AS image,
       count(DISTINCT other) AS votes,
       collect(DISTINCT other.user) AS voters,
       collect(DISTINCT shared.model) AS via_phones
ORDER BY votes DESC, model
"""

# ถ่วงน้ำหนักด้วย Jaccard similarity ของคนที่สนใจ (คนรสนิยมใกล้มีน้ำหนักมากกว่า)
Q_RECO_WEIGHTED = """
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
       rec.image AS image,
       round(sum(jaccard) * 1000) / 1000.0 AS score,
       count(DISTINCT other) AS votes, collect(DISTINCT other.user) AS voters
ORDER BY score DESC, model
"""

# อีกสัญญาณหนึ่ง: ยี่ห้อ + ระดับราคาที่ผู้ใช้สนใจ (content-based ผ่านโหนด Brand/Tier)
Q_RECO_CONTENT = """
MATCH (me:User {user: $user})
MATCH (rec:Phone)
WHERE NOT (me)-[:LIKES]->(rec)
OPTIONAL MATCH (me)-[:LIKES]->(liked:Phone)-[:BY_BRAND]->(b:Brand)<-[:BY_BRAND]-(rec)
WITH me, rec, count(DISTINCT liked) AS brand_matches, collect(DISTINCT b.name) AS brands
OPTIONAL MATCH (me)-[:LIKES]->(liked2:Phone)-[:IN_TIER]->(t:Tier)<-[:IN_TIER]-(rec)
WITH rec, brand_matches, brands, count(DISTINCT liked2) AS tier_matches,
     collect(DISTINCT t.name) AS tiers
WHERE brand_matches + tier_matches > 0
RETURN rec.phone_id AS phone_id, rec.model AS model, rec.brand AS brand, rec.tier AS tier,
       rec.image AS image, brand_matches, brands, tier_matches, tiers,
       brand_matches + tier_matches AS content_score
ORDER BY content_score DESC, brand_matches DESC, model
"""

Q_RECO_RATED = """
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
       rec.image AS image,
       round(sum(jaccard * rt.stars / 5.0) * 1000) / 1000.0 AS score,
       count(DISTINCT other) AS votes, collect(DISTINCT other.user) AS voters,
       reduce(acc = [], x IN collect(DISTINCT via_models) | acc + x) AS via_phones,
       round(avg(rt.stars) * 100) / 100.0 AS avg_stars
ORDER BY score DESC, model
"""

Q_POPULAR = """
MATCH (p:Phone)<-[:LIKES]-(u:User)
RETURN p.phone_id AS phone_id, p.model AS model, p.brand AS brand,
       p.image AS image, count(u) AS likes
ORDER BY likes DESC, model LIMIT 5
"""

Q_GRAPH_EDGES = """
MATCH (a)-[r:LIKES|BY_BRAND|IN_TIER]->(b)
RETURN labels(a)[0] AS a_type, coalesce(a.user, a.model, a.name) AS a_label, a.phone_id AS a_id,
       type(r) AS rel,
       labels(b)[0] AS b_type, coalesce(b.model, b.name, b.user) AS b_label, b.phone_id AS b_id
"""


class PhoneRecommender:
    """ระบบแนะนำมือถือ: ให้คะแนน 3 วิธี + วิธีผสม และอธิบายย้อนหลังได้"""

    def __init__(self, uri, user="neo4j", password=None, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def _run(self, query, **params):
        with self.driver.session(database=self.database) as s:
            return [r.data() for r in s.run(query, **params)]

    # ---------- ข้อมูลตั้งต้น ----------
    def reset(self):
        self._run(Q_RESET)

    def ensure_constraints(self):
        for q in Q_CONSTRAINTS:
            self._run(q)

    def import_data(self, users, phones, likes, ratings=None):
        self._run(Q_LOAD_USERS, rows=[{"user": u["user"], "age": u["age"], "group": u["group"]}
                                      for u in users])
        self._run(Q_LOAD_PHONES, rows=[{k: p.get(k) for k in
                                        ("phone_id", "model", "brand", "tier", "image",
                                         "image_title")} for p in phones])
        self._run(Q_LOAD_LIKES, rows=[{"user": u, "phone_id": p} for u, p in likes])
        if ratings:
            self._run(Q_LOAD_RATINGS,
                      rows=[{"user": u, "phone_id": p, "stars": s} for u, p, s in ratings])

    def stats(self):
        row = self._run(Q_STATS)[0]
        return {"users": row["users"], "phones": row["phones"], "likes": row["likes"],
                "ratings": row["ratings"], "brands": row["brands"], "tiers": row["tiers"]}

    def users(self):
        return [r["user"] for r in
                self._run("MATCH (u:User) RETURN u.user AS user ORDER BY u.user")]

    def phones(self):
        return self._run("""
            MATCH (p:Phone)
            OPTIONAL MATCH (p)<-[:LIKES]-(u:User)
            RETURN p.phone_id AS phone_id, p.model AS model, p.brand AS brand, p.tier AS tier,
                   p.image AS image, count(DISTINCT u) AS likes
            ORDER BY likes DESC, p.model""")

    # ---------- คำถามพื้นฐาน ----------
    def liked_phones(self, user):
        return self._run(Q_LIKED, user=user)

    def similar_users(self, user):
        return self._run(Q_SIMILAR, user=user)

    # ---------- คำแนะนำ ----------
    def recommend_votes(self, user, top_n=5):
        return self._run(Q_RECO_VOTES, user=user)[:top_n]

    def recommend_weighted(self, user, top_n=5):
        return self._run(Q_RECO_WEIGHTED, user=user)[:top_n]

    def recommend_content(self, user, top_n=5):
        return self._run(Q_RECO_CONTENT, user=user)[:top_n]

    def recommend_rated(self, user, top_n=5):
        """สัญญาณที่ 5: ให้เพื่อนที่รสนิยมใกล้ถ่วงด้วย “คะแนนดาว” ที่เขาให้รุ่นนั้น"""
        return self._run(Q_RECO_RATED, user=user)[:top_n]

    def rating_stats(self):
        """ดาวเฉลี่ยของแต่ละรุ่น (ใช้แสดงบนการ์ด)"""
        return {r["phone_id"]: r for r in self._run(Q_RATINGS)}

    def run_readonly(self, query, limit=300):
        """รัน Cypher แบบอ่านข้อมูลเท่านั้น (ใช้ในหน้า Graph Explorer / Admin)"""
        q = query.strip().rstrip(";").strip()
        if not q:
            raise ValueError("พิมพ์คำสั่ง Cypher ก่อน")
        banned = ("CREATE ", "MERGE ", "DELETE ", "DETACH ", " SET ", "REMOVE ", "DROP ",
                  "LOAD CSV", "CALL DB", "CALL APOC", "FOREACH ")
        up = " " + q.upper().replace("\n", " ") + " "
        hit = [b for b in banned if b in up]
        if hit:
            raise ValueError("หน้านี้อนุญาตเฉพาะคำสั่งอ่านข้อมูล (MATCH / RETURN / WITH) — พบ %s"
                             % ", ".join(h.strip() for h in hit))
        return self._run(q)[:limit]

    def add_rating(self, user, phone_id, stars):
        self._run("""
            MERGE (u:User {user: $user}) SET u.node_type = 'user'
            WITH u MATCH (p:Phone {phone_id: $phone_id})
            MERGE (u)-[rt:RATED]->(p) SET rt.stars = $stars""",
                  user=user, phone_id=phone_id, stars=float(stars))

    def recommend_hybrid(self, user, top_n=5, weight_collab=0.6):
        """รวมสัญญาณเพื่อน (ถ่วง Jaccard) กับสัญญาณยี่ห้อ/ระดับราคา แล้ว normalize เป็น 0-1"""
        collab = {r["phone_id"]: r for r in self._run(Q_RECO_WEIGHTED, user=user)}
        content = {r["phone_id"]: r for r in self._run(Q_RECO_CONTENT, user=user)}
        max_c = max([r["score"] for r in collab.values()] or [0]) or 1
        max_g = max([r["content_score"] for r in content.values()] or [0]) or 1
        out = OrderedDict()
        for pid in set(collab) | set(content):
            c, g = collab.get(pid, {}), content.get(pid, {})
            base = c or g
            out[pid] = {
                "phone_id": pid, "model": base["model"], "brand": base.get("brand"),
                "tier": base.get("tier"), "image": base.get("image"),
                "score": round(weight_collab * c.get("score", 0) / max_c
                               + (1 - weight_collab) * g.get("content_score", 0) / max_g, 3),
                "collab": round(c.get("score", 0), 3),
                "content_score": g.get("content_score", 0),
                "brand_matches": g.get("brand_matches", 0),
                "voters": c.get("voters", []),
                "via_phones": c.get("via_phones", []),
                "because": ("เพื่อนที่รสนิยมใกล้ + ยี่ห้อ/ระดับราคาที่คุณสนใจ" if c and g else
                            "เพื่อนที่รสนิยมใกล้สนใจ" if c else "ยี่ห้อ/ระดับราคาที่คุณสนใจ"),
            }
        return sorted(out.values(), key=lambda r: (-r["score"], r["model"]))[:top_n]

    def popular(self, top_n=5):
        return self._run(Q_POPULAR)[:top_n]

    def graph_edges(self):
        return self._run(Q_GRAPH_EDGES)

    # ---------- เดโมสด: เพิ่มความสนใจแล้วคำแนะนำเปลี่ยนทันที ----------
    def add_like(self, user, phone_id):
        self._run("""
            MERGE (u:User {user: $user}) SET u.node_type = 'user'
            WITH u MATCH (p:Phone {phone_id: $phone_id})
            MERGE (u)-[:LIKES]->(p)""", user=user, phone_id=phone_id)

    def remove_like(self, user, phone_id):
        self._run("""
            MATCH (u:User {user: $user})-[r:LIKES]->(p:Phone {phone_id: $phone_id})
            DELETE r""", user=user, phone_id=phone_id)
