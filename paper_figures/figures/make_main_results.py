"""Main results figure. (a) Generalization-precision plane: each method moves from learning from feedback alone (open)
to learning with the lesson (filled); (b) test accuracy and (c) single-cell accuracy for the same conditions. Reads
data/main_table_fb.json, data/gepa_explicit.json, data/extra_fb.json, data/review_analysis2.json; writes
figures/main_results.pdf. Run from the repository root: python figures/make_main_results.py"""
import glob
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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
# one colour per method (Okabe-Ito, colour-blind safe) and a curvature that keeps the arrows from the crowded corner apart
COL = {"History": "#555555", "ACE": "#0072B2", "GEPA": "#E69F00", "DC": "#009E73", "TF-GRPO": "#CC79A7",
       "EvoSkill": "#D55E00", "RB": "#56B4E9"}
RAD = {"History": 0.0, "ACE": -0.12, "GEPA": 0.12, "DC": 0.0, "TF-GRPO": 0.0, "EvoSkill": 0.0, "RB": 0.0}

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

fig = plt.figure(figsize=(7.0, 2.55))
gs = fig.add_gridspec(1, 4, width_ratios=[1.62, 0.16, 0.72, 0.72], wspace=0.07, left=0.06, right=0.995, bottom=0.17, top=0.92)
ax = fig.add_subplot(gs[0])
axb = fig.add_subplot(gs[2])
axc = fig.add_subplot(gs[3], sharey=axb)

# (a) generalization-precision plane: arrows from feedback alone (open) to + lesson (filled), one colour per method
XL, YL = (-2, 72), (24, 103)
# faint regions: memorized exceptions (top left), learned category (top right), over-generalization (bottom)
ax.add_patch(Rectangle((-2, 80), 27, 23, fc="#f2f2f2", ec="none", zorder=0))
ax.add_patch(Rectangle((45, 80), 27, 23, fc="#edf2f9", ec="none", zorder=0))
ax.add_patch(Rectangle((-2, 24), 74, 38, fc="#faf5ef", ec="none", zorder=0))
ax.text(0.5, 102, "remembers the exceptions", ha="left", va="top", fontsize=6.8, color=MID, style="italic")
ax.text(71, 102, "learns the category", ha="right", va="top", fontsize=6.8, color=BLUE, style="italic")
ax.text(71, 25.5, "over-generalizes", ha="right", va="bottom", fontsize=6.8, color=REF, style="italic")
for name, short, a_s, a_h, ks, kh in rows:
    x0, y0, x1, y1 = cells[ks]["inc_unseen"], cells[ks]["exc"], cells[kh]["inc_unseen"], cells[kh]["exc"]
    col = COL[short]
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=col, lw=1.25, shrinkA=3.4, shrinkB=3.6, mutation_scale=8.5,
                                connectionstyle=f"arc3,rad={RAD[short]}"))
    ax.plot(x0, y0, "o", ms=4.3, mfc="white", mec=col, mew=0.9, zorder=3)
    ax.plot(x1, y1, "o", ms=4.3, mfc=col, mec=col, zorder=3)
ax.plot(frozen["inc_unseen"], frozen["exc"], marker="s", ms=4.0, mfc=GRAY, mec="white", mew=0.5, ls="none", zorder=4)
ax.set_xlim(*XL)
ax.set_ylim(*YL)
ax.set_xticks([0, 20, 40, 60])
ax.set_yticks([30, 50, 70, 90])
ax.set_xlabel("unseen members excluded (%)")
ax.set_ylabel("non-members kept (%)")
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
ax.text(-0.11, 1.02, "(a)", transform=ax.transAxes, fontsize=8.5, fontweight="bold", va="bottom")
mk = lambda **k: plt.Line2D([], [], ls="none", ms=4.3, **k)
h = [plt.Line2D([], [], color=COL[r[1]], lw=1.4, marker="o", ms=4.3, label=r[1]) for r in rows]
lg = ax.legend(handles=h, loc="lower right", bbox_to_anchor=(1.0, 0.16), ncol=2, fontsize=6.9, handlelength=1.5,
               handletextpad=0.4, columnspacing=1.0, labelspacing=0.35, borderaxespad=0.2)
ax.add_artist(lg)
key = [mk(marker="o", mfc="white", mec=DARK, mew=0.9, label="feedback alone"), mk(marker="o", mfc=DARK, mec=DARK, label="+ lesson"),
       mk(marker="s", mfc=GRAY, mec="white", label="frozen")]
ax.legend(handles=key, loc="lower right", bbox_to_anchor=(1.0, 0.065), ncol=3, fontsize=6.7, handletextpad=0.2,
          columnspacing=0.8, borderaxespad=0.2)

# (b, c) accuracy per level with the certifying model and with GPT-6-Sol: frozen agent, history reference, and the mean
# of ACE and Dynamic Cheatsheet learning from feedback alone and with the lesson; the gray band is the frozen staircase
sol = load("sol6_levels.json")
pct = lambda l: [100 * x for x in l]
mean2 = lambda a, b: [(x + y) / 2 for x, y in zip(a, b)]
luna = {"frozen": pct(main["frozen"]), "history": pct(extra["history"]["levels"]),
        "self": mean2(pct(main["methods"]["ACE/self"]["levels"]), pct(main["methods"]["DC-Cu/self"]["levels"])),
        "lesson": mean2(pct(main["methods"]["ACE/hint"]["levels"]), pct(main["methods"]["DC-Cu/hint"]["levels"]))}
sol6 = {"frozen": pct(sol["frozen"]), "history": pct(sol["hist"]), "self": mean2(pct(sol["ace/self"]), pct(sol["dc/self"])),
        "lesson": mean2(pct(sol["ace/hint"]), pct(sol["dc/hint"]))}
LINES = [("frozen", "frozen agent", GRAY, (0, (3, 2)), "s", GRAY), ("history", "history", COL["History"], (0, (1, 1.3)), "o", "white"),
         ("self", "ACE/DC, feedback alone", "#b5473a", "-", "o", "white"),
         ("lesson", "ACE/DC + lesson", "#1f4e8c", "-", "o", "#1f4e8c")]
X = [1, 2, 3, 4]
for axx, data, tag, name in ((axb, luna, "(b)", "GPT-6-Luna"), (axc, sol6, "(c)", "GPT-6-Sol")):
    axx.fill_between(X, [76, 56, 36, 16], [84, 64, 44, 24], color="#e6e6e6", lw=0, zorder=0)
    for k, lab, col, ls, mk_, fc in LINES:
        axx.plot(X, data[k], color=col, ls=ls, lw=1.3, zorder=2, label=lab)
        axx.plot(X, data[k], mk_, ms=3.6, mfc=fc, mec=col, mew=0.9, zorder=3)
    axx.set_xticks(X)
    axx.set_xticklabels(["L1", "L2", "L3", "L4"])
    axx.set_xlim(0.8, 4.2)
    axx.set_ylim(0, 100)
    axx.set_yticks([0, 25, 50, 75, 100])
    axx.grid(axis="y", color="#ececec", lw=0.5)
    axx.set_axisbelow(True)
    for s_ in ("top", "right"):
        axx.spines[s_].set_visible(False)
    axx.text(-0.02 if axx is axc else -0.3, 1.02, tag, transform=axx.transAxes, fontsize=8.5, fontweight="bold", va="bottom")
    axx.text(0.12 if axx is axc else 0.02, 1.02, name, transform=axx.transAxes, fontsize=8, va="bottom",
             ha="left") if False else axx.annotate(name, xy=(0, 1.02), xycoords="axes fraction", xytext=(17, 0),
                                                   textcoords="offset points", fontsize=8, va="bottom")
axb.set_ylabel("test accuracy (%)")
axc.tick_params(axis="y", labelleft=False)
axc.text(4.15, 27, "frozen\nstaircase", fontsize=6.3, color=MID, ha="right", va="bottom", linespacing=0.95, style="italic")
lh = [plt.Line2D([], [], color=c, ls=ls, lw=1.3, marker=m, ms=3.6, mfc=fc, mec=c, label=l) for _, l, c, ls, m, fc in LINES]
axb.legend(handles=lh, loc="lower left", bbox_to_anchor=(0.0, 0.0), fontsize=6.4, handlelength=2.0, handletextpad=0.35,
           labelspacing=0.25, borderaxespad=0.2)

fig.savefig(ROOT / "figures/main_results.pdf", pad_inches=0.02)
print("wrote figures/main_results.pdf")
