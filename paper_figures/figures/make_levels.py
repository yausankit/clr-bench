"""Per-level test accuracy of each method (self and hint) against the frozen agent: 20 chains, version 0, levels 1-4,
explicit practice feedback. Reads data/main_table_fb.json and writes figures/levels.pdf.
Run from the repository root: python figures/make_levels.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/main_table_fb.json").read_text())
frozen = [100 * x for x in d["frozen"]]
methods = ["ACE", "GEPA*", "DC-Cu", "TF-GRPO", "EvoSkill", "ReasoningBank"]
levels = [1, 2, 3, 4]

plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "legend.fontsize": 6.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "pdf.fonttype": 42})
fig, axes = plt.subplots(2, 3, figsize=(7.0, 3.0), sharey=True, sharex=True)
for ax, m in zip(axes.flat, methods):
    self_ = [100 * x for x in d["methods"][f"{m}/self"]["levels"]]
    hint = [100 * x for x in d["methods"][f"{m}/hint"]["levels"]]
    ax.plot(levels, frozen, color="0.55", linestyle="--", marker="o", markersize=2.5, linewidth=1, label="Frozen")
    ax.plot(levels, self_, color="#1f6fb4", marker="s", markersize=2.5, linewidth=1.3, label="Self")
    ax.plot(levels, hint, color="#d9541e", linestyle=":", marker="^", markersize=3, linewidth=1.3, label="Hint")
    ax.set_title(m.rstrip("*"))
    ax.set_xticks(levels, [f"L{k}" for k in levels])
    ax.set_ylim(0, 100)
    ax.grid(axis="y", linewidth=0.4, alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
for row in axes:
    row[0].set_ylabel("Test accuracy (%)")
handles, labels = axes[0][0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.03))
fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=0.8, h_pad=0.8)
fig.savefig(ROOT / "figures/levels.pdf", bbox_inches="tight")
print("wrote figures/levels.pdf")
