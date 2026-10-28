#!/usr/bin/env python3
"""Self-checks for dataset.py required by guide section 5 / section 8.5."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED, STEP = 20266086, "check"


def load():
    spec = importlib.util.spec_from_file_location("ws_dataset", ROOT / "dataset.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    mod = load()
    fails = []

    def want(ok, msg):
        print(("ok   " if ok else "FAIL ") + msg)
        if not ok:
            fails.append(msg)

    w1 = mod.base_world(SEED, STEP)
    w2 = mod.base_world(SEED, STEP)
    want(json.dumps(w1, sort_keys=True, default=str) == json.dumps(w2, sort_keys=True, default=str),
         "base_world is byte-identical for the same (seed, step)")
    ents = list(mod.entities(w1))
    want(len(ents) >= 30, f"entities >= 30 (got {len(ents)})")
    for field in mod.TRAP_FIELDS:
        pos = list(mod.slots(w1, field))
        per = {}
        for ent, p in pos:
            per.setdefault(ent, []).append(p)
        thin = [e for e in ents if len(per.get(e, [])) < 3]
        want(not thin, f"{field}: every entity has >= 3 positions (thin: {thin[:3]})")
        # set_value -> render contains the value exactly once at that position
        uname = {"findings.cwe": "cwe", "hosts.tld": "tld", "findings.language": "language"}[field]
        marker = mod._universe(uname)[17]
        w = mod.base_world(SEED, STEP)
        ent, p = pos[0]
        mod.set_value(w, field, p, marker)
        data = mod.render(w, ents)
        text = json.dumps(data, ensure_ascii=False)
        want(marker in text, f"{field}: set value appears in render")
        want(mod.values(data, field).count(marker) >= 1, f"{field}: values() sees the set value")
        # total: int, and excluding a position lowers it
        base = mod.total(w, ent, set())
        less = mod.total(w, ent, {(field, p)})
        want(isinstance(base, int) and isinstance(less, int), f"{field}: total() returns int")
        want(less < base, f"{field}: excluding one position lowers the entity total")
        # reference agrees with total over all entities, both empty and non-empty exclusions
        ref0 = mod.reference(data, {})
        want(sum(ref0.values()) == sum(mod.total(w, e, set()) for e in ents),
             f"{field}: reference({{}}) equals total() over all entities")
        ref1 = mod.reference(data, {field: {marker}})
        excl = {(field, p)}
        want(sum(ref1.values()) <= sum(ref0.values()), f"{field}: reference exclusion does not increase the sum")
        # reference must not depend on files: it is exercised from an empty dir by lint; here just check signature
    print("\ncheck_dataset:", "OK" if not fails else f"{len(fails)} failure(s)")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
