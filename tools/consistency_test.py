#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ทดสอบว่า backend Neo4j (Cypher) กับ backend สำรอง (หน่วยความจำ) ให้ผลตรงกัน

    py -3.13 tools/consistency_test.py bolt://127.0.0.1:7687 neo4j <password> [database]

ตรวจ 5 อย่างต่อผู้ใช้ 1 คน × 12 คน: similar_users, votes, weighted, content, hybrid
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "data"))

from recommender import PhoneRecommender        # noqa: E402
from graph_fallback import from_files           # noqa: E402

uri = sys.argv[1] if len(sys.argv) > 1 else "bolt://127.0.0.1:7687"
user = sys.argv[2] if len(sys.argv) > 2 else "neo4j"
pw = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("NEO4J_PASSWORD", "")
db = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("NEO4J_DATABASE", "phones")

real = PhoneRecommender(uri, user, pw, database=db)
loc = from_files()
print("Neo4j :", real.driver.get_server_info().agent, "| database:", db)
print("stats ตรงกัน:", real.stats() == loc.stats(), real.stats(), loc.stats())

fails = []
for u in real.users():
    a = [(r["user"], round(r["jaccard"], 3), r["common_count"]) for r in real.similar_users(u)]
    b = [(r["user"], round(r["jaccard"], 3), r["common_count"]) for r in loc.similar_users(u)]
    if a != b:
        fails.append((u, "similar_users", a, b))

    va = {r["model"]: r["votes"] for r in real.recommend_votes(u, 999)}
    vb = {r["model"]: r["votes"] for r in loc.recommend_votes(u, 999)}
    if va != vb:
        fails.append((u, "votes", va, vb))

    wa = [(r["model"], r["score"]) for r in real.recommend_weighted(u, 5)]
    wb = [(r["model"], r["score"]) for r in loc.recommend_weighted(u, 5)]
    if wa != wb:
        fails.append((u, "weighted", wa, wb))

    ca = [(r["model"], r["content_score"], r["brand_matches"], r["tier_matches"])
          for r in real.recommend_content(u, 5)]
    cb = [(r["model"], r["content_score"], r["brand_matches"], r["tier_matches"])
          for r in loc.recommend_content(u, 5)]
    if ca != cb:
        fails.append((u, "content", ca, cb))

    ha = [(r["model"], r["score"], r["because"]) for r in real.recommend_hybrid(u, 5)]
    hb = [(r["model"], r["score"], r["because"]) for r in loc.recommend_hybrid(u, 5)]
    if ha != hb:
        fails.append((u, "hybrid", ha, hb))

    ra = [(r["model"], r["score"], r["votes"], r["avg_stars"]) for r in real.recommend_rated(u, 5)]
    rb = [(r["model"], r["score"], r["votes"], r["avg_stars"]) for r in loc.recommend_rated(u, 5)]
    if ra != rb:
        fails.append((u, "rated", ra, rb))

if fails:
    print("\nไม่ตรงกัน %d จุด:" % len(fails))
    for u, what, a, b in fails:
        print(f"  {u} / {what}\n     neo4j : {a}\n     local : {b}")
    sys.exit(1)
print("ผลตรงกันครบทุกข้อ (12 คน × 6 การตรวจ) — backend สำรองเชื่อถือได้")
real.close()
