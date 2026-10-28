"""clrsynth certify <dataset>: certify a pool of candidates before any chain is built.

Each candidate (a list C with one choice of A, P_M, N_p, N_t) is probed in two stages. Stage 1 probes it alone, in a
one-slot chain (P0, then P1, then P1H; a failure stops the sequence). Stage 2 places each stage-1 survivor in a mock
five-level chain laid out like the dataset's chains, its other four levels filled with stage-1 survivors of the other
fields, and probes it again: the other levels' examples tell the model what kind of category the labels are, which
makes classes easier to guess and to generalize (10-21 TR: P1 rose by about 0.5 and half failed P0 once in a chain).
Only stage-2 passes count. A list with many members gets more variants with disjoint A and P_M, so sibling
chains can share C without sharing a trap value. Results go to out/<dataset>/POOL.json; make-chain then draws only
certified variants and still runs the full-chain probes as a final check. The command reports, per field, how many
certified variants there are against how many the dataset's chains need, so missing lists are found before any
chain is built."""
import json
import sys
from collections import Counter
from pathlib import Path

from .inputs import Dataset, load_chain
from .candidates import FieldContext, Candidate, allocate_slots, build_candidate
from .chain import Chain, PlacementError, P1_LOW, P1_HIGH
from .probe import Endpoint, parse_json_answer, judge_p0, judge_p1, judge_p1h
from .screen import screen

MARGIN = 1.3      # stage-2 passes wanted per needed slot (full-chain probes reject a few)
STAGE1_MARGIN = 3  # stage-1 passes wanted per needed slot (stage 2 rejects many)
MAX_VARIANTS = 3


def needs(ds, cfgs):
    """Slots per field summed over the dataset's chains."""
    need = Counter()
    for cfg in cfgs:
        for s in allocate_slots(ds, cfg):
            need[s["field"]] += 1
    return need


def _save(path, pool):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(pool, indent=1, ensure_ascii=False, sort_keys=True))
    tmp.replace(path)


def _log(log_dir, key, kind, items, replies):
    log_dir.mkdir(parents=True, exist_ok=True)
    for it, rep in zip(items, replies):
        name = f"{key}_{kind}_v{it['version'] if it['version'] is not None else '-'}_{it['sample']}.json"
        (log_dir / name).write_text(json.dumps({**it, "reply": rep}, ensure_ascii=False, indent=1))


def certify(chain_paths, out_root):
    cfgs = [load_chain(p) for p in chain_paths]
    ds = Dataset(cfgs[0]["_inputs_root"], cfgs[0]["dataset"])
    for p in chain_paths:          # screen merges into out/<dataset>/SCREEN.json and skips screened lists
        screen(p, out_root)
    out = Path(out_root) / "out" / ds.name
    log_dir = Path(out_root) / "logs" / ds.name / "certify"
    pool_path = out / "POOL.json"
    pool = json.loads(pool_path.read_text()) if pool_path.exists() else {}
    scr = json.loads((out / "SCREEN.json").read_text())
    need = needs(ds, cfgs)
    ep = Endpoint()
    band = cfgs[0]["probe"].get("p1_band", [P1_LOW, P1_HIGH])
    criterion = cfgs[0]["probe"].get("criterion", "soft")

    for field, n_need in sorted(need.items()):
        cfg = next(c for c in cfgs if any(f["field"] == field for f in c["fields"]))
        fc = FieldContext(ds, cfg, field)
        lists = [c for c in fc.c_order() if scr.get(c, {}).get("pass")]
        for k in range(MAX_VARIANTS):
            have = sum(v["pass1"] for c in lists for v in pool.get(c, {}).get("variants", []))
            if have >= STAGE1_MARGIN * n_need:
                break
            # variant k for every list on the first pass; later passes only for lists with a certified variant
            todo = []
            for c in lists:
                entry = pool.setdefault(c, {"field": field, "variants": [], "done": False})
                if entry["done"] or len(entry["variants"]) > k:
                    continue
                if k > 0 and not any(v["pass1"] for v in entry["variants"]):
                    continue
                avoid = {x for v in entry["variants"] for x in [v["cand"]["A"], *v["cand"]["P_M"]]}
                cand, why = build_candidate(fc, c, avoid, 1)
                if cand is None:
                    entry["done"] = True
                    entry["stop_reason"] = why
                    continue
                try:
                    chain = Chain(ds, cfg, [{"level": 1, "field": field, "cand": cand}])
                    chain.public_example(1)
                except PlacementError as e:
                    entry["done"] = True
                    entry["stop_reason"] = f"placement: {e}"
                    continue
                todo.append((c, cand, chain))
            if not todo:
                continue
            results = {c: {"cand": cand.to_dict(), "pass1": False, "pass": False} for c, cand, _ in todo}
            alive = todo
            for kind in ("P0", "P1", "P1H"):
                if kind == "P1" and not band:
                    continue
                batches = [(c, cand, chain, chain.probe_prompts([1], kinds=(kind,))) for c, cand, chain in alive]
                flat = [it["prompt"] for *_, items in batches for it in items]
                replies = iter(ep.run_all(flat))
                nxt = []
                for c, cand, chain, items in batches:
                    reps = [next(replies) for _ in items]
                    _log(log_dir, f"{c}_k{k}", kind, items, reps)
                    parsed = [parse_json_answer(r) for r in reps]
                    if kind == "P0":
                        v = judge_p0(cand, 1, parsed)
                    elif kind == "P1":
                        v = judge_p1(cand, 1, list(zip([it["version"] for it in items], parsed)), band)
                    else:
                        v = judge_p1h(cand, 1, list(zip([it["version"] for it in items], parsed)), criterion, set())
                    results[c][kind] = {key: v[key] for key in v if key != "samples"}
                    if v["pass"]:
                        nxt.append((c, cand, chain))
                alive = nxt
            for c, *_ in alive:
                results[c]["pass1"] = True
            for c, r in results.items():
                pool[c]["variants"].append(r)
            _save(pool_path, pool)

    stage2(ds, cfgs, pool, pool_path, ep, band, criterion, log_dir)

    ok = True
    print(f"certify {ds.name}: certified variants per field (need = slots over the dataset's chains)")
    for field, n_need in sorted(need.items()):
        have = sum(v["pass"] for e in pool.values() if e["field"] == field for v in e["variants"])
        stage1 = sum(v["pass1"] for e in pool.values() if e["field"] == field for v in e["variants"])
        concepts = sum(any(v["pass"] for v in e["variants"]) for e in pool.values() if e["field"] == field)
        flag = "OK" if have >= n_need else "SHORT"
        ok = ok and have >= n_need
        print(f"  {field}: {have} certified variants from {concepts} lists (stage 1: {stage1}); need {n_need} "
              f"[{flag}]")
    _save(pool_path, pool)
    if not ok:
        print("certify: some fields are short; add lists for them (see CLRSYNTH_ADD_DATASET_ZH.md) and rerun",
              file=sys.stderr)
    return 0 if ok else 2


def mock_slots(ds, cfg, fc_by_field, pool, field, cand, seed_key):
    """A five-level layout like the dataset's chains with `cand` at the last slot of its field and the other slots
    filled with stage-1 survivors of their fields: distinct concepts, member-disjoint pools within a universe."""
    from .inputs import seeded_order
    layout = allocate_slots(ds, cfg)
    j = max(s["level"] for s in layout if s["field"] == field)
    chosen = {j: cand}
    for s in layout:
        if s["level"] == j:
            continue
        fc = fc_by_field[s["field"]]
        options = [Candidate.from_dict(v["cand"]) for c, e in pool.items() if e["field"] == s["field"]
                   for v in e["variants"] if v["pass1"]]
        for o in seeded_order(options, 0, "mock", seed_key, s["level"]):
            if any(o.C == x.C for x in chosen.values()):
                continue
            same_u = [x for lvl, x in chosen.items() if fc_by_field[next(l["field"] for l in layout
                                                                          if l["level"] == lvl)].uname == fc.uname]
            if any(set(o.pool()) & set(x.pool()) for x in same_u):
                continue
            chosen[s["level"]] = o
            break
        else:
            return None, j
    return [{"level": s["level"], "field": s["field"], "cand": chosen[s["level"]]} for s in layout], j


def stage2(ds, cfgs, pool, pool_path, ep, band, criterion, log_dir):
    """Re-probe every stage-1 survivor inside a mock chain; `pass` is the stage-2 verdict."""
    cfg = cfgs[0]
    fc_by_field = {f["field"]: FieldContext(ds, cfg, f["field"]) for f in cfg["fields"]}
    todo = []
    for c, e in sorted(pool.items()):
        for k, v in enumerate(e["variants"]):
            if not v["pass1"] or "stage2" in v or e["field"] not in fc_by_field:
                continue
            cand = Candidate.from_dict(v["cand"])
            slots, j = mock_slots(ds, cfg, fc_by_field, pool, e["field"], cand, f"{c}/{k}")
            if slots is None:
                v["stage2"] = {"error": "no mock context"}
                continue
            try:
                chain = Chain(ds, cfg, slots)
                chain.public_example(max(s["level"] for s in slots))
            except PlacementError as err:
                v["stage2"] = {"error": f"placement: {err}"}
                continue
            todo.append((c, k, v, cand, chain, j))
    alive = todo
    for kind in ("P0", "P1", "P1H"):
        if kind == "P1" and not band:
            continue
        batches = [(c, k, v, cand, chain, j, chain.probe_prompts([j], kinds=(kind,)))
                   for c, k, v, cand, chain, j in alive]
        replies = iter(ep.run_all([it["prompt"] for *_, items in batches for it in items]))
        nxt = []
        for c, k, v, cand, chain, j, items in batches:
            reps = [next(replies) for _ in items]
            _log(log_dir, f"{c}_k{k}_ctx", kind, items, reps)
            parsed = [parse_json_answer(r) for r in reps]
            if kind == "P0":
                res = judge_p0(cand, j, parsed)
            elif kind == "P1":
                res = judge_p1(cand, j, list(zip([it["version"] for it in items], parsed)), band)
            else:
                res = judge_p1h(cand, j, list(zip([it["version"] for it in items], parsed)), criterion, set())
            v.setdefault("stage2", {})[kind] = {key: res[key] for key in res if key != "samples"}
            v["stage2"]["context"] = [s["cand"].C for s in chain.slots]
            if res["pass"]:
                nxt.append((c, k, v, cand, chain, j))
        alive = nxt
        _save(pool_path, pool)
    for c, k, v, *_ in alive:
        v["pass"] = True
    _save(pool_path, pool)

