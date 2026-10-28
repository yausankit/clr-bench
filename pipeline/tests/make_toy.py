"""Write a toy dataset (inputs/TOY) used by the tests: 40 entities, JSON answers,
fields records.item (150 values, 2 slots), records.tag (120 values, 2 slots), records.color (40 values, 1 slot)."""
import sys
from pathlib import Path

import yaml

DATASET_PY = '''
import hashlib, random
ANSWER_FORMAT = "json"
TRAP_FIELDS = ["records.item", "records.tag", "records.color"]
TASK = "Every record adds its qty to the total of the entity it belongs to."
ENTITY_NOUN = "entity"
def _rng(seed, step):
    return random.Random(int(hashlib.sha256(f"{seed}/{step}/toy".encode()).hexdigest(), 16))
def base_world(seed, step):
    r = _rng(seed, step)
    recs = {}
    n = 0
    for e in range(40):
        for _ in range(4):
            n += 1
            recs[f"R{n:04d}"] = {"id": f"R{n:04d}", "entity": f"E{e:02d}", "item": "I000", "tag": "T000",
                                 "color": "C00", "qty": r.randint(1, 3)}
    return {"records": recs}
def entities(world):
    return sorted({r["entity"] for r in world["records"].values()})
def slots(world, field):
    return sorted((r["entity"], rid) for rid, r in world["records"].items())
def set_value(world, field, pos, value):
    world["records"][pos][field.split(".")[1]] = value
def total(world, entity, excluded):
    skip = {p for _, p in excluded}
    return sum(r["qty"] for rid, r in world["records"].items() if r["entity"] == entity and rid not in skip)
def render(world, entity_ids):
    keep = set(entity_ids)
    return {"entities": [{"id": e} for e in sorted(keep)],
            "records": [dict(r) for rid, r in sorted(world["records"].items()) if r["entity"] in keep]}
def reference(data, excluded):
    out = {e["id"]: 0 for e in data["entities"]}
    for r in data["records"]:
        if any(r[f.split(".")[1]] in vals for f, vals in excluded.items()):
            continue
        out[r["entity"]] += r["qty"]
    return out
'''


def universe(prefix, n, width, attr_mod):
    rows = ["value\tentity\tattr:zone"]
    for i in range(n):
        rows.append(f"{prefix}{i:0{width}d}\t{prefix} number {i}\tz{i % attr_mod}")
    return "\n".join(rows) + "\n"


def lists_for(prefix, n, width, rules):
    out = []
    for lid, pred in rules:
        members = [f"{prefix}{i:0{width}d}" for i in range(n) if pred(i)]
        out.append({"id": lid, "name": lid.replace("_", " "), "synonyms": [], "members": members,
                    "disputed": [], "changes": [], "out_of_universe": [], "official_count": len(members),
                    "source": "toy", "salience": 1000 - len(out)})
    return out


def write(root):
    root = Path(root) / "TOY"
    for d in ("universes", "lists", "chains"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "dataset.py").write_text(DATASET_PY)
    specs = {"item": ("I", 150, 3), "tag": ("T", 120, 3), "color": ("C", 40, 2)}
    rules = {
        "item": [("item_fives", lambda i: i % 5 == 0), ("item_sevens", lambda i: i % 7 == 0),
                 ("item_low", lambda i: i < 40), ("item_evens_low", lambda i: i % 2 == 0 and i < 70),
                 ("item_tens", lambda i: i % 10 in (0, 3)), ("item_mid", lambda i: 30 <= i < 80),
                 ("item_elevens", lambda i: i % 11 == 0), ("item_thirteens", lambda i: i % 13 in (0, 2)),
                 ("item_band", lambda i: 50 <= i < 120), ("item_threes", lambda i: i % 3 == 0 and i < 100),
                 ("item_sq", lambda i: i in {0, 1, 4, 9, 16, 25, 35, 36, 49, 64, 70, 81, 100, 105, 121, 140, 144})],
        "tag": [("tag_fours", lambda i: i % 4 == 0), ("tag_sixes", lambda i: i % 6 == 0),
                ("tag_low", lambda i: i < 36), ("tag_nines", lambda i: i % 9 == 0),
                ("tag_band", lambda i: 20 <= i < 60), ("tag_fives", lambda i: i % 5 == 1),
                ("tag_sevens", lambda i: i % 7 == 0), ("tag_high", lambda i: i >= 80),
                ("tag_tens", lambda i: i % 10 in (0, 6)), ("tag_mixed", lambda i: i % 12 in (0, 3, 8))],
        "color": [("color_evens", lambda i: i % 2 == 0), ("color_threes", lambda i: i % 3 == 0),
                  ("color_low", lambda i: i < 15), ("color_band", lambda i: 10 <= i < 30),
                  ("color_fives", lambda i: i % 5 == 0), ("color_odd_low", lambda i: i % 2 == 1 and i < 25)],
    }
    for name, (prefix, n, width) in specs.items():
        (root / "universes" / f"{name}.tsv").write_text(universe(prefix, n, width, 4))
        (root / "lists" / f"{name}.yaml").write_text(yaml.safe_dump(lists_for(prefix, n, width, rules[name]),
                                                                    sort_keys=False))
    (root / "universes" / "color.desc.tsv").write_text(
        "value\tdescription\n" + "".join(f"C{i:02d}\ttoy shade number {i}\n" for i in range(40)))
    templates, fields_cfg = [], []
    for name in specs:
        ids = [l for l, _ in rules[name]]
        tids = []
        for i in range(len(ids) // 2):
            tid = f"{name}_rule_{i}"
            tids.append(tid)
            templates.append({"id": tid, "field": f"records.{name}", "effect": "exclude_record",
                              "source": "toy", "plausible": [ids[2 * i], ids[2 * i + 1], ids[(2 * i + 2) % len(ids)]]})
        fields_cfg.append({"field": f"records.{name}", "universe": name, "templates": tids})
    scen = {"id": "TOY", "business_process": "A toy ledger sums record quantities per entity.",
            "fields": {f"records.{n}": {"universe": n, "value_form": "code" if n == "color" else "self_describing"}
                       for n in specs},
            "rule_templates": templates}
    (root / "scenario.yaml").write_text(yaml.safe_dump(scen, sort_keys=False))
    chain = {"id": "TOY1", "dataset": "TOY", "seed": 7, "period": {"start": 2025, "end": 2026},
             "snapshot": "2026-10-16", "fields": fields_cfg, "slots": 5, "probe": {"criterion": "soft"}}
    (root / "chains" / "TOY1.yaml").write_text(yaml.safe_dump(chain, sort_keys=False))
    return root


if __name__ == "__main__":
    print(write(sys.argv[1]))
