"""Main results table (LaTeX). Per-level accuracy from data/main_table_fb.json (methods, frozen) and data/extra_fb.json
(references); single-cell accuracy, inc on unseen members and exc from data/review_analysis.json.
Writes sections/table_main.tex. Run from the repository root: python figures/make_table.py"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def rnd(v, nd=0):
    """Round half up (the text uses the same rule)."""
    q = Decimal(1).scaleb(-nd)
    return f"{Decimal(repr(round(v, 9))).quantize(q, ROUND_HALF_UP)}"

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "data/main_table_fb.json").read_text())
extra = json.loads((ROOT / "data/extra_fb.json").read_text()) if (ROOT / "data/extra_fb.json").exists() else {}
diag = json.loads((ROOT / "data/review_analysis.json").read_text())["cells_diag"]
ra2 = ROOT / "data/review_analysis2.json"
for k, v in (json.loads(ra2.read_text())["all_cells"].items() if ra2.exists() else []):
    diag.setdefault(k, v)
gepa = json.loads((ROOT / "data/gepa_explicit.json").read_text()) if (ROOT / "data/gepa_explicit.json").exists() else {}
pct = lambda xs: [100 * x for x in xs]
frozen = pct(d["frozen"])
f_avg = sum(frozen) / 4


def row(name, levels, key, delta=True):
    avg = sum(levels) / 4
    g = diag.get(key, {})
    fmt = lambda v: rnd(v) if v is not None else "--"
    cells = [rnd(x) for x in levels] + [rnd(avg, 1), ("+" if avg >= f_avg else "") + rnd(avg - f_avg, 1) if delta else "--",
                                            fmt(g.get("single")), fmt(g.get("inc_m2" if key.startswith("rg_") else "inc_unseen")), fmt(g.get("exc"))]
    return f"    {name} & " + " & ".join(cells) + " \\\\"


lines = [
    "\\begin{table}[t]",
    "  \\caption{GPT-6-Luna: accuracy per level and average, change over the frozen agent ($\\Delta$), single-cell accuracy,",
    "  inc$_u$, and exc (\\%). Rows without + learn from feedback alone. $^\\dagger$With a format note (Appendix~\\ref{sec:gepa}). $^\\ast$$m_1$ is",
    "  revealed in practice; inc$_u$ counts $m_2$ only.}",
    "  \\label{tab:main}",
    "  \\small",
    "  \\setlength{\\tabcolsep}{2.6pt}",
    "  \\begin{tabular}{@{}lrrrrrrrrr@{}}",
    "    \\toprule",
    "    & L1 & L2 & L3 & L4 & Avg & $\\Delta$ & Single & inc$_u$ & exc \\\\",
    "    \\midrule",
    row("Frozen", frozen, "frozen/ref", delta=False),
]
REFS = [("history", "hist/ref", "History"), ("oracle", "oracle/ref", "Lesson only"),
        ("histhint", "histhint/ref", "History + lesson"), ("histconv", "histconv/ref", "History + convention"),
        ("histproc", "histproc/ref", "History + procedure"), ("nameoracle", "nameoracle/ref", "Class-name oracle"),
        ("nameproc", "nameproc/ref", "\\quad + procedure"), ("webonly", "webonly/ref", "Web lookup"),
        ("histweb", "histweb/ref", "History + Web lookup"), ("histwebng", "histwebng/ref", "\\quad without the class")]
for k, key, label in REFS:
    if k in extra:
        lines.append(row(label, pct(extra[k]["levels"]), key))
    else:
        lines.append(f"    {label} & \\multicolumn{{9}}{{c}}{{(running)}} \\\\")
lv2 = json.loads(ra2.read_text()).get("levels", {}) if ra2.exists() else {}
if "rg_hist/self" in lv2:  # placed after History
    i = next(j for j, l in enumerate(lines) if l.startswith("    History &"))
    lines.insert(i + 1, row("\\quad rewarded practice$^\\ast$", pct(lv2["rg_hist/self"]), "rg_hist/self"))
lines.append("    \\midrule")
DISPLAY = {"DC-Cu": "Dynamic Cheatsheet", "TF-GRPO": "Training-Free GRPO"}
EXTRA_ROWS = {"ACE": ("ace", "ace"), "GEPA*": ("gepa", "gepa"), "DC-Cu": ("dc", "dc")}
for k in ["ACE", "GEPA*", "DC-Cu", "TF-GRPO", "EvoSkill", "ReasoningBank"]:
    name, code = k.rstrip("*"), {"ACE": "ace", "GEPA*": "gepa", "DC-Cu": "dc", "TF-GRPO": "tfgrpo",
                                  "EvoSkill": "evoskill", "ReasoningBank": "rb"}[k]
    if k == "GEPA*" and "neutral_self" in gepa and "neutral_hint" in gepa:
        lines.append(row("GEPA$^\\dagger$", pct(gepa["neutral_self"]["levels"]), "gepaN/self"))
        lines.append(row("\\quad +\\,lesson", pct(gepa["neutral_hint"]["levels"]), "gepaN/hint"))
    else:
        lines.append(row(DISPLAY.get(name, name), pct(d["methods"][f"{k}/self"]["levels"]), f"{code}/self"))
        lines.append(row("\\quad +\\,lesson", pct(d["methods"][f"{k}/hint"]["levels"]), f"{code}/hint"))
    if k in EXTRA_ROWS:
        a, b = EXTRA_ROWS[k]
        for tag, label in (("convm", "\\quad +\\,convention"), ("webm", "\\quad +\\,Web lookup"),
                           ("webngm", "\\quad +\\,Web lookup w/o class")):
            if f"{tag}_{b}/hint" in lv2:
                lines.append(row(label, pct(lv2[f"{tag}_{b}/hint"]), f"{tag}_{b}/hint"))
        if f"rg_{a}/self" in lv2:
            lines.append(row("\\quad rewarded practice$^\\ast$", pct(lv2[f"rg_{a}/self"]), f"rg_{a}/self"))
    if k != "ReasoningBank":
        lines.append("    \\addlinespace[2pt]")
lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}", ""]
# Appendix: every condition. Main text: the core conditions only.
full = [l.replace("\\label{tab:main}", "\\label{tab:mainfull}").replace(
    "\\caption{GPT-6-Luna:", "\\caption{All conditions, GPT-6-Luna:") for l in lines]
(ROOT / "sections/table_main_full.tex").write_text("\n".join(full))
DROP = ("    Lesson only &", "    History + procedure &", "    \\quad + procedure &", "    Web lookup &",
        "    \\quad without the class &", "    \\quad +\\,Web lookup w/o class &", "    \\quad rewarded practice")
core = [l for l in lines if not l.startswith(DROP)]
core = core
txt = "\n".join(core).replace(" $^\\ast$$m_1$\n  is revealed in practice. Further", "\n  Further")
(ROOT / "sections/table_main.tex").write_text(txt)
print("wrote sections/table_main.tex and table_main_full.tex")
