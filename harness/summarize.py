#!/usr/bin/env python3
"""Aggregate scored runs over chains: test accuracy (overall and per level, in %), the share of single-member cells
passed, and the value-level diagnostics inc_u (unseen members of the hidden class handled as members) and exc
(non-members handled as non-members), version 0, levels 1-4.

usage: python harness/summarize.py <out root> [--file SCORES_ALL.json] [--json out.json]
<out root> holds one run directory per chain (as written by harness/run_condition.sh).
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def slots():
    out = {}
    for d in sorted((REPO / "data/chains").iterdir()):
        if (d / "CHAIN.json").exists():
            for s in json.loads((d / "CHAIN.json").read_text())["slots"]:
                out[(d.name, s["level"])] = s
    return out


def summarize(rows, slot):
    pct = lambda v: round(100 * sum(v) / len(v), 1) if v else None
    single, incu, exc = [], [], []
    for c, r in rows:
        single += [i["passed"] for i in r["instances"] if i["cell"].startswith("single")]
        for x in r.get("diagnostics", []):
            m = re.match(r"diag_L(\d+)_T(\d+)_", x["instance_id"])
            if not m or int(m.group(1)) != r["level"]:
                continue
            if x["kind"] == "inc":
                if x["value"] != slot[(c, int(m.group(2)))]["P_M"][0]:  # the member revealed in practice is not unseen
                    incu.append(x["passed"])
            else:
                exc.append(x["passed"])
    return dict(acc=pct([r["score"] for _, r in rows]),
                levels={f"L{k}": pct([r["score"] for _, r in rows if r["level"] == k]) for k in range(1, 5)},
                single=pct(single), inc_u=pct(incu), exc=pct(exc), n_level_scores=len(rows),
                chains=len({c for c, _ in rows}))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--file", default="SCORES_ALL.json")
    p.add_argument("--json")
    a = p.parse_args()
    slot = slots()
    groups = defaultdict(list)
    for f in sorted(Path(a.root).glob(f"*/{a.file}")):
        c = f.parent.name
        for r in json.loads(f.read_text())["rows"]:
            if r["version"] == 0 and r["level"] <= 4:
                groups[(r["method"], r["mode"])].append((c, r))
    out = {f"{m}/{mode}": summarize(rows, slot) for (m, mode), rows in sorted(groups.items())}
    for k, v in out.items():
        lv = " ".join(f"{x}={y}" for x, y in v["levels"].items())
        print(f"{k:22s} acc={v['acc']} {lv} single={v['single']} inc_u={v['inc_u']} exc={v['exc']} chains={v['chains']}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
