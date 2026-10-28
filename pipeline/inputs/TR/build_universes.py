"""Build universes/{airline,airport,currency}.tsv from raw/ (Wikidata SPARQL JSON + ISO 4217 page).

Deterministic: reads only files in raw/, writes sorted TSV.
"""
import io
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "universes")


def rows(name):
    with open(os.path.join(RAW, name + ".json"), encoding="utf-8") as fh:
        d = json.load(fh)
    return [{k: v["value"] for k, v in b.items()} for b in d["results"]["bindings"]]


def write_tsv(name, header, data):
    path = os.path.join(OUT, name + ".tsv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(header) + "\n")
        for r in data:
            fh.write("\t".join(str(r[h]) for h in header) + "\n")
    print(name, len(data))


def airport_universe():
    sitelinks = {r["article"].split("/wiki/")[-1].replace("_", " "): r["item"].split("/")[-1]
                 for r in rows("airline_sitelinks")}
    del sitelinks
    ap = rows("airports")
    by_code = {}
    for r in ap:
        code = r.get("iata", "").strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", code):
            continue
        by_code.setdefault(code, []).append(r)
    data = []
    for code in sorted(by_code):
        group = by_code[code]
        labels = {g.get("itemLabel", "").strip() for g in group}
        if len(group) > 1 or len(labels) > 1:
            continue  # one code, several entities: not usable as a single value
        r = group[0]
        data.append({"value": code, "entity": r.get("itemLabel", "").strip(),
                     "qid": r["item"].split("/")[-1],
                     "attr:country": r.get("countryLabel", "?") or "?",
                     "attr:region": r.get("continentLabel", "?") or "?"})
    write_tsv("airport", ["value", "entity", "qid", "attr:country", "attr:region"], data)


def airline_universe():
    has_article = {r["item"].split("/")[-1] for r in rows("airline_sitelinks")}
    air = rows("airlines")
    seen = {}
    for r in air:
        lab = r.get("itemLabel", "").strip()
        qid = r["item"].split("/")[-1]
        if not lab or lab == qid or qid not in has_article:
            continue
        seen.setdefault(lab, []).append(r)
    data = []
    for lab in sorted(seen):
        group = seen[lab]
        if len({g["item"] for g in group}) > 1:
            continue
        r = group[0]
        data.append({"value": lab, "entity": lab, "qid": r["item"].split("/")[-1],
                     "attr:country": r.get("countryLabel", "?") or "?",
                     "attr:region": r.get("continentLabel", "?") or "?"})
    write_tsv("airline", ["value", "entity", "qid", "attr:country", "attr:region"], data)


def currency_rows():
    """Active ISO 4217 currencies from the raw Wikipedia table: code, name, locations text, region."""
    with open(os.path.join(RAW, "iso4217_page.json"), encoding="utf-8") as fh:
        html = json.load(fh)["parse"]["text"]
    t = pd.read_html(io.StringIO(html))[1].fillna("")
    # country -> continent, from the Wikidata country table
    cont = {}
    for r in rows("country_relations"):
        if "continentLabel" in r:
            cont.setdefault(r["countryLabel"], r["continentLabel"])
    skip_codes = {"XXX", "XTS", "XAU", "XAG", "XPD", "XPT", "XDR", "XBA", "XBB", "XBC", "XBD",
                  "XSU", "XUA", "XFO", "XFU", "XRE", "XTS", "XAD", "CHE", "CHW", "UYW"}
    # territories and shared currencies that are not named as a country in the Locations column
    region_override = {
        "BMD": "North America", "BSD": "North America", "FKP": "South America", "GMD": "Africa",
        "HKD": "Asia", "KYD": "North America", "MOP": "Asia", "SHP": "Africa", "XCD": "North America",
        "XPF": "Oceania", "EUR": "Europe", "CNY": "Asia",
    }
    data = []
    for _, r in t.iterrows():
        code = str(r["Code"]).strip()
        name = re.sub(r"\[[^\]]*\]", "", str(r["Currency"])).strip()
        dec = str(r["D[a]"]).strip()
        if code in skip_codes or dec == "." or "funds code" in name.lower():
            continue
        locs = str(r["Locations listed for this currency[b]"]).strip()
        if locs == "nan":
            locs = ""
        first = re.split(r"[,(\[]", locs)[0].strip() if locs else ""
        first = re.sub(r"\[.*?\]", "", first).strip()
        region = region_override.get(code) or cont.get(first, "?")
        data.append({"code": code, "entity": name, "locations": locs, "region": region,
                     "primary": first})
    return data


def currency_universe():
    data = []
    for r in currency_rows():
        data.append({"value": r["code"], "entity": r["entity"], "qid": "", "attr:region": r["region"]})
    write_tsv("currency", ["value", "entity", "qid", "attr:region"], data)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    airline_universe()
    airport_universe()
    currency_universe()
