"""Benchmark statistics table (main text) from data/chain_facts.json, data/domain_stats.json, data/search_stats.json and
data/review_analysis.json. Writes sections/table_stats.tex. Run from the repository root."""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text())
facts, dom, search, ra = load("chain_facts.json"), load("domain_stats.json"), load("search_stats.json"), load("review_analysis.json")


def kind(name):
    n = name.lower()
    if any(k in n for k in ("language", "italic", "slavic")):
        return "language groups"
    if any(k in n for k in ("alliance", "oneworld", "skyteam", "airlines group", "skytrax")):
        return "airline alliances"
    if any(k in n for k in ("nato", "g7", "group of seven", "g20", "group of twenty", "oecd", "brics", "opec", "asean member",
                            "commonwealth", "european union", "economic area", "schengen", "arab league", "asia-pacific",
                            "council of europe", "islamic cooperation", "missile technology", "african union")):
        return "intergovernmental groupings"
    if any(k in n for k in ("stoxx", "dow jones", "nasdaq", "aex", "systemically important", "g-14", "super league",
                            "champions league", "club world cup")):
        return "indices and clubs"
    if any(k in n for k in ("universit",)):
        return "university networks"
    if any(k in n for k in ("microsoft", "office", "port", "ftp")):
        return "software and ports"
    return "standards and classifications"


slots = [s for v in facts.values() for s in v["slots"] if s["level"] <= 4]
kinds = collections.Counter(kind(s["name"]) for s in slots)
universes = {(d, f["universe"]): f for d, v in dom.items() for f in v["fields"].values()}
n_values = sum(f["values"] for f in universes.values())
n_lists = sum(f["lists"] for f in universes.values())
ident = ra["identifiability"]
rows = [("Domains / chains", f"{len(dom)} / {len(facts)}"),
        ("Levels per chain", "4"),
        ("Hidden classes", f"{len(slots)}"),
        ("Practice / test tasks", "80 / 80"),
        ("Values with descriptions", f"{n_values / 1000:.1f}k"),
        ("Named lists in the library", f"{n_lists:,}")]
lines = ["\\begin{table}[t]", "  \\caption{Statistics of \\bench.}", "  \\label{tab:stats}", "  \\small",
         "  \\setlength{\\tabcolsep}{4pt}", "  \\begin{tabular}{@{}lr@{}}", "    \\toprule"]
lines += [f"    {a} & {b} \\\\" for a, b in rows]
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
(ROOT / "sections/table_stats.tex").write_text("\n".join(lines))
print(dict(kinds), n_values, n_lists)
