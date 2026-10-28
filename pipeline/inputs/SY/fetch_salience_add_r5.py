#!/usr/bin/env python3
"""Fetch English-Wikipedia search hits and pageviews for the ADD_SY_a5 lists."""
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
API = "https://en.wikipedia.org/w/api.php"
PV = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
      "all-access/user/{title}/monthly/20251001/20260930")


def get(url, tries=8):
    delay = 30
    for _ in range(tries):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "clrsynth-add-lists/1.0 (dataset build)"})
            with urllib.request.urlopen(request, timeout=90) as handle:
                return handle.read()
        except urllib.error.HTTPError as error:
            if error.code == 429:
                print(f"429, wait {delay}s", file=sys.stderr)
                time.sleep(delay)
                delay = min(delay * 2, 600)
                continue
            if error.code >= 500:
                time.sleep(15)
                continue
            raise
        except Exception:
            time.sleep(8)
    raise SystemExit(f"gave up: {url}")


def main():
    with (ROOT / "add_lists_spec_r5.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    for row in rows:
        lid = row["id"]
        search_path = RAW / f"search_medicine_{lid}.json"
        if not search_path.exists() or search_path.stat().st_size < 10:
            url = API + "?" + urllib.parse.urlencode(
                {"action": "query", "list": "search", "srsearch": row["search"],
                 "srlimit": 3, "format": "json"})
            search_path.write_bytes(get(url))
        time.sleep(2.0)
        hits = (json.loads(search_path.read_text()).get("query") or {}).get("search") or []
        if not hits:
            print(lid, "no hit")
            continue
        title = hits[0]["title"]
        pageview_path = RAW / f"pageviews_medicine_{lid}.json"
        if not pageview_path.exists() or pageview_path.stat().st_size < 10:
            pageview_path.write_bytes(get(PV.format(
                title=urllib.parse.quote(title.replace(" ", "_"), safe=""))))
        time.sleep(0.6)
        print(lid, "->", title)


if __name__ == "__main__":
    main()
