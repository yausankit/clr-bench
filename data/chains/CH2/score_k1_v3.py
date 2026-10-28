#!/usr/bin/env python3
"""K1 v3 scoring: score_k1_v3.py --version v --program L1=prog1.py --program L2=prog2.py ...
Per level score = passed scored cells / 5. Diagnostics are reported per value, not scored."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "harness_k1_test"))
from runner import run_candidate


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--program", action="append", default=[], help="L<k>=path")
    p.add_argument("--diagnostics", action="store_true")
    a = p.parse_args()
    progs = {}
    for item in a.program:
        lvl, _, path = item.partition("=")
        progs[int(lvl.lstrip("L"))] = Path(path).read_text(encoding="utf-8")
    tests = json.loads((HERE / f"test_k1_v{a.version}.json").read_text(encoding="utf-8"))
    out = {"version": a.version, "levels": {}, "instances": []}
    for k in sorted(progs):
        cells = [t for t in tests if t["level"] == k]
        passed = 0
        for t in cells:
            res = run_candidate(progs[k], t["data"])
            ok = bool(res.get("ok") and res.get("value") == t["expected"])
            passed += ok
            out["instances"].append({"instance_id": t["instance_id"], "cell": t["cell"], "passed": ok,
                                     "expected": t["expected"], "got": res.get("value"),
                                     "error": res.get("error_type")})
        out["levels"][f"L{k}"] = round(passed / 5, 2)
    if a.diagnostics:
        diag = json.loads((HERE / "diagnostics.json").read_text(encoding="utf-8"))
        out["diagnostics"] = []
        for d in diag:
            if d["level"] in progs:
                res = run_candidate(progs[d["level"]], d["data"])
                out["diagnostics"].append({"instance_id": d["instance_id"], "value": d["value"],
                                           "kind": d["kind"], "passed": res.get("value") == d["expected"]})
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
