#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""วาดกราฟ bipartite (ผู้ใช้ ↔ รุ่นมือถือ) ของคำแนะนำ — ใช้ทั้งในแอปและสคริปต์ตรวจภาพ"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

BG = "#0E1626"
ORANGE, CYAN, GREEN, YELLOW, TEXT = "#FF8833", "#38BDF8", "#34D399", "#FBBF24", "#E9EFFA"


def build(engine, who, recs):
    """สร้างกราฟย่อยรอบผู้ใช้ที่เลือก: ตัวเรา + รุ่นที่สนใจ + คนรสนิยมใกล้ + รุ่นที่แนะนำ"""
    G = nx.Graph()
    mine = {p["phone_id"] for p in engine.liked_phones(who)}
    G.add_node(who, kind="user", label=who)
    for p in engine.liked_phones(who):
        G.add_node(p["phone_id"], kind="phone", label=p["model"])
        G.add_edge(who, p["phone_id"], rel="likes")
    voters = {r["phone_id"]: set(r.get("voters", [])) for r in recs}
    for s in engine.similar_users(who):
        G.add_node(s["user"], kind="user", label=s["user"])
        for pid in s["common"]:
            if pid in G:
                G.add_edge(s["user"], pid, rel="likes")
        for r in recs:
            if s["user"] in voters.get(r["phone_id"], ()):
                G.add_node(r["phone_id"], kind="phone", label=r["model"])
                G.add_edge(s["user"], r["phone_id"], rel="likes", path=True)
    return G, mine, set(voters)


def layout(G):
    users = sorted([n for n, d in G.nodes(data=True) if d["kind"] == "user"],
                   key=lambda n: (n != list(G.nodes)[0], n))
    phones = sorted([n for n, d in G.nodes(data=True) if d["kind"] == "phone"],
                    key=lambda n: G.nodes[n]["label"])
    n = max(len(users), len(phones), 1)
    pos = {}
    for i, u in enumerate(users):
        pos[u] = (-1.0, i + (n - len(users)) / 2 - (n - 1) / 2)
    for i, p in enumerate(phones):
        pos[p] = (1.0, i + (n - len(phones)) / 2 - (n - 1) / 2)
    return pos, n


def draw(engine, who, recs, font="DejaVu Sans", title=None):
    G, mine, recommended = build(engine, who, recs)
    pos, n = layout(G)
    fig, ax = plt.subplots(figsize=(12.2, max(6.2, n * 0.66)))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for a, b, d in G.edges(data=True):
        x, y = [pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]]
        if d.get("path"):
            ax.plot(x, y, "--", color=GREEN, lw=2.8, alpha=1.0, zorder=3)
        else:
            ax.plot(x, y, "-", color="#3C4C6E", lw=1.3, alpha=0.85, zorder=1)

    def color(node):
        d = G.nodes[node]
        if d["kind"] == "user":
            return ORANGE if node == who else CYAN
        if node in mine:
            return YELLOW
        if node in recommended:
            return GREEN
        return "#5A6E96"

    def short(label, n=24):
        return label if len(label) <= n else label[:n - 1] + "…"

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_size=[2200 if x == who else
                                      (1500 if G.nodes[x]["kind"] == "user" else 1200)
                                      for x in G],
                           node_color=[color(x) for x in G], edgecolors=BG, linewidths=2)
    texts = nx.draw_networkx_labels(
        G, pos, ax=ax, font_family=font, font_size=11, font_color=TEXT,
        labels={x: (short(G.nodes[x]["label"]) if G.nodes[x]["kind"] == "phone"
                    else G.nodes[x]["label"]) for x in G})
    for node, t in texts.items():
        if G.nodes[node]["kind"] == "phone":
            t.set_position((pos[node][0] + 0.34, pos[node][1])); t.set_ha("left")
        else:
            t.set_position((pos[node][0] - 0.34, pos[node][1])); t.set_ha("right")
    for node, t in texts.items():
        if node == who:
            t.set_fontweight("bold"); t.set_fontsize(13)

    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", ms=13, mfc=ORANGE, mec=BG,
               label=f"ผู้ใช้ที่เลือก ({who})"),
        Line2D([], [], marker="o", ls="", ms=11, mfc=CYAN, mec=BG, label="ผู้ใช้ที่รสนิยมใกล้"),
        Line2D([], [], marker="o", ls="", ms=11, mfc=YELLOW, mec=BG, label="รุ่นที่สนใจแล้ว"),
        Line2D([], [], marker="o", ls="", ms=11, mfc=GREEN, mec=BG, label="รุ่นที่ระบบแนะนำ"),
        Line2D([], [], ls="--", lw=2.4, color=GREEN, label="เส้นทาง 3 hop ที่ระบบเดิน"),
    ], loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=3, frameon=False, labelcolor=TEXT,
        prop={"family": font, "size": 11.5})
    if title:
        ax.set_title(title, fontfamily=font, color=TEXT, fontsize=14, pad=44)
    ax.axis("off")
    ax.set_xlim(-2.75, 3.45)
    ys = [y for _, y in pos.values()]
    ax.set_ylim(min(ys) - 0.8, max(ys) + 0.8)
    fig.tight_layout()
    return fig


def thai_font(project_root):
    """โหลดฟอนต์ Sarabun จาก Google Fonts (ไม่ต้องติดตั้ง/ไม่ต้องสิทธิ์ admin)"""
    import os, urllib.request
    from matplotlib import font_manager as fm
    d = os.path.join(project_root, "assets", "fonts")
    os.makedirs(d, exist_ok=True)
    try:
        for fn in ("Sarabun-Regular.ttf", "Sarabun-Bold.ttf"):
            p = os.path.join(d, fn)
            if not os.path.exists(p):
                urllib.request.urlretrieve(
                    "https://github.com/google/fonts/raw/main/ofl/sarabun/" + fn, p)
            fm.fontManager.addfont(p)
        return fm.FontProperties(fname=os.path.join(d, "Sarabun-Regular.ttf")).get_name()
    except Exception:
        return "DejaVu Sans"


if __name__ == "__main__":
    import os, sys
    ROOT = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "data"))
    from graph_fallback import from_files
    eng = from_files()
    f = thai_font(ROOT)
    out = os.path.join(ROOT, "tools", "out"); os.makedirs(out, exist_ok=True)
    for who in ("สมชาย", "มะลิ", "กัญญา"):
        fig = draw(eng, who, eng.recommend_weighted(who, 3), font=f,
                   title=f"กราฟคำแนะนำสำหรับ {who}")
        p = os.path.join(out, f"graph_{who}.png")
        fig.savefig(p, dpi=115, facecolor=BG)
        plt.close(fig)
        print("wrote", p)
