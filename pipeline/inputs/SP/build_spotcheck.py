#!/usr/bin/env python3
"""Create SPOTCHECK.tsv with programmatically verified raw-source evidence."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import yaml

from build_inputs import (build_club_universe, build_company_universe, load_metadata, load_pageprops,
                          load_countries, country_code, norm_name, record_key)
from parse_sources import members_for
from source_specs import CLUB_LISTS, COMPANY_LISTS, COUNTRY_LISTS

ROOT = Path(__file__).resolve().parent
OUT = ROOT


def choose(values, n, salt):
    ordered = sorted(values, key=lambda value: hashlib.sha256(f"{salt}/{value}".encode()).hexdigest())
    return ordered[:n]


def canonical_value_map(items, canonical, pageprops):
    out = {}
    for item in items:
        item_out = defaultdict(list)
        page, records = members_for(item)
        page_key = item["spec"]["page"]
        for record in records:
            key = record_key(record, pageprops)
            value = canonical.get(key)
            if value:
                item_out[value].append((page_key, record))
        out[item["id"]] = item_out
    return out


def main():
    pageprops = load_pageprops()
    metadata = load_metadata()
    club_canonical, _, _ = build_club_universe(pageprops, metadata)
    company_canonical, _, _ = build_company_universe(pageprops, metadata)
    _, by_code, by_name = load_countries()
    org_qids = json.loads((ROOT / "raw" / "metadata" / "org_qids.json").read_text(encoding="utf-8"))
    org_rows = json.loads((ROOT / "raw" / "countries" / "org_memberships.json").read_text(encoding="utf-8"))
    rows_by_org = defaultdict(list)
    for binding_index, row in enumerate(org_rows["results"]["bindings"], 1):
        org = row["org"]["value"].rsplit("/", 1)[-1]
        rows_by_org[org].append((binding_index, row))
    club_lookup = canonical_value_map(CLUB_LISTS, club_canonical, pageprops)
    company_lookup = canonical_value_map(COMPANY_LISTS, company_canonical, pageprops)
    list_sets = {
        "club": {x["id"]: x for x in yaml.safe_load((OUT / "lists" / "club.yaml").read_text())},
        "co_sponsor": {x["id"]: x for x in yaml.safe_load((OUT / "lists" / "co_sponsor.yaml").read_text())},
        "market_country": {x["id"]: x for x in yaml.safe_load((OUT / "lists" / "market_country.yaml").read_text())},
    }
    values = {}
    for universe in list_sets:
        with (OUT / "universes" / f"{universe}.tsv").open(encoding="utf-8") as fh:
            values[universe] = [row["value"] for row in csv.DictReader(fh, delimiter="\t")]
    records = []
    for universe, specs in (("club", CLUB_LISTS), ("co_sponsor", COMPANY_LISTS),
                            ("market_country", COUNTRY_LISTS)):
        for spec in specs:
            item = list_sets[universe][spec["id"]]
            member_set = set(item["members"])
            for role in ("member", "nonmember"):
                pool = member_set if role == "member" else set(values[universe]) - member_set
                for value in choose(pool, 5, f"{universe}/{spec['id']}/{role}"):
                    if universe != "market_country":
                        lookup = club_lookup if universe == "club" else company_lookup
                        list_lookup = lookup.get(spec["id"], {})
                        found = list_lookup.get(value)
                        if role == "member" and found:
                            page_key, record = found[0]
                            evidence = (f"raw/pages/{page_key}.json: {record['evidence']}; "
                                        f"title={record['title']!r}; display={record['display']!r}")
                            verified = "PASS"
                        else:
                            page_key = spec["spec"]["page"]
                            row_count = len(members_for(spec)[1])
                            evidence = (f"raw/pages/{page_key}.json: scanned all {row_count} parsed rows at "
                                        f"{spec['spec']}; canonical member set contains no {value!r}")
                            verified = "PASS" if role == "nonmember" and not found else "FAIL"
                    else:
                        org = org_qids[spec["id"]]
                        hits = []
                        for binding_index, row in rows_by_org.get(org, []):
                            code = country_code(row.get("itemLabel", {}).get("value", ""),
                                                row.get("iso", {}).get("value"), by_name)
                            if code == value:
                                hits.append((binding_index, row))
                        if role == "member":
                            if hits:
                                binding_index, row = hits[0]
                                evidence = (f"raw/countries/org_memberships.json: binding row {binding_index}; "
                                            f"org={org}; item={row['itemLabel']['value']!r}; iso={row.get('iso', {}).get('value')}")
                                verified = "PASS"
                            else:
                                evidence = f"raw/countries/org_memberships.json: no active row for {value!r} and {org}"
                                verified = "FAIL"
                        else:
                            row_count = len(rows_by_org.get(org, []))
                            evidence = (f"raw/countries/org_memberships.json: scanned {row_count} active P463 "
                                        f"binding rows for {org}; none maps to country code {value!r}")
                            verified = "PASS" if not hits else "FAIL"
                    records.append({"list_id": spec["id"], "role": role, "value": value,
                                    "evidence": evidence, "verified": verified})
    with (OUT / "SPOTCHECK.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["list_id", "role", "value", "evidence", "verified"],
                                delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    failed = [row for row in records if row["verified"] != "PASS"]
    print(f"SPOTCHECK rows: {len(records)}, failed: {len(failed)}")
    if failed:
        raise SystemExit(f"spotcheck failures: {failed[:5]}")


if __name__ == "__main__":
    main()
