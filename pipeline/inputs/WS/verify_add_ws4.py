#!/usr/bin/env python3
"""Programmatic checks for the WS4 CWE additions, using only raw/ and produced inputs."""
import csv
import io
import json
import re
import zipfile
from pathlib import Path

import yaml

import build_add_ws4 as build

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
NS = "{http://cwe.mitre.org/cwe-7}"


def main():
    root, xml_name = build.xml_source()
    weak = {w.get("ID"): w for w in root.find(NS + "Weaknesses").findall(NS + "Weakness")}
    cats = {c.get("ID"): c for c in root.find(NS + "Categories").findall(NS + "Category")}
    universe = {"CWE-" + wid for wid, w in weak.items()
                if w.get("Status") != "Deprecated" and w.get("Abstraction") != "Pillar"}
    assert len(universe) == 934

    base_text = (RAW / "base_add_ws4_cwe.yaml").read_text(encoding="utf-8")
    final_text = (ROOT / "lists" / "cwe.yaml").read_text(encoding="utf-8")
    assert final_text.startswith(base_text.rstrip("\n") + "\n")
    base = yaml.safe_load(base_text)
    final = yaml.safe_load(final_text)
    new = final[len(base):]
    assert len(new) == 18 == len(build.NEW_LISTS)
    assert len({entry["id"] for entry in final}) == len(final)
    assert all(entry["official_count"] == len(entry["members"]) + len(entry["disputed"]) +
               len(entry["out_of_universe"]) for entry in final)

    for entry, config in zip(new, build.NEW_LISTS):
        list_id, view, cid, official_name, title = config
        assert entry["id"] == list_id
        expected_ids = build.class_tree(root, cid) if view == "1000" else build.category_members(root, cid)
        expected_all = {mid for mid in expected_ids if mid in weak}
        expected_members = {"CWE-" + mid for mid in expected_all if "CWE-" + mid in universe}
        expected_out = {"CWE-" + mid for mid in expected_all if "CWE-" + mid not in universe}
        assert set(entry["members"]) == expected_members, list_id
        assert set(entry["out_of_universe"]) == expected_out, list_id
        assert entry["official_count"] == len(expected_all), list_id
        assert len(entry["members"]) >= 8, list_id
        assert entry["source"] == f"https://cwe.mitre.org/data/definitions/{cid}.html"
        source_name = weak[cid].get("Name") if view == "1000" else cats[cid].get("Name")
        assert entry["synonyms"][0] == source_name, (list_id, entry["synonyms"][0], source_name)
        items = json.loads((RAW / "ws4_pageviews" / f"pv_{title}.json").read_text())["items"]
        assert len(items) == 12
        assert items[0]["timestamp"] == "2025100100" and items[-1]["timestamp"] == "2026090100"
        assert entry["salience"] == sum(int(item["views"]) for item in items), list_id

    failures = []
    for entry in new:
        members = set(entry["members"])
        best = max((sum(1 for other in final if other["id"] != entry["id"] and value in other["members"])
                    for value in members), default=0)
        if best < 2:
            failures.append((entry["id"], best))
    assert not failures, failures

    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    lines = io.TextIOWrapper(z.open(xml_name), encoding="utf-8").read().splitlines()
    spot_path = ROOT / "SPOTCHECK.tsv"
    base_spot = (RAW / "base_add_ws4_SPOTCHECK.tsv").read_text(encoding="utf-8")
    spot_text = spot_path.read_text(encoding="utf-8")
    assert spot_text.startswith(base_spot)
    rows = list(csv.DictReader(io.StringIO(spot_text), delimiter="\t"))
    new_ids = {entry["id"] for entry in new}
    rows = [row for row in rows if row["list_id"] in new_ids]
    by_id = {entry["id"]: entry for entry in new}
    assert len(rows) == 180
    for list_id in new_ids:
        subset = [row for row in rows if row["list_id"] == list_id]
        assert sum(row["role"] == "member" for row in subset) == 5, list_id
        assert sum(row["role"] == "nonmember" for row in subset) == 5, list_id
        members = set(by_id[list_id]["members"])
        for row in subset:
            assert row["universe"] == "cwe"
            assert (row["value"] in members) == (row["role"] == "member"), (list_id, row)
            assert row["value"].startswith("CWE-") and row["value"] in universe
            match = re.search(r"cwec_v4\.20\.xml:(\d+)", row["evidence"])
            assert match and 1 <= int(match.group(1)) <= len(lines), row
            raw_line = lines[int(match.group(1)) - 1].strip()
            mid = row["value"].split("-")[1]
            if row["role"] == "member" and by_id[list_id]["id"].startswith("cwe1000_"):
                assert f'Weakness ID="{mid}"' in raw_line or "Related_Weakness" in raw_line, row
            elif row["role"] == "member":
                assert raw_line.startswith("<Has_Member"), row
            else:
                assert f'Weakness ID="{mid}"' in raw_line, row
                assert "no Has_Member path" in row["evidence"] or "no path to root" in row["evidence"]

    scenario = yaml.safe_load((ROOT / "scenario.yaml").read_text(encoding="utf-8"))
    template = next(t for t in scenario["rule_templates"] if t["id"] == "cwe_official_category")
    assert set(template["plausible"]) == new_ids
    for chain in sorted((ROOT / "chains").glob("WS*.yaml")):
        spec = yaml.safe_load(chain.read_text(encoding="utf-8"))
        cwe_field = next(field for field in spec["fields"] if field["field"] == "findings.cwe")
        assert "cwe_official_category" in cwe_field["templates"], chain
        assert cwe_field["templates"][:4] == ["cwe_category", "cwe_owasp", "cwe_cisq", "cwe_view"]

    print(f"verify: {len(new)} lists, {len(rows)} spotcheck rows, raw lines {len(lines)}; OK")


if __name__ == "__main__":
    main()
