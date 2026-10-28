"""Append 5 member / 5 non-member rows for every list added in TR round 2.

Every row is derived from raw/: the membership list of the country group (raw/wiki/<article>.wiki),
the airline's country (raw/airlines.json), the fixed-rate table, the euro pegged-currencies table,
the currency-union table, or the ISO 4217 table. Deterministic.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_currency_extra as bce  # noqa: E402
import build_tr2_lists as btl  # noqa: E402

RAW = os.path.join(HERE, "raw")
ALIAS = {"Ivory Coast": ["Ivory Coast", "Côte d'Ivoire", "Cote d'Ivoire"],
         "The Gambia": ["Gambia", "The Gambia"],
         "The Bahamas": ["Bahamas", "The Bahamas"],
         "Democratic Republic of the Congo": ["Democratic Republic of the Congo", "DR Congo"],
         "People's Republic of China": ["China", "People's Republic of China"],
         "São Tomé and Príncipe": ["São Tomé and Príncipe", "Sao Tome"],
         "East Timor": ["Timor-Leste", "East Timor"],
         "Cape Verde": ["Cape Verde", "Cabo Verde"],
         "Czech Republic": ["Czech Republic", "Czechia"],
         "Turkey": ["Turkey", "Türkiye"]}


def spread(items, k=5):
    items = sorted(items)
    if len(items) <= k:
        return items
    idx = [round(j * (len(items) - 1) / (k - 1)) for j in range(k)]
    return [items[i] for i in idx]


def wiki_lines(article):
    path = os.path.join(RAW, "wiki", article.replace(" ", "_") + ".json")
    if not os.path.exists(path.replace(".json", ".wiki")):
        text = json.load(open(path, encoding="utf-8"))["parse"]["wikitext"]
        with open(path.replace(".json", ".wiki"), "w", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
    return open(path.replace(".json", ".wiki"), encoding="utf-8").read().splitlines()


def country_line(lines, country):
    al = ALIAS.get(country, [country])
    for i, line in enumerate(lines, 1):
        if any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", line) for a in al):
            return i
    return None


def airline_index():
    bindings = json.load(open(os.path.join(RAW, "airlines.json"), encoding="utf-8"))["results"]["bindings"]
    out = {}
    for n, b in enumerate(bindings, 1):
        out.setdefault(b.get("itemLabel", {}).get("value", ""),
                       (b.get("countryLabel", {}).get("value", ""), n))
    return out


def iso_rows():
    table = bce.iso_table()
    out = {}
    for _, row in table.iterrows():
        code = str(row["Code"]).strip()
        out[code] = (re.sub(r"\[[^\]]*\]", "", str(row["D[a]"])).strip(),
                     str(row["Currency"]).strip(),
                     str(row["Locations listed for this currency[b]"]).strip())
    return out


def fixed_rows_with_lines():
    text = wiki_lines("List_of_circulating_fixed_exchange_rate_currencies")
    rows = btl.fixed_rate_rows()
    # align rows (parsed in file order) with the line of their currency link
    links = [i for i, l in enumerate(text, 1)
             if l.startswith("|") and re.search(r"\[\[[^\]\|]+", l) and "rowspan" not in l.split("|")[0]]
    out = []
    for n, (display, anchor, code) in enumerate(rows):
        out.append((display, anchor, code, links[n] if n < len(links) else 0))
    return out


def euro_rows_with_lines():
    lines = wiki_lines("International_status_and_usage_of_the_euro")
    start = next(i for i, l in enumerate(lines) if l.startswith("==Pegged currencies=="))
    out = []
    for i in range(start, len(lines)):
        l = lines[i]
        if i > start and l.startswith("=="):
            break
        m = re.match(r"^\|\s*([A-Z]{3})(?:\s*\|\|.*)?$", l)
        if m:
            out.append((m.group(1), i + 1))
    return out


def union_rows_with_lines():
    lines = wiki_lines("Currency_union")
    start = next(i for i, l in enumerate(lines) if l.strip() == "===Existing===")
    end = next(i for i, l in enumerate(lines[start + 1:], start + 1) if l.strip().startswith("==="))
    names = btl.iso_name_map()
    out = []
    for i in range(start, end):
        l = lines[i]
        if not l.startswith("|[[") and not l.startswith("| [["):
            continue
        for link in re.findall(r"\[\[([^\]\|#]+)", l):
            link = btl.norm_name(link)
            codes = btl.UNION_NAMES.get(link)
            if codes is None:
                code = names.get(link)
                codes = [code] if code else []
            for c in codes:
                out.append((c, i + 1))
    return out


def main():
    values = bce.universe_codes()
    c2c = bce.country_currency()
    iso = iso_rows()
    airlines = airline_index()
    airline_lists = {x["id"]: x for x in yaml.safe_load(open(os.path.join(HERE, "lists", "airline.yaml")))}
    currency_lists = {x["id"]: x for x in yaml.safe_load(open(os.path.join(HERE, "lists", "currency.yaml")))}
    out = []
    new_air = [b[0] for b in btl.AIRLINE_BLOCS]
    new_cur = ["usd_pegged_currencies", "eur_linked_currencies", "fixed_exchange_rate_currencies",
               "currency_union_currencies", "eccas_currencies", "sica_currencies"]
    uni_rows = btl.universe_rows("airline")
    country_of = {r["value"]: r["attr:country"] for r in uni_rows}
    airline_values = sorted(country_of)
    for lid in new_air:
        spec = next(b for b in btl.AIRLINE_BLOCS if b[0] == lid)
        article, countries = spec[2], spec[4]
        lines = wiki_lines(article)
        members = airline_lists[lid]["members"]
        for v in spread(members):
            c = country_of[v]
            ln = country_line(lines, c)
            assert ln, (lid, v, c)
            cn = airlines[v][1]
            out.append([lid, "airline", v, "member",
                        f"raw/wiki/{article.replace(' ', '_')}.wiki:{ln} names {c} + "
                        f"raw/airlines.json binding {cn} (itemLabel={v}, countryLabel={c})",
                        lines[ln - 1].strip()[:200]])
        nonmembers = [v for v in airline_values if country_of[v] not in set(countries)]
        for v in spread(nonmembers):
            c = country_of[v]
            cn = airlines[v][1]
            out.append([lid, "airline", v, "nonmember",
                        f"raw/wiki/{article.replace(' ', '_')}.wiki member list ({len(countries)} states) "
                        f"does not name {c} + raw/airlines.json binding {cn} (itemLabel={v}, countryLabel={c})",
                        ""])
    fixed = fixed_rows_with_lines()
    fixed_by_code = {c: (d, a, ln) for d, a, c, ln in fixed if c}
    for lid, kind in [("usd_pegged_currencies", "usd"), ("fixed_exchange_rate_currencies", "fixed")]:
        members = currency_lists[lid]["members"]
        for code in spread(members):
            d, a, ln = fixed_by_code[code]
            out.append([lid, "currency", code, "member",
                        f"raw/wiki/List_of_circulating_fixed_exchange_rate_currencies.wiki:{ln} "
                        f"({d}, anchor {a}) + raw/iso4217_page.json row {code}",
                        wiki_lines("List_of_circulating_fixed_exchange_rate_currencies")[ln - 1].strip()[:200]])
        anchors = {"usd": ["USD"], "fixed": None}[kind]
        pool = [c for c in sorted(values) if c not in set(members)
                and (anchors is None and c not in fixed_by_code or anchors and
                     (c not in fixed_by_code or fixed_by_code[c][1] not in anchors))]
        for code in spread(pool):
            if code in fixed_by_code:
                d, a, ln = fixed_by_code[code]
                ev = (f"raw/wiki/List_of_circulating_fixed_exchange_rate_currencies.wiki:{ln} "
                      f"({d}, anchor {a}) + raw/iso4217_page.json row {code}")
                raw = wiki_lines("List_of_circulating_fixed_exchange_rate_currencies")[ln - 1].strip()[:200]
            else:
                ev = (f"raw/wiki/List_of_circulating_fixed_exchange_rate_currencies.wiki has no row for "
                      f"{code} + raw/iso4217_page.json row {code}")
                raw = iso[code][1]
            out.append([lid, "currency", code, "nonmember", ev, raw])
    euro = euro_rows_with_lines()
    euro_codes = {c for c, _ in euro}
    lines = wiki_lines("International_status_and_usage_of_the_euro")
    for code in spread(currency_lists["eur_linked_currencies"]["members"]):
        ln = next(i for c, i in euro if c == code)
        out.append(["eur_linked_currencies", "currency", code, "member",
                    f"raw/wiki/International_status_and_usage_of_the_euro.wiki:{ln} (pegged-currencies table) "
                    f"+ raw/iso4217_page.json row {code}", lines[ln - 1].strip()[:200]])
    for code in spread([c for c in sorted(values) if c not in euro_codes]):
        out.append(["eur_linked_currencies", "currency", code, "nonmember",
                    f"raw/wiki/International_status_and_usage_of_the_euro.wiki pegged-currencies table has no "
                    f"row for {code} + raw/iso4217_page.json row {code}", iso[code][1]])
    union = union_rows_with_lines()
    union_codes = {c for c, _ in union}
    ulines = wiki_lines("Currency_union")
    for code in spread(currency_lists["currency_union_currencies"]["members"]):
        ln = next(i for c, i in union if c == code)
        out.append(["currency_union_currencies", "currency", code, "member",
                    f"raw/wiki/Currency_union.wiki:{ln} (existing-unions table) + raw/iso4217_page.json row "
                    f"{code}", ulines[ln - 1].strip()[:200]])
    for code in spread([c for c in sorted(values) if c not in union_codes]):
        out.append(["currency_union_currencies", "currency", code, "nonmember",
                    f"raw/wiki/Currency_union.wiki existing-unions table has no row for {code} + "
                    f"raw/iso4217_page.json row {code}", iso[code][1]])
    for lid in ("eccas_currencies", "sica_currencies"):
        lst = currency_lists[lid]
        spec = next(b for b in [("eccas_currencies", "Economic Community of Central African States",
                                 ["Angola", "Burundi", "Cameroon", "Central African Republic", "Chad",
                                  "Republic of the Congo", "Democratic Republic of the Congo",
                                  "Equatorial Guinea", "Gabon", "Rwanda", "São Tomé and Príncipe"]),
                                ("sica_currencies", "Central American Integration System",
                                 ["Belize", "Costa Rica", "Dominican Republic", "El Salvador", "Guatemala",
                                  "Honduras", "Nicaragua", "Panama"])] if b[0] == lid)
        article, countries = spec[1], spec[2]
        lines = wiki_lines(article)
        by_code = {}
        for c in countries:
            by_code.setdefault({"El Salvador": "USD"}.get(c, c2c.get(c)), c)
        for code in spread(lst["members"]):
            c = by_code[code]
            ln = country_line(lines, c)
            assert ln, (lid, code, c)
            out.append([lid, "currency", code, "member",
                        f"raw/wiki/{article.replace(' ', '_')}.wiki:{ln} names {c} + raw/iso4217_page.json row "
                        f"{code}", lines[ln - 1].strip()[:200]])
        pool = [c for c in sorted(values) if c not in set(lst["members"])]
        for code in spread(pool):
            home = iso[code][2][:60]
            out.append([lid, "currency", code, "nonmember",
                        f"raw/wiki/{article.replace(' ', '_')}.wiki member list ({len(countries)} states) has no "
                        f"country using {code} + raw/iso4217_page.json row {code} ({home})", iso[code][1]])
    path = os.path.join(HERE, "SPOTCHECK.tsv")
    old = [line.rstrip("\n").split("\t") for line in open(path, encoding="utf-8")]
    header = old[0]
    drop = set(new_air) | set(new_cur) | set(btl.DROP_AIRLINE) | set(btl.DROP_CURRENCY)
    body = [r for r in old[1:] if r[0] not in drop]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for r in body:
            fh.write("\t".join(r) + "\n")
        for r in out:
            fh.write("\t".join(r) + "\n")
    print("appended", len(out), "rows for", len(new_air) + len(new_cur), "lists")


if __name__ == "__main__":
    main()
