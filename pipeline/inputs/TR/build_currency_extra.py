"""Append new currency lists to lists/currency.yaml (the 18 existing entries stay byte-identical).

Sources: the English Wikipedia membership tables stored in raw/wiki/<article>.json and the
ISO 4217 table stored in raw/iso4217_page.json.  Deterministic: output depends only on raw files,
salience/currency.tsv and the constants below.

Run:  python3 build_currency_extra.py    (twice, then cmp)
"""
import io
import json
import os
import re

import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
LISTS = os.path.join(HERE, "lists", "currency.yaml")
UNIVERSE = os.path.join(HERE, "universes", "currency.tsv")

EUROZONE = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Estonia", "Finland", "France",
            "Germany", "Greece", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
            "Netherlands", "Portugal", "Slovakia", "Slovenia", "Spain"]
OVERRIDES = {
    "Côte d'Ivoire": "XOF",
    "DR Congo": "CDF",
    "East Timor": "USD",
    "Micronesia": "USD",
    "French Polynesia": "XPF",
    "New Caledonia": "XPF",
}
SKIP_SECONDARY = {"BOV", "CHE", "CHW", "CLF", "COU", "MXV", "USN", "UYI", "VED"}


def universe_codes():
    with open(UNIVERSE, encoding="utf-8") as fh:
        fh.readline()
        return {line.split("\t")[0] for line in fh if line.strip()}


def iso_table():
    html = json.load(open(os.path.join(RAW, "iso4217_page.json"), encoding="utf-8"))["parse"]["text"]
    return pd.read_html(io.StringIO(html))[1].fillna("")


def country_currency():
    """ISO 4217 locations column -> currency code, plus the euro area and a few label variants."""
    table = iso_table()
    out = {}
    for _, row in table.iterrows():
        code = str(row["Code"]).strip()
        if code in SKIP_SECONDARY:
            continue
        locs = str(row["Locations listed for this currency[b]"]).strip()
        if not locs or locs == "nan":
            continue
        for part in re.split(r",\s*", locs):
            name = re.sub(r"\s*\((?:[A-Z]{2})\)", "", part)
            name = re.sub(r"\s*\(pegged[^)]*\)", "", name)
            name = re.sub(r"\[[^\]]*\]", "", name).strip()
            if name:
                out.setdefault(name, code)
    for c in EUROZONE:
        out[c] = "EUR"
    out.update(OVERRIDES)
    return out


def roster(spec, c2c, values):
    members, out = [], []
    for c in spec:
        code = c2c.get(c)
        if code is None:
            out.append(c)
        elif code in values:
            members.append(code)
        else:
            out.append(code)
    return sorted(set(members)), sorted(set(out))


ORGS = [
    # id, name, article, organisation, member countries, note
    ("g7_currencies", "Currencies of Group of Seven member states", "Group of Seven", "G7",
     ["Canada", "France", "Germany", "Italy", "Japan", "United Kingdom", "United States"],
     "seven member states"),
    ("oecd_currencies", "Currencies of OECD member states", "OECD",
     "Organisation for Economic Co-operation and Development",
     ["Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia", "Costa Rica", "Czech Republic",
      "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland",
      "Israel", "Italy", "Japan", "South Korea", "Latvia", "Lithuania", "Luxembourg", "Mexico",
      "Netherlands", "New Zealand", "Norway", "Poland", "Portugal", "Slovakia", "Slovenia", "Spain",
      "Sweden", "Switzerland", "Turkey", "United Kingdom", "United States"],
     "38 member countries"),
    ("nato_currencies", "Currencies of NATO member states", "NATO", "NATO",
     ["Albania", "Belgium", "Bulgaria", "Canada", "Croatia", "Czech Republic", "Denmark", "Estonia",
      "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Italy", "Latvia", "Lithuania",
      "Luxembourg", "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal",
      "Romania", "Slovakia", "Slovenia", "Spain", "Sweden", "Turkey", "United Kingdom",
      "United States"],
     "32 member states"),
    ("sco_currencies", "Currencies of Shanghai Cooperation Organisation member states",
     "Shanghai Cooperation Organisation", "Shanghai Cooperation Organisation",
     ["China", "India", "Iran", "Kazakhstan", "Kyrgyzstan", "Pakistan", "Russia", "Tajikistan",
      "Uzbekistan", "Belarus"],
     "ten member states since Belarus joined in 2024"),
    ("eaeu_currencies", "Currencies of Eurasian Economic Union member states",
     "Eurasian Economic Union", "Eurasian Economic Union",
     ["Armenia", "Belarus", "Kazakhstan", "Kyrgyzstan", "Russia"],
     "five member states"),
    ("turkic_states_currencies", "Currencies of Organization of Turkic States member states",
     "Organization of Turkic States", "Organization of Turkic States",
     ["Azerbaijan", "Kazakhstan", "Kyrgyzstan", "Turkey", "Uzbekistan"],
     "five full members (observers excluded)"),
    ("cplp_currencies", "Currencies of Community of Portuguese Language Countries member states",
     "Community of Portuguese Language Countries", "Community of Portuguese Language Countries",
     ["Angola", "Brazil", "Cape Verde", "Guinea-Bissau", "Mozambique", "Portugal",
      "São Tomé and Príncipe", "East Timor", "Equatorial Guinea"],
     "nine full member states"),
    ("ecowas_currencies", "Currencies of ECOWAS member states", "ECOWAS",
     "Economic Community of West African States",
     ["Benin", "Cape Verde", "Côte d'Ivoire", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Liberia",
      "Nigeria", "Senegal", "Sierra Leone", "Togo"],
     "12 member states after the January 2025 withdrawal of Burkina Faso, Mali and Niger"),
    ("eac_currencies", "Currencies of East African Community partner states", "East African Community",
     "East African Community",
     ["Burundi", "DR Congo", "Kenya", "Rwanda", "Somalia", "South Sudan", "Tanzania", "Uganda"],
     "eight partner states"),
    ("sadc_currencies", "Currencies of Southern African Development Community member states",
     "Southern African Development Community", "Southern African Development Community",
     ["Angola", "Botswana", "Comoros", "DR Congo", "Eswatini", "Lesotho", "Madagascar", "Malawi",
      "Mauritius", "Mozambique", "Namibia", "Seychelles", "South Africa", "Tanzania", "Zambia",
      "Zimbabwe"],
     "16 member states"),
    ("sacu_currencies", "Currencies of Southern African Customs Union member states",
     "Southern African Customs Union", "Southern African Customs Union",
     ["Botswana", "Eswatini", "Lesotho", "Namibia", "South Africa"],
     "five member states"),
    ("caricom_currencies", "Currencies of Caribbean Community member states", "Caribbean Community",
     "Caribbean Community",
     ["Antigua and Barbuda", "Bahamas", "Barbados", "Belize", "Dominica", "Grenada", "Guyana", "Haiti",
      "Jamaica", "Montserrat", "Saint Kitts and Nevis", "Saint Lucia",
      "Saint Vincent and the Grenadines", "Suriname", "Trinidad and Tobago"],
     "15 full members (associate members excluded)"),
    ("mercosur_currencies", "Currencies of Mercosur member states", "Mercosur", "Mercosur",
     ["Argentina", "Bolivia", "Brazil", "Paraguay", "Uruguay", "Venezuela"],
     "six member states; Venezuela suspended since December 2016"),
    ("amu_currencies", "Currencies of Arab Maghreb Union member states", "Arab Maghreb Union",
     "Arab Maghreb Union",
     ["Algeria", "Libya", "Mauritania", "Morocco", "Tunisia"],
     "five member states"),
    ("opec_currencies", "Currencies of OPEC member countries", "OPEC",
     "Organization of the Petroleum Exporting Countries",
     ["Algeria", "Republic of the Congo", "Equatorial Guinea", "Gabon", "Iran", "Iraq", "Kuwait",
      "Libya", "Nigeria", "Saudi Arabia", "Venezuela"],
     "11 member countries as of May 2026"),
    ("nordic_council_currencies", "Currencies of Nordic Council member states", "Nordic Council",
     "Nordic Council",
     ["Denmark", "Finland", "Iceland", "Norway", "Sweden"],
     "five full members (self-governing regions excluded)"),
    ("pif_currencies", "Currencies of Pacific Islands Forum member states", "Pacific Islands Forum",
     "Pacific Islands Forum",
     ["Australia", "Cook Islands", "Fiji", "French Polynesia", "Kiribati", "Marshall Islands",
      "Micronesia", "Nauru", "New Caledonia", "New Zealand", "Niue", "Palau", "Papua New Guinea",
      "Samoa", "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu"],
     "18 member states"),
]

SPECIAL = ["mercosur_currencies"]


def currency_lists():
    values = universe_codes()
    c2c = country_currency()
    items = []
    for lid, name, article, org, countries, note in ORGS:
        members, out = roster(countries, c2c, values)
        disputed = []
        if lid in SPECIAL:
            disputed = ["VES"]
            members = [m for m in members if m not in disputed]
        official = len(members) + len(disputed) + len(out)
        if official != len(countries):
            note = f"{note} ({official} distinct currencies)"
        it = {"id": lid, "name": name, "kind": "currency_org", "org": org, "synonyms": [],
              "wiki": article, "members": members, "disputed": disputed, "changes": [],
              "official_count": official, "out_of_universe": out,
              "source": f"member list in raw/wiki/{article.replace(' ', '_')}.json + ISO 4217 table "
                        f"(raw/iso4217_page.json)", "note": note}
        items.append(it)
    # ISO 4217 standard classes: number of decimal places.
    table = iso_table()
    for lid, name, digits, note in [
            ("zero_minor_unit_currencies", "ISO 4217 currencies with zero decimal places", 0,
             "currencies whose ISO 4217 minor unit is 0"),
            ("three_minor_unit_currencies", "ISO 4217 currencies with three decimal places", 3,
             "currencies whose ISO 4217 minor unit is 3")]:
        codes = []
        for _, row in table.iterrows():
            code = str(row["Code"]).strip()
            dec = re.sub(r"\[[^\]]*\]", "", str(row["D[a]"])).strip()
            if dec != str(digits):
                continue
            if "funds code" in str(row["Currency"]).lower():
                continue
            codes.append(code)
        members = sorted(c for c in codes if c in values)
        out = sorted(c for c in codes if c not in values)
        items.append({"id": lid, "name": name, "kind": "currency_standard", "synonyms": [],
                      "wiki": "ISO 4217", "members": members, "disputed": [], "changes": [],
                      "official_count": len(codes), "out_of_universe": out,
                      "source": "ISO 4217 table column D[a] (raw/iso4217_page.json)",
                      "note": note})
    # Name family: currencies whose ISO name ends in rial or riyal.
    members = sorted(r["Code"] for _, r in table.iterrows()
                     if re.search(r"\b(rial|riyal)$", str(r["Currency"]).strip(), re.I)
                     and str(r["Code"]).strip() in values)
    items.append({"id": "rial_named_currencies", "name": "Currencies named rial or riyal",
                  "kind": "name_family", "synonyms": [], "wiki": "Rial",
                  "members": members, "disputed": [], "changes": [],
                  "official_count": len(members), "out_of_universe": [],
                  "source": "ISO 4217 table currency names (raw/iso4217_page.json)"})
    return items


def salience_map():
    path = os.path.join(HERE, "salience", "currency.tsv")
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in list(fh)[1:]:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 4:
                    out[p[0]] = int(float(p[3] or 0))
    return out


def main():
    sal = salience_map()
    new = currency_lists()
    new_ids = {it["id"] for it in new}
    parsed = yaml.safe_load(open(LISTS, encoding="utf-8")) or []
    existing = [it for it in parsed if it["id"] not in new_ids]
    assert len(existing) == 18, len(existing)
    for it in new:
        it["salience"] = sal.get(it["id"], 0)
        it.setdefault("synonyms", [])
    order = ["id", "name", "kind", "org", "synonyms", "wiki", "members", "disputed", "changes",
             "official_count", "out_of_universe", "source", "salience", "note"]
    out = existing + [{k: it[k] for k in order if k in it} for it in new]
    with open(LISTS, "w", encoding="utf-8") as fh:
        yaml.safe_dump(out, fh, allow_unicode=True, sort_keys=False, width=120)
    print("wrote", len(out), "lists (", len(new), "new )")


if __name__ == "__main__":
    main()
