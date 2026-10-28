"""TR round 2: drop name-readable lists and append country-group / regime lists.

Airline lists: airlines whose country of headquarters (raw/airlines.json, carried in
universes/airline.tsv) belongs to an official country group whose member list is stored in
raw/wiki/<article>.wiki.

Currency lists: parsed from official tables stored in raw/ (fixed exchange rate list, euro
linked-regime table, ISO 4217 locations column) and from country memberships joined with the
ISO 4217 country -> currency table.

The existing entries stay byte-identical: the yaml files are edited as text blocks by id.
Run twice and cmp the outputs.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
sys.path.insert(0, HERE)
import build_currency_extra as bce  # noqa: E402

AIRLINE_LISTS = os.path.join(HERE, "lists", "airline.yaml")
CURRENCY_LISTS = os.path.join(HERE, "lists", "currency.yaml")
UNIVERSES = os.path.join(HERE, "universes")

DROP_AIRLINE = ["latam_airlines_group", "tui_group", "dhl_aviation_group", "asl_aviation_group",
                "avianca_group", "jal_group"]
DROP_CURRENCY = ["dollar_named_currencies", "peso_named_currencies", "dinar_named_currencies",
                 "franc_named_currencies", "pound_named_currencies", "rupee_named_currencies",
                 "rial_named_currencies"]
DROP_OWN = ["shared_currencies"]  # an intermediate of this round, replaced by currency_union_currencies


def blocks(path):
    text = open(path, encoding="utf-8").read()
    parts = [p for p in re.split(r"(?m)^(?=- id: )", text) if p.strip()]
    out = []
    for p in parts:
        m = re.match(r"- id: (\S+)", p)
        out.append((m.group(1), p if p.endswith("\n") else p + "\n"))
    return out


def dump_item(item):
    return yaml.safe_dump([item], allow_unicode=True, sort_keys=False, width=120)


def salience_map(universe):
    path = os.path.join(HERE, "salience", universe + ".tsv")
    out = {}
    if os.path.exists(path):
        for line in list(open(path, encoding="utf-8"))[1:]:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4:
                out[p[0]] = int(float(p[3] or 0))
    return out


ORDER = ["id", "name", "kind", "org", "parents", "section", "synonyms", "wiki", "members",
         "disputed", "changes", "official_count", "out_of_universe", "source", "salience", "note"]


def ordered(items):
    return [{k: it[k] for k in ORDER if k in it} for it in items]


def universe_rows(name):
    out = []
    with open(os.path.join(UNIVERSES, name + ".tsv"), encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            out.append(dict(zip(head, line.rstrip("\n").split("\t"))))
    return out


# ---------------------------------------------------------------- airline lists
AIRLINE_BLOCS = [
    ("nordic_airlines", "Airlines of Nordic Council member states", "Nordic Council", "Nordic Council",
     ["Denmark", "Finland", "Iceland", "Norway", "Sweden"], "five sovereign member states"),
    ("baltic_airlines", "Airlines of Baltic Assembly member states", "Baltic Assembly", "Baltic Assembly",
     ["Estonia", "Latvia", "Lithuania"], "three member states"),
    ("visegrad_airlines", "Airlines of Visegrad Group member states", "Visegrad Group", "Visegrad Group",
     ["Czech Republic", "Hungary", "Poland", "Slovakia"], "four member states"),
    ("benelux_airlines", "Airlines of Benelux Union member states", "Benelux", "Benelux Union",
     ["Belgium", "Luxembourg", "Netherlands"], "three member states"),
    ("caricom_airlines", "Airlines of Caribbean Community member states", "Caribbean Community",
     "Caribbean Community",
     ["Antigua and Barbuda", "The Bahamas", "Barbados", "Belize", "Dominica", "Grenada", "Guyana",
      "Haiti", "Jamaica", "Montserrat", "Saint Kitts and Nevis", "Saint Lucia",
      "Saint Vincent and the Grenadines", "Suriname", "Trinidad and Tobago"],
     "fifteen full member states"),
    ("mercosur_airlines", "Airlines of Mercosur member states", "Mercosur", "Mercosur",
     ["Argentina", "Bolivia", "Brazil", "Paraguay", "Uruguay"],
     "five member states after Bolivia joined in 2024; Venezuela suspended since 2016"),
    ("andean_airlines", "Airlines of Andean Community member states", "Andean Community",
     "Andean Community", ["Bolivia", "Colombia", "Ecuador", "Peru"], "four member states"),
    ("ecowas_airlines", "Airlines of ECOWAS member states", "ECOWAS",
     "Economic Community of West African States",
     ["Benin", "Cape Verde", "Ivory Coast", "The Gambia", "Ghana", "Guinea", "Guinea-Bissau",
      "Liberia", "Nigeria", "Senegal", "Sierra Leone", "Togo"],
     "twelve member states after the January 2025 withdrawal of Burkina Faso, Mali and Niger"),
    ("sadc_airlines", "Airlines of Southern African Development Community member states",
     "Southern African Development Community", "Southern African Development Community",
     ["Angola", "Botswana", "Comoros", "Democratic Republic of the Congo", "Eswatini", "Lesotho",
      "Madagascar", "Malawi", "Mauritius", "Mozambique", "Namibia", "Seychelles", "South Africa",
      "Tanzania", "Zambia", "Zimbabwe"], "sixteen member states"),
    ("eac_airlines", "Airlines of East African Community partner states", "East African Community",
     "East African Community",
     ["Burundi", "Democratic Republic of the Congo", "Kenya", "Rwanda", "Somalia", "South Sudan",
      "Tanzania", "Uganda"], "eight partner states"),
    ("eaeu_airlines", "Airlines of Eurasian Economic Union member states", "Eurasian Economic Union",
     "Eurasian Economic Union", ["Armenia", "Belarus", "Kazakhstan", "Kyrgyzstan", "Russia"],
     "five member states"),
    ("turkic_airlines", "Airlines of Organization of Turkic States member states",
     "Organization of Turkic States", "Organization of Turkic States",
     ["Azerbaijan", "Kazakhstan", "Kyrgyzstan", "Turkey", "Uzbekistan"],
     "five full member states (observers excluded)"),
    ("cplp_airlines", "Airlines of Community of Portuguese Language Countries member states",
     "Community of Portuguese Language Countries", "Community of Portuguese Language Countries",
     ["Angola", "Brazil", "Cape Verde", "Guinea-Bissau", "Mozambique", "Portugal",
      "São Tomé and Príncipe", "East Timor", "Equatorial Guinea"], "nine full member states"),
    ("pif_airlines", "Airlines of Pacific Islands Forum member states", "Pacific Islands Forum",
     "Pacific Islands Forum",
     ["Australia", "Cook Islands", "Fiji", "French Polynesia", "Kiribati", "Marshall Islands",
      "Micronesia", "Nauru", "New Caledonia", "New Zealand", "Niue", "Palau", "Papua New Guinea",
      "Samoa", "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu"], "eighteen member states"),
    ("efta_airlines", "Airlines of European Free Trade Association member states",
     "European Free Trade Association", "European Free Trade Association",
     ["Iceland", "Liechtenstein", "Norway", "Switzerland"], "four member states"),
    ("amu_airlines", "Airlines of Arab Maghreb Union member states", "Arab Maghreb Union",
     "Arab Maghreb Union", ["Algeria", "Libya", "Mauritania", "Morocco", "Tunisia"],
     "five member states"),
    ("sco_airlines", "Airlines of Shanghai Cooperation Organisation member states",
     "Shanghai Cooperation Organisation", "Shanghai Cooperation Organisation",
     ["People's Republic of China", "India", "Iran", "Kazakhstan", "Kyrgyzstan", "Pakistan",
      "Russia", "Tajikistan", "Uzbekistan", "Belarus"],
     "ten member states since Belarus joined in 2024"),
    ("african_union_airlines", "Airlines of African Union member states", "African Union",
     "African Union",
     ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cameroon", "Cape Verde",
      "Central African Republic", "Chad", "Comoros", "Ivory Coast", "Democratic Republic of the Congo",
      "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon",
      "The Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya",
      "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia",
      "Niger", "Nigeria", "Rwanda", "São Tomé and Príncipe", "Senegal", "Seychelles", "Sierra Leone",
      "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda",
      "Zambia", "Zimbabwe", "Sahrawi Arab Democratic Republic"], "fifty-five member states"),
    ("commonwealth_airlines", "Airlines of Commonwealth of Nations member states",
     "Commonwealth of Nations", "Commonwealth of Nations",
     ["Antigua and Barbuda", "Australia", "The Bahamas", "Bangladesh", "Barbados", "Belize",
      "Botswana", "Brunei", "Cameroon", "Canada", "Cyprus", "Dominica", "Eswatini", "Fiji", "Gabon",
      "The Gambia", "Ghana", "Grenada", "Guyana", "India", "Jamaica", "Kenya", "Kiribati", "Lesotho",
      "Malawi", "Malaysia", "Maldives", "Malta", "Mauritius", "Mozambique", "Namibia", "Nauru",
      "New Zealand", "Nigeria", "Pakistan", "Papua New Guinea", "Rwanda", "Saint Kitts and Nevis",
      "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "Seychelles", "Sierra Leone",
      "Singapore", "Solomon Islands", "South Africa", "Sri Lanka", "Tanzania", "Togo", "Tonga",
      "Trinidad and Tobago", "Tuvalu", "Uganda", "United Kingdom", "Vanuatu", "Zambia"],
     "fifty-six member states"),
]


def airline_items():
    uni = universe_rows("airline")
    sal = salience_map("airline")
    items = []
    for lid, name, article, org, countries, note in AIRLINE_BLOCS:
        cset = set(countries)
        mem = sorted(r["value"] for r in uni if r["attr:country"] in cset)
        assert len(mem) >= 5, (lid, len(mem))
        assert len({r["attr:country"] for r in uni if r["value"] in set(mem)}) >= 3, lid
        items.append({"id": lid, "name": name, "kind": "bloc", "org": org, "synonyms": [],
                      "wiki": article, "members": mem, "disputed": [], "changes": [],
                      "official_count": len(mem), "out_of_universe": [],
                      "source": "member-state list in raw/wiki/%s.wiki joined with airline country of "
                                "headquarters (raw/airlines.json)" % article.replace(" ", "_"),
                      "salience": sal.get(lid, 0), "note": note})
    return ordered(items)


# ---------------------------------------------------------------- currency lists
ANCHOR_CODES = {"United States dollar": "USD", "Euro": "EUR", "Pound sterling": "GBP",
                "Indian rupee": "INR", "Singapore dollar": "SGD", "New Zealand dollar": "NZD",
                "Danish krone": "DKK", "Hong Kong dollar": "HKD", "South African rand": "ZAR",
                "Australian dollar": "AUD", "Russian ruble": "RUB"}
NAME_FIX = {"CFA franc, Central African": "XAF", "CFA franc, West African": "XOF",
            "CFP franc": "XPF", "Barbadian dollar": "BBD", "Eastern Caribbean dollar": "XCD",
            "Central African CFA franc": "XAF", "West African CFA franc": "XOF",
            "Comorian franc": "KMF"}


def norm_name(s):
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"<[^>]*>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def iso_name_map():
    out = {}
    for _, row in bce.iso_table().iterrows():
        code = str(row["Code"]).strip()
        out.setdefault(norm_name(str(row["Currency"])), code)
    return out


def fixed_rate_rows():
    """(display name, anchor code, code or None) for every row of the fixed-rate list."""
    text = open(os.path.join(RAW, "wiki",
                             "List_of_circulating_fixed_exchange_rate_currencies.wiki"),
                encoding="utf-8").read()
    names = iso_name_map()
    rows, carry, left = [], None, 0
    for block in text.split("\n|-")[1:]:
        cells = [c for c in re.split(r"\n\|", "\n" + block.strip("\n")) if c.strip()]
        if not cells:
            continue
        first = cells[0].strip()
        if not first.startswith(("{{flag", "[[")):
            continue
        m = re.search(r"\[\[([^\]\|#]+)", first)
        if not m:
            continue
        link = norm_name(m.group(1))
        display = NAME_FIX.get(link, link)
        anchor = None
        if len(cells) > 1:
            second = cells[1]
            a = re.search(r"\[\[([^\]\|#]+)", second)
            if a and "rowspan" in second.split("|")[0]:
                anchor = ANCHOR_CODES.get(a.group(1))
                left = int(re.search(r'rowspan="(\d+)"', second).group(1)) - 1
            elif a:
                anchor = ANCHOR_CODES.get(a.group(1))
        if anchor is None and left > 0:
            anchor = carry
            left -= 1
        carry = anchor
        code = display if display and re.fullmatch(r"[A-Z]{3}", display) else names.get(display)
        rows.append((display, anchor, code))
    return rows


def euro_linked_codes():
    lines = open(os.path.join(RAW, "wiki", "International_status_and_usage_of_the_euro.wiki"),
                 encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("==Pegged currencies=="))
    out = []
    for l in lines[start + 1:]:
        if l.startswith("=="):
            break
        m = re.match(r"^\|\s*([A-Z]{3})(?:\s*\|\|.*)?$", l)
        if m:
            out.append(m.group(1))
    return out


def locations_count(code):
    for _, row in bce.iso_table().iterrows():
        if str(row["Code"]).strip() == code:
            loc = str(row["Locations listed for this currency[b]"]).strip()
            if not loc or loc == "nan":
                return 0
            return len([p for p in re.split(r",\s*", loc) if p.strip()])
    return 0


UNION_NAMES = {"CFA franc": ["XOF", "XAF"], "Israeli new sheqel": ["ILS"],
               "CFP franc": ["XPF"], "Eastern Caribbean dollar": ["XCD"]}


def union_codes():
    """Currency cell of every row in the 'Existing' table of the Currency union article."""
    text = open(os.path.join(RAW, "wiki", "Currency_union.wiki"), encoding="utf-8").read()
    start = text.index("===Existing===")
    end = text.index("\n===", start + 20)
    names = iso_name_map()
    out, skipped = set(), []
    for block in text[start:end].split("\n|-")[1:]:
        cells = [c for c in re.split(r"\n\|", "\n" + block.strip("\n")) if c.strip()]
        if len(cells) < 2:
            continue
        union = re.sub(r"\s+", " ", cells[1])
        links = re.findall(r"\[\[([^\]\|#]+)", cells[0])
        for link in links:
            link = norm_name(link)
            if union.startswith("[[Sterling area]] (former)"):
                skipped.append(link)
                continue
            codes = UNION_NAMES.get(link)
            if codes is None:
                code = names.get(link)
                codes = [code] if code else []
            out.update(codes)
    return sorted(out), sorted(skipped)


def org_currency_list(countries):
    c2c = bce.country_currency()
    values = bce.universe_codes()
    members, out = set(), set()
    for c in countries:
        code = c2c.get(c)
        if code is None:
            out.add(c)
        elif code in values:
            members.add(code)
        else:
            out.add(code)
    return sorted(members), sorted(out)


def currency_items():
    values = bce.universe_codes()
    sal = salience_map("currency")
    items = []
    rows = fixed_rate_rows()
    assert len(rows) >= 40, len(rows)
    usd_rows = [(d, c) for d, a, c in rows if a == "USD"]
    usd_mem = sorted({c for _, c in usd_rows if c in values})
    usd_out = sorted(d for d, c in usd_rows if c not in values)
    items.append({"id": "usd_pegged_currencies", "name": "Currencies pegged to the United States dollar",
                  "kind": "currency_peg", "synonyms": [], "wiki": "International use of the U.S. dollar",
                  "members": usd_mem, "disputed": [], "changes": [],
                  "official_count": len(usd_rows), "out_of_universe": usd_out,
                  "source": "anchor-currency column of raw/wiki/"
                            "List_of_circulating_fixed_exchange_rate_currencies.wiki",
                  "note": "USD-anchored rows of the circulating fixed exchange rate list"})
    eur = [c for c in euro_linked_codes() if c in values]
    items.append({"id": "eur_linked_currencies",
                  "name": "Currencies whose exchange rate regime is linked to the euro",
                  "kind": "currency_peg", "synonyms": [],
                  "wiki": "International status and usage of the euro", "members": sorted(eur),
                  "disputed": [], "changes": [], "official_count": len(eur), "out_of_universe": [],
                  "source": "pegged-currencies table of raw/wiki/"
                            "International_status_and_usage_of_the_euro.wiki",
                  "note": "conventional pegs, currency board, ERM II and basket pegs listed there"})
    fixed_mem = sorted({c for _, _, c in rows if c in values})
    fixed_out = sorted(d for d, _, c in rows if c not in values)
    items.append({"id": "fixed_exchange_rate_currencies",
                  "name": "Currencies listed with a circulating fixed exchange rate", "kind": "currency_peg",
                  "synonyms": [], "wiki": "Fixed exchange rate system", "members": fixed_mem,
                  "disputed": [], "changes": [], "official_count": len(rows),
                  "out_of_universe": fixed_out,
                  "source": "raw/wiki/List_of_circulating_fixed_exchange_rate_currencies.wiki",
                  "note": "all rows of the circulating fixed exchange rate list"})
    union, skipped = union_codes()
    assert skipped == ["Pound sterling"], skipped
    items.append({"id": "currency_union_currencies",
                  "name": "Currencies of existing currency unions listed in the Currency union article",
                  "kind": "currency_union", "synonyms": [], "wiki": "Currency union",
                  "members": [c for c in union if c in values],
                  "disputed": [], "changes": [], "official_count": len(union), "out_of_universe": [],
                  "source": "currency column of the 'Existing' table in raw/wiki/Currency_union.wiki",
                  "note": "the sterling area row is marked former and is not included"})
    for lid, name, article, org, countries, note in [
            ("eccas_currencies", "Currencies of Economic Community of Central African States member states",
             "Economic Community of Central African States", "ECCAS",
             ["Angola", "Burundi", "Cameroon", "Central African Republic", "Chad",
              "Republic of the Congo", "Democratic Republic of the Congo", "Equatorial Guinea", "Gabon",
              "Rwanda", "São Tomé and Príncipe"], "eleven member states"),
            ("sica_currencies", "Currencies of Central American Integration System member states",
             "Central American Integration System", "SICA",
             ["Belize", "Costa Rica", "Dominican Republic", "El Salvador", "Guatemala", "Honduras",
              "Nicaragua", "Panama"], "eight member states; El Salvador uses the US dollar")]:
        mem, out = org_currency_list(countries)
        if lid == "sica_currencies":
            mem = sorted(set(mem) - {"SVC"} | {"USD"})
            out = sorted(set(out) - {"USD"})
        items.append({"id": lid, "name": name, "kind": "currency_org", "org": org, "synonyms": [],
                      "wiki": article, "members": mem, "disputed": [], "changes": [],
                      "official_count": len(mem) + len(out), "out_of_universe": out,
                      "source": "member-state list in raw/wiki/%s.wiki + ISO 4217 table "
                                "(raw/iso4217_page.json)" % article.replace(" ", "_"),
                      "salience": sal.get(lid, 0), "note": note})
    for it in items:
        it["salience"] = sal.get(it["id"], 0)
    return ordered(items)


def merge(path, drops, new_items):
    drop = set(drops) | {it["id"] for it in new_items}
    kept = [(i, t) for i, t in blocks(path) if i not in drop]
    kept += [(it["id"], dump_item(it)) for it in new_items]
    open(path, "w", encoding="utf-8").write("".join(t for _, t in kept))
    return len(kept)


def main():
    a = merge(AIRLINE_LISTS, DROP_AIRLINE, airline_items())
    c = merge(CURRENCY_LISTS, DROP_CURRENCY + DROP_OWN, currency_items())
    print("airline", a, "currency", c)


if __name__ == "__main__":
    main()
