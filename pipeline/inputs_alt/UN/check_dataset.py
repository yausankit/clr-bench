#!/usr/bin/env python3
"""Required deterministic, identifier, and interface checks for UN."""
import importlib.util
import json
import random
import re
from pathlib import Path

P = Path(__file__).with_name("dataset.py")
spec = importlib.util.spec_from_file_location("un_dataset_check", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

chain_paths = sorted((P.parent / "chains").glob("*.yaml"))
assert chain_paths, "no chain configs"
seeds = []
for path in chain_paths:
    match = re.search(r"^seed:\s*(\d+)\s*$", path.read_text(encoding="utf-8"), re.M)
    assert match, f"{path.name}: missing integer seed"
    seeds.append((path.stem, int(match.group(1))))
assert len({seed for _, seed in seeds}) == len(seeds), "chain seeds are not unique"

for chain_name, seed in seeds:
    step = f"check_dataset/{chain_name}"
    a = m.base_world(seed, step)
    b = m.base_world(seed, step)
    assert json.dumps(a, sort_keys=True, separators=(",", ":")) == json.dumps(
        b, sort_keys=True, separators=(",", ":")
    ), f"{chain_name}: not deterministic"
    ents = m.entities(a)
    assert len(ents) >= 30, (chain_name, len(ents))

    for table, key in (("applications", "application_id"),
                       ("applicants", "applicant_id"),
                       ("references", "reference_id")):
        ids = [row[key] for row in a[table]]
        assert len(ids) == len(set(ids)), f"{chain_name}: duplicate {table}.{key}"

    for field_index, field in enumerate(m.TRAP_FIELDS):
        positions = m.slots(a, field)
        counts = {entity: 0 for entity in ents}
        for entity, _ in positions:
            counts[entity] += 1
        assert min(counts.values()) >= 3, (chain_name, field, min(counts.values()))

        # Assign a fresh marker to several deterministic random positions. With a
        # unique marker, tuple exclusions and rendered value exclusions describe
        # the same set of records.
        rng = random.Random(seed + field_index)
        chosen = rng.sample(positions, min(5, len(positions)))
        fresh = m.base_world(seed, step)
        marker = f"__check_{chain_name}_{field_index}__"
        excluded_positions = set()
        for entity, pos in chosen:
            m.set_value(fresh, field, pos, marker)
            excluded_positions.add((field, pos))
        rendered = m.reference(m.render(fresh, ents), {field: {marker}})
        for entity in ents:
            got = m.total(fresh, entity, excluded_positions)
            assert got == rendered[entity], (
                chain_name, field, entity, got, rendered[entity]
            )

print("check_dataset OK: " + ", ".join(
    f"{name} seed={seed}" for name, seed in seeds
))
