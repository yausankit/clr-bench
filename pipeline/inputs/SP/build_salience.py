#!/usr/bin/env python3
"""Build the salience tables from saved Wikimedia pageview JSON snapshots."""
import csv
import json
from pathlib import Path

from parse_sources import load_page
from source_specs import CLUB_LISTS, COMPANY_LISTS, COUNTRY_LISTS

ROOT = Path(__file__).resolve().parent


def item_page_title(item):
    key = item["spec"]["page"] if "spec" in item else item["page"]
    return load_page(key)["title"]


def all_items():
    return [("club", item) for item in CLUB_LISTS] + \
        [("co_sponsor", item) for item in COMPANY_LISTS] + \
        [("market_country", item) for item in COUNTRY_LISTS]


def pageview_count(path):
    if not path.exists():
        return 0, "missing raw pageview snapshot"
    obj = json.loads(path.read_text(encoding="utf-8"))
    items = obj.get("items") or []
    return sum(int(row.get("views") or 0) for row in items), f"{len(items)} monthly buckets"


def build():
    rows_by_universe = {}
    for universe, item in all_items():
        title = item_page_title(item)
        raw = ROOT / "salience" / "raw" / universe / f"{item['id']}.json"
        count, note = pageview_count(raw)
        rows_by_universe.setdefault(universe, []).append({
            "concept_id": item["id"], "wiki_title": title, "match": "exact_title",
            "pageviews_12m": str(count), "note": note,
        })
    for universe, rows in rows_by_universe.items():
        out = ROOT / "salience" / f"{universe}.tsv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["concept_id", "wiki_title", "match", "pageviews_12m", "note"],
                               delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: r["concept_id"]))
    return {universe: {r["concept_id"]: int(r["pageviews_12m"]) for r in rows}
            for universe, rows in rows_by_universe.items()}


if __name__ == "__main__":
    result = build()
    print(json.dumps({u: len(v) for u, v in result.items()}, sort_keys=True))
