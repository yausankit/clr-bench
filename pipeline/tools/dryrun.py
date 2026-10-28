"""Dry run without probes: take each slot's first candidate, build every instance, print a summary.
usage: python tools/dryrun.py <inputs-root> <dataset>"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clrsynth.inputs import Dataset, load_chain
from clrsynth.candidates import FieldContext, allocate_slots, candidates_for_slot
from clrsynth.chain import Chain
from clrsynth.build import build_instances

ds = Dataset(sys.argv[1], sys.argv[2])
cfg = load_chain(ds.chain_paths()[0])
slots = allocate_slots(ds, cfg)
ctx = {s["field"]: FieldContext(ds, cfg, s["field"]) for s in cfg["fields"]}
picked = []
for s in slots:
    fc = ctx[s["field"]]
    excl, tried = set(), set()
    for p in picked:
        if p["field"] == s["field"]:
            excl |= set(p["cand"].pool())
            tried.add(p["cand"].C)
    t = time.time()
    c, r = candidates_for_slot(fc, excl, s["level"], tried=tried)
    print(f"L{s['level']} {s['field']}: {len(c)} candidates {[x.C for x in c]} ({time.time() - t:.1f}s); "
          f"rejected: {r[:4]}")
    if not c:
        sys.exit(1)
    picked.append({"level": s["level"], "field": s["field"], "cand": c[0]})
    x = c[0]
    print(f"   A={x.A} P_M={x.P_M} N_p={x.N_p} N_t={x.N_t} comp={x.comp_A}")
t = time.time()
ch = Chain(ds, cfg, picked)
sh, pv = build_instances(ch)
print(f"build_instances {time.time() - t:.1f}s, diagnostics {len(sh['diag'])}")
if len(sys.argv) > 3:
    print(ch.prompt(5, "test", sh["public"][5]["data"]))
