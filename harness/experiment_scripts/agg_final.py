"""Summarize finished baseline chains: official Frozen (harness programs) + methods, per level, per dataset;
plus diagnostic pass rates (inc: unseen members included; exc: non-members excluded), which do not depend on
the practice/test aggregation."""
import json, subprocess, sys, collections
from pathlib import Path
B = Path(__file__).resolve().parent
AG = B.parent.parent
done = sorted({x for x in (B / "logs" / "DONE.txt").read_text().split() if x[:2].isalpha() and x[2:].isdigit()})
CHAINS = dict(l.split(chr(9)) for l in (B / "CHAINS.tsv").read_text().splitlines() if l)
sys.path.insert(0, str(B / done[0] / "harness_k1_test"))
from x_runner import extract_code  # noqa
table = collections.defaultdict(lambda: collections.defaultdict(list))   # (arm, method, dataset) -> level -> scores
diag = collections.defaultdict(lambda: {"inc": [0, 0], "exc": [0, 0]})  # (arm, method) -> kind -> [pass, total]
for c in done:
    d = c[:2]
    chain = Path(CHAINS[c])
    progs = []
    for k in range(1, 6):
        src = json.loads((B / c / f"frozen_k1_v0/L{k}/FINAL_PROGRAM.json").read_text())["text"]
        p = B / c / f"frozen_k1_v0/L{k}/program.py"
        p.write_text(extract_code(src))
        progs += ["--program", f"L{k}={p}"]
    for v in range(3):
        out = subprocess.run([sys.executable, str(chain / "score_k1_v3.py"), "--version", str(v), *progs, "--diagnostics"],
                             capture_output=True, text=True, timeout=1800)
        res = json.loads(out.stdout)
        for k, s in res["levels"].items():
            table[("frozen", "frozen", d)][int(k[1])].append(s)
        for x in res.get("diagnostics", []):
            diag[("frozen", "frozen")][x["kind"]][0] += x["passed"]
            diag[("frozen", "frozen")][x["kind"]][1] += 1
    for r in json.loads((B / c / "SCORES_ALL.json").read_text())["rows"]:
        table[(r["mode"], r["method"], d)][r["level"]].append(r["score"])
        for x in r.get("diagnostics", []):
            diag[(r["mode"], r["method"])][x["kind"]][0] += x["passed"]
            diag[(r["mode"], r["method"])][x["kind"]][1] += 1
arms = sorted({(a, m) for a, m, _ in table})
datasets = sorted({d for _, _, d in table})
def row(a, m, ds):
    lv = collections.defaultdict(list)
    for d in ds:
        for k, s in table[(a, m, d)].items():
            lv[k] += s
    vals = [sum(lv[k]) / len(lv[k]) for k in range(1, 6)]
    return vals, sum(vals)
out = {"chains": done, "overall": {}, "per_dataset": {}, "diagnostics": {}}
for a, m in arms:
    vals, tot = row(a, m, datasets)
    out["overall"][f"{a}/{m}"] = {"levels": [round(x, 3) for x in vals], "sum": round(tot, 3)}
    for d in datasets:
        v2, t2 = row(a, m, [d])
        out["per_dataset"].setdefault(d, {})[f"{a}/{m}"] = {"levels": [round(x, 3) for x in v2], "sum": round(t2, 3)}
    g = diag[(a, m)]
    out["diagnostics"][f"{a}/{m}"] = {k: round(p / t, 3) if t else None for k, (p, t) in g.items()}
(B / "SUMMARY.json").write_text(json.dumps(out, indent=1))
print("chains", len(done))
for k, v in out["overall"].items():
    print(f"{k:18s}", v["levels"], "sum", v["sum"], "| diag inc/exc", out["diagnostics"][k].get("inc"), out["diagnostics"][k].get("exc"))
