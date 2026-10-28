"""Analysis figure (one column): revealed vs unseen members excluded, and exclusion of the never-shown member under
standard and rewarded practice. Reads data/main_table_fb.json, data/gepa_explicit.json, data/extra_fb.json, data/sol6_levels.json,
data/review_analysis.json and data/review_analysis2.json; writes figures/results_overview.pdf.
Run from the repository root: python figures/make_results_figure.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as S
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
main, gepa, extra, sol = load("main_table_fb.json"), load("gepa_explicit.json"), load("extra_fb.json"), load("sol6_levels.json")
ra, ra2 = load("review_analysis.json"), load("review_analysis2.json")
cells = ra2["all_cells"]
S.apply()
fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.95), gridspec_kw=dict(wspace=0.5))

# (a) revealed vs unseen members excluded
ax = axes[0]
grp = [("ACE", ra["cells_diag"]["ace/self"]["inc_revealed"], cells["ace/self"]["inc_unseen"]),
       ("GEPA", 100 * gepa["neutral_inc_revealed"]["self"], cells["gepaN/self"]["inc_unseen"]),
       ("DC", ra["cells_diag"]["dc/self"]["inc_revealed"], cells["dc/self"]["inc_unseen"]),
       ("Hist.", ra["cells_diag"]["hist/ref"]["inc_revealed"], cells["hist/ref"]["inc_unseen"])]
for i, (lab, rev, uns) in enumerate(grp):
    S.bar(ax, i - 0.19, rev, 0.36, S.LBLUE)
    S.bar(ax, i + 0.19, uns, 0.36, S.RED)
ax.set_xticks(range(4))
ax.set_xticklabels([g[0] for g in grp])
ax.set_xlim(-0.6, 3.6)
ax.set_ylim(0, 108)
ax.set_yticks([0, 25, 50, 75, 100])
ax.grid(axis="x", visible=False)
ax.set_ylabel("members excluded (%)")
S.title(ax, "a", "Revealed vs. unseen", y=1.13)
S.key(ax, [("revealed", S.LBLUE), ("unseen", S.RED)], y=1.0, dx=0.5)

# (b) exclusion of the never-shown member m2, standard vs rewarded practice
ax = axes[1]
pairs = [("ACE", "ace/self", "rg_ace/self"), ("GEPA", "gepaN/self", "rg_gepa/self"), ("DC", "dc/self", "rg_dc/self"),
         ("Hist.", "hist/ref", "rg_hist/self")]
for i, (lab, a, b) in enumerate(pairs):
    S.bar(ax, i - 0.19, cells[a]["inc_m2"], 0.36, S.GRAY, ymax=54)
    S.bar(ax, i + 0.19, cells[b]["inc_m2"], 0.36, S.BLUE, ymax=54)
ax.set_xticks(range(4))
ax.set_xticklabels([p[0] for p in pairs])
ax.set_xlim(-0.6, 3.6)
ax.set_ylim(0, 54)
ax.set_yticks([0, 10, 20, 30, 40, 50])
ax.grid(axis="x", visible=False)
ax.set_ylabel("unseen $m_2$ excluded (%)")
S.title(ax, "b", "Rewarded practice", y=1.13)
S.key(ax, [("standard", S.GRAY), ("rewarded", S.BLUE)], y=1.0, dx=0.52)

fig.savefig(ROOT / "figures/results_overview.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/results_overview.pdf")
