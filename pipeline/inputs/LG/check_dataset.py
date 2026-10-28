#!/usr/bin/env python3
"""Self-check of dataset.py (guide section 5): determinism, entity count, positions per entity,
set_value visibility, total/reference agreement, values() extraction."""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("lg_dataset", HERE / "dataset.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SEED = 20266088
fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {name}{'' if ok else ' -- ' + str(detail)}")
    if not ok:
        fails.append(name)


w1 = mod.base_world(SEED, "check")
w2 = mod.base_world(SEED, "check")
a = json.dumps(w1, sort_keys=True, default=str)
b = json.dumps(w2, sort_keys=True, default=str)
check("base_world deterministic", a == b)
w3 = mod.base_world(SEED + 1, "check")
check("different seed gives a different world", json.dumps(w3, sort_keys=True) != a)

ents = mod.entities(w1)
check("entities >= 30", len(ents) >= 30, len(ents))
for f in mod.TRAP_FIELDS:
    per = {}
    for e, p in mod.slots(w1, f):
        per.setdefault(e, []).append(p)
    thin = [e for e in ents if len(per.get(e, [])) < 3]
    check(f"{f}: every entity has >= 3 positions", not thin, thin[:3])

values = {}
for line in (HERE / "universes" / "tld.tsv").read_text().splitlines()[1:]:
    values.setdefault("tld", []).append(line.split("\t")[0])
for name in ("port", "client_app", "user"):
    values[name] = [l.split("\t")[0] for l in (HERE / "universes" / f"{name}.tsv").read_text().splitlines()[1:]]
uni = {"proxy_connections.tld": "tld", "proxy_connections.port": "port",
       "proxy_connections.client_app": "client_app", "ssh_logins.user": "user"}

for f in mod.TRAP_FIELDS:
    v = values[uni[f]][len(values[uni[f]]) // 2]
    w = mod.base_world(SEED, "check")
    e, p = mod.slots(w, f)[0]
    before = mod.total(w, e, set())
    mod.set_value(w, f, p, v)
    after = mod.total(w, e, {(f, p)})
    data = mod.render(w, ents)
    check(f"{f}: set_value appears in render()", v in mod.values(data, f), v)
    check(f"{f}: values() count of the new value", mod.values(data, f).count(v) >= 1)
    check(f"{f}: total() int with empty and non-empty excluded",
          isinstance(mod.total(w, e, set()), int) and isinstance(after, int))
    check(f"{f}: excluding one position lowers the total", after < before, (before, after))
    ref = mod.reference(data, {f: {v}})
    table, name = f.split(".")
    key = "proxy" if table == "proxy_connections" else "logins"
    excl = set()
    for rid, rec in w[key].items():
        got = rec["host"].rsplit(".", 1)[-1] if name == "tld" else rec[name if name != "client_app" else "app"]
        if got == v:
            excl.add((f, rid))
    tot = {x: mod.total(w, x, excl) for x in ents}
    check(f"{f}: reference matches total", ref == tot)

print("\nRESULT:", "OK" if not fails else f"{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
