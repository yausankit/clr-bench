#!/usr/bin/env python3
"""Append the country-group ccTLD lists to lists/tld.yaml from raw/curated/lists_tld_groups.json.

Every member is checked against the saved official membership page in raw/official/ (the exact
country name printed on the page must occur in it), mapped to its ccTLD with the IANA root zone in
raw/iana/tlds-alpha-by-domain.txt, and counted against official_count. Existing entries of
lists/tld.yaml are read and written back unchanged; only the group lists are replaced/appended, so
running the script twice is idempotent.
"""
import json, re, html
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def visible_text(path):
    t = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t).lower()


def universe(name):
    lines = (ROOT / "universes" / f"{name}.tsv").read_text(encoding="utf-8").splitlines()
    return [l.split("\t")[0] for l in lines[1:] if l.strip()]


def main():
    groups = json.loads((ROOT / "raw" / "curated" / "lists_tld_groups.json").read_text())["lists"]
    values = universe("tld")
    root = {l.strip().lower() for l in (ROOT / "raw" / "iana" / "tlds-alpha-by-domain.txt")
            .read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
    path = ROOT / "lists" / "tld.yaml"
    existing = yaml.safe_load(path.read_text(encoding="utf-8"))
    ids = {g["id"] for g in groups}
    base = [it for it in existing if it["id"] not in ids]
    new = []
    for g in groups:
        text = visible_text(g["official_file"])
        inside, outside = [], []
        for m in g["members"]:
            iso = m["iso"].lower()
            if m["name"].lower() not in text:
                raise SystemExit(f"{g['id']}: {m['name']!r} not found in {g['official_file']}")
            (inside if iso in values and iso in root else outside).append(iso)
        disputed = [d.lower() for d in g.get("disputed") or []]
        if len(inside) + len(disputed) + len(outside) != g["official_count"]:
            raise SystemExit(f"{g['id']}: {len(inside)}+{len(disputed)}+{len(outside)} != {g['official_count']}")
        new.append({"id": g["id"], "name": g["name"], "synonyms": g.get("synonyms") or [],
                    "members": inside, "disputed": disputed, "changes": g.get("changes") or [],
                    "out_of_universe": outside, "official_count": g["official_count"],
                    "source": g["source"], "salience": 0})
    out = base + new
    path.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")

    sets = {it["id"]: set(it["members"]) for it in out}
    print(f"lists/tld.yaml: {len(out)} lists ({len(new)} group lists), "
          f"{sum(len(it['members']) for it in new)} new members")
    for g in new:
        best = sorted(((len([l for l, s in sets.items() if l != g["id"] and v in s]), v)
                       for v in g["members"]), reverse=True)[0]
        print(f"  {g['id']}: {len(g['members'])} members, official_count "
              f"{g['official_count']}, overlap {best[0]} lists at {best[1]}")


if __name__ == "__main__":
    main()
