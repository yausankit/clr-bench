#!/usr/bin/env python3
"""Append verified five-member/five-nonmember spot checks for the new lists."""
import csv
import sys
from pathlib import Path

import yaml

from add_sources import LIST_SPECS, build_item, line_contains_entry, raw_path, universe

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "SPOTCHECK.tsv"
FIELDS = ["list_id", "universe", "role", "value", "evidence_file", "evidence_line", "evidence", "check"]


def main():
    rows, failures = [], 0
    for spec in LIST_SPECS:
        item, entries, evidence = build_item(spec)
        values = universe(spec["universe"])
        rel = "raw/add_lists/" + spec["raw"]
        source_lines = raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines()
        members = item["members"][:5]
        if len(members) < 5:
            print(f"FAIL {item['id']}: only {len(members)} members", file=sys.stderr)
            failures += 1
            continue
        ordered = sorted(values - set(item["members"]) - set(item["disputed"]))
        nonmembers = ordered[:5]
        for role, picked in (("member", members), ("nonmember", nonmembers)):
            for value in picked:
                ok = value in values
                if role == "member":
                    entry = evidence[value]
                    line = int(entry["line"])
                    in_member_list = value in item["members"]
                    line_ok = 1 <= line <= len(source_lines) and line_contains_entry(source_lines[line - 1], entry["name"])
                    ok = ok and in_member_list and line_ok
                    text = (f"source entry {entry['name']!r} at {rel}:{line}; "
                            f"member of {item['id']} parsed from {spec['title']}")
                else:
                    ok = ok and value not in item["members"] and value not in item["disputed"]
                    line = 1
                    text = (f"absent from {item['id']}; source list scanned at {rel}:1-{len(source_lines)} "
                            f"({item['official_count']} entries)")
                if not ok:
                    failures += 1
                rows.append({"list_id": item["id"], "universe": spec["universe"], "role": role,
                             "value": value, "evidence_file": rel, "evidence_line": line,
                             "evidence": text.replace("\t", " "), "check": "PASS" if ok else "FAIL"})

    with OUT.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)
    print(f"SPOTCHECK.tsv: appended {len(rows)} rows, {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
