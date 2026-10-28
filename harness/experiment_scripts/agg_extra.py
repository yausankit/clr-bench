"""Aggregate the overnight runs (2026-10-25): GPT-6-Sol for the other four methods (baselines_sol6_more) and update-step
text variants on GPT-6-Luna (baselines_lessn/convn/procn/namem). Per condition: accuracy, accuracy per level, single,
inc_u, exc, and the number of level scores. Run from $CLRBENCH_RUNS; writes /tmp/agg_extra.json."""
import json, os, re, subprocess, sys
CH = dict(l.split("\t") for l in open("baselines_final/CHAINS.tsv").read().splitlines() if l)
PY = os.environ.get("PYTHON", "python3")
sys.path.insert(0, "baselines_fb/TR1/harness_k1_test")
from x_runner import extract_code
SLOTS = {}
for c, d in CH.items():
    for s in json.load(open(f"{d}/CHAIN.json"))["slots"]:
        SLOTS[(c, s["level"])] = s


def summarize(rows):
    f = lambda v: round(100 * sum(v) / len(v), 1) if v else None
    acc = [r["score"] for c, r in rows]
    levels = [f([r["score"] for c, r in rows if r["level"] == k]) for k in range(1, 5)]
    single = [i["passed"] for c, r in rows for i in r["instances"] if i["cell"].startswith("single")]
    incu, exc = [], []
    for c, r in rows:
        for x in r.get("diagnostics", []):
            m = re.match(r"diag_L(\d+)_T(\d+)_", x["instance_id"])
            if not m or int(m.group(1)) != r["level"]:
                continue
            s = SLOTS[(c, int(m.group(2)))]
            if x["kind"] == "inc":
                if x["value"] != s["P_M"][0]:
                    incu.append(x["passed"])
            else:
                exc.append(x["passed"])
    return dict(acc=f(acc), levels=levels, single=f(single), inc_u=f(incu), exc=f(exc), n=len(rows))


def frozen_rows(base):
    rows = []
    for c, d in CH.items():
        for k in range(1, 5):
            fp = f"{base}/{c}/frozen_k1_v0/L{k}/FINAL_PROGRAM.json"; prog = f"{base}/{c}/frozen_k1_v0/L{k}/program.py"
            if os.path.exists(fp) and not os.path.exists(prog):
                open(prog, "w").write(extract_code(json.load(open(fp))["text"].strip()).strip() + "\n")
            if not os.path.exists(prog):
                continue
            cp = subprocess.run([PY, f"{d}/score_k1_v3.py", "--version", "0", "--program", f"L{k}={os.path.abspath(prog)}", "--diagnostics"],
                                cwd=d, capture_output=True, text=True, timeout=600)
            try:
                sc = json.loads(cp.stdout)
            except Exception:
                continue
            rows.append((c, dict(level=k, score=sc["levels"][f"L{k}"], instances=sc["instances"], diagnostics=sc.get("diagnostics", []))))
    return rows


def method_rows(base, method, mode, fn="SCORES_ALL.json"):
    rows = []
    for c in CH:
        p = f"{base}/{c}/{fn}"
        if os.path.exists(p):
            for r in json.load(open(p))["rows"]:
                if r["version"] == 0 and r["level"] <= 4 and r["method"] == method and r["mode"] == mode:
                    rows.append((c, r))
    return rows


out = {"sol6_more": {m: summarize(method_rows("baselines_sol6_more", m, "self")) for m in ("gepa", "tfgrpo", "evoskill", "rb")}}
for v in ("lessn", "convn", "procn", "namem"):
    out[v] = {m: summarize(method_rows(f"baselines_{v}", m, "hint")) for m in ("ace", "dc")}
json.dump(out, open("/tmp/agg_extra.json", "w"), indent=1)
print(json.dumps(out))
