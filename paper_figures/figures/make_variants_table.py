"""Appendix table: text added to the update step of ACE and Dynamic Cheatsheet on GPT-6-Luna (procedure only, convention
only and the whole lesson under a neutral heading; the class names with feedback kept). Reads
data/update_text_variants.json; writes sections/table_variants.tex. Run from the repository root."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/update_text_variants.json").read_text())
d.update(json.loads((ROOT / "data/convention_level1.json").read_text()))
V = [("procn", "procedure, neutral heading"), ("convn", "convention, neutral heading"),
     ("lessn", "lesson, neutral heading"), ("convl1", "convention at level 1 only"),
     ("namem", "class names + feedback")]
lines = ["\\begin{table}[t]",
         "  \\caption{Text added to the update step (GPT-6-Luna); columns as in Table~\\ref{tab:mainfull}. Neutral heading:",
         "  ``UPDATE NOTE'' instead of ``VERIFIED LESSON''.}",
         "  \\label{tab:variants}", "  \\small", "  \\setlength{\\tabcolsep}{2.6pt}",
         "  \\begin{tabular}{@{}llrrrrrrrr@{}}", "    \\toprule",
         "    & Update-step text & L1 & L2 & L3 & L4 & Avg & Single & inc$_u$ & exc \\\\", "    \\midrule"]
for m, name in (("ace", "ACE"), ("dc", "DC")):
    for i, (k, lab) in enumerate(V):
        r = d[k][m]
        lines.append(f"    {name if i == 0 else ''} & {lab} & " + " & ".join(f"{x:.0f}" for x in r["levels"]) +
                     f" & {Decimal(repr(round(r['acc'], 6))).quantize(Decimal('0.1'), ROUND_HALF_UP)} & {r['single']:.0f} & {r['inc_u']:.0f} & {r['exc']:.0f} \\\\")
    if m == "ace":
        lines.append("    \\addlinespace[2pt]")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_variants.tex").write_text("\n".join(lines))
print("wrote sections/table_variants.tex")
