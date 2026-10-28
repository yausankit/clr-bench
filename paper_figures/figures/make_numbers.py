"""Numbers quoted in the text that come from runs added after the main experiment. Writes sections/numbers.tex
(\newcommand per number; "??" while the run is still missing). Run from the repository root: python figures/make_numbers.py"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def rnd(v, nd=0):
    """Round half up (the text uses the same rule)."""
    q = Decimal(1).scaleb(-nd)
    return f"{Decimal(repr(round(v, 9))).quantize(q, ROUND_HALF_UP)}"

ROOT = Path(__file__).resolve().parents[1]
load = lambda n: json.loads((ROOT / "data" / n).read_text()) if (ROOT / "data" / n).exists() else {}
extra, gepa = load("extra_fb.json"), load("gepa_explicit.json")
ra2 = load("review_analysis2.json")
cells = ra2.get("all_cells", {})
NAMES = {"ace/self": "ACE", "gepaN/self": "GEPA", "dc/self": "Dynamic Cheatsheet", "tfgrpo/self": "Training-Free GRPO",
         "evoskill/self": "EvoSkill", "rb/self": "ReasoningBank"}
best = max(NAMES, key=lambda k: ra2["subset_excl_recent"][k]["inc_unseen"]) if ra2 else None
best_name = NAMES.get(best, "??")
single = lambda k: rnd(cells[k]['single']) if cells.get(k, {}).get("single") is not None else "??"
avg = lambda lv: rnd(sum(100 * x for x in lv) / len(lv), 1)
nums = {
    "histhintavg": avg(extra["histhint"]["levels"]) if "histhint" in extra else "??",
    "nameoracleavg": avg(extra["nameoracle"]["levels"]) if "nameoracle" in extra else "??",
    "histconvavg": avg(extra["histconv"]["levels"]) if "histconv" in extra else "??",
    "histprocavg": avg(extra["histproc"]["levels"]) if "histproc" in extra else "??",
    "nameprocavg": avg(extra["nameproc"]["levels"]) if "nameproc" in extra else "??",
    "histconvsingle": single("histconv/ref") if "histconv" in extra else "??",
    "histprocsingle": single("histproc/ref") if "histproc" in extra else "??",
    "nameprocsingle": single("nameproc/ref") if "nameproc" in extra else "??",
    **{f"{tag}{m}incm{w}": rnd(cells[key][f"inc_m{j}"], 1) if cells.get(key, {}).get(f"inc_m{j}") is not None else "??"
       for tag, m, key in (("rg", "ace", "rg_ace/self"), ("rg", "dc", "rg_dc/self"), ("rg", "hist", "rg_hist/self"),
                           ("rg", "gepa", "rg_gepa/self"), ("std", "ace", "ace/self"), ("std", "dc", "dc/self"),
                           ("std", "hist", "hist/ref"), ("std", "gepa", "gepaN/self"))
       for j, w in ((1, "one"), (2, "two"))},
    "rgaceavg": rnd(sum(ra2["levels"]["rg_ace/self"]) * 25, 1) if "rg_ace/self" in ra2.get("levels", {}) else "??",
    "rggepaavg": rnd(sum(ra2["levels"]["rg_gepa/self"]) * 25, 1) if "rg_gepa/self" in ra2.get("levels", {}) else "??",
    "rgdcavg": rnd(sum(ra2["levels"]["rg_dc/self"]) * 25, 1) if "rg_dc/self" in ra2.get("levels", {}) else "??",
    "rghistavg": rnd(sum(ra2["levels"]["rg_hist/self"]) * 25, 1) if "rg_hist/self" in ra2.get("levels", {}) else "??",
    "webonlyavg": avg(extra["webonly"]["levels"]) if "webonly" in extra else "??",
    "histwebavg": avg(extra["histweb"]["levels"]) if "histweb" in extra else "??",
    "webonlysingle": single("webonly/ref"), "histwebsingle": single("histweb/ref"),
    **{f"webm{m}avg": rnd(sum(ra2["levels"][f"webm_{m}/hint"]) * 25, 1) if f"webm_{m}/hint" in ra2.get("levels", {}) else "??"
       for m in ("ace", "gepa", "dc")},
    **{f"webm{m}single": single(f"webm_{m}/hint") for m in ("ace", "gepa", "dc")},
    **{f"{t}{m}avg": rnd(sum(ra2["levels"][f"{t}_{m}/hint"]) * 25, 1) if f"{t}_{m}/hint" in ra2.get("levels", {}) else "??"
       for t in ("convm", "webngm") for m in ("ace", "gepa", "dc")},
    **{f"{t}{m}single": single(f"{t}_{m}/hint") for t in ("convm", "webngm") for m in ("ace", "gepa", "dc")},
    "histwebngavg": avg(extra["histwebng"]["levels"]) if "histwebng" in extra else "??",
    "histwebngsingle": single("histwebng/ref"),
    "histwebngexc": rnd(cells["histwebng/ref"]["exc"]) if "histwebng/ref" in cells else "??",
    "histwebngincu": rnd(cells["histwebng/ref"]["inc_unseen"]) if "histwebng/ref" in cells else "??",
    "stdaceavg": "52.5",
    "ncandidates": rnd(load("search_stats.json").get("mean_candidates", 0), 1),
    "nexcluded": str(len(ra2["excluded_slots"])) if ra2 else "??",
    "nflagged": str(len(ra2["excluded_or_recent"])) if ra2 else "??",
    "nclean": str(80 - len(ra2["excluded_or_recent"])) if ra2 else "??",
    "subsetbest": best_name if ra2 else "??",
    "subsetbestincu": rnd(ra2["subset_excl_recent"][best]["inc_unseen"], 1) if ra2 else "??",
    "subsethistincu": rnd(ra2["subset_excl_recent"]["hist/ref"]["inc_unseen"], 1) if ra2 else "??",
    "subsetbestsingle": rnd(ra2["subset_excl_recent"][best]["single"], 1) if ra2 else "??",
    "subsethistsingle": rnd(ra2["subset_excl_recent"]["hist/ref"]["single"], 1) if ra2 else "??",
    "gepaorigavg": avg(gepa["orig"]["levels"]) if "orig" in gepa else "??",
    "gepaorigmax": str(gepa["orig"]["max_programs"]) if "orig" in gepa else "??",
    "gepaneutralselfavg": avg(gepa["neutral_self"]["levels"]) if "neutral_self" in gepa else "??",
    "gepaneutralhintavg": avg(gepa["neutral_hint"]["levels"]) if "neutral_hint" in gepa else "??",
}
lines = ["%% Generated by figures/make_numbers.py; do not edit by hand."]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in nums.items()]
(ROOT / "sections/numbers.tex").write_text("\n".join(lines) + "\n")
print(nums)
