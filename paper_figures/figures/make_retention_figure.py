"""Appendix figure: retention of every rule. For each condition, the rate of excluding unseen members (top row) and of
keeping non-members (bottom row) of rule j when tested at level k >= j. Reads data/retention.json; writes
figures/retention.pdf. Run from the repository root."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as S
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/retention.json").read_text())
S.apply()
# one muted blue ramp for both rows, light enough that dark numbers stay readable
RAMP = LinearSegmentedColormap.from_list("ramp", ["#ffffff", "#7f9cc6"]).with_extremes(bad="white")
conds = [("luna/ace/self", "Luna, ACE"), ("luna/dc/self", "Luna, DC"), ("luna/hist", "Luna, history"),
         ("sol6/ace/self", "Sol, ACE"), ("sol6/dc/self", "Sol, DC"), ("sol6/hist", "Sol, history")]
fig, axes = plt.subplots(2, 6, figsize=(7.0, 2.7), gridspec_kw=dict(wspace=0.12, hspace=0.32))
for row, (metric, lab) in enumerate((("inc_u", "unseen members excluded"), ("exc", "non-members kept"))):
    for col, (key, name) in enumerate(conds):
        ax = axes[row, col]
        m = np.full((4, 4), np.nan)
        for k in range(1, 5):
            for j in range(1, k + 1):
                v = d[key][metric].get(f"L{k}R{j}")
                if v is not None:
                    m[k - 1, j - 1] = v
        ax.imshow(m, cmap=RAMP, vmin=0, vmax=100, interpolation="nearest")
        for k in range(4):
            for j in range(4):
                if not np.isnan(m[k, j]):
                    ax.text(j, k, f"{m[k, j]:.0f}", ha="center", va="center", fontsize=6.2, color=S.INK)
        ax.set_xticks(range(4)); ax.set_yticks(range(4))
        ax.set_xticklabels([f"R{j}" for j in range(1, 5)], fontsize=6.3)
        ax.set_yticklabels([f"L{k}" for k in range(1, 5)] if col == 0 else [], fontsize=6.3)
        ax.tick_params(length=0)
        ax.grid(False)
        for s_ in ax.spines.values():
            s_.set_visible(False)
        if row == 0:
            ax.set_title(name, fontsize=7.2, pad=3)
    axes[row, 0].set_ylabel(lab, fontsize=7)
fig.savefig(ROOT / "figures/retention.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/retention.pdf")
