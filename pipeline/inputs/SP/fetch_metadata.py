#!/usr/bin/env python3
"""Fetch page QIDs and compact Wikidata metadata for all SP source members."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import requests

from parse_sources import members_for
from source_specs import CLUB_LISTS, CLUB_UNIVERSE_EXTRAS, COMPANY_LISTS, COUNTRY_LISTS

ROOT = Path(__file__).resolve().parent
META = ROOT / "raw" / "metadata"
META.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "CLRSynth-SP/2.0 (dataset snapshot; public-data build)"}


def chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def get_json(url, params=None, post=None, timeout=120):
    wait = 60
    while True:
        try:
            if post is None:
                req = urllib.request.Request(url + ("?" + urllib.parse.urlencode(params) if params else ""),
                                             headers=UA)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            resp = requests.post(url, data=post, headers=UA, timeout=timeout)
            if resp.status_code == 429 or resp.status_code >= 500:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            print(f"retry {url}: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(wait)
            wait = min(wait * 2, 600)


def pageprops(titles):
    title_list = sorted(set(titles))
    merged = {}
    for path in sorted(META.glob("pageprops_*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        for page in obj.get("query", {}).get("pages", []):
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            if qid:
                merged[page["title"]] = qid
        for link in (obj.get("query", {}).get("normalized", []) + obj.get("query", {}).get("redirects", [])):
            if link["to"] in merged:
                merged[link["from"]] = merged[link["to"]]
    missing = [title for title in title_list if title not in merged]
    for batch in chunks(missing, 45):
        import hashlib
        tag = hashlib.sha256("\n".join(batch).encode()).hexdigest()[:10]
        path = META / f"pageprops_{tag}.json"
        if path.exists():
            obj = json.loads(path.read_text(encoding="utf-8"))
        else:
            obj = get_json("https://en.wikipedia.org/w/api.php", {
                "action": "query", "prop": "pageprops", "ppprop": "wikibase_item",
                "titles": "|".join(batch), "format": "json", "formatversion": "2", "redirects": "1",
            })
            path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            time.sleep(2.1)
        for page in obj.get("query", {}).get("pages", []):
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            if qid:
                merged[page["title"]] = qid
        for norm in obj.get("query", {}).get("normalized", []):
            if norm["to"] in merged:
                merged[norm["from"]] = merged[norm["to"]]
        for redir in obj.get("query", {}).get("redirects", []):
            if redir["to"] in merged:
                merged[redir["from"]] = merged[redir["to"]]
        print(f"pageprops batch {tag}: {len(merged)} titles mapped", flush=True)
    return merged


def entity_info(qids):
    qids = sorted(set(qids))
    have = set()
    for path in sorted(META.glob("entity_info_*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        have |= {b["item"]["value"].rsplit("/", 1)[-1] for b in obj["results"]["bindings"]}
    missing = [qid for qid in qids if qid not in have]
    for batch in chunks(missing, 60):
        import hashlib
        tag = hashlib.sha256("\n".join(batch).encode()).hexdigest()[:10]
        path = META / f"entity_info_{tag}.json"
        if path.exists():
            continue
        values = " ".join(f"wd:{q}" for q in batch)
        query = f"""SELECT ?item ?label ?desc ?country ?countryLabel WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item rdfs:label ?label. FILTER(LANG(?label) = "en") }}
  OPTIONAL {{ ?item schema:description ?desc. FILTER(LANG(?desc) = "en") }}
  OPTIONAL {{ ?item wdt:P17 ?country. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}"""
        obj = get_json("https://query.wikidata.org/sparql", post={"query": query, "format": "json"})
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"entity info batch {tag}: {len(batch)} QIDs", flush=True)
        time.sleep(2.1)


def country_orgs(org_qids):
    values = " ".join(f"wd:{q}" for q in sorted(set(org_qids.values())))
    query = f"""SELECT ?org ?orgLabel ?item ?itemLabel ?iso WHERE {{
  VALUES ?org {{ {values} }}
  ?item p:P463 ?statement. ?statement ps:P463 ?org.
  FILTER NOT EXISTS {{ ?statement pq:P582 ?end. }}
  OPTIONAL {{ ?item wdt:P297 ?iso. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} ORDER BY ?org ?itemLabel"""
    (ROOT / "raw" / "countries" / "org_memberships.sparql").write_text(query + "\n", encoding="utf-8")
    obj = get_json("https://query.wikidata.org/sparql", post={"query": query, "format": "json"})
    out = ROOT / "raw" / "countries" / "org_memberships.json"
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"country memberships: {len(obj['results']['bindings'])} rows", flush=True)


def main():
    rows = {}
    for item in CLUB_LISTS + CLUB_UNIVERSE_EXTRAS + COMPANY_LISTS:
        page, members = members_for(item)
        rows[item["id"]] = members
        print(f"parsed {item['id']}: {len(members)} members ({page['title']})", flush=True)
    titles = [m["title"] for members in rows.values() for m in members]
    from parse_sources import load_page
    titles = [load_page(item["page"])["title"] for item in COUNTRY_LISTS] + titles
    qid_by_title = pageprops(titles)
    all_qids = set(qid_by_title.values())
    org_qids = {item["id"]: item["wikidata"] for item in COUNTRY_LISTS}
    (META / "org_qids.json").write_text(json.dumps(org_qids, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    entity_info(all_qids)
    country_orgs(org_qids)
    print("metadata fetch complete", flush=True)


if __name__ == "__main__":
    main()
