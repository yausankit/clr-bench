#!/usr/bin/env python3
"""Verify the WS3 list supplement, source counts, overlap, and SPOTCHECK evidence."""
import csv
import yaml
from pathlib import Path

import build_ws3_lists as B

ROOT = Path(__file__).resolve().parent


def main():
    baseline = yaml.safe_load((ROOT / "raw" / "base_ws3_language.yaml").read_text(encoding="utf-8"))
    current = yaml.safe_load((ROOT / "lists" / "language.yaml").read_text(encoding="utf-8"))
    assert current[:len(baseline)] == baseline, "original language lists changed"

    entries = B.build_entries()
    source_file = {spec["id"]: spec["page"] + ".wikitext" for spec in B.SPECS}
    for entry in entries:
        entry["_source_file"] = source_file[entry["id"]]
    new = {entry["id"]: entry for entry in entries}
    assert len(new) == 20, len(new)
    assert sum(len(entry["members"]) >= 10 for entry in entries) >= 10

    universe = set()
    with (ROOT / "universes" / "language.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            universe.add(row["value"])

    all_lists = baseline + [{key: value for key, value in entry.items() if not key.startswith("_")}
                            for entry in entries]
    by_id = {item["id"]: set(item["members"]) for item in all_lists}
    assert len(by_id) == len(all_lists), "duplicate list id"
    for entry in entries:
        members = set(entry["members"])
        assert len(members) >= 5
        assert 2 * len(members) <= len(universe)
        assert entry["official_count"] == len(members) + len(entry["out_of_universe"])
        competitors = [other for other, values in by_id.items()
                       if other != entry["id"] and values != members and values & members]
        assert len(competitors) >= 2, (entry["id"], competitors)
        assert entry["_source_title"] and entry["_source_range"]

    rows = list(csv.DictReader((ROOT / "SPOTCHECK.tsv").open(encoding="utf-8"), delimiter="\t"))
    new_rows = [row for row in rows if row["list_id"] in new]
    assert len(new_rows) == 200, len(new_rows)
    for lid, entry in new.items():
        part = [row for row in new_rows if row["list_id"] == lid]
        members = [row for row in part if row["role"] == "member"]
        nonmembers = [row for row in part if row["role"] == "nonmember"]
        assert len(members) == 5 and len(nonmembers) == 5, lid
        expected = set(entry["members"])
        assert {row["value"] for row in members} <= expected
        assert all(row["value"] not in expected for row in nonmembers)
        assert all(row["universe"] == "language" and "raw/wiki_ws3/" in row["evidence"] for row in part)
        assert all("absent from parsed table" in row["evidence"] for row in nonmembers)

    large = sum(len(entry["members"]) >= 10 for entry in entries)
    print(f"verify OK: 20 new lists, {large} large, 200 SPOTCHECK rows, counts and overlap reconcile")


if __name__ == "__main__":
    main()
