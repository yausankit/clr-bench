"""Main-text table on the clean slots (no flawed evidence, no recent membership changes): accuracy on the kept cells,
change relative to the frozen agent, single-cell accuracy, inc on unseen members, and exc, from
data/review_analysis2.json (subset_excl_recent). Writes sections/table_clean.tex. Run from the repository root."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def rnd(v, nd=0):
    """Round half up (the text uses the same rule)."""
    q = Decimal(1).scaleb(-nd)
    return f"{Decimal(repr(round(v, 9))).quantize(q, ROUND_HALF_UP)}"


ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT / "data/review_analysis2.json").read_text())
sub = r["subset_excl_recent"]
n = 80 - len(r["excluded_or_recent"])
f_acc = sub["frozen/ref"]["cells"]
GROUPS = [
    [("frozen/ref", "Frozen"), ("hist/ref", "History"), ("rg_hist/self", "\\quad rewarded practice"), ("oracle/ref", "Lesson only"), ("histhint/ref", "History + lesson"),
     ("histconv/ref", "History + convention"), ("histproc/ref", "History + procedure"),
     ("histweb/ref", "History + Web lookup"), ("histwebng/ref", "\\quad without the class"),
     ("nameoracle/ref", "Class-name oracle"), ("nameproc/ref", "\\quad + procedure")],
    [("ace/self", "ACE (self)"), ("ace/hint", "\\quad +\\,lesson"), ("convm_ace/hint", "\\quad +\\,convention"), ("webm_ace/hint", "\\quad +\\,Web lookup"),
     ("gepaN/self", "GEPA$^\\dagger$ (self)"), ("gepaN/hint", "\\quad +\\,lesson"), ("convm_gepa/hint", "\\quad +\\,convention"), ("webm_gepa/hint", "\\quad +\\,Web lookup"),
     ("dc/self", "Dyn.\\ Cheatsheet (self)"), ("dc/hint", "\\quad +\\,lesson"), ("convm_dc/hint", "\\quad +\\,convention"), ("webm_dc/hint", "\\quad +\\,Web lookup")],
]
lines = ["\\begin{table}[t]",
         f"  \\caption{{Results on the {n} clean slots (Section~\\ref{{sec:construction}}): accuracy on their test cells (Acc), change",
         "  relative to the frozen agent ($\\Delta$), single-cell accuracy, rate of excluding unseen members (inc$_u$; for rewarded",
         "  practice, $m_1$ is revealed and inc$_u$ counts $m_2$ only, so its Acc and Single are easier), and rate of keeping",
         "  non-members (exc), in \\%. Acc is computed over the clean cells and the single cells of these slots, so only $\\Delta$ is",
         "  comparable with Table~\\ref{tab:mainfull}.",
         "  Other methods and conditions are in Table~\\ref{tab:mainfull}. $^\\dagger$With the neutral format note.}",
         "  \\label{tab:clean}", "  \\small", "  \\setlength{\\tabcolsep}{3.2pt}",
         "  \\begin{tabular}{@{}lrrrrr@{}}", "    \\toprule",
         "    & Acc & $\\Delta$ & Single & inc$_u$ & exc \\\\", "    \\midrule"]
for gi, g in enumerate(GROUPS):
    for key, name in g:
        if key not in sub or sub[key].get("cells") is None:
            continue
        x = sub[key]
        inc = x["inc_m2"] if key.startswith("rg_") else x["inc_unseen"]
        d = "--" if key == "frozen/ref" else ("+" if x["cells"] >= f_acc else "") + rnd(x["cells"] - f_acc, 1)
        lines.append(f"    {name} & {rnd(x['cells'], 1)} & {d} & {rnd(x['single'])} & {rnd(inc)} & {rnd(x['exc'])} \\\\")
    if gi < len(GROUPS) - 1:
        lines.append("    \\midrule")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_clean.tex").write_text("\n".join(lines))
print("wrote sections/table_clean.tex")
