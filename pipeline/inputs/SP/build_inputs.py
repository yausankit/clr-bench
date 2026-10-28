#!/usr/bin/env python3
"""Build inputs/SP universes, lists, scenario, chains, sources, and descriptions from raw snapshots."""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from build_salience import build as build_salience
from parse_sources import load_page, members_for, source_url
from source_specs import (CLUB_LISTS, CLUB_UNIVERSE_EXTRAS, COMPANY_LISTS, COUNTRY_LISTS,
                          TEMPLATES)

ROOT = Path(__file__).resolve().parent
OUT = ROOT
RAW = ROOT / "raw"

SPECIAL_TITLE_KEYS = {"FedEx Freight"}
CLUB_VALUE_OVERRIDES = {"Q631": "Inter Milan", "Q994811": "Red Bull Salzburg"}
EXCLUDED_CLUB_QIDS = {"Q175687", "Q19482"}

COMPANY_CORE_IDS = {"cac_40", "ibex_35", "ftse_mib", "dax", "aex", "bel_20",
                    "euro_stoxx_50", "dow_jones", "sp_100", "nasdaq_100", "stoxx_europe_600"}

INDEX_COUNTRY = {
    "cac_40": "France", "ibex_35": "Spain", "ftse_mib": "Italy", "dax": "Germany",
    "aex": "Netherlands", "bel_20": "Belgium", "euro_stoxx_50": "Europe",
    "dow_jones": "United States", "sp_100": "United States", "nasdaq_100": "United States",
}

COUNTRY_ALIASES = {
    "united states": "US", "united states of america": "US", "u s a": "US",
    "united kingdom": "GB", "united kingdom of great britain and northern ireland": "GB",
    "great britain": "GB", "czech republic": "CZ", "czechia": "CZ",
    "south korea": "KR", "korea republic of": "KR", "republic of korea": "KR",
    "north korea": "KP", "korea democratic people s republic of": "KP",
    "russia": "RU", "russian federation": "RU", "turkey": "TR", "turkiye": "TR",
    "netherlands": "NL", "netherlands kingdom of the": "NL", "holland": "NL",
    "bolivia": "BO", "bolivia plurinational state of": "BO",
    "venezuela": "VE", "venezuela bolivarian republic of": "VE",
    "iran": "IR", "iran islamic republic of": "IR", "syria": "SY", "syrian arab republic": "SY",
    "vietnam": "VN", "viet nam": "VN", "laos": "LA", "lao people s democratic republic": "LA",
    "tanzania": "TZ", "tanzania united republic of": "TZ", "moldova": "MD",
    "moldova republic of": "MD", "brunei": "BN", "brunei darussalam": "BN",
    "cape verde": "CV", "cabo verde": "CV", "ivory coast": "CI", "cote d ivoire": "CI",
    "democratic republic of the congo": "CD", "congo democratic republic of the": "CD",
    "republic of the congo": "CG", "congo": "CG", "palestine": "PS", "palestine state of": "PS",
    "united arab emirates": "AE", "hong kong": "HK", "macau": "MO", "macao": "MO",
    "taiwan": "TW", "taiwan province of china": "TW", "micronesia": "FM",
    "micronesia federated states of": "FM", "bahamas": "BS", "gambia": "GM",
    "saint lucia": "LC", "saint vincent and the grenadines": "VC",
    "sao tome and principe": "ST", "timor-leste": "TL", "east timor": "TL",
    "eswatini": "SZ", "swaziland": "SZ", "north macedonia": "MK", "macedonia": "MK",
    "republic of ireland": "IE", "ireland": "IE", "kyrgyzstan": "KG", "kyrgyz republic": "KG",
    "kingdom of denmark": "DK", "realm of the united kingdom": "GB", "chinese taipei": "TW",
}

COUNTRY_SPECIAL_OUT = {
    "g20_members": {"European Union", "African Union"},
    "african_union_members": {"Sahrawi Arab Democratic Republic"},
}

COUNTRY_MEMBER_ALLOW = {
    "asean_members": {"BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN"},
}

COUNTRY_CHANGES = {
    "nato_members": [("FI", "2023-04-04"), ("SE", "2024-03-07")],
}


def norm_name(text):
    text = str(text).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def load_json_files(pattern):
    for path in sorted(ROOT.glob(pattern)):
        yield json.loads(path.read_text(encoding="utf-8"))


def load_pageprops():
    mapping = {}
    for obj in load_json_files("raw/metadata/pageprops_*.json"):
        query = obj.get("query", {})
        for page in query.get("pages", []):
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            if qid:
                mapping[page["title"]] = qid
        for link in query.get("normalized", []) + query.get("redirects", []):
            if link["to"] in mapping:
                mapping[link["from"]] = mapping[link["to"]]
    return mapping


def load_metadata():
    meta = defaultdict(lambda: {"label": "", "desc": "", "countries": set()})
    for obj in load_json_files("raw/metadata/entity_info_*.json"):
        for row in obj.get("results", {}).get("bindings", []):
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            item = meta[qid]
            if row.get("label"):
                item["label"] = row["label"]["value"]
            if row.get("desc"):
                item["desc"] = row["desc"]["value"]
            if row.get("countryLabel"):
                item["countries"].add(row["countryLabel"]["value"])
    return meta


def record_key(record, pageprops):
    title = record["title"].replace("_", " ")
    if title in SPECIAL_TITLE_KEYS:
        return f"title:{title}"
    return pageprops.get(title) or pageprops.get(record["display"]) or f"title:{title}"


def canonicalise(items, pageprops, metadata):
    displays = defaultdict(Counter)
    aliases = defaultdict(set)
    for records in items:
        for record in records:
            key = record_key(record, pageprops)
            displays[key][record["display"]] += 1
            aliases[key].add(record["display"])
    canonical = {}
    for key, counts in displays.items():
        value = sorted(counts, key=lambda x: (len(x), -counts[x], x))[0]
        canonical[key] = CLUB_VALUE_OVERRIDES.get(key, value)
    used = Counter(canonical.values())
    for key, value in list(canonical.items()):
        if used[value] > 1:
            country = sorted(metadata.get(key, {}).get("countries") or ["?"])[0]
            canonical[key] = f"{value} ({country})"
    return canonical, aliases


def forbidden_list_words(universe):
    terms, acronyms = set(), set()
    items = CLUB_LISTS if universe == "club" else COMPANY_LISTS if universe == "co_sponsor" else COUNTRY_LISTS
    for item in items:
        for text in [item["name"], item["id"].replace("_", " ")] + list(item.get("synonyms") or []):
            if len(text) >= 4:
                terms.add(norm_name(text))
        for token in re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", item["name"] + " " + " ".join(item.get("synonyms") or [])):
            if token not in {"II", "III", "IV"}:
                acronyms.add(token)
    return terms, acronyms


def safe_description(universe, qid, metadata, country, fallback):
    desc = (metadata.get(qid, {}).get("desc") or "").strip().rstrip(".")
    terms, acronyms = forbidden_list_words(universe)
    low = " " + norm_name(desc) + " "
    leaked = any(f" {term} " in low for term in terms) or any(
        token in re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", desc) for token in acronyms)
    if desc and not leaked and sum(ch.isascii() for ch in desc) >= 0.9 * len(desc):
        text = desc[0].upper() + desc[1:]
        if len(text) <= 199:
            return text + "."
    return fallback


def write_universe(name, rows, desc_rows):
    OUT.joinpath("universes").mkdir(parents=True, exist_ok=True)
    attrs = [key[5:] for key in rows[0] if key.startswith("attr:")] if rows else []
    fields = ["value", "entity", "aliases"] + [f"attr:{a}" for a in attrs]
    with (OUT / "universes" / f"{name}.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda r: r["value"]):
            writer.writerow({key: row.get(key, "") for key in fields})
    with (OUT / "universes" / f"{name}.desc.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["value", "description", "source"], delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        for row in sorted(desc_rows, key=lambda r: r["value"]):
            writer.writerow(row)


def build_club_universe(pageprops, metadata):
    all_records = [members_for(item)[1] for item in CLUB_LISTS]
    all_records += [members_for(item)[1] for item in CLUB_UNIVERSE_EXTRAS]
    canonical, aliases = canonicalise(all_records, pageprops, metadata)
    keys = sorted(key for key in canonical if key not in EXCLUDED_CLUB_QIDS)
    rows, desc = [], []
    for key in keys:
        value = canonical[key]
        info = metadata.get(key, {})
        entity = info.get("label") or value
        countries = sorted(info.get("countries") or ["?"])
        country = countries[0]
        rows.append({"value": value, "entity": entity, "aliases": "|".join(sorted(aliases[key] - {value})),
                     "attr:country": country})
        fallback = f"Association football club based in {country}." if country != "?" else "Association football club."
        description = safe_description("club", key, metadata, country, fallback)
        desc.append({"value": value, "description": description,
                     "source": key if key.startswith("Q") else "universe"})
    return canonical, rows, desc


def build_company_universe(pageprops, metadata):
    core, fallback_country = [], defaultdict(set)
    for item in COMPANY_LISTS:
        if item["id"] not in COMPANY_CORE_IDS:
            continue
        records = members_for(item)[1]
        core.append(records)
        for record in records:
            key = record_key(record, pageprops)
            if record.get("country"):
                fallback_country[key].add(record["country"])
            index_country = INDEX_COUNTRY.get(item["id"])
            if index_country and index_country != "Europe":
                fallback_country[key].add(index_country)
    canonical, aliases = canonicalise(core, pageprops, metadata)
    keys = sorted(canonical)
    rows, desc = [], []
    for key in keys:
        value = canonical[key]
        info = metadata.get(key, {})
        entity = info.get("label") or value
        countries = sorted(info.get("countries") or ["?"])
        country = countries[0]
        if country == "?" and fallback_country.get(key):
            country = sorted(fallback_country[key])[0]
        rows.append({"value": value, "entity": entity, "aliases": "|".join(sorted(aliases[key] - {value})),
                     "attr:country": country})
        fallback = f"Publicly traded company based in {country}." if country != "?" else "Publicly traded company."
        description = safe_description("co_sponsor", key, metadata, country, fallback)
        desc.append({"value": value, "description": description,
                     "source": key if key.startswith("Q") else "universe"})
    return canonical, rows, desc


def load_countries():
    data = json.loads((RAW / "countries" / "iso3166.json").read_text(encoding="utf-8"))
    by_code, by_name = {}, {}
    for row in data:
        code = row["alpha-2"].upper()
        by_code[code] = row
        by_name[norm_name(row["name"])] = code
    for name, code in COUNTRY_ALIASES.items():
        by_name[norm_name(name)] = code
    return data, by_code, by_name


def country_code(label, iso, by_name):
    if iso:
        return iso.upper()
    return by_name.get(norm_name(label))


def build_country_universe():
    data, by_code, _ = load_countries()
    rows, desc = [], []
    for row in data:
        code = row["alpha-2"].upper()
        region = row.get("region") or "?"
        rows.append({"value": code, "entity": row["name"], "aliases": "",
                     "attr:region": region})
        desc.append({"value": code,
                     "description": (f"{row['name']} is a country or territory in {region}."
                                     if region != "?" else f"{row['name']} is a country or territory."),
                     "source": "ISO 3166-1 snapshot"})
    return rows, desc, by_code, _


def list_yaml_record(item, universe, members, out_of_universe, source, salience, changes=None):
    return {
        "id": item["id"], "name": item["name"], "synonyms": list(item.get("synonyms") or []),
        "members": sorted(members), "disputed": [], "changes": changes or [],
        "out_of_universe": sorted(out_of_universe), "official_count": len(members) + len(out_of_universe),
        "source": source, "salience": int(salience),
    }


def build_source_lists(template, canonical, universe_values, pageprops, salience, changes_by_id=None):
    result = []
    for item in template:
        page, source_members = members_for(item)
        members, outside, changes = set(), set(), []
        for record in source_members:
            key = record_key(record, pageprops)
            value = canonical.get(key)
            if value in universe_values:
                members.add(value)
            else:
                outside.add(value or record["display"])
        if changes_by_id and item["id"] in changes_by_id:
            for value in changes_by_id[item["id"]]:
                if value in members:
                    changes.append({"value": value, "date": "2026-05-30", "event": "joined"})
        result.append(list_yaml_record(item, template, members, outside, source_url(page),
                                       salience.get(item["id"], 0), changes))
    return result


def build_country_lists(by_name, by_code, org_qids, salience):
    obj = json.loads((RAW / "countries" / "org_memberships.json").read_text(encoding="utf-8"))
    rows_by_org = defaultdict(dict)
    for row in obj["results"]["bindings"]:
        org = row["org"]["value"].rsplit("/", 1)[-1]
        item = row["item"]["value"].rsplit("/", 1)[-1]
        rows_by_org[org][item] = {
            "label": row.get("itemLabel", {}).get("value", item),
            "iso": row.get("iso", {}).get("value"),
        }
    result = []
    for item in COUNTRY_LISTS:
        qid = org_qids[item["id"]]
        members, outside = set(), set()
        for member in rows_by_org.get(qid, {}).values():
            code = country_code(member["label"], member["iso"], by_name)
            allow = COUNTRY_MEMBER_ALLOW.get(item["id"])
            if allow is not None and code not in allow:
                continue
            if code and code in by_code:
                members.add(code)
            elif member["label"] in COUNTRY_SPECIAL_OUT.get(item["id"], set()):
                outside.add(member["label"])
        outside |= COUNTRY_SPECIAL_OUT.get(item["id"], set()) - outside
        record = list_yaml_record(item, None, members, outside,
                                  f"https://www.wikidata.org/wiki/{qid}", salience.get(item["id"], 0))
        record["changes"] = [{"value": value, "date": date, "event": "joined"}
                             for value, date in COUNTRY_CHANGES.get(item["id"], []) if value in members]
        result.append(record)
    return result


def write_lists(club_lists, company_lists, country_lists):
    OUT.joinpath("lists").mkdir(parents=True, exist_ok=True)
    for name, items in (("club", club_lists), ("co_sponsor", company_lists), ("market_country", country_lists)):
        (OUT / "lists" / f"{name}.yaml").write_text(
            yaml.safe_dump(items, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_scenario():
    rules = []
    for field, templates in TEMPLATES.items():
        for template in templates:
            rules.append({"id": template["id"], "field": field, "effect": "exclude_record",
                          "source": template["source"], "rule": template["rule"],
                          "plausible": template["lists"]})
    scenario = {
        "business_process": ("A sports marketing agency reconciles sponsorship activation counts for sponsor "
                             "brands before settlement."),
        "fields": {
            "activations.club": {"universe": "club", "value_form": "self_describing"},
            "activations.co_sponsor": {"universe": "co_sponsor", "value_form": "self_describing"},
            "activations.market_country": {"universe": "market_country", "value_form": "code"},
        },
        "rule_templates": rules,
        "label_nouns": ["settlement lane", "review tag", "audit lane", "handling class", "review code"],
    }
    (OUT / "scenario.yaml").write_text(yaml.safe_dump(scenario, allow_unicode=True, sort_keys=False),
                                       encoding="utf-8")


def write_chains():
    OUT.joinpath("chains").mkdir(parents=True, exist_ok=True)
    field_specs = [
        {"field": "activations.club", "universe": "club",
         "templates": [t["id"] for t in TEMPLATES["activations.club"]]},
        {"field": "activations.co_sponsor", "universe": "co_sponsor",
         "templates": [t["id"] for t in TEMPLATES["activations.co_sponsor"]]},
        {"field": "activations.market_country", "universe": "market_country",
         "templates": [t["id"] for t in TEMPLATES["activations.market_country"]]},
    ]
    for suffix, seed in (("1", 20266106), ("2", 20266107)):
        cfg = {"id": f"SP{suffix}", "dataset": "SP", "seed": seed,
               "period": {"start": 2026, "end": 2026}, "snapshot": "2026-10-16",
               "fields": field_specs, "slots": 5, "probe": {"criterion": "soft"}}
        (OUT / "chains" / f"SP{suffix}.yaml").write_text(
            yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_sources():
    sources = OUT / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    lines = ["# SP public source snapshots", "",
             "Snapshot: 2026-10-16T23:59:59Z. Each Wikipedia page is the newest revision at or before that "
             "timestamp: `action=query&prop=revisions&rvstart=...&rvdir=older` selected the revision and "
             "`action=parse&oldid=...&prop=text|revid` saved the JSON response byte-for-byte. Every page link "
             "below includes its exact oldid.",
             "Wikidata member statements were fetched through the public Query Service; the exact SPARQL is in "
             "`raw/countries/org_memberships.sparql`. Entity labels, descriptions, and countries came from the "
             "Wikidata Query Service using the saved QID sets.", "",
             "Wikipedia pages:"]
    for path in sorted((RAW / "pages").glob("*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))["parse"]
        lines.append(f"- `{path.name}`: {source_url(page)}")
    lines += ["- `raw/countries/iso3166.json`: "
              "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json",
              "- `raw/countries/org_memberships.json`: generated by "
              "https://query.wikidata.org/sparql using `raw/countries/org_memberships.sparql`.",
              "- `raw/metadata/*.json`: MediaWiki pageprops and Wikidata label/description/country queries."]
    lines += ["", "To re-fetch (optionally through an HTTP proxy: `export HTTPS_PROXY=<proxy> "
              "HTTP_PROXY=<proxy>`), run "
              "`python fetch_pages.py` (it stages a complete revision set before replacing `raw/pages/`), "
              "`python fetch_metadata.py`, and `python fetch_salience.py`."]
    lines += ["", "Pageviews: Wikimedia REST API, monthly buckets 2025-10 through 2026-09, saved under "
              "`inputs/SP/salience/raw/`.", "",
              "The generated dataset is category (b): `dataset.py` creates the synthetic sponsorship world from "
              "the seed; the public sources supply only the real-world value universes and closed lists."]
    (sources / "FETCH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    hashes = []
    for path in sorted(RAW.rglob("*")):
        if path.is_file():
            hashes.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}")
    for path in sorted((OUT / "salience" / "raw").rglob("*")):
        if path.is_file():
            hashes.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}")
    (sources / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="utf-8")


def main():
    pageprops = load_pageprops()
    metadata = load_metadata()
    salience = build_salience()
    club_canonical, club_rows, club_desc = build_club_universe(pageprops, metadata)
    company_canonical, company_rows, company_desc = build_company_universe(pageprops, metadata)
    country_rows, country_desc, by_code, by_name = build_country_universe()
    write_universe("club", club_rows, club_desc)
    write_universe("co_sponsor", company_rows, company_desc)
    write_universe("market_country", country_rows, country_desc)
    club_values = {row["value"] for row in club_rows}
    company_values = {row["value"] for row in company_rows}
    changes = {"ucl_winners": sorted(v for v in club_values if "Paris Saint-Germain" in v)}
    club_lists = build_source_lists(CLUB_LISTS, club_canonical, club_values, pageprops,
                                    salience.get("club", {}), changes)
    company_lists = build_source_lists(COMPANY_LISTS, company_canonical, company_values, pageprops,
                                       salience.get("co_sponsor", {}))
    org_qids = json.loads((RAW / "metadata" / "org_qids.json").read_text(encoding="utf-8"))
    country_lists = build_country_lists(by_name, by_code, org_qids, salience.get("market_country", {}))
    write_lists(club_lists, company_lists, country_lists)
    write_scenario()
    write_chains()
    write_sources()
    print(json.dumps({
        "club_values": len(club_rows), "company_values": len(company_rows), "country_values": len(country_rows),
        "club_lists": len(club_lists), "company_lists": len(company_lists), "country_lists": len(country_lists),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
