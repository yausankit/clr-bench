"""Generalization-specificity plane (GPT-6-Luna, 20 chains): each method moves from learning from feedback alone (open)
to learning with the lesson (filled); x is the rate of excluding unseen members, y the rate of keeping non-members.
Reads data/main_table_fb.json, data/gepa_explicit.json, data/extra_fb.json, data/review_analysis2.json; writes
figures/plane.pdf. Run from the repository root."""
import glob
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

for f in glob.glob("/usr/local/texlive/*/texmf-dist/fonts/opentype/public/libertine/LinLibertine_R*.otf"):
    fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Linux Libertine O", "font.size": 8, "axes.linewidth": 0.6, "axes.edgecolor": "#333333",
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                     "xtick.color": "#333333", "ytick.color": "#333333", "axes.labelcolor": "#222222",
                     "legend.frameon": False, "pdf.fonttype": 42, "mathtext.fontset": "custom",
                     "mathtext.rm": "Linux Libertine O"})

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
main, gepa, extra, cells = load("main_table_fb.json"), load("gepa_explicit.json"), load("extra_fb.json"), \
    load("review_analysis2.json")["all_cells"]
avg = lambda l: 100 * sum(l) / len(l)
DARK, BLUE, REF, GRAY, MID = "#222222", "#1f4e8c", "#b5651d", "#9a9a9a", "#7d7d7d"
# one colour per method (Okabe-Ito, colour-blind safe)
COL = {"History": "#555555", "ACE": "#0072B2", "GEPA": "#E69F00", "DC": "#009E73", "TF-GRPO": "#CC79A7",
       "EvoSkill": "#D55E00", "RB": "#56B4E9"}

# (name, short name, accuracy self, accuracy +lesson, cells key self, cells key +lesson)
rows = [("History", "History", avg(extra["history"]["levels"]), avg(extra["histhint"]["levels"]), "hist/ref", "histhint/ref"),
        ("ACE", "ACE", avg(main["methods"]["ACE/self"]["levels"]), avg(main["methods"]["ACE/hint"]["levels"]), "ace/self", "ace/hint"),
        ("GEPA", "GEPA", avg(gepa["neutral_self"]["levels"]), avg(gepa["neutral_hint"]["levels"]), "gepaN/self", "gepaN/hint"),
        ("Dynamic Cheatsheet", "DC", avg(main["methods"]["DC-Cu/self"]["levels"]), avg(main["methods"]["DC-Cu/hint"]["levels"]),
         "dc/self", "dc/hint"),
        ("Training-Free GRPO", "TF-GRPO", avg(main["methods"]["TF-GRPO/self"]["levels"]),
         avg(main["methods"]["TF-GRPO/hint"]["levels"]), "tfgrpo/self", "tfgrpo/hint"),
        ("EvoSkill", "EvoSkill", avg(main["methods"]["EvoSkill/self"]["levels"]), avg(main["methods"]["EvoSkill/hint"]["levels"]),
         "evoskill/self", "evoskill/hint"),
        ("ReasoningBank", "RB", avg(main["methods"]["ReasoningBank/self"]["levels"]),
         avg(main["methods"]["ReasoningBank/hint"]["levels"]), "rb/self", "rb/hint")]
frozen = {"acc": avg(main["frozen"]), **{k: cells["frozen/ref"][k] for k in ("single", "inc_unseen", "exc")}}

fig, ax = plt.subplots(figsize=(3.4, 2.75))

# (a) generalization-precision plane: arrows from feedback alone (open) to + lesson (filled), one colour per method
XL, YL = (-2, 72), (24, 103)
# corner labels: memorized exceptions (top left), learned category (top right), over-generalization (bottom)
ax.text(0.5, 102, "remembers the exceptions", ha="left", va="top", fontsize=6.8, color=MID, style="italic")
ax.text(71, 102, "learns the category", ha="right", va="top", fontsize=6.8, color=BLUE, style="italic")
ax.text(71, 25.5, "over-generalizes", ha="right", va="bottom", fontsize=6.8, color=REF, style="italic")
for name, short, a_s, a_h, ks, kh in rows:
    x0, y0, x1, y1 = cells[ks]["inc_unseen"], cells[ks]["exc"], cells[kh]["inc_unseen"], cells[kh]["exc"]
    col = COL[short]
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=col, lw=1.25, shrinkA=3.4, shrinkB=3.6, mutation_scale=8.5,
                                connectionstyle="arc3,rad=0"))
    ax.plot(x0, y0, "o", ms=4.3, mfc="white", mec=col, mew=0.9, zorder=3)
    ax.plot(x1, y1, "o", ms=4.3, mfc=col, mec=col, zorder=3)
ax.plot(frozen["inc_unseen"], frozen["exc"], marker="s", ms=4.0, mfc=GRAY, mec="white", mew=0.5, ls="none", zorder=4)
# inset: frozen and Training-Free GRPO, which overlap in the top-left corner
ZX, ZY = (0.2, 2.2), (93.3, 96.7)
ins = ax.inset_axes([0.28, 0.47, 0.25, 0.19])
x0, y0, x1, y1 = (cells[k][m] for k in ("tfgrpo/self", "tfgrpo/hint") for m in ("inc_unseen", "exc"))
col = COL["TF-GRPO"]
ins.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=2,
             arrowprops=dict(arrowstyle="-|>", color=col, lw=1.0, shrinkA=3.4, shrinkB=3.6, mutation_scale=7))
ins.plot(x0, y0, "o", ms=4.3, mfc="white", mec=col, mew=0.9, zorder=3)
ins.plot(x1, y1, "o", ms=4.3, mfc=col, mec=col, zorder=3)
ins.plot(frozen["inc_unseen"], frozen["exc"], marker="s", ms=4.0, mfc=GRAY, mec="white", mew=0.5, ls="none", zorder=4)
ins.set_xlim(*ZX)
ins.set_ylim(*ZY)
ins.set_xticks([0.5, 1, 1.5, 2])
ins.set_xticklabels(["0.5", "1", "1.5", "2"])
ins.set_yticks([94, 95, 96])
ins.tick_params(labelsize=5.8, length=1.8, pad=1.2)
for s_ in ins.spines.values():
    s_.set_linewidth(0.5)
    s_.set_edgecolor(MID)
    s_.set_linestyle((0, (2, 1.5)))
ins.set_facecolor("white")
ins.set_zorder(6)
ax.indicate_inset_zoom(ins, edgecolor=MID, lw=0.5, ls=(0, (2, 1.5)), alpha=1)
ax.set_xlim(*XL)
ax.set_ylim(*YL)
ax.set_xticks([0, 20, 40, 60])
ax.set_yticks([30, 50, 70, 90])
ax.set_xlabel("unseen members excluded (%)")
ax.set_ylabel("non-members kept (%)")
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
mk = lambda **k: plt.Line2D([], [], ls="none", ms=4.3, **k)
h = [plt.Line2D([], [], color=COL[r[1]], lw=1.4, marker="o", ms=4.3, label=r[1]) for r in rows]
h.append(mk(marker="s", mfc=GRAY, mec="white", label="frozen"))
lg = ax.legend(handles=h, loc="lower right", bbox_to_anchor=(1.0, 0.16), ncol=2, fontsize=6.9, handlelength=1.5,
               handletextpad=0.4, columnspacing=1.0, labelspacing=0.35, borderaxespad=0.2)
ax.add_artist(lg)
key = [mk(marker="o", mfc="white", mec=DARK, mew=0.9, label="feedback alone"), mk(marker="o", mfc=DARK, mec=DARK, label="+ lesson")]
ax.legend(handles=key, loc="lower right", bbox_to_anchor=(1.0, 0.065), ncol=2, fontsize=6.7, handletextpad=0.2,
          columnspacing=0.8, borderaxespad=0.2)

fig.savefig(ROOT / "figures/plane.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/plane.pdf")
