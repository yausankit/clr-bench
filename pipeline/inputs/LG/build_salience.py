#!/usr/bin/env python3
"""Salience for the LG lists: monthly English Wikipedia pageviews for the 12 months before the
snapshot (2025-10-01 .. 2026-09-30).

    python3 build_salience.py --fetch   # fetch raw JSON (needs the proxy tunnel), rate 0.5 s
    python3 build_salience.py           # rebuild salience/<universe>.tsv from the raw JSON
"""
import csv, hashlib, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

import yaml

from add_sources import LIST_SPECS

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
START, END = "2025100100", "2026093000"
API = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
       "all-access/all-agents/{title}/monthly/{start}/{end}")
FALLBACK = {"iana_system_ports": "List of TCP and UDP port numbers",
            "iana_user_ports": "List of TCP and UDP port numbers"}
TITLES = {}


def load_titles():
    for name, f in (("tld", "lists_tld.json"), ("tld", "lists_tld_extra.json"),
                    ("tld", "lists_tld_groups.json"),
                    ("port", "lists_port.json"), ("client_app", "lists_client_app.json"),
                    ("user", "lists_user.json")):
        path = ROOT / "raw" / "curated" / f
        data = json.loads(path.read_text())
        items = data.get("org_lists") or data.get("lists") or []
        for it in items:
            if it.get("wiki"):
                TITLES[it["id"]] = it["wiki"]
    TITLES.update(FALLBACK)
    TITLES.update({spec["id"]: spec["wiki"] for spec in LIST_SPECS})


def dataset_lists():
    out = {}
    for p in sorted((ROOT / "lists").glob("*.yaml")):
        out[p.stem] = [str(x["id"]) for x in yaml.safe_load(p.read_text())]
    return out


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    for universe, ids in dataset_lists().items():
        for lid in ids:
            path = RAW / f"{lid}.json"
            if path.exists():
                continue
            title = TITLES[lid]
            url = API.format(title=urllib.parse.quote(title.replace(" ", "_"), safe=""), start=START, end=END)
            req = urllib.request.Request(url, headers={"User-Agent": "clrsynth-dataset-builder/1.0"})
            data, status, attempt = None, 0, 0
            while data is None:
                try:
                    with urllib.request.urlopen(req, timeout=90) as r:
                        data, status = json.loads(r.read().decode()), r.status
                except urllib.error.HTTPError as x:
                    status = x.code
                    if x.code == 404:
                        data = {"items": []}
                        break
                    wait = min(600, 60 * 2 ** min(attempt, 4))
                    print(f"retry {lid}: HTTP {x.code}, sleep {wait}s", flush=True)
                    time.sleep(wait)
                except Exception as x:
                    wait = min(600, 60 * 2 ** min(attempt, 4))
                    print(f"retry {lid}: {x}, sleep {wait}s", flush=True)
                    time.sleep(wait)
                attempt += 1
            path.write_text(json.dumps({"concept_id": lid, "wiki_title": title, "status": status,
                                        "url": url, "items": data.get("items", [])},
                                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"{lid}: {title} -> {status} {len(data.get('items', []))} months", flush=True)
            time.sleep(0.5)


def rebuild():
    load_titles()
    for universe, ids in dataset_lists().items():
        rows = []
        for lid in ids:
            path = RAW / f"{lid}.json"
            if not path.exists():
                rows.append({"concept_id": lid, "wiki_title": TITLES.get(lid, ""), "match": "none",
                             "pageviews_12m": 0, "note": "no raw file"})
                continue
            d = json.loads(path.read_text())
            views = sum(int(i.get("views", 0)) for i in d.get("items", []))
            status = d.get("status")
            match = "exact" if d.get("items") else "none"
            note = "monthly pageviews 2025-10..2026-09" if d.get("items") else f"HTTP {status}: no article data"
            rows.append({"concept_id": lid, "wiki_title": d["wiki_title"], "match": match,
                         "pageviews_12m": views, "note": note})
        with (ROOT / "salience" / f"{universe}.tsv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["concept_id", "wiki_title", "match", "pageviews_12m", "note"],
                               delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"salience/{universe}.tsv: {len(rows)} rows, {sum(1 for r in rows if r['match']=='exact')} matched")


if __name__ == "__main__":
    load_titles()
    if "--fetch" in sys.argv:
        fetch()
    rebuild()
