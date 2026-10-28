#!/usr/bin/env python3
"""Recompute salience/<U>.tsv from salience/titles.tsv and the raw Wikimedia pageview JSON files."""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAL = ROOT / "salience"
RAW = SAL / "raw"


def main():
    by_universe = {}
    rows = list(csv.DictReader(open(SAL / "titles.tsv", encoding="utf-8"), delimiter="\t"))
    for r in rows:
        title = r["wiki_title"].strip()
        views, match, note = 0, "none", r["note"]
        path = RAW / ("pv_" + title.replace("/", "_") + ".json")
        if title and path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data.get("items") or []
            views = sum(int(x["views"]) for x in items)
            months = len(items)
            if months == 12:
                match = "exact"
            else:
                match = "partial"
                note = f"{months} monthly points"
        elif title:
            match, note = "missing", "pageview request unavailable"
        lid = r["concept_id"]
        uname = lid.split("_")[0]
        if lid.startswith("cwe") or lid.startswith("owasp") or lid.startswith("sfp") or lid.startswith("cisq") \
                or lid in ("bad_coding_practices", "audit", "authenticate_actors", "authorize_actors",
                           "cross_cutting", "encrypt_data", "identify_actors", "limit_access",
                           "limit_exposure", "manage_user_sessions", "validate_inputs",
                           "verify_message_integrity"):
            uname = "cwe"
        elif lid.endswith("_languages") or lid.endswith("_official") or lid == "india_eighth_schedule":
            uname = "language"
        else:
            uname = "tld"
        by_universe.setdefault(uname, []).append((lid, title, match, views, note))
    for uname, items in sorted(by_universe.items()):
        out = SAL / f"{uname}.tsv"
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(["concept_id", "wiki_title", "match", "pageviews_12m", "note"])
            for lid, title, match, views, note in sorted(items):
                w.writerow([lid, title, match, views, note])
        print(uname, len(items), "lists", sum(1 for x in items if x[2] == "exact"), "exact matches")


if __name__ == "__main__":
    main()
