"""Accuracy per level (difficulty curve): frozen agent, history reference, and the mean of ACE, GEPA, and Dynamic
Cheatsheet in the self, +hypothesize, and +lesson conditions. Writes figures/levels_curve.pdf. Run from the repository root."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
main, gepa, extra, ra2 = load("main_table_fb.json"), load("gepa_explicit.json"), load("extra_fb.json"), load("review_analysis2.json")
lv = ra2["levels"]
pct = lambda l: [100 * x for x in l]
mean3 = lambda ls: [sum(v) / 3 for v in zip(*ls)]
self3 = mean3([pct(main["methods"]["ACE/self"]["levels"]), pct(gepa["neutral_self"]["levels"]), pct(main["methods"]["DC-Cu/self"]["levels"])])
les3 = mean3([pct(main["methods"]["ACE/hint"]["levels"]), pct(gepa["neutral_hint"]["levels"]), pct(main["methods"]["DC-Cu/hint"]["levels"])])
hyp3 = mean3([pct(lv[f"hypm_{m}/hint"]) for m in ("ace", "gepa", "dc")])
series = [("frozen", pct(main["frozen"]), "#64748b", (0, (3, 2)), "o"),
          ("history", pct(extra["history"]["levels"]), "#2f5fb3", (0, (1, 1.5)), "s"),
          ("methods, self", self3, "#b8433a", "-", "o"),
          ("methods + hypothesize", hyp3, "#7f9ed6", "-", "^"),
          ("methods + lesson", les3, "#2e7d4f", "-", "D")]
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
                     "font.size": 7, "axes.edgecolor": "#94a3b8", "axes.linewidth": 0.6, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(3.3, 1.9))
for lab, ys, c, ls, mk in series:
    ax.plot([1, 2, 3, 4], ys, color=c, ls=ls, lw=1.3, marker=mk, ms=3.2, label=lab)
ax.plot([1, 2, 3, 4], [80, 60, 40, 20], color="#cbd2dc", lw=4, zorder=0, solid_capstyle="round", alpha=0.6)
ax.text(4.08, 20, "staircase", fontsize=6, color="#94a3b8", va="center")
ax.set_xticks([1, 2, 3, 4])
ax.set_xticklabels(["Level 1", "Level 2", "Level 3", "Level 4"])
ax.set_ylabel("test accuracy (%)")
ax.set_ylim(10, 95)
ax.set_xlim(0.8, 4.55)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e2e6ec", lw=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=6, loc="upper right", handlelength=1.6)
fig.savefig(ROOT / "figures/levels_curve.pdf", bbox_inches="tight", pad_inches=0.02)
print([round(x, 1) for x in self3], [round(x, 1) for x in hyp3], [round(x, 1) for x in les3])
