"""Consistency checks over a built chain's files, for example that the practice and test tasks share records and
rules, that value pools of different levels are disjoint, and that every expected answer is reproduced."""
import json
import os
import re
import sys
from pathlib import Path

import yaml

STOP = {"a", "an", "the", "of", "in", "and", "at", "for", "to", "on", "by", "class", "tag", "code", "group"}


def _load(od, rel):
    return json.loads((od / rel).read_text(encoding="utf-8"))


def leaf_values(data):
    out = []
    if isinstance(data, dict):
        for v in data.values():
            out.extend(leaf_values(v))
    elif isinstance(data, list):
        for v in data:
            out.extend(leaf_values(v))
    else:
        out.append(str(data))
    return out


def count_value(data, value):
    """Occurrences of a value: exact leaf match for JSON data; whole-token match for text."""
    if isinstance(data, str):
        # dots, dashes, underscores and slashes join a token (a label inside a host name is not a value)
        return len(re.findall(r"(?<![A-Za-z0-9._/-])" + re.escape(value) + r"(?![A-Za-z0-9._/-])", data))
    if isinstance(data, dict) and all(isinstance(v, str) for v in data.values()) and data:
        # files format: search file texts by token
        return sum(count_value(v, value) for v in data.values())
    return sum(1 for x in leaf_values(data) if x == value)


def changed_values(a, b):
    """How many leaves (JSON) or lines (text and files) differ between two inputs; None if the shapes differ."""
    import difflib
    if isinstance(a, str) and isinstance(b, str):
        sm = difflib.SequenceMatcher(None, a.splitlines(), b.splitlines(), autojunk=False)
        return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    if isinstance(a, dict) and isinstance(b, dict) and a and all(isinstance(v, str) for v in a.values()):
        if set(a) != set(b):
            return None
        return sum(changed_values(a[k], b[k]) for k in a)
    la, lb = leaf_values(a), leaf_values(b)
    if len(la) != len(lb):
        return None
    return sum(x != y for x, y in zip(la, lb))


PAIR_LIMIT = 6   # m_v and N_p, plus fields a dataset derives from them (a route string, a log line)


def check(ds, cfg, od):
    od = Path(od)
    mod = ds.module
    meta = _load(od, "CHAIN.json")
    slots = sorted(meta["slots"], key=lambda s: s["level"])
    levels = [s["level"] for s in slots]
    by_level = {s["level"]: s for s in slots}
    results = {}
    failed = []

    def rec(name, ok, detail=None):
        results[name] = {"pass": bool(ok), **({"detail": detail} if detail is not None else {})}
        if not ok:
            failed.append(name)

    def sets_ref(k):
        return {s["level"]: {s["A"], *s["P_M"]} for s in slots if s["level"] <= k}

    def excluded(sets):
        out = {}
        for lvl, vals in sets.items():
            out.setdefault(by_level[lvl]["field"], set()).update(vals)
        return out

    def answer(data, sets, agg):
        tot = mod.reference(data, excluded(sets))
        vals = list(tot.values())
        return max(vals) if agg == "max" else sum(vals)

    def variant(k, j, vals):
        s = sets_ref(k)
        s[j] = set(vals)
        return s

    def pool(s):
        return [s["A"], *s["P_M"], s["N_p"], *s["N_t"]]

    # keyed by (field, value): the same string can be a value of two universes (AZN: an airport and a currency)
    all_pool = {(s["field"], v): (s["level"], role) for s in slots for v, role in
                [(s["A"], "A")] + [(m, "P_M") for m in s["P_M"]] + [(s["N_p"], "N_p")] + [(t, "N_t") for t in s["N_t"]]}

    def fv(levels_values):
        """{level: values} -> {(field, value)}"""
        return {(by_level[l]["field"], v) for l, vals in levels_values.items() for v in vals}

    field_values = getattr(mod, "values", None)

    def occurrences(data, v, field):
        if field_values is None:
            return count_value(data, v)
        return field_values(data, field).count(v)

    def allowed_counts(data, allowed, where):
        bad = []
        numeric_text = isinstance(data, str) and field_values is None
        for (field, v), (lvl, role) in all_pool.items():
            n = occurrences(data, v, field)
            if (field, v) in allowed and n == 0:
                bad.append(f"{v} missing")
            if (field, v) not in allowed and n > 0 and not (numeric_text and v.isdigit()):
                bad.append(f"{v} ({role} of L{lvl}) present")
        return bad

    # 1. prompts
    prompts = {(k, sp): (od / "prompts" / f"L{k}.{sp}.txt").read_text(encoding="utf-8")
               for k in levels for sp in ("practice", "test")}
    for sp in ("practice", "test"):
        lines = {k: [l for l in prompts[(k, sp)].splitlines() if l.startswith("Return the ")] for k in levels}
        rec(f"summary_sentence_{sp}", len({tuple(v) for v in lines.values()}) == 1 and all(len(v) == 1 for v in lines.values()))
    refs = {key: p[p.index("Value reference:"):p.index("Example input:")] for key, p in prompts.items()}
    rec("value_reference_identical", len(set(refs.values())) == 1)
    ref_text = next(iter(refs.values()))
    ref_vals = {}
    current = None
    for line in ref_text.splitlines()[1:]:
        if line.endswith(":") and not line.startswith("- "):
            current = line[:-1]
            ref_vals[current] = set()
        elif line.startswith("- ") and current:
            ref_vals[current].add(line[2:].split(" — ")[0])
    rec("value_reference_covers_pools", all(set(pool(s)) <= ref_vals.get(s["field"], set()) for s in slots))
    for s in slots:
        lst = {l.id: l for l in ds.lists[s["universe"]]}[s["C"]]
        bad = (ref_vals.get(s["field"], set()) - set(pool(s))) & (set(lst.members) | set(lst.disputed))
        others = [o for o in slots if o["field"] == s["field"] and o is not s]
        bad -= {v for o in others for v in pool(o)}
        rec(f"H7_background_L{s['level']}", not bad, sorted(bad)[:5])
    # 2. tasks vs prompts, hidden counts, shared files
    course = meta["course_id"]
    for v in range(3):
        for k in levels:
            pr = _load(od, f"bundle_k1_v{v}/private/{course}.L{k}.practice.json")
            te = _load(od, f"bundle_k1_v{v}/private/{course}.L{k}.test.json")
            rec(f"task_prompt_v{v}_L{k}", pr["prompt"] == prompts[(k, "practice")] and te["prompt"] == prompts[(k, "test")])
            rec(f"practice_hidden_count_v{v}_L{k}", len(pr["hidden"]) == 2 * k + 1
                and pr["expected"][1:] == [h["expected"] for h in pr["hidden"]])
            rec(f"test_cells_v{v}_L{k}", len(te["hidden"]) == 5)
            rec(f"test_public_expected_v{v}_L{k}", te["expected"][0] == answer(te["public"], sets_ref(k), "sum"),
                [te["expected"][0], answer(te["public"], sets_ref(k), "sum")])
    for k in levels:
        shared = []
        for v in range(3):
            pr = _load(od, f"bundle_k1_v{v}/private/{course}.L{k}.practice.json")
            te = _load(od, f"bundle_k1_v{v}/private/{course}.L{k}.test.json")
            shared.append(json.dumps([pr["public"], pr["hidden"][0], [h for h in te["hidden"] if h["stratum"].startswith("clean")]], sort_keys=True))
        rec(f"shared_across_versions_L{k}", len(set(shared)) == 1)
    # 3. per-instance checks
    diag = _load(od, "diagnostics.json")
    for v in range(3):
        views = _load(od, f"practice_views_v{v}.json")
        tests = _load(od, f"test_k1_v{v}.json")
        lit_scores, all_scores = {}, {}
        for k in levels:
            A = fv({j: {by_level[j]["A"]} for j in levels if j <= k})
            lit = {j: {by_level[j]["A"]} for j in levels if j <= k}
            alld = {j: set(pool(by_level[j])) for j in levels if j <= k}
            for x in [x for x in views if x["level"] == k]:
                name = f"v{v}_L{k}_{x['view']}"
                exp = answer(x["data"], sets_ref(k), "max")
                rec(f"reference_{name}", exp == x["expected"], [exp, x["expected"]])
                if x["view"] in ("public", "h-0"):
                    allowed = A
                    rec(f"literal_pass_{name}", answer(x["data"], lit, "max") == x["expected"]
                        and answer(x["data"], alld, "max") == x["expected"])
                elif x["view"].startswith("h-XN"):   # m_v and N_p changed in
                    j = x["trap"]
                    s = by_level[j]
                    allowed = A | fv({j: {s["P_M"][v], s["N_p"]}})
                    rec(f"identify_{name}", answer(x["data"], variant(k, j, {s["A"]}), "max") != x["expected"]
                        and answer(x["data"], variant(k, j, pool(s)), "max") != x["expected"])
                else:   # h-X: m_v changed in
                    j = x["trap"]
                    s = by_level[j]
                    allowed = A | fv({j: {s["P_M"][v]}})
                    rec(f"identify_{name}", answer(x["data"], variant(k, j, {s["A"]}), "max") != x["expected"])
                if x["view"] not in ("public", "h-0"):
                    public = next(y for y in views if y["level"] == k and y["view"] == "public")
                    n = changed_values(public["data"], x["data"])
                    rec(f"pair_of_public_{name}", n is not None and 1 <= n <= PAIR_LIMIT, n)
                bad = allowed_counts(x["data"], allowed, name)
                rec(f"code_count_{name}", not bad, bad[:5])
            lp = ap = 0
            for t in [t for t in tests if t["level"] == k]:
                name = f"v{v}_{t['instance_id']}"
                exp = answer(t["data"], sets_ref(k), "sum")
                rec(f"reference_{name}", exp == t["expected"], [exp, t["expected"]])
                lp += answer(t["data"], lit, "sum") == t["expected"]
                ap += answer(t["data"], alld, "sum") == t["expected"]
                if t["cell"].startswith("clean"):
                    allowed = A
                    rec(f"identify_{name}", all(answer(t["data"], variant(k, j, set()), "sum") != t["expected"]
                                                for j in levels if j <= k))
                else:
                    j = t["trap"]
                    s = by_level[j]
                    mv = s["P_M"][v]
                    U = [m for m in s["P_M"] if m != mv]
                    allowed = A | fv({j: set(U) | set(s["N_t"])})
                    progs = [{s["A"]}, {s["A"], mv}, set(pool(s))] + [{s["A"], *s["P_M"]} - {u} for u in U] \
                        + [{s["A"], *s["P_M"], t2} for t2 in s["N_t"]]
                    rec(f"identify_{name}", all(answer(t["data"], variant(k, j, pr), "sum") != t["expected"]
                                                for pr in progs))
                bad = allowed_counts(t["data"], allowed, name)
                rec(f"code_count_{name}", not bad, bad[:5])
            lit_scores[k], all_scores[k] = lp / 5, ap / 5
        target = {k: round((5 - k) / 5, 2) for k in levels}
        rec(f"L-lit_scores_v{v}", {k: round(x, 2) for k, x in lit_scores.items()} == target, lit_scores)
        rec(f"L-all_scores_v{v}", {k: round(x, 2) for k, x in all_scores.items()} == target, all_scores)
    for d in diag:
        k, j = d["level"], d["trap"]
        s = by_level[j]
        name = d["instance_id"]
        exp = answer(d["data"], sets_ref(k), "sum")
        rec(f"reference_{name}", exp == d["expected"])
        prog = {s["A"]} if d["kind"] == "inc" else set(pool(s))
        rec(f"identify_{name}", answer(d["data"], variant(k, j, prog), "sum") != d["expected"])
        A = fv({i: {by_level[i]["A"]} for i in levels if i <= k})
        bad = allowed_counts(d["data"], A | fv({j: {d["value"]}}), name)
        rec(f"code_count_{name}", not bad, bad[:5])
    # 4. H1, H2, H6 from delivered traps and lists
    for s in slots:
        lists = {l.id: l for l in ds.lists[s["universe"]]}
        C = lists[s["C"]]
        members = set(C.members)
        h1 = all(v in members for v in [s["A"], *s["P_M"]]) and not any(v in members or v in C.disputed
                                                                        for v in [s["N_p"], *s["N_t"]])
        rec(f"H1_L{s['level']}", h1 and len(set(pool(s))) == 12)
        h2 = [l for l in s["comp_A"] if any(t in lists[l].members for t in s["N_t"])]
        rec(f"H2_L{s['level']}", len(h2) >= 2, h2)
        label_words = {w.lower() for w in re.findall(r"[A-Za-z]+", by_level[s["level"]]["label"])} - STOP
        c_words = {w.lower() for text in [C.name, C.id.replace("_", " "), *C.synonyms]
                   for w in re.findall(r"[A-Za-z]+", text)} - STOP
        overlap = {w for w in label_words & c_words if len(w) >= 3}  # a code letter like the B of B4 is no word
        rec(f"label_overlap_L{s['level']}", not overlap, sorted(overlap))
    rec("concepts_distinct", len({s["C"] for s in slots}) == len(slots), sorted(s["C"] for s in slots))
    for i, s in enumerate(slots):
        for o in slots[i + 1:]:
            if o["universe"] == s["universe"]:
                rec(f"H6_L{s['level']}_L{o['level']}", not (set(pool(s)) & set(pool(o))) and s["C"] != o["C"])
    # 5. delivered reference programs through the delivered harness
    sys.path.insert(0, str(od / "harness_k1_test"))
    try:
        import importlib
        runner = importlib.import_module("runner")
        importlib.reload(runner)
        tests0 = _load(od, "test_k1_v0.json")
        views0 = _load(od, "practice_views_v0.json")
        for k in levels:
            code = (od / "controls" / f"reference_L{k}.py").read_text(encoding="utf-8")
            ok = all(runner.run_candidate(code, t["data"], timeout=60).get("value") == t["expected"]
                     for t in tests0 if t["level"] == k)
            env = {**os.environ, "CLRSYNTH_SPLIT": "practice"}
            ok_p = all(runner.run_candidate(code, x["data"], timeout=60, env=env).get("value") == x["expected"]
                       for x in views0 if x["level"] == k)
            rec(f"harness_reference_L{k}", ok and ok_p)
    finally:
        sys.path.pop(0)
        sys.modules.pop("runner", None)
    report = {"pass": not failed, "failed": failed, "checks": len(results), "results": results}
    (od / "ZERO_CHECK.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
    return report
