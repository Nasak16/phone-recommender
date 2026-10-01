#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backend สำรอง: คิดคำแนะนำในหน่วยความจำด้วยตรรกะเดียวกับ Cypher ใน recommender.py

ใช้เมื่อไม่มี Neo4j (เช่น ตอน deploy บน Streamlit Cloud ที่ยังไม่ได้ตั้งค่า Aura)
ตรรกะให้คะแนนเขียนให้ตรงกับ Cypher ทีละบรรทัด และ tools/consistency_test.py ไว้พิสูจน์
ว่า 2 backend ให้ผลเหมือนกันทุกคน
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


class LocalPhoneRecommender:
    def __init__(self, users, phones, likes):
        self.users_list = [dict(u) for u in users]
        self.phones_list = [dict(p) for p in phones]
        self.by_id = {p["phone_id"]: p for p in self.phones_list}
        self.likes = {u["user"]: set() for u in self.users_list}
        for u, p in likes:
            self.likes.setdefault(u, set()).add(p)

    # ---------- ข้อมูล ----------
    def close(self):
        pass

    def stats(self):
        return {"users": len(self.users_list), "phones": len(self.phones_list),
                "likes": sum(len(v) for v in self.likes.values()),
                "brands": len({p["brand"] for p in self.phones_list}),
                "tiers": len({p["tier"] for p in self.phones_list})}

    def users(self):
        return sorted(self.likes)

    def phones(self):
        out = []
        for p in self.phones_list:
            d = {k: p.get(k) for k in ("phone_id", "model", "brand", "tier", "image")}
            d["likes"] = sum(1 for v in self.likes.values() if p["phone_id"] in v)
            out.append(d)
        return sorted(out, key=lambda r: (-r["likes"], r["model"]))

    def liked_phones(self, user):
        return sorted([
            {"phone_id": p["phone_id"], "model": p["model"], "brand": p["brand"],
             "tier": p["tier"], "image": p["image"], "brands": [p["brand"]], "tiers": [p["tier"]]}
            for pid in self.likes.get(user, ())
            for p in [self.by_id[pid]]
        ], key=lambda r: r["model"])

    # ---------- ความคล้าย ----------
    def similar_users(self, user):
        mine = self.likes.get(user, set())
        rows = []
        for other, theirs in self.likes.items():
            if other == user:
                continue
            common = sorted(mine & theirs)
            if not common:
                continue
            union = len(mine) + len(theirs) - len(common)
            rows.append({"user": other, "common_count": len(common), "common": common,
                         "n_mine": len(mine), "n_theirs": len(theirs),
                         "jaccard": len(common) / union})
        return sorted(rows, key=lambda r: (-r["jaccard"], r["user"]))

    # ---------- คำแนะนำ ----------
    def _score(self, user):
        """ให้คะแนนแบบถ่วงน้ำหนัก Jaccard (และคืน votes มาด้วยเพื่อใช้แสดงผล)"""
        mine = self.likes.get(user, set())
        votes, voters, via, score = {}, {}, {}, {}
        for other, theirs in self.likes.items():
            if other == user:
                continue
            common = mine & theirs
            if not common:
                continue
            jac = len(common) / (len(mine) + len(theirs) - len(common))
            for pid in theirs - mine:
                votes[pid] = votes.get(pid, 0) + 1
                voters.setdefault(pid, []).append(other)
                via.setdefault(pid, set()).update(common)
                score[pid] = score.get(pid, 0.0) + jac
        rows = []
        for pid in votes:
            p = self.by_id[pid]
            rows.append({"phone_id": pid, "model": p["model"], "brand": p["brand"],
                         "tier": p["tier"], "image": p["image"],
                         "votes": votes[pid], "voters": sorted(voters[pid]),
                         "score": round(score[pid], 3),
                         "via_phones": sorted(self.by_id[x]["model"] for x in via[pid])})
        return sorted(rows, key=lambda r: (-r["score"], r["model"]))

    def recommend_votes(self, user, top_n=5):
        return self._score(user)[:top_n]

    def recommend_weighted(self, user, top_n=5):
        return self._score(user)[:top_n]

    def recommend_content(self, user, top_n=5):
        """สัญญาณยี่ห้อ + ระดับราคา: นับจำนวนรุ่นที่ผู้ใช้สนใจซึ่งใช้ยี่ห้อ/ระดับราคาเดียวกัน"""
        mine = self.likes.get(user, set())
        my_brands = {}
        my_tiers = {}
        for pid in mine:
            p = self.by_id[pid]
            my_brands[p["brand"]] = my_brands.get(p["brand"], 0) + 1
            my_tiers[p["tier"]] = my_tiers.get(p["tier"], 0) + 1
        rows = []
        for pid, p in self.by_id.items():
            if pid in mine:
                continue
            bm = my_brands.get(p["brand"], 0)
            tm = my_tiers.get(p["tier"], 0)
            if bm + tm == 0:
                continue
            rows.append({"phone_id": pid, "model": p["model"], "brand": p["brand"],
                         "tier": p["tier"], "image": p["image"],
                         "brand_matches": bm, "tier_matches": tm,
                         "brands": [p["brand"]] if bm else [], "tiers": [p["tier"]] if tm else [],
                         "content_score": bm + tm})
        return sorted(rows, key=lambda r: (-r["content_score"], -r["brand_matches"],
                                           r["model"]))[:top_n]

    def recommend_hybrid(self, user, top_n=5, weight_collab=0.6):
        collab = {r["phone_id"]: r for r in self._score(user)}
        content = {r["phone_id"]: r for r in self.recommend_content(user, top_n=999)}
        max_c = max([r["score"] for r in collab.values()] or [0]) or 1
        max_g = max([r["content_score"] for r in content.values()] or [0]) or 1
        out = {}
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
                "voters": c.get("voters", []), "via_phones": c.get("via_phones", []),
                "because": ("เพื่อนที่รสนิยมใกล้ + ยี่ห้อ/ระดับราคาที่คุณสนใจ" if c and g else
                            "เพื่อนที่รสนิยมใกล้สนใจ" if c else "ยี่ห้อ/ระดับราคาที่คุณสนใจ"),
            }
        return sorted(out.values(), key=lambda r: (-r["score"], r["model"]))[:top_n]

    def popular(self, top_n=5):
        out = []
        for p in self.phones_list:
            n = sum(1 for v in self.likes.values() if p["phone_id"] in v)
            out.append({"phone_id": p["phone_id"], "model": p["model"], "brand": p["brand"],
                        "image": p["image"], "likes": n})
        return sorted(out, key=lambda r: (-r["likes"], r["model"]))[:top_n]

    def graph_edges(self):
        edges = []
        for user, phones in self.likes.items():
            for pid in phones:
                edges.append({"a_type": "User", "a_label": user, "a_id": None, "rel": "LIKES",
                              "b_type": "Phone", "b_label": self.by_id[pid]["model"], "b_id": pid})
        for p in self.phones_list:
            edges.append({"a_type": "Phone", "a_label": p["model"], "a_id": p["phone_id"],
                          "rel": "BY_BRAND", "b_type": "Brand", "b_label": p["brand"], "b_id": None})
            edges.append({"a_type": "Phone", "a_label": p["model"], "a_id": p["phone_id"],
                          "rel": "IN_TIER", "b_type": "Tier", "b_label": p["tier"], "b_id": None})
        return edges

    # ---------- แก้ข้อมูลชั่วคราว (เดโม) ----------
    def add_like(self, user, phone_id):
        self.likes.setdefault(user, set()).add(phone_id)
        if user not in [u["user"] for u in self.users_list]:
            self.users_list.append({"user": user, "age": None, "group": "ผู้ใช้ใหม่"})

    def remove_like(self, user, phone_id):
        self.likes.get(user, set()).discard(phone_id)


def from_files():
    """อ่านข้อมูลชุดเดียวกับที่โหลดเข้า Neo4j"""
    import seed_data
    users, phones, likes = seed_data.graph_data()
    return LocalPhoneRecommender(users, phones, likes)
