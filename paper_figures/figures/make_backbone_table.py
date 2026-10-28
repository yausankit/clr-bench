"""Backbone comparison table (main text): frozen agent and class-name oracle per base model.
Reads data/models_scores.json, data/frozen_sonnet_vs_luna.json, data/extra_fb.json, data/review_analysis.json,
data/sol6_frozen.json and data/learn_sol6.json. Writes sections/table_backbones.tex and sections/table_sol.tex. Run from the repository root."""
import json
import statistics
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
ms, fz, extra, ra = load("models_scores.json"), load("frozen_sonnet_vs_luna.json"), load("extra_fb.json"), load("review_analysis.json")
STAIR = [0.8, 0.6, 0.4, 0.2]


def r(v, nd=1):
    return f"{Decimal(repr(round(v, 9))).quantize(Decimal(1).scaleb(-nd), ROUND_HALF_UP)}"


def above(key):
    return sum(1 for c in fz for k in range(4) if fz[c][key][k] > STAIR[k] + 1e-9)


rows = []
luna_f = [statistics.mean(fz[c]["luna"][k] for c in fz) for k in range(4)]
d = ra["cells_diag"]["nameoracle/ref"]
rows.append(("GPT-6-Luna (high)$^\\ast$", luna_f, above("luna"), extra["nameoracle"]["levels"], d["single"], d["inc_unseen"], d["exc"]))
for tag, name in (("gpt-5.6-luna", "GPT-5.6-Luna (high)"), ("gpt-5.6-terra", "GPT-5.6-Terra (high)")):
    m = ms[tag]
    rows.append((name, m["frozen_levels"], m["frozen_above_staircase"], m["oracle_levels"], m["oracle_single"], m["oracle_inc"], m["oracle_exc"]))
son_f = [statistics.mean(fz[c]["sonnet"][k] for c in fz) for k in range(4)]
rows.append(("Claude Sonnet 5.5 (low)", son_f, above("sonnet"), None, None, None, None))
sol = load("sol6_frozen.json")
sol_f = [statistics.mean(sol[c][k] for c in sol) for k in range(4)]
sol_above = sum(1 for c in sol for k in range(4) if sol[c][k] > STAIR[k] + 1e-9)
rows.append(("GPT-6-Sol (high)", sol_f, sol_above, None, None, None, None))
lines = ["\\begin{table}[t]",
         "  \\caption{Other base models. Frozen: accuracy per level without feedback and the number of the 80 level scores above",
         "  the staircase (a class guessed). Oracle: the class-name oracle, accuracy and single-cell accuracy, inc$_u$, exc (\\%).",
         "  $^\\ast$Evaluated and certifying model.}",
         "  \\label{tab:backbones}", "  \\small", "  \\setlength{\\tabcolsep}{2.4pt}",
         "  \\begin{tabular}{@{}lccrrrr@{}}", "    \\toprule",
         "    & Frozen & $>$stair & Oracle & Single & inc$_u$ & exc \\\\", "    \\midrule"]
for name, f, ab, o, sg, iu, ex in rows:
    fr = "/".join(r(x, 2).lstrip("0") for x in f)
    oo = r(100 * sum(o) / 4) if o else "--"
    lines.append(f"    {name} & {fr} & {ab} & {oo} & {r(sg, 0) if sg is not None else '--'} & "
                 f"{r(iu, 0) if iu is not None else '--'} & {r(ex, 0) if ex is not None else '--'} \\\\")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_backbones.tex").write_text("\n".join(lines))
print("\n".join(lines[10:-4]))

# learning conditions with GPT-6-Luna and GPT-6-Sol (all six methods learning from feedback alone; ACE and DC also with
# the lesson). Luna: data/learn_sol6.json and the paper's main results (GEPA with the neutral note); Sol: the same file
# and data/sol6_all_methods.json for GEPA, Training-Free GRPO, EvoSkill, and ReasoningBank.
learn, allm, solh = load("learn_sol6.json"), load("sol6_all_methods.json"), load("sol6_hint.json")
mainfb, gepa, cells = load("main_table_fb.json"), load("gepa_explicit.json"), load("review_analysis2.json")["all_cells"]
extra = load("extra_fb.json")
mean = lambda l: 100 * sum(l) / len(l)
d = lambda acc, c: dict(acc=acc, single=c["single"], inc_u=c["inc_unseen"], exc=c["exc"])
M = mainfb["methods"]
# (row label, Luna values, Sol values)
rows_ = [("Frozen", learn["luna"]["frozen"], learn["sol6"]["frozen"]),
         ("History", learn["luna"]["hist"], learn["sol6"]["hist"]),
         ("\\quad + lesson", d(mean(extra["histhint"]["levels"]), cells["histhint/ref"]), solh["histhint"]),
         ("ACE", learn["luna"]["ace/self"], learn["sol6"]["ace/self"]),
         ("\\quad + lesson", learn["luna"]["ace/hint"], learn["sol6"]["ace/hint"]),
         ("Dynamic Cheatsheet", learn["luna"]["dc/self"], learn["sol6"]["dc/self"]),
         ("\\quad + lesson", learn["luna"]["dc/hint"], learn["sol6"]["dc/hint"]),
         ("GEPA$^\\dagger$", d(mean(gepa["neutral_self"]["levels"]), cells["gepaN/self"]), allm["sol"]["gepa"]),
         ("\\quad + lesson", d(mean(gepa["neutral_hint"]["levels"]), cells["gepaN/hint"]), solh["gepa"]),
         ("Training-Free GRPO", d(mean(M["TF-GRPO/self"]["levels"]), cells["tfgrpo/self"]), allm["sol"]["tfgrpo"]),
         ("\\quad + lesson", d(mean(M["TF-GRPO/hint"]["levels"]), cells["tfgrpo/hint"]), solh["tfgrpo"]),
         ("EvoSkill", d(mean(M["EvoSkill/self"]["levels"]), cells["evoskill/self"]), allm["sol"]["evoskill"]),
         ("\\quad + lesson", d(mean(M["EvoSkill/hint"]["levels"]), cells["evoskill/hint"]), solh["evoskill"]),
         ("ReasoningBank", d(mean(M["ReasoningBank/self"]["levels"]), cells["rb/self"]), allm["sol"]["rb"]),
         ("\\quad + lesson", d(mean(M["ReasoningBank/hint"]["levels"]), cells["rb/hint"]), solh["rb"])]
lines = ["\\begin{table}[t]",
         "  \\caption{Both base models: accuracy, single-cell accuracy, inc$_u$, and exc",
         "  (\\%). Methods learn from feedback alone unless marked + lesson. $^\\dagger$With a format note (Appendix~\\ref{sec:gepa}).}",
         "  \\label{tab:sol}", "  \\small", "  \\setlength{\\tabcolsep}{2.6pt}",
         "  \\begin{tabular}{@{}lrrrrrrrr@{}}", "    \\toprule",
         "    & \\multicolumn{4}{c}{GPT-6-Luna} & \\multicolumn{4}{c}{GPT-6-Sol} \\\\",
         "    \\cmidrule(lr){2-5}\\cmidrule(l){6-9}",
         "    & Acc & Single & inc$_u$ & exc & Acc & Single & inc$_u$ & exc \\\\", "    \\midrule"]
for i, (name, lv, sv) in enumerate(rows_):
    cells_ = [r(lv["acc"]), r(lv["single"], 0), r(lv["inc_u"], 0), r(lv["exc"], 0),
              r(sv["acc"]), r(sv["single"], 0), r(sv["inc_u"], 0), r(sv["exc"], 0)]
    lines.append(f"    {name} & " + " & ".join(cells_) + " \\\\")
    if i in (0, 2, 6):
        lines.append("    \\addlinespace[2pt]")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_sol.tex").write_text("\n".join(lines))
print("\n".join(lines))
