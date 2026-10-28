"""Main results figure: test accuracy per level for each method and the history reference, with GPT-6-Luna and GPT-6-Sol,
learning from feedback alone (open markers) and with the lesson in the update step (filled markers; GPT-6-Sol with the
lesson was run for ACE and Dynamic Cheatsheet). The gray band is the staircase of an agent that applies each rule only to
the example. Reads data/main_table_fb.json, data/gepa_explicit.json, data/extra_fb.json, data/sol6_all_methods.json,
data/sol6_levels.json; writes figures/main_levels.pdf. Run from the repository root."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as S
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
main, gepa, extra = load("main_table_fb.json"), load("gepa_explicit.json"), load("extra_fb.json")
sol_all, sol_lv, sol_h = load("sol6_all_methods.json")["sol"], load("sol6_levels.json"), load("sol6_hint.json")
pct = lambda l: [100 * x for x in l]
S.apply()
LUNA, SOL = "#b5473a", "#1f4e8c"

# (panel title, Luna self, Luna + lesson, Sol self, Sol + lesson or None)
M = main["methods"]
panels = [("History", pct(extra["history"]["levels"]), pct(extra["histhint"]["levels"]), sol_all["hist"]["levels"], sol_h["histhint"]["levels"]),
          ("ACE", pct(M["ACE/self"]["levels"]), pct(M["ACE/hint"]["levels"]), sol_all["ace"]["levels"], pct(sol_lv["ace/hint"])),
          ("Dynamic Cheatsheet", pct(M["DC-Cu/self"]["levels"]), pct(M["DC-Cu/hint"]["levels"]), sol_all["dc"]["levels"],
           pct(sol_lv["dc/hint"])),
          ("GEPA", pct(gepa["neutral_self"]["levels"]), pct(gepa["neutral_hint"]["levels"]), sol_all["gepa"]["levels"], sol_h["gepa"]["levels"]),
          ("Training-Free GRPO", pct(M["TF-GRPO/self"]["levels"]), pct(M["TF-GRPO/hint"]["levels"]), sol_all["tfgrpo"]["levels"], sol_h["tfgrpo"]["levels"]),
          ("EvoSkill", pct(M["EvoSkill/self"]["levels"]), pct(M["EvoSkill/hint"]["levels"]), sol_all["evoskill"]["levels"], sol_h["evoskill"]["levels"]),
          ("ReasoningBank", pct(M["ReasoningBank/self"]["levels"]), pct(M["ReasoningBank/hint"]["levels"]), sol_all["rb"]["levels"], sol_h["rb"]["levels"])]
X = [1, 2, 3, 4]
fig, axes = plt.subplots(2, 4, figsize=(7.0, 3.15), sharex=True, sharey=True, gridspec_kw=dict(wspace=0.1, hspace=0.42))
for ax, (title, ls, lh, ss, sh) in zip(axes.flat, panels):
    ax.fill_between(X, [76, 56, 36, 16], [84, 64, 44, 24], color="#e6e6e6", lw=0, zorder=0)
    for ys, col, filled, style in ((ls, LUNA, False, "-"), (lh, LUNA, True, (0, (3, 1.5))), (ss, SOL, False, "-"),
                                   (sh, SOL, True, (0, (3, 1.5)))):
        if ys is None:
            continue
        ax.plot(X, ys, color=col, lw=1.25, ls=style, zorder=2)
        ax.plot(X, ys, "o", ms=3.6, mfc=col if filled else "white", mec=col, mew=0.9, zorder=3)
    ax.set_title(title, fontsize=7.8, pad=3)
    ax.set_xticks(X)
    ax.set_xticklabels(["L1", "L2", "L3", "L4"])
    ax.set_xlim(0.75, 4.25)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", color="#ececec", lw=0.5)
    ax.set_axisbelow(True)
for ax in axes[:, 0]:
    ax.set_ylabel("test accuracy (%)")
# legend in the eighth cell
lg = axes[1, 3]
lg.axis("off")
mk = lambda col, filled, style, lab: plt.Line2D([], [], color=col, lw=1.25, ls=style, marker="o", ms=3.6,
                                                mfc=col if filled else "white", mec=col, mew=0.9, label=lab)
h = [mk(LUNA, False, "-", "GPT-6-Luna, feedback alone"), mk(LUNA, True, (0, (3, 1.5)), "GPT-6-Luna, + lesson"),
     mk(SOL, False, "-", "GPT-6-Sol, feedback alone"), mk(SOL, True, (0, (3, 1.5)), "GPT-6-Sol, + lesson"),
     plt.Rectangle((0, 0), 1, 1, fc="#e6e6e6", ec="none", label="frozen staircase")]
lg.legend(handles=h, loc="center", fontsize=6.6, handlelength=2.2, handletextpad=0.4, labelspacing=0.55)
fig.savefig(ROOT / "figures/main_levels.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote figures/main_levels.pdf")
