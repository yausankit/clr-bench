"""Self-checks for dataset.py (guide section 5).  Run from the dataset directory: python3 check_dataset.py"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dataset", ROOT / "dataset.py")
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)

SEED = 20266089
failures = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(name)


w1 = ds.base_world(SEED, "check")
w2 = ds.base_world(SEED, "check")
check("deterministic base_world", json.dumps(w1, sort_keys=True) == json.dumps(w2, sort_keys=True))
ents = ds.entities(w1)
check("entities >= 30", len(ents) >= 30, str(len(ents)))
for field in ds.TRAP_FIELDS:
    pos = ds.slots(w1, field)
    per = {}
    for ent, p in pos:
        per.setdefault(ent, []).append(p)
    thin = [e for e in ents if len(per.get(e, [])) < 3]
    check(f"{field}: >=3 positions per entity", not thin, str(len(thin)))
    ent, p = pos[0]
    universe = {"medications.ingredient": "medicine", "conditions.code": "condition",
                "procedures.code": "procedure"}[field]
    values = [line.split("\t")[0] for line in
              (ROOT / "universes" / f"{universe}.tsv").read_text().splitlines()[1:]]
    new = values[len(values) // 2]
    before = ds.render(w1, ents)
    ds.set_value(w1, field, p, new)
    after = ds.render(w1, ents)
    text = json.dumps(after, ensure_ascii=False)
    check(f"{field}: set_value visible in render", new in text)
    check(f"{field}: values() sees the new value", ds.values(after, field).count(new) >= 1)
    base = ds.total(w1, ent, set())
    less = ds.total(w1, ent, {(field, p)})
    check(f"{field}: excluding a position lowers the total", isinstance(base, int) and less < base,
          f"{base} -> {less}")
    check(f"{field}: total is int", isinstance(ds.total(w1, ent, set()), int))
    ref = ds.reference(after, {})
    check(f"{field}: reference(render) == total()", ref[ent] == base)

data = ds.render(w1, ents)
check("reference over all rows sums to total", sum(ds.reference(data, {}).values()) ==
      sum(ds.total(w1, e, set()) for e in ents))
print("FAILURES", failures if failures else "none")
raise SystemExit(1 if failures else 0)
