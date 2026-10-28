"""Rough overview figure: one level of a chain (task, practice feedback, test). Writes figures/overview.pdf.
Run from the repository root: python figures/make_overview.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({"font.size": 6.5, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(3.4, 3.3))
ax.set_xlim(0, 10); ax.set_ylim(0, 13); ax.axis("off")


def box(x, y, w, h, title, lines, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.25", linewidth=0.8,
                                edgecolor=color, facecolor="white"))
    ax.text(x + 0.2, y + h - 0.35, title, fontsize=7, fontweight="bold", color=color, va="top")
    for i, (text, style) in enumerate(lines):
        ax.text(x + 0.25, y + h - 1.05 - 0.62 * i, text, va="top", color=style.get("c", "black"),
                fontstyle=style.get("s", "normal"))


box(0.1, 8.6, 9.8, 4.1, "Task (level 1)", [
    ("Count reimbursable flight segments per department.", {}),
    ("Rule: segments in review queue B8 are not counted.", {}),
    ("Field note: Lufthansa is in review queue B8.", {}),
    ("Hidden: founding members of Star Alliance (not shown)", {"c": "0.45", "s": "italic"}),
], "#333333")
box(0.1, 4.45, 9.8, 3.75, "Practice feedback (edits of a public example)", [
    ("Wrong on a hidden input: expected 16, got 17.", {}),
    ("'Thai Airways' is in review queue B8, like 'Lufthansa'.", {"c": "#1f6fb4"}),
    ("'ITA Airways' is not in review queue B8.", {"c": "#d9541e"}),
    ("The agent updates its state (playbook, prompt, ...).", {"c": "0.45", "s": "italic"}),
], "#1f6fb4")
box(0.1, 0.1, 9.8, 3.35, "Test (sum over departments)", [
    ("Unseen members: United Airlines, SAS -> exclude", {"c": "#1f6fb4"}),
    ("Look-alike non-members: Norse Atlantic UK -> keep", {"c": "#d9541e"}),
    ("A frozen agent excludes only Lufthansa and fails.", {"c": "0.45", "s": "italic"}),
], "#333333")
for y0, y1 in ((8.6, 8.2), (4.45, 3.45)):
    ax.annotate("", xy=(5, y1), xytext=(5, y0), arrowprops=dict(arrowstyle="->", color="0.4", linewidth=0.9))
fig.savefig(ROOT / "figures/overview.pdf", bbox_inches="tight")
print("wrote figures/overview.pdf")
