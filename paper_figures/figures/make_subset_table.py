"""Appendix table: single-cell accuracy, inc on unseen members and exc on all slots and without the 12 audited slots,
from data/review_analysis2.json (audit exclusions). Writes sections/table_subset.tex. Run from the repository root."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def rnd(v, nd=0):
    """Round half up (the text uses the same rule)."""
    q = Decimal(1).scaleb(-nd)
    return f"{Decimal(repr(round(v, 9))).quantize(q, ROUND_HALF_UP)}"

ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT / "data/review_analysis2.json").read_text())
CONDS = [("hist/ref", "History"), ("histhint/ref", "History + lesson"), ("histconv/ref", "History + convention"),
         ("nameproc/ref", "Name oracle + procedure"),
         ("ace/self", "ACE (self)"), ("ace/hint", "\\quad +\\,lesson"), ("gepaN/self", "GEPA$^\\dagger$ (self)"),
         ("gepaN/hint", "\\quad +\\,lesson"), ("dc/self", "Dynamic Cheatsheet (self)"), ("dc/hint", "\\quad +\\,lesson")]
fmt = lambda v: "--" if v is None else rnd(v, 1)
lines = ["\\begin{table}[t]",
         f"  \\caption{{Single-cell accuracy and inc$_u$ (\\%) on all 80 slots, without the {len(r['excluded_slots'])} slots with flawed evidence",
         f"  (errors, open lists, duplicates, ambiguity, and two slots from a first audit), and also without the slots whose memberships changed after October 2023",
         f"  ({80 - len(r['excluded_or_recent'])} slots remain). $^\\dagger$With the neutral format note.}}",
         "  \\label{tab:subset}", "  \\small", "  \\setlength{\\tabcolsep}{3pt}",
         "  \\begin{tabular}{@{}lrrrrrr@{}}", "    \\toprule",
         "    & \\multicolumn{2}{c}{All} & \\multicolumn{2}{c}{No flawed} & \\multicolumn{2}{c}{No flawed/recent} \\\\",
         "    \\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(l){6-7}",
         "    & Single & inc$_u$ & Single & inc$_u$ & Single & inc$_u$ \\\\", "    \\midrule"]
for k, name in CONDS:
    groups = [r["all_cells"].get(k, {}), r["subset_excl"].get(k, {}), r["subset_excl_recent"].get(k, {})]
    lines.append(f"    {name} & " + " & ".join(fmt(x.get(f)) for x in groups for f in ("single", "inc_unseen")) + " \\\\")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_subset.tex").write_text("\n".join(lines))
print("wrote sections/table_subset.tex")
