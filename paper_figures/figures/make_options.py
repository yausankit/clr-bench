"""Three candidate presentations of the main results (20 chains, version 0, levels 1-4, explicit practice feedback).
Reads data/main_table_fb.json and writes
  figures/opt1_dumbbell.pdf  overall accuracy: frozen, self and hint per method (column width)
  figures/opt2_delta.pdf     per-level accuracy minus frozen, self and hint (full width, 2 x 3 panels)
  figures/opt3_diag.pdf      value-level diagnostics: inc (unseen members included) vs exc (non-members kept)
Run from the repository root: python figures/make_options.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/main_table_fb.json").read_text())
_g = ROOT / "data/gepa_explicit.json"
if _g.exists():  # main results use GEPA with the neutral format note
    _g = json.loads(_g.read_text())
    d["methods"]["GEPA*/self"]["levels"] = _g["neutral_self"]["levels"]
    d["methods"]["GEPA*/hint"]["levels"] = _g["neutral_hint"]["levels"]
KEYS = ["ACE", "GEPA*", "DC-Cu", "TF-GRPO", "EvoSkill", "ReasoningBank"]
NAME = {k: k.rstrip("*") for k in KEYS}
SELF, HINT, FROZEN = "#1f6fb4", "#d9541e", "0.45"
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "legend.fontsize": 6.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "pdf.fonttype": 42})
frozen = [100 * x for x in d["frozen"]]
f_avg = sum(frozen) / 4
lv = lambda k, arm: [100 * x for x in d["methods"][f"{k}/{arm}"]["levels"]]
avg = lambda k, arm: sum(lv(k, arm)) / 4

# Option 1: dumbbell of overall accuracy
fig, ax = plt.subplots(figsize=(3.3, 2.0))
order = sorted(KEYS, key=lambda k: avg(k, "hint"))
for i, k in enumerate(order):
    s, h = avg(k, "self"), avg(k, "hint")
    ax.plot([min(s, h, f_avg), max(s, h, f_avg)], [i, i], color="0.8", linewidth=2, zorder=1)
    ax.scatter(s, i, color=SELF, marker="o", s=22, zorder=3, label="Self" if i == 0 else None)
    ax.scatter(h, i, color=HINT, marker="^", s=26, zorder=3, label="+ lesson" if i == 0 else None)
ax.axvline(f_avg, color=FROZEN, linestyle="--", linewidth=1, label="Frozen", zorder=2)
ax.set_yticks(range(len(order)), [NAME[k] for k in order])
ax.set_xlabel("Test accuracy, levels 1-4 (%)")
ax.grid(axis="x", linewidth=0.4, alpha=0.5)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="lower right", frameon=False, ncol=1)
fig.tight_layout()
fig.savefig(ROOT / "figures/opt1_dumbbell.pdf", bbox_inches="tight")

# Option 2: per-level gain over the frozen agent
levels = [1, 2, 3, 4]
fig, axes = plt.subplots(2, 3, figsize=(7.0, 3.0), sharey=True, sharex=True)
for ax, k in zip(axes.flat, KEYS):
    ax.axhline(0, color=FROZEN, linestyle="--", linewidth=1, label="Frozen")
    ax.plot(levels, [a - b for a, b in zip(lv(k, "self"), frozen)], color=SELF, marker="s", markersize=2.5,
            linewidth=1.3, label="Self")
    ax.plot(levels, [a - b for a, b in zip(lv(k, "hint"), frozen)], color=HINT, linestyle=":", marker="^",
            markersize=3, linewidth=1.3, label="+ lesson")
    ax.set_title(NAME[k])
    ax.set_xticks(levels, [f"L{x}" for x in levels])
    ax.grid(axis="y", linewidth=0.4, alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
for row in axes:
    row[0].set_ylabel("Gain over Frozen (pts)")
h, l = axes[0][0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.03))
fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=0.8, h_pad=0.8)
fig.savefig(ROOT / "figures/opt2_delta.pdf", bbox_inches="tight")

# Option 3: diagnostics, inc (x) vs exc (y), arrow from self to hint
MARK = dict(zip(KEYS, ["o", "s", "D", "v", "P", "X"]))
LABEL_OFFSET = {"ACE": (6, 6), "GEPA*": (-30, -10), "DC-Cu": (-24, 6), "TF-GRPO": (5, -8), "EvoSkill": (5, -3),
                "ReasoningBank": (5, -3)}
diag = json.loads((ROOT / "data/review_analysis.json").read_text())["cells_diag"]
for _k, _v in json.loads((ROOT / "data/review_analysis2.json").read_text())["all_cells"].items():
    diag.setdefault(_k, _v)
CODE = {"ACE": "ace", "GEPA*": "gepaN", "DC-Cu": "dc", "TF-GRPO": "tfgrpo", "EvoSkill": "evoskill", "ReasoningBank": "rb"}
fig, ax = plt.subplots(figsize=(3.3, 2.6))
for key, name, off in (("frozen/ref", "Frozen", (4, 3)), ("hist/ref", "History", (4, -8)),
                       ("histhint/ref", "History+lesson", (-30, 6)), ("nameoracle/ref", "Name oracle", (-28, -9))):
    ax.scatter(diag[key]["inc_unseen"], diag[key]["exc"], color=FROZEN, marker="*", s=30, zorder=3)
    ax.annotate(name, (diag[key]["inc_unseen"], diag[key]["exc"]), textcoords="offset points", xytext=off, fontsize=6)
for k in KEYS:
    code = CODE[k]
    si, se = diag[f"{code}/self"]["inc_unseen"], diag[f"{code}/self"]["exc"]
    hi, he = diag[f"{code}/hint"]["inc_unseen"], diag[f"{code}/hint"]["exc"]
    ax.annotate("", xy=(hi, he), xytext=(si, se), arrowprops=dict(arrowstyle="->", color="0.6", linewidth=0.8))
    ax.scatter(si, se, color=SELF, marker=MARK[k], s=20, zorder=3)
    ax.scatter(hi, he, color=HINT, marker=MARK[k], s=20, zorder=3)
    ax.annotate(NAME[k], (si, se), textcoords="offset points", xytext=LABEL_OFFSET[k], fontsize=6)
ax.set_xlim(-3, 80); ax.set_ylim(25, 100)
ax.set_xlabel("Unseen members excluded by the rule, inc$_u$ (%)")
ax.set_ylabel("Non-members kept, exc (%)")
ax.grid(linewidth=0.4, alpha=0.5)
ax.spines[["top", "right"]].set_visible(False)
ax.scatter([], [], color=SELF, marker="o", s=20, label="Self")
ax.scatter([], [], color=HINT, marker="o", s=20, label="+ lesson")
ax.legend(loc="lower right", frameon=False)
fig.tight_layout()
fig.savefig(ROOT / "figures/opt3_diag.pdf", bbox_inches="tight")
print("wrote figures/opt1_dumbbell.pdf, figures/opt2_delta.pdf, figures/opt3_diag.pdf")
