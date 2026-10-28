"""Fetch English Wikipedia wikitext snapshots for the organisations behind the new currency lists."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "wiki")
PROXY = os.environ.get("HTTPS_PROXY", "")  # optional HTTP proxy; empty means direct

TITLES = sys.argv[1:] or [
    "Group of Seven", "OECD", "NATO", "Shanghai Cooperation Organisation",
    "Eurasian Economic Union", "Organization of Turkic States",
    "Community of Portuguese Language Countries", "ECOWAS", "East African Community",
    "Southern African Development Community", "Southern African Customs Union",
    "Caribbean Community", "Mercosur", "Arab Maghreb Union", "OPEC", "Nordic Council",
    "Pacific Islands Forum", "Central American Integration System", "Rial", "ISO 4217",
]


def slug(title):
    return re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")


def fetch(title):
    url = ("https://en.wikipedia.org/w/api.php?action=parse&prop=wikitext&format=json"
           "&formatversion=2&redirects=1&page=" + urllib.parse.quote(title.replace(" ", "_")))
    out = subprocess.run(["curl", "-sS", "-x", PROXY, "-w", "\n%{http_code}", url],
                         capture_output=True, text=True)
    body, _, code = out.stdout.rpartition("\n")
    if code != "200":
        raise RuntimeError(f"{title}: HTTP {code}")
    return json.loads(body)


def main():
    os.makedirs(RAW, exist_ok=True)
    for t in TITLES:
        path = os.path.join(RAW, slug(t) + ".json")
        if os.path.exists(path):
            print("have", t)
            continue
        d = fetch(t)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
        print("saved", t, len(d["parse"]["wikitext"]))
        time.sleep(2)


if __name__ == "__main__":
    main()
