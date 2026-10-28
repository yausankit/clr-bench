"""Appendix table of all hidden classes (chain, level, field, class name) from data/chain_facts.json.
Writes sections/table_classes.tex. Run from the repository root: python figures/make_classes_table.py"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
facts = json.loads((ROOT / "data/chain_facts.json").read_text())
DOMAIN = {"TR": "Travel audit", "SY": "Pharmacy review", "WS": "Web security", "LG": "System logs",
          "SP": "Sponsorship", "CH": "Chemical imports", "MN": "Raw materials", "SH": "Port inspections",
          "UN": "Scholarships", "GR": "Travel grants"}


def tex(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
             .replace("#", "\\#"))


def short(name):
    if "category:" in name:  # CWE view prefix: keep the category itself
        name = name.split("category:", 1)[1].strip()
    for a, b in (("member states", "members"), ("member countries", "members"), ("member airlines", "airlines"),
                 ("Founding member airlines of ", "Founders of "), ("constituents, October 2026", "constituents")):
        name = name.replace(a, b)
    return name


rows = []
for c in sorted(facts):
    slots = sorted((s for s in facts[c]["slots"] if s["level"] <= 4), key=lambda s: s["level"])
    cells = [tex(short(s["name"])) for s in slots]
    rows.append(f"{c} & " + " & ".join(cells) + " \\\\")
lines = ["\\begin{table*}[t]",
         "  \\caption{Hidden classes, one row per chain (levels 1--4). "
         + ", ".join(f"{k}: {v}" for k, v in DOMAIN.items()) + ".}",
         "  \\label{tab:classes}",
         "  \\scriptsize",
         "  \\setlength{\\tabcolsep}{3pt}",
         "  \\begin{tabular}{@{}lp{0.225\\textwidth}p{0.225\\textwidth}p{0.225\\textwidth}p{0.225\\textwidth}@{}}",
         "    \\toprule",
         "    Chain & Level 1 & Level 2 & Level 3 & Level 4 \\\\",
         "    \\midrule"]
lines += ["    " + r for r in rows]
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}", ""]
(ROOT / "sections/table_classes.tex").write_text("\n".join(lines))
print("wrote sections/table_classes.tex with", len(rows), "rows")
