"""Benchmark composition figure (Section 3.3): (a) sunburst of the 80 hidden classes by domain (inner), trap field
(middle), and type of grouping (outer); (b) number of competing published lists that also contain the example;
(c) size of the value universe of each trap field; (d) length of the test task statement per level. Reads
data/composition.json, data/domain_stats.json; writes figures/composition.pdf. Run from the repository root."""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as S
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
comp = json.loads((ROOT / "data/composition.json").read_text())
dom = json.loads((ROOT / "data/domain_stats.json").read_text())
S.apply()
DN = {"TR": "Travel audit", "SY": "Pharmacy", "WS": "Web security", "LG": "System logs", "SP": "Sponsorship",
      "CH": "Chemicals", "MN": "Raw materials", "SH": "Port control", "UN": "Scholarships", "GR": "Travel grants"}


def kind(name):
    n = name.lower()
    if any(k in n for k in ("language", "italic", "slavic")): return "language groups"
    if any(k in n for k in ("alliance", "oneworld", "skyteam", "airlines group", "skytrax")): return "airline alliances"
    if any(k in n for k in ("nato", "g7", "group of seven", "g20", "group of twenty", "oecd", "brics", "opec", "asean member",
                            "commonwealth", "european union", "economic area", "schengen", "arab league", "asia-pacific",
                            "council of europe", "islamic cooperation", "missile technology", "african union")):
        return "intergovernmental"
    if any(k in n for k in ("stoxx", "dow jones", "nasdaq", "aex", "systemically important", "g-14", "super league",
                            "champions league", "club world cup")): return "indices and clubs"
    if "universit" in n: return "university networks"
    if any(k in n for k in ("microsoft", "office", "port", "ftp")): return "software and ports"
    return "standards and classifications"


TYPES = [("intergovernmental", "#4c78a8"), ("standards and classifications", "#59a14f"), ("airline alliances", "#e15759"),
         ("indices and clubs", "#f28e2b"), ("software and ports", "#b07aa1"), ("university networks", "#9c755f"),
         ("language groups", "#edc948")]
TCOL = dict(TYPES)
slots = comp["slots"]
order = list(DN)
fig = plt.figure(figsize=(7.0, 2.75))
gs = fig.add_gridspec(2, 3, width_ratios=[1.3, 1, 0.95], hspace=0.75, wspace=0.55)
ax = fig.add_subplot(gs[:, 0])
# (a) sunburst
inner, middle, outer, mid_lab = [], [], [], []
for d in order:
    ds = [s for s in slots if s["chain"][:2] == d]
    inner.append(len(ds))
    for f in sorted({s["field"] for s in ds}):
        fs = [s for s in ds if s["field"] == f]
        middle.append(len(fs)); mid_lab.append(f.split(".")[-1].replace("_", " "))
        cnt = collections.Counter(kind(s["name"]) for s in fs)
        for t, _ in TYPES:
            if cnt[t]: outer.append((cnt[t], TCOL[t]))
base = plt.get_cmap("tab20c")
dcols = [plt.get_cmap("Pastel1")(i % 9) if i < 9 else "#d9d9d9" for i in range(10)]
dcols = ["#c6dbef", "#fdd0a2", "#c7e9c0", "#dadaeb", "#fcbba1", "#d9f0d3", "#fee6ce", "#deebf7", "#e5d8bd", "#f2f0f7"]
ax.pie(inner, radius=0.62, colors=dcols, startangle=90, counterclock=False,
       wedgeprops=dict(width=0.62, edgecolor="white", linewidth=1.0))
mcols = []
for d, n in zip(order, inner):
    k = len({s["field"] for s in slots if s["chain"][:2] == d})
    mcols += [dcols[order.index(d)]] * k
ax.pie(middle, radius=0.82, colors=mcols, startangle=90, counterclock=False,
       wedgeprops=dict(width=0.2, edgecolor="white", linewidth=0.8, alpha=0.75))
ax.pie([o[0] for o in outer], radius=1.0, colors=[o[1] for o in outer], startangle=90, counterclock=False,
       wedgeprops=dict(width=0.18, edgecolor="white", linewidth=0.5))
# domain labels inside
ang = 90
for d, n in zip(order, inner):
    a = np.deg2rad(ang - 180 * n / 80)
    ang -= 360 * n / 80
    x, y = np.cos(a), np.sin(a)
    ax.plot([0.66 * x, 1.06 * x], [0.66 * y, 1.06 * y], color="#9a9a9a", lw=0.4, zorder=5) if False else None
    ax.text(1.1 * x, 1.1 * y, DN[d], ha="left" if x >= 0.05 else ("right" if x <= -0.05 else "center"),
            va="center", fontsize=5.8, color=S.INK)
ax.set_aspect("equal")
ax.set_xlim(-1.75, 1.75)
ax.set_ylim(-1.25, 1.25)
ax.add_patch(plt.Circle((0, 0), 0.17, color="white", zorder=3))
ax.text(0, 0, "80\nclasses", ha="center", va="center", fontsize=6.3, fontweight="bold", color=S.INK, linespacing=0.9, zorder=4)
h = [plt.Rectangle((0, 0), 1, 1, fc=c, ec="none", label=t) for t, c in TYPES]
ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=5.6, handlelength=0.9,
          handletextpad=0.35, columnspacing=0.6, labelspacing=0.25)
ax.set_title("(a) Domains, trap fields, and class types", fontsize=7.2, pad=2, loc="left", x=-0.05)
# (b) competing lists per example
axb = fig.add_subplot(gs[0, 1])
c = [s["competing"] for s in slots]
axb.hist(c, bins=range(0, max(c) + 2), color="#4c78a8", edgecolor="white", linewidth=0.5)
axb.set_xlabel("other lists containing the example", fontsize=6.6)
axb.set_ylabel("slots", fontsize=6.6)
axb.set_title("(b) Competing groupings", fontsize=7.2, pad=3, loc="left")
axb.text(0.97, 0.92, f"mean {np.mean(c):.1f}", transform=axb.transAxes, ha="right", fontsize=6.2, color=S.SUB)
# (c) value universe sizes
axc = fig.add_subplot(gs[:, 2])
uni = {}
for d, v in dom.items():
    for f, x in v["fields"].items():
        uni[x["universe"]] = max(uni.get(x["universe"], 0), x["values"])
names = sorted(uni, key=uni.get)
axc.barh(range(len(names)), [uni[n] for n in names], color="#59a14f", height=0.66)
axc.set_xscale("log")
axc.set_yticks(range(len(names)))
axc.set_yticklabels([n.replace("_", " ") for n in names], fontsize=6)
axc.set_xlabel("values with descriptions", fontsize=6.6)
axc.set_title("(c) Value universes", fontsize=7.2, pad=3, loc="left")
# (d) task length per level
axd = fig.add_subplot(gs[1, 1])
by_chain = collections.defaultdict(dict)
for p in comp["prompts"]:
    by_chain[p["chain"]][p["level"]] = p["test_chars"] / 4 / 1000
for c, lv in by_chain.items():
    axd.plot([1, 2, 3, 4], [lv[k] for k in range(1, 5)], color="#c9ced6", lw=0.6, zorder=1)
med = [float(np.median([lv[k] for lv in by_chain.values()])) for k in range(1, 5)]
axd.plot([1, 2, 3, 4], med, color=S.BLUE, lw=1.6, marker="o", ms=3.6, mec="white", mew=0.6, zorder=3)
for k, m in zip(range(1, 5), med):
    axd.text(k, m + 0.35, f"{m:.1f}", ha="center", va="bottom", fontsize=5.8, color=S.BLUE, zorder=4)
axd.set_xticks([1, 2, 3, 4]); axd.set_xticklabels(["L1", "L2", "L3", "L4"])
axd.set_xlim(0.8, 4.2)
axd.set_ylabel("k tokens", fontsize=6.6)
axd.set_title("(d) Test task length per level", fontsize=7.2, pad=3, loc="left")
axd.text(0.03, 0.95, "median, one line per chain", transform=axd.transAxes, fontsize=5.6, color=S.SUB, va="top")
for sp in ("top", "right"):
    axd.spines[sp].set_visible(False)
fig.savefig(ROOT / "figures/composition.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/composition.pdf")
