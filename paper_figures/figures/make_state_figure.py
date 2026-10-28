"""State content figure: (a) what the state written after each level says about that level's label (annotated by
GPT-6-Luna, test outcomes hidden), per condition, ACE and Dynamic Cheatsheet pooled; (b) unseen members excluded and
non-members kept by the program, grouped by the annotated state content. Reads data/state_annotation_items.jsonl and
data/state_annotation_outcomes.json; writes figures/state_content.pdf. Run from the repository root."""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as S
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
items = {}
for l in (ROOT / "data/state_annotation_items.jsonl").read_text().splitlines():
    r = json.loads(l); items[(r["model"], r["cond"], r["method"], r["chain"], r["level"])] = r["category"]
outc = json.loads((ROOT / "data/state_annotation_outcomes.json").read_text())
S.apply()
GROUP = {"exact": "category", "broader": "category", "members_enumerated": "category", "other_group": "wrong rule",
         "attribute": "wrong rule", "exceptions": "exceptions or nothing", "none": "exceptions or nothing"}
CATS = [("category", "names the class", S.BLUE), ("wrong rule", "wrong rule", S.LBLUE),
        ("exceptions or nothing", "only seen values", "#d9d9d9")]
items = {k: GROUP.get(v) for k, v in items.items() if v in GROUP}
CONDS = [(("luna", "self"), "Luna, feedback alone"), (("luna", "rewarded"), "Luna, rewarded practice"),
         (("luna", "procn"), "Luna, + procedure"), (("luna", "convn"), "Luna, + convention"),
         (("luna", "hint"), "Luna, + lesson"), (("sol", "self"), "Sol, feedback alone"), (("sol", "hint"), "Sol, + lesson")]
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.25), gridspec_kw=dict(width_ratios=[1.75, 1], wspace=0.28))
# rows grouped by base model, with a gap between the groups
ypos, labels, model_mid = [], [], {}
y = 0.0
for g in ("sol", "luna"):
    rows = [c for c in CONDS if c[0][0] == g][::-1]
    start = y
    for (model, cond), name in rows:
        ypos.append(((model, cond), y)); labels.append((y, name.split(", ", 1)[1])); y += 1
    model_mid[g] = (start + y - 1) / 2
    y += 0.7
for (model, cond), yy in ypos:
    cnt = collections.Counter(v for k, v in items.items() if k[0] == model and k[1] == cond)
    n = sum(cnt.values()); left = 0
    for key, lab, col in CATS:
        w = 100 * cnt.get(key, 0) / n
        ax.barh(yy, w, left=left, color=col, height=0.6, edgecolor="white", linewidth=0.8)
        if w >= 9:
            ax.text(left + w / 2, yy, f"{w:.0f}", ha="center", va="center", fontsize=6.3,
                    color="white" if col == S.BLUE else S.INK)
        left += w
ax.set_yticks([l[0] for l in labels])
ax.set_yticklabels([l[1] for l in labels])
ax.tick_params(axis="y", length=0)
for g, name in (("luna", "GPT-6-Luna"), ("sol", "GPT-6-Sol")):
    ax.text(-0.355, model_mid[g], name, transform=ax.get_yaxis_transform(), rotation=90, ha="center", va="center",
            fontsize=7, fontweight="bold", color=S.INK)
lo = min(yy for (_, yy) in labels if True) if False else None
ax.set_ylim(-0.55, y - 0.15)
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xlabel("share of states (%)")
ax.grid(False)
ax.spines["left"].set_visible(False)
S.title(ax, "a", "What the state records", y=1.13)
S.key(ax, [(c[1], c[2]) for c in CATS], y=1.0, xs=[0.0, 0.3, 0.55])
# (b) outcomes by state content, pooled over models and conditions
groups = collections.defaultdict(lambda: [0, 0.0, 0.0])
for k, v in outc.items():
    *_, cat = k.split("/")
    g = GROUP.get(cat)
    if g and v["inc_u"] is not None:
        a = groups[g]; a[0] += v["n"]; a[1] += v["n"] * v["inc_u"]; a[2] += v["n"] * (v["exc"] or 0)
names = [c[0] for c in CATS]
x = np.arange(len(names))
inc = [groups[n][1] / groups[n][0] for n in names]; exc = [groups[n][2] / groups[n][0] for n in names]
for xi in x:
    S.bar(ax2, xi - 0.16, inc[xi], 0.28, S.RED)
    S.bar(ax2, xi + 0.16, exc[xi], 0.28, S.GRAY)
ax2.set_xticks(x)
ax2.set_xticklabels(["names the\nclass", "wrong\nrule", "only seen\nvalues"], fontsize=6.6)
for t, c in zip(ax2.get_xticklabels(), CATS):
    t.set_bbox(dict(boxstyle="square,pad=0.15", fc="none", ec="none"))
for xi, c in enumerate(CATS):
    ax2.plot([xi], [-0.045], marker="s", ms=4.2, color=c[2], transform=ax2.get_xaxis_transform(), clip_on=False)
ax2.set_ylim(0, 108)
ax2.set_yticks([0, 25, 50, 75, 100])
ax2.grid(axis="y", color="#ececec", lw=0.5)
ax2.set_axisbelow(True)
ax2.set_ylabel("rate in the test program (%)")
ax2.set_xlim(-0.55, 2.55)
ax2.tick_params(axis="x", length=0, pad=11)
ax2.grid(axis="x", visible=False)
S.title(ax2, "b", "What the program does", y=1.13)
S.key(ax2, [("unseen excluded", S.RED), ("non-members kept", S.GRAY)], y=1.0, xs=[0.0, 0.5])
fig.savefig(ROOT / "figures/state_content.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/state_content.pdf")
