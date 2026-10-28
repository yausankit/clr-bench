"""Fetch English-Wikipedia search hits and 12-month pageviews for the ADD_SY_a2 medicine lists.

MediaWiki API: one request at a time, >= 2 s apart.  Pageviews REST: one at a time, >= 0.5 s apart.
429 backs off 60 s, doubling, capped at 600 s.  Raw JSON is stored under salience/raw/.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
API = "https://en.wikipedia.org/w/api.php"
PV = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
      "all-access/user/{title}/monthly/20251001/20260930")


def get(url, tries=8):
    delay = 60
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "clrsynth-add-lists/1.0 (dataset build)"})
            with urllib.request.urlopen(req, timeout=90) as fh:
                return fh.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"429, wait {delay}s", file=sys.stderr)
                time.sleep(delay)
                delay = min(delay * 2, 600)
                continue
            if e.code >= 500:
                time.sleep(30)
                continue
            raise
        except Exception:
            time.sleep(10)
    raise SystemExit(f"gave up: {url}")


def main():
    with (ROOT / "add_lists_spec_medicine.tsv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    for row in rows:
        lid = row["id"]
        sp = RAW / f"search_medicine_{lid}.json"
        if not sp.exists():
            url = API + "?" + urllib.parse.urlencode(
                {"action": "query", "list": "search", "srsearch": row.get("search") or row["name"],
                 "srlimit": 3, "format": "json"})
            sp.write_bytes(get(url))
        time.sleep(2.0)
        hits = (json.loads(sp.read_text()).get("query") or {}).get("search") or []
        if not hits:
            print(lid, "no hit")
            continue
        title = hits[0]["title"]
        pp = RAW / f"pageviews_medicine_{lid}.json"
        if not pp.exists():
            pp.write_bytes(get(PV.format(title=urllib.parse.quote(title.replace(" ", "_"), safe=""))))
        time.sleep(0.6)
        print(lid, "->", title)


if __name__ == "__main__":
    main()
