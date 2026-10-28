#!/usr/bin/env python3
"""Self-check for the SP dataset interface required by guide section 5."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sp_dataset", ROOT / "dataset.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main():
    seed = 20266106
    w1 = mod.base_world(seed, "check")
    w2 = mod.base_world(seed, "check")
    assert json.dumps(w1, sort_keys=True, default=str) == json.dumps(w2, sort_keys=True, default=str)
    ents = mod.entities(w1)
    assert len(ents) >= 30
    for field in mod.TRAP_FIELDS:
        pos = mod.slots(w1, field)
        per = {entity: 0 for entity in ents}
        for entity, _ in pos:
            per[entity] += 1
        assert min(per.values()) >= 3, (field, min(per.values()))
        entity, position = pos[0]
        before = mod.total(w1, entity, set())
        assert isinstance(before, int)
        mod.set_value(w1, field, position, "CHECK-MARKER")
        data = mod.render(w1, ents)
        assert mod.values(data, field).count("CHECK-MARKER") == 1
        after = mod.total(w1, entity, {(field, position)})
        assert isinstance(after, int) and after < before
        assert sum(mod.reference(data, {}).values()) == sum(mod.total(w1, e, set()) for e in ents)
        assert sum(mod.reference(data, {field: {"CHECK-MARKER"}}).values()) == sum(
            mod.total(w1, e, {(field, position)}) for e in ents)
    sample = mod.render(w1, ents[:7])
    size = len(json.dumps(sample, ensure_ascii=False, indent=1))
    assert size <= 50000
    print(f"check_dataset OK: {len(ents)} entities, "
          f"{len(w1['activations'])} activations, 7-entity render {size} chars")


if __name__ == "__main__":
    main()
