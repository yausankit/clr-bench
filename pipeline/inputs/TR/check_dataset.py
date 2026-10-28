"""Self-checks for dataset.py required by the guide (section 5).

Run:  python3 check_dataset.py [seed]
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    spec = importlib.util.spec_from_file_location("tr_dataset", os.path.join(HERE, "dataset.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _universe_values(field):
    name = {"segments.airline": "airline", "segments.arrival_airport": "airport",
            "claims.currency": "currency"}[field]
    with open(os.path.join(HERE, "universes", name + ".tsv"), encoding="utf-8") as fh:
        fh.readline()
        return [line.split("\t")[0] for line in fh if line.strip()]


def main(seed=20266093):
    m = load()
    ok = True

    def need(cond, msg):
        nonlocal ok
        print(("ok   " if cond else "FAIL ") + msg)
        ok = ok and bool(cond)

    w1 = m.base_world(seed, "check")
    w2 = m.base_world(seed, "check")
    need(json.dumps(w1, sort_keys=True) == json.dumps(w2, sort_keys=True),
         "base_world is byte-identical for the same (seed, step)")
    ents = m.entities(w1)
    need(len(ents) >= 30, f"entities >= 30 (got {len(ents)})")
    for f in m.TRAP_FIELDS:
        pos = list(m.slots(w1, f))
        per = {}
        for e, p in pos:
            per.setdefault(e, []).append(p)
        need(all(len(per.get(e, [])) >= 3 for e in ents), f"{f}: every entity has >= 3 positions")
        need(all(isinstance(m.total(w1, e, set()), int) for e in ents), f"{f}: total() is int")
        e0 = ents[0]
        base = m.total(w1, e0, set())
        something = any(m.total(w1, e0, {(f, p)}) < base for p in per[e0])
        need(something, f"{f}: excluding a position lowers total()")
    for f in m.TRAP_FIELDS:
        vals = sorted(set(_universe_values(f)))
        e, p = list(m.slots(w1, f))[0]
        w3 = m.base_world(seed, "check-set")
        new = vals[len(vals) // 2]
        other = vals[0] if vals[0] != new else vals[1]
        for e2, p2 in m.slots(w3, f):
            if p2 != p:
                m.set_value(w3, f, p2, other)
        m.set_value(w3, f, p, new)
        data = m.render(w3, [e])
        text = json.dumps(data)
        need(new in text, f"{f}: set value appears in render()")
        need(m.values(data, f).count(new) == 1, f"{f}: values() reports the new value once")
        need(m.reference(data, {})[e] == m.total(w3, e, set()), f"{f}: reference() equals total()")
        need(sum(m.reference(data, {f: {new}}).values()) < sum(m.reference(data, {}).values()),
             f"{f}: excluding by value lowers reference()")
    print("ALL OK" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 20266093))
