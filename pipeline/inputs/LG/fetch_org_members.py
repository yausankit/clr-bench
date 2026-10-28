#!/usr/bin/env python3
"""Fetch current member states of intergovernmental organisations from Wikidata (P463),
dropping memberships that ended on or before the snapshot date. Raw JSON per organisation
is stored in raw/wikidata/<key>.json and is the evidence used by the list builder."""
import json, os, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "raw" / "wikidata"
OUT.mkdir(parents=True, exist_ok=True)
SNAPSHOT = "2026-10-16"
ORGS = {
    "eu": ("European Union", "Q458"),
    "schengen": ("Schengen Area", "Q392755"),
    "eurozone": ("Eurozone", "Q8268"),
    "nato": ("NATO", "Q7184"),
    "commonwealth": ("Commonwealth of Nations", "Q7785"),
    "asean": ("ASEAN", "Q7768"),
    "g20": ("G20", "Q180392"),
    "brics": ("BRICS", "Q240313"),
    "oecd": ("OECD", "Q41550"),
    "african_union": ("African Union", "Q7813"),
    "arab_league": ("Arab League", "Q7172"),
    "nordic_council": ("Nordic Council", "Q6204"),
    "gcc": ("Gulf Cooperation Council", "Q179807"),
    "caricom": ("CARICOM", "Q207284"),
    "pacific_islands_forum": ("Pacific Islands Forum", "Q1135888"),
    "g7": ("G7", "Q102688"),
    "five_eyes": ("Five Eyes", "Q1055193"),
    "cplp": ("Community of Portuguese Language Countries", "Q1055634"),
    "oif": ("Organisation internationale de la Francophonie", "Q134102"),
    "opec": ("OPEC", "Q7795"),
    "cis": ("Commonwealth of Independent States", "Q598007"),
    "saarc": ("South Asian Association for Regional Cooperation", "Q1046701"),
    "apec": ("Asia-Pacific Economic Cooperation", "Q170481"),
}
Q = """SELECT ?item ?itemLabel ?iso ?end WHERE {
  ?item p:P463 ?st. ?st ps:P463 wd:%s.
  OPTIONAL { ?st pq:P582 ?end }
  OPTIONAL { ?item wdt:P297 ?iso }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "clrsynth-dataset-builder/1.0"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as x:
            wait = min(600, 30 * 2 ** attempt)
            print(f"retry {wait}s: {x}", flush=True)
            time.sleep(wait)
    raise SystemExit("fetch failed")


def main():
    for key, (name, qid) in ORGS.items():
        path = OUT / f"{key}.json"
        if path.exists():
            print(f"skip {key}")
            continue
        url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
            {"query": Q % qid, "format": "json"})
        d = fetch(url)
        rows = []
        for b in d["results"]["bindings"]:
            end = b.get("end", {}).get("value", "")
            if end and end[:10] <= SNAPSHOT:
                continue
            rows.append({"item": b["item"]["value"].rsplit("/", 1)[-1],
                         "label": b.get("itemLabel", {}).get("value", ""),
                         "iso": b.get("iso", {}).get("value", ""),
                         "end": end})
        rows.sort(key=lambda r: (r["iso"], r["label"]))
        path.write_text(json.dumps({"org": name, "qid": qid, "query": Q % qid,
                                    "snapshot": SNAPSHOT, "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        print(f"{key}: {len(rows)} live members, {sum(1 for r in rows if r['iso'])} with ISO", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
