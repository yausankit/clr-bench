"""Appendix tables from existing data: per-domain average accuracy (data/per_domain.json) and the frozen agent with a
second base model (data/frozen_sonnet_vs_luna.json). Writes sections/table_domain_results.tex and
sections/table_sonnet_frozen.tex. Run from the repository root: python figures/make_appendix_tables.py"""
import json
import statistics
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rnd(v, nd=1):
    q = Decimal(1).scaleb(-nd)
    return f"{Decimal(repr(round(v, 9))).quantize(q, ROUND_HALF_UP)}"


DOMAIN = {"TR": "Travel audit", "SY": "Pharmacy review", "WS": "Web security", "LG": "System logs", "SP": "Sponsorship",
          "CH": "Chemical imports", "MN": "Raw materials", "SH": "Port inspections", "UN": "Scholarships",
          "GR": "Travel grants"}
pd = json.loads((ROOT / "data/per_domain.json").read_text())
cols = [("frozen", "Frozen"), ("hist", "History"), ("ace/self", "ACE"), ("ace/hint", "+L"), ("dc/self", "DC"),
        ("dc/hint", "+L"), ("histhint", "Hist.+L")]
lines = ["\\begin{table}[t]",
         "  \\caption{Average test accuracy (\\%, levels 1--4) per domain, two chains each. +L: with the lesson.}",
         "  \\label{tab:domainres}", "  \\small", "  \\setlength{\\tabcolsep}{3pt}",
         "  \\begin{tabular}{@{}l" + "r" * len(cols) + "@{}}", "    \\toprule",
         "    Domain & " + " & ".join(c for _, c in cols) + " \\\\", "    \\midrule"]
for k, name in DOMAIN.items():
    lines.append(f"    {name} & " + " & ".join(rnd(pd[k][c]) for c, _ in cols) + " \\\\")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_domain_results.tex").write_text("\n".join(lines))

fz = json.loads((ROOT / "data/frozen_sonnet_vs_luna.json").read_text())
lv = {t: [statistics.mean(fz[c][t][k] for c in fz) for k in range(4)] for t in ("luna", "sonnet")}
lines = ["\\begin{table}[t]",
         "  \\caption{The frozen agent with the evaluated model and with a second base model (Claude Sonnet 5.5, low",
         "  reasoning effort), 20 chains, levels 1--4. The design target is .80/.60/.40/.20.}",
         "  \\label{tab:sonnet}", "  \\small",
         "  \\begin{tabular}{@{}lrrrrr@{}}", "    \\toprule", "    & L1 & L2 & L3 & L4 & Avg \\\\", "    \\midrule"]
for t, name in (("luna", "GPT-6-Luna (high)"), ("sonnet", "Sonnet 5.5 (low)")):
    lines.append(f"    {name} & " + " & ".join(rnd(x, 2) for x in lv[t]) + f" & {rnd(100 * sum(lv[t]) / 4)} \\\\")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_sonnet_frozen.tex").write_text("\n".join(lines))
above = sum(1 for c in fz for k in range(4) if fz[c]["sonnet"][k] > [0.8, 0.6, 0.4, 0.2][k] + 1e-9)
print("wrote tables; sonnet cells above staircase:", above)
