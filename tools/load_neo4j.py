#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""โหลดข้อมูลมือถือ/ผู้ใช้/ความสนใจ เข้า Neo4j แล้วพิมพ์ผลตรวจสอบ

    py -3.13 tools/load_neo4j.py bolt://127.0.0.1:7687 neo4j <password> [database]
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "data"))

from recommender import PhoneRecommender          # noqa: E402
import seed_data                                  # noqa: E402

URI = sys.argv[1] if len(sys.argv) > 1 else "bolt://127.0.0.1:7687"
USER = sys.argv[2] if len(sys.argv) > 2 else "neo4j"
PW = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("NEO4J_PASSWORD", "")
DB = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("NEO4J_DATABASE", "phones")

users, phones, likes = seed_data.graph_data()
ratings = seed_data.ratings_data(phones)
rec = PhoneRecommender(URI, USER, PW, database=DB)
print("เชื่อมต่อ:", URI, "| database:", DB)
print("server:", rec.driver.get_server_info().agent)
rec.reset()
rec.ensure_constraints()
rec.import_data(users, phones, likes, ratings)
print("ข้อมูลในกราฟ:", rec.stats())

target = "สมชาย"
print(f"\n--- {target} สนใจ (จาก Cypher) ---")
for p in rec.liked_phones(target):
    print("   ", p["phone_id"], p["brand"], p["model"], "|", p["tier"])

print(f"\n--- ใครรสนิยมใกล้ {target} (Jaccard) ---")
for r in rec.similar_users(target):
    print(f"    {r['user']:8s} สนใจร่วม {r['common_count']} รุ่น {r['common']} | "
          f"Jaccard {r['jaccard']:.3f}")

print(f"\n--- แนะนำให้ {target}: นับโหวต ---")
for r in rec.recommend_votes(target, 5):
    print(f"    {r['brand']} {r['model'][:24]:26s} votes={r['votes']} voters={r['voters']}")

print(f"\n--- แนะนำให้ {target}: ถ่วงน้ำหนัก Jaccard ---")
for r in rec.recommend_weighted(target, 5):
    print(f"    {r['brand']} {r['model'][:24]:26s} score={r['score']} voters={r['voters']}")

print(f"\n--- แนะนำให้ {target}: ตามยี่ห้อ/ระดับราคา ---")
for r in rec.recommend_content(target, 5):
    print(f"    {r['brand']} {r['model'][:24]:26s} ยี่ห้อตรง {r['brand_matches']} · "
          f"ระดับราคาตรง {r['tier_matches']} (รวม {r['content_score']})")

print(f"\n--- แนะนำให้ {target}: เพื่อนถ่วงด้วยคะแนนดาว ---")
for r in rec.recommend_rated(target, 5):
    print(f"    {r['brand']} {r['model'][:24]:26s} score={r['score']} votes={r['votes']} "
          f"ดาวเฉลี่ย={r['avg_stars']}")

print(f"\n--- ดาวเฉลี่ยต่อรุ่น (Top 5) ---")
for pid, s in list(rec.rating_stats().items())[:5]:
    print(f"    {pid} ดาวเฉลี่ย {s['avg_stars']} จาก {s['n_raters']} คน")

print(f"\n--- แนะนำให้ {target}: ผสมสองสัญญาณ ---")
for r in rec.recommend_hybrid(target, 5):
    print(f"    {r['brand']} {r['model'][:24]:26s} score={r['score']} เพื่อน={r['collab']} "
          f"ยี่ห้อ/ราคา={r['content_score']} เพราะ: {r['because']}")

print("\n--- ยอดนิยม (baseline) ---")
for r in rec.popular():
    print(f"    {r['brand']} {r['model'][:24]:26s} likes={r['likes']}")

print("\n--- ทุกคนได้อะไร (top-3 weighted) ---")
for u in rec.users():
    top = rec.recommend_weighted(u, 3)
    print(f"    {u:8s} -> " + ", ".join(f"{r['brand']} {r['model'][:16]}({r['score']})"
                                       for r in top))
rec.close()
