"""Accuracy per level for the two base models side by side (GPT-6-Luna, GPT-6-Sol): frozen agent, history reference, and
the mean of ACE and Dynamic Cheatsheet in the self and +lesson conditions. Writes figures/backbone_levels.pdf."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
main, extra, sol = load("main_table_fb.json"), load("extra_fb.json"), load("sol6_levels.json")
pct = lambda l: [100 * x for x in l]
mean2 = lambda a, b: [(x + y) / 2 for x, y in zip(a, b)]
luna = {"frozen": pct(main["frozen"]), "history": pct(extra["history"]["levels"]),
        "self": mean2(pct(main["methods"]["ACE/self"]["levels"]), pct(main["methods"]["DC-Cu/self"]["levels"])),
        "lesson": mean2(pct(main["methods"]["ACE/hint"]["levels"]), pct(main["methods"]["DC-Cu/hint"]["levels"]))}
sol6 = {"frozen": pct(sol["frozen"]), "history": pct(sol["hist"]), "self": mean2(pct(sol["ace/self"]), pct(sol["dc/self"])),
        "lesson": mean2(pct(sol["ace/hint"]), pct(sol["dc/hint"]))}
STY = [("frozen", "frozen", "#64748b", (0, (3, 2)), "o"), ("history", "history", "#2f5fb3", (0, (1, 1.5)), "s"),
       ("self", "ACE/DC, self", "#b8433a", "-", "o"), ("lesson", "ACE/DC + lesson", "#2e7d4f", "-", "D")]
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
                     "font.size": 7, "axes.edgecolor": "#94a3b8", "axes.linewidth": 0.6, "pdf.fonttype": 42})
fig, axes = plt.subplots(1, 2, figsize=(4.6, 1.65), sharey=True, gridspec_kw=dict(wspace=0.12))
for ax, data, title in ((axes[0], luna, "GPT-6-Luna (certifying model)"), (axes[1], sol6, "GPT-6-Sol")):
    ax.plot([1, 2, 3, 4], [80, 60, 40, 20], color="#cbd2dc", lw=4, zorder=0, solid_capstyle="round", alpha=0.6)
    for k, lab, c, ls, mk in STY:
        ax.plot([1, 2, 3, 4], data[k], color=c, ls=ls, lw=1.3, marker=mk, ms=3.2, label=lab)
    ax.set_title(title, fontsize=7.5, loc="left", fontweight="bold", color="#1e293b")
    ax.set_xticks([1, 2, 3, 4]); ax.set_xticklabels(["L1", "L2", "L3", "L4"])
    ax.set_ylim(0, 100)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e2e6ec", lw=0.5); ax.set_axisbelow(True)
axes[0].set_ylabel("test accuracy (%)")
axes[1].legend(frameon=False, fontsize=6, loc="lower left", handlelength=1.6)
fig.savefig(ROOT / "figures/backbone_levels.pdf", bbox_inches="tight", pad_inches=0.02)
print("luna", {k: [round(x) for x in v] for k, v in luna.items()}); print("sol6", {k: [round(x) for x in v] for k, v in sol6.items()})
