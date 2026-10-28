#!/usr/bin/env python3
"""Append the raw/add_lists source lists to lists/user.yaml and lists/client_app.yaml.

build_lists.py first recreates the pre-existing files from raw/curated/.  This script reads the
new source files under raw/add_lists/, parses their own tables/files, and appends new records
without rewriting the existing records.
"""
from pathlib import Path

import yaml

from add_sources import LIST_SPECS, build_item

ROOT = Path(__file__).resolve().parent


def main():
    built = {}
    for spec in LIST_SPECS:
        item, entries, evidence = build_item(spec)
        built.setdefault(spec["universe"], []).append(item)
        print(f"{item['id']}: official={item['official_count']} inside={len(item['members'])} "
              f"disputed={len(item['disputed'])} outside={len(item['out_of_universe'])}")

    for universe, items in built.items():
        path = ROOT / "lists" / f"{universe}.yaml"
        text = path.read_text(encoding="utf-8")
        old = yaml.safe_load(text) or []
        old_ids = {str(item["id"]) for item in old}
        duplicate = old_ids & {item["id"] for item in items}
        if duplicate:
            raise SystemExit(f"{path}: new ids already present: {sorted(duplicate)}")
        if not text.endswith("\n"):
            text += "\n"
        text += yaml.safe_dump(items, allow_unicode=True, sort_keys=False)
        path.write_text(text, encoding="utf-8")
        print(f"lists/{universe}.yaml: {len(old)} -> {len(old) + len(items)} lists")


if __name__ == "__main__":
    main()
