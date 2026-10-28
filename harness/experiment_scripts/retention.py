"""Retention of earlier rules: at test level k, exclusion of unseen members (inc_u) and keeping of non-members (exc) for
each rule j <= k, from the value-level diagnostics already scored. Conditions: GPT-6-Luna (baselines_fb; history from
SCORES_EXTRA.json) and GPT-6-Sol (baselines_backbone_sol6). Writes /tmp/retention.json."""
import json, re
CH = dict(l.split("\t") for l in open("baselines_final/CHAINS.tsv").read().splitlines() if l)
SLOTS = {}
for c, d in CH.items():
    for s in json.load(open(f"{d}/CHAIN.json"))["slots"]:
        SLOTS[(c, s["level"])] = s


def rows(base, method, mode, fn):
    out = []
    for c in CH:
        try:
            data = json.load(open(f"{base}/{c}/{fn}"))["rows"]
        except FileNotFoundError:
            continue
        out += [(c, r) for r in data if r["version"] == 0 and r["level"] <= 4 and r["method"] == method and r["mode"] == mode]
    return out


def matrix(rs):
    inc = {(k, j): [] for k in range(1, 5) for j in range(1, k + 1)}
    exc = {(k, j): [] for k in range(1, 5) for j in range(1, k + 1)}
    for c, r in rs:
        for x in r.get("diagnostics", []):
            m = re.match(r"diag_L(\d+)_T(\d+)_", x["instance_id"])
            if not m or int(m.group(1)) != r["level"]:
                continue
            k, j = int(m.group(1)), int(m.group(2))
            if x["kind"] == "inc":
                if x["value"] != SLOTS[(c, j)]["P_M"][0]:
                    inc[(k, j)].append(x["passed"])
            else:
                exc[(k, j)].append(x["passed"])
    f = lambda v: round(100 * sum(v) / len(v), 1) if v else None
    return {"inc_u": {f"L{k}R{j}": f(v) for (k, j), v in inc.items()}, "exc": {f"L{k}R{j}": f(v) for (k, j), v in exc.items()}}


out = {}
for tag, base, hist_fn in (("luna", "baselines_fb", "SCORES_EXTRA.json"), ("sol6", "baselines_backbone_sol6", "SCORES_ALL.json")):
    for m in ("ace", "dc"):
        for mode in ("self", "hint"):
            out[f"{tag}/{m}/{mode}"] = matrix(rows(base, m, mode, "SCORES_ALL.json"))
    out[f"{tag}/hist"] = matrix(rows(base, "hist", "self", hist_fn))
json.dump(out, open("/tmp/retention.json", "w"), indent=1)
for k, v in out.items():
    print(k, "inc_u", v["inc_u"])
