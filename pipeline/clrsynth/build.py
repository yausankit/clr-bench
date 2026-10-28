"""Build the K1 v3 deliverables of a chain from its pinned slots (v1 spec section 6, K1 v3 sections 2-4)."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from .candidates import Candidate
from .chain import Chain

HARNESS_DIR = Path(__file__).parent / "harness"


def pinned_chain(ds, cfg, state):
    slots = [{"level": s["level"], "field": s["field"], "cand": Candidate.from_dict(s["pinned"])}
             for s in state["slots"]]
    return Chain(ds, cfg, slots)


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        content = json.dumps(content, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")


def build_instances(chain):
    """All instances for levels 1..5. Returns dict with shared and per-version parts."""
    levels = [s["level"] for s in chain.slots]
    K = max(levels)
    shared = {"public": {}, "h0": {}, "clean": {}, "diag": []}
    per_v = {v: {"hX": {}, "hXN": {}, "single": {}} for v in range(3)}
    for k in levels:
        ref = ("__ref__", chain.ref_sets(k))
        A = chain.a_placements(k)
        shared["public"][k] = chain.public_example(k)
        shared["h0"][k] = chain.make_instance(f"L{k}/h0", A, "max", [ref])
        shared["clean"][k] = []
        for c in range(5 - k):
            reqs = [ref] + [(f"none_{s['level']}", chain.variant(k, s["level"], set()))
                            for s in chain.slots if s["level"] <= k]
            shared["clean"][k].append(chain.make_instance(f"L{k}/clean/{c}", A, "sum", reqs))
        for s in chain.slots:
            j = s["level"]
            if j > k:
                continue
            c = s["cand"]
            f = s["field"]
            for x in [*c.P_M, c.N_p, *c.N_t]:
                member = x in c.P_M
                req = ("a", chain.variant(k, j, {c.A})) if member else ("c", chain.variant(k, j, set(c.pool())))
                inst = chain.make_instance(f"L{k}/diag/{j}/{x}", A + [(f, x)], "sum", [ref, req])
                shared["diag"].append({"level": k, "trap": j, "value": x,
                                       "kind": "inc" if member else "exc", **inst})
            for v in range(3):
                mv = c.P_M[v]
                U = [m for m in c.P_M if m != mv]
                reqs = [ref, ("a", chain.variant(k, j, {c.A})),
                        ("b", chain.variant(k, j, {c.A, mv})),
                        ("c", chain.variant(k, j, set(c.pool())))]
                reqs += [(f"d_{u}", chain.variant(k, j, set(c.members()) - {u})) for u in U]
                reqs += [(f"e_{t}", chain.variant(k, j, set(c.members()) | {t})) for t in c.N_t]
                place = A + [(f, u) for u in U] + [(f, t) for t in c.N_t]
                per_v[v]["single"][(k, j)] = chain.make_instance(f"L{k}/single/{j}/v{v}", place, "sum", reqs)
                per_v[v]["hX"][(k, j)] = chain.pair_view(k, j, v)
                per_v[v]["hXN"][(k, j)] = chain.pair_view(k, j, v, both=True)
    return shared, per_v


def _strip(inst, extra=None):
    out = {"data": inst["data"], "expected": inst["expected"], "entities": inst["entities"],
           "placements": inst["placements"]}
    if inst.get("changes"):
        out["changes"] = inst["changes"]   # practice views: which values differ from the public example
    if extra:
        out.update(extra)
    return out


def build(ds, cfg, state, od, commit=None):
    od = Path(od)
    chain = pinned_chain(ds, cfg, state)
    shared, per_v = build_instances(chain)
    levels = [s["level"] for s in chain.slots]
    course = f"CLR_{cfg['id']}"
    fmt = chain.fmt
    written = []

    def w(rel, content):
        _write(od / rel, content)
        written.append(rel)

    meta = {"id": cfg["id"], "dataset": cfg["dataset"], "seed": cfg["seed"], "answer_format": fmt,
            "course_id": course, "fields": chain.fields,
            "background": chain.background,
            "slots": [{"level": s["level"], "field": s["field"], "label": chain.labels[s["level"]],
                       **s["cand"].to_dict()} for s in chain.slots]}
    w("CHAIN.json", meta)
    for s in chain.slots:
        w(f"TRAPS/L{s['level']}.yaml", yaml.safe_dump({"label": chain.labels[s["level"]],
                                                       **s["cand"].to_dict()}, allow_unicode=True, sort_keys=True))
    lists = {u: {l.id: l for l in ls} for u, ls in ds.lists.items()}
    w("CONCEPTS.json", {f"L{s['level']}": {
        "C": s["cand"].C, "name": lists[s["cand"].universe][s["cand"].C].name,
        "synonyms": lists[s["cand"].universe][s["cand"].C].synonyms,
        "competitors": [{"id": l, "name": lists[s["cand"].universe][l].name} for l in s["cand"].comp_A]}
        for s in chain.slots})
    prompts = {}
    for k in levels:
        ex = shared["public"][k]["data"]
        for split in ("practice", "test"):
            prompts[(k, split)] = chain.prompt(k, split, ex)
            w(f"prompts/L{k}.{split}.txt", prompts[(k, split)])
    diag = [{"instance_id": f"diag_L{d['level']}_T{d['trap']}_{d['kind']}_{i}", "level": d["level"],
             "trap": d["trap"], "value": d["value"], "kind": d["kind"],
             **_strip(d)} for i, d in enumerate(shared["diag"])]
    w("diagnostics.json", diag)
    # the public example in a test task is answered with the test aggregation (sum)
    public_sum = {k: sum(shared["public"][k]["ref_totals"]) for k in levels}
    for v in range(3):
        views, tests = [], []
        for k in levels:
            views.append({"view": "public", "level": k, **_strip(shared["public"][k])})
            views.append({"view": "h-0", "level": k, **_strip(shared["h0"][k])})
            for j in [l for l in levels if l <= k]:
                views.append({"view": f"h-X_{j}_v{v}", "level": k, "trap": j, **_strip(per_v[v]["hX"][(k, j)])})
            for j in [l for l in levels if l <= k]:
                views.append({"view": f"h-XN_{j}_v{v}", "level": k, "trap": j, **_strip(per_v[v]["hXN"][(k, j)])})
            for c, inst in enumerate(shared["clean"][k]):
                tests.append({"instance_id": f"L{k}_clean_{c}", "level": k, "cell": f"clean_{k}", **_strip(inst)})
            for j in [l for l in levels if l <= k]:
                tests.append({"instance_id": f"L{k}_single_{j}_v{v}", "level": k, "cell": f"single_{k}_{j}",
                              "trap": j, **_strip(per_v[v]["single"][(k, j)])})
        w(f"practice_views_v{v}.json", views)
        w(f"test_k1_v{v}.json", tests)
        tasks = []
        for k in levels:
            pv = [x for x in views if x["level"] == k]
            public = next(x for x in pv if x["view"] == "public")
            hidden = [x for x in pv if x["view"] != "public"]
            base = {"adapter": f"python_{fmt}", "axis": "CLRSYNTH", "course_id": course, "dataset": ds.name,
                    "field_strata": {"value": k}, "kind": "python", "language": "python", "level": k,
                    "schemas": {}, "source_group": cfg["id"],
                    "system": "You write one executable Python 3 program that solves the task.",
                    "public": public["data"], "reference_source": f"controls/reference_L{k}.py"}
            practice = {**base, "split": "practice", "task_id": f"{course}.L{k}.practice",
                        "title": f"{course} L{k} practice", "prompt": prompts[(k, "practice")],
                        "hidden": [{"coverage": h["view"], "stratum": h["view"], "data": h["data"],
                                    "expected": h["expected"], **({"changes": h["changes"]} if h.get("changes") else {})}
                                   for h in hidden],
                        "expected": [public["expected"]] + [h["expected"] for h in hidden]}
            cells = [x for x in tests if x["level"] == k]
            test = {**base, "split": "test", "task_id": f"{course}.L{k}.test",
                    "title": f"{course} L{k} test", "prompt": prompts[(k, "test")],
                    "hidden": [{"coverage": c["cell"], "stratum": c["cell"], "data": c["data"],
                                "expected": c["expected"]} for c in cells],
                    "expected": [public_sum[k]] + [c["expected"] for c in cells]}
            w(f"bundle_k1_v{v}/private/{course}.L{k}.practice.json", practice)
            w(f"bundle_k1_v{v}/private/{course}.L{k}.test.json", test)
            for t in (practice, test):
                tasks.append({key: t[key] for key in ("adapter", "course_id", "level", "prompt", "task_id", "title",
                                                      "language", "kind", "dataset", "split", "system")})
        w(f"bundle_k1_v{v}/public/TASKS.json", tasks)
    for hdir in [f"harness_k1_v{v}" for v in range(3)] + ["harness_k1_test"]:
        for name in ("runner.py", "worker.py", "run_candidate.py", "score_base.py"):
            src = (HARNESS_DIR / name).read_text().replace("__FORMAT__", fmt)
            w(f"{hdir}/{name}", src)
    w("score_k1_v3.py", (HARNESS_DIR / "score_k1_v3.py").read_text())
    module_src = (ds.root / "dataset.py").read_text()
    for k in levels:
        for name, sets in (("reference", chain.ref_sets(k)), ("L-lit", chain.lit(k)),
                           ("L-all", chain.all_described(k))):
            w(f"controls/{name}_L{k}.py", control_program(chain, module_src, sets))
    manifest = []
    for rel in sorted(set(written)):
        manifest.append(f"{hashlib.sha256((od / rel).read_bytes()).hexdigest()}  {rel}")
    inputs = sorted(p for p in ds.root.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                    and "raw" not in p.relative_to(ds.root).parts)
    for p in inputs:
        manifest.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  input:{p.relative_to(ds.root)}")
    if commit:
        manifest.append(f"commit {commit}")
    _write(od / "MANIFEST.sha256", "\n".join(manifest) + "\n")
    return written


def control_program(chain, module_src, level_sets):
    """A delivered control program: the dataset's reference() plus a rule set, wrapped in solve(data).
    Practice tasks aggregate with max, test tasks with sum; the split comes from CLRSYNTH_SPLIT (default test)."""
    excluded = {}
    for lvl, vals in sorted(level_sets.items()):
        excluded.setdefault(chain.slot(lvl)["field"], set()).update(vals)
    payload = {f: sorted(v) for f, v in sorted(excluded.items())}
    return (module_src.rstrip() + "\n\n\n# ---- clrsynth control program ----\n"
            "import os as _os\n"
            f"_EXCLUDED = {{k: set(v) for k, v in {payload!r}.items()}}\n\n\n"
            "def solve(data):\n"
            "    vals = list(reference(data, _EXCLUDED).values())\n"
            "    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)\n")


def verify_repro(ds, cfg, state, od):
    od = Path(od)
    with tempfile.TemporaryDirectory(prefix="clrsynth-repro-") as tmp:
        build(ds, cfg, state, tmp)
        diffs = []
        for line in (od / "MANIFEST.sha256").read_text().splitlines():
            digest, _, rel = line.partition("  ")
            if not rel or rel.startswith("input:") or line.startswith("commit"):
                continue
            other = Path(tmp) / rel
            if not other.exists() or hashlib.sha256(other.read_bytes()).hexdigest() != digest:
                diffs.append(rel)
        return diffs
