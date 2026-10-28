#!/usr/bin/env python3
"""Local checks for the CH data interface required by the guide."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import dataset as d  # noqa: E402


def main() -> None:
    w1 = d.base_world(20266102, "check")
    w2 = d.base_world(20266102, "check")
    assert json.dumps(w1, sort_keys=True) == json.dumps(w2, sort_keys=True), "world is not deterministic"
    ents = d.entities(w1)
    assert len(ents) >= 30, len(ents)
    for field in d.TRAP_FIELDS:
        positions = d.slots(w1, field)
        counts = {e: 0 for e in ents}
        for entity, _ in positions:
            counts[entity] += 1
        assert min(counts.values()) >= 3, (field, min(counts.values()))
        value = d.values(d.render(w1, ents[:1]), field)[0]
        entity, pos = positions[0]
        d.set_value(w1, field, pos, value)
        assert value in d.values(d.render(w1, [entity]), field)
        before = d.total(w1, entity, set())
        after = d.total(w1, entity, {(field, pos)})
        assert isinstance(before, int) and isinstance(after, int)
        assert after < before, (field, before, after)
        rendered = d.render(w1, [entity])
        ref_clean = d.reference(rendered, {})
        assert ref_clean == {entity: before}, (field, ref_clean, before)
        target_value = d.values(rendered, field)[0]
        ref_excluded = d.reference(rendered, {field: {target_value}})
        assert ref_excluded[entity] < before, (field, ref_excluded[entity], before)
    sample = d.render(w1, ents[:7])
    assert len(json.dumps(sample)) <= 50000, len(json.dumps(sample))
    print(f"ok: {len(ents)} entities; positions="
          + ", ".join(f"{field}:{len(d.slots(w1, field))}" for field in d.TRAP_FIELDS)
          + f"; sample_chars={len(json.dumps(sample))}")


if __name__ == "__main__":
    main()
