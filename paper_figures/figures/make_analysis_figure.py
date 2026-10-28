"""Benchmark analyses figure: (a) single-cell outcome breakdown, (b) practice pass rate vs test generalization,
(c) practice cost vs test generalization. Reads data/bench_analysis.json; writes figures/analysis_overview.pdf.
Run from the repository root: python figures/make_analysis_figure.py"""
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as S
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/bench_analysis.json").read_text())
S.apply()
INK, SUB = S.INK, S.SUB
BLUE, LBLUE, GREEN, RED, GRAY, AMBER = S.BLUE, S.LBLUE, S.GREEN, S.RED, S.GRAY, S.AMBER
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.45), gridspec_kw=dict(width_ratios=[1.6, 1, 1], wspace=0.4))


def style(ax, title):
    tag, text = title.split("  ", 1)
    S.title(ax, tag.strip("()"), text, y=1.13)


# (a) outcome breakdown of single cells
ax = axes[0]
rows = [("History", "hist/ref"), ("ACE", "ace/self"), ("GEPA", "gepaN/self"), ("DC", "dc/self"), ("TF-GRPO", "tfgrpo/self"),
        ("EvoSkill", "evoskill/self"), ("RB", "rb/self")]
for i, (lab, k) in enumerate(rows):
    y = len(rows) - 1 - i
    left = 0
    for part, col in (("correct", GREEN), ("under", RED), ("over", AMBER)):
        v = d[k][part]
        ax.barh(y, v, left=left, color=col, height=0.62, edgecolor=S.BG, linewidth=0.8, zorder=3)
        left += v
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in rows][::-1])
ax.set_xlim(0, 100)
ax.set_xlabel("single test cells (%)")
from matplotlib.patches import Patch
S.key(ax, [("correct", GREEN), ("unseen counted", RED), ("non-member dropped", AMBER)], y=1.0, xs=[0.0, 0.22, 0.6])
style(ax, "(a)  How single cells fail")

# (b) practice pass rate vs single-cell accuracy
ax = axes[1]
pts = [("ACE", "ace/self", RED), ("GEPA", "gepaN/self", RED), ("DC", "dc/self", RED), ("TF-GRPO", "tfgrpo/self", RED),
       ("EvoSkill", "evoskill/self", RED), ("RB", "rb/self", RED), ("History", "hist/ref", BLUE),
       ("ACE+L", "ace/hint", GREEN), ("DC+L", "dc/hint", GREEN), ("GEPA+L", "gepaN/hint", GREEN)]
off = {"ACE": (3, 2), "GEPA": (3, -6), "DC": (-12, 4), "TF-GRPO": (-2, 6), "EvoSkill": (4, -3), "RB": (2, 6),
       "History": (-26, 4), "ACE+L": (3, 2), "DC+L": (-24, 3), "GEPA+L": (-32, -3)}
for lab, k, c in pts:
    x, y = d[k]["practice_pass"], d[k]["correct"]
    ax.scatter(x, y, s=24, color=c, edgecolor="white", linewidth=0.7, zorder=3)
    ax.annotate(lab, (x, y), textcoords="offset points", xytext=off[lab], fontsize=5.6, color=INK)
ax.set_xlim(-5, 105)
ax.set_ylim(-3, 52)
ax.set_xlabel("practice levels passed (%)")
ax.set_ylabel("single cells correct (%)")
style(ax, "(b)  Passing practice is not learning")

# (c) practice cost vs single-cell accuracy
ax = axes[2]
cost = [("ACE", "ace/self", RED), ("GEPA", "gepaN/self", RED), ("DC", "dc/self", RED), ("TF-GRPO", "tfgrpo/self", RED),
        ("EvoSkill", "evoskill/self", RED), ("RB", "rb/self", RED), ("History", "hist/ref", BLUE),
        ("ACE+L", "ace/hint", GREEN), ("DC+L", "dc/hint", GREEN), ("EvoSkill+L", "evoskill/hint", GREEN)]
off = {"ACE": (4, -7), "GEPA": (3, -6), "DC": (3, 3), "TF-GRPO": (-14, 4), "EvoSkill": (-36, 2), "RB": (3, 2),
       "History": (3, 2), "ACE+L": (3, 2), "DC+L": (3, 2), "EvoSkill+L": (-34, 7)}
for lab, k, c in cost:
    x, y = d[k]["practice_tokens_in"] / 20 / 1e6, d[k]["correct"]
    ax.scatter(x, y, s=24, color=c, edgecolor="white", linewidth=0.7, zorder=3)
    right = lab.startswith("EvoSkill")
    ax.annotate(lab, (x, y), textcoords="offset points", xytext=(3, 7) if right else off[lab], fontsize=5.6, color=INK,
                ha="right" if right else "left")
ax.set_xscale("log")
ax.set_ylim(-3, 52)
ax.set_xlabel("practice input tokens per chain (M)")
ax.set_ylabel("single cells correct (%)")
style(ax, "(c)  Practice cost and learning")

axes[0].grid(axis="y", visible=False)
for a in axes[1:]:
    S.key(a, [("self", RED), ("history", BLUE), ("+ lesson", GREEN)], x=0.12, y=1.0, marker="o", size=4)
fig.savefig(ROOT / "figures/analysis_overview.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/analysis_overview.pdf")
