#!/usr/bin/env python3
"""Append the WS2 language and CWE lists to lists/*.yaml. Reads only raw/ (+ the pageview JSON in salience/raw/)."""
import csv
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI2 = RAW / "wiki_ws2"
NS = "{http://cwe.mitre.org/cwe-7}"

CHARTER_PAGE = "European_Charter_for_Regional_or_Minority_Languages"
CHARTER = [  # list id, flagcountry row in the charter table
    ("austria_charter_languages", "Austria"),
    ("bosnia_charter_languages", "Bosnia and Herzegovina"),
    ("croatia_charter_languages", "Croatia"),
    ("finland_charter_languages", "Finland"),
    ("hungary_charter_languages", "Hungary"),
    ("poland_charter_languages", "Poland"),
    ("romania_charter_languages", "Romania"),
    ("serbia_charter_languages", "Serbia"),
    ("slovakia_charter_languages", "Slovakia"),
    ("slovenia_charter_languages", "Slovenia"),
    ("spain_charter_languages", "Spain"),
    ("ukraine_charter_languages", "Ukraine"),
]

# display name used in the charter table -> ISO 639-1 code, or None when the language has no ISO 639-1 code
NAME2CODE = {
    "Albanian": "sq", "Armenian": "hy", "Aragonese": "an", "Aranese": "oc", "Occitan": "oc", "Basque": "eu",
    "Belarusian": "be", "Bosnian": "bs", "Bulgarian": "bg", "Burgenland Croatian": "hr",
    "Catalan": "ca", "Croatian": "hr", "Czech": "cs", "Danish": "da", "French": "fr",
    "Galician": "gl", "German": "de", "Greek": "el", "Hebrew": "he", "Hungarian": "hu",
    "Irish": "ga", "Italian": "it", "Lithuanian": "lt", "Macedonian": "mk", "Norwegian": "no",
    "Polish": "pl", "Portuguese": "pt", "Romanian": "ro", "Russian": "ru", "Serbian": "sr",
    "Slovak": "sk", "Slovene": "sl", "Spanish": "es", "Swedish": "sv", "Tatar": "tt",
    "Turkish": "tr", "Ukrainian": "uk", "Valencian": "ca", "Yiddish": "yi", "North Sami": "se",
    "Sardinian": "sc", "Welsh": "cy", "Cornish": "kw", "Manx Gaelic": "gv",
    "Scottish Gaelic": "gd", "Frisian": "fy", "Limburgish": "li", "English": "en",
    "Azerbaijani": "az", "Kazakh": "kk", "Kyrgyz": "ky", "Turkmen": "tk", "Uzbek": "uz",
    "Tajik": "tg", "Persian": "fa", "Pashto": "ps", "Ossetian": "os", "Kurdish": "ku",
    "Romani": None, "Rusyn": None, "Ladino": None, "Karaim": None, "Kashub": None, "Lemko": None,
    "Bunjevac": None, "Vlach": None, "Boyash Romanian": None, "Istro-Romanian": None,
    "Inari Sami": None, "Karelian": None, "Skolt Sami": None, "Lule Sami": None, "South Sami": None,
    "Kven": None, "Meänkieli": None, "Crimean Tatar": None, "Gagauz": None, "Krymchak": None,
    "Rumeika": None, "Urum": None, "Lower Sorbian": None, "Upper Sorbian": None,
    "North Frisian": None, "Saterland Frisian": None, "Low German": None, "Low Saxon": None,
    "Papiamento": None, "Yenish": None, "Amazigh": None, "Asturian": None, "Leonese": None,
    "Extremaduran": None, "Fala": None, "Ceuta Arabic": None, "Franco-Provençal": None,
    "Friulian": None, "Ladin": None, "Moravian Croatian": "hr", "Cypriot Maronite Arabic": None,
    "Assyrian": None, "Kurdish": "ku", "Yezidi": None, "Scots": None, "Ulster-Scots": None,
    "Manx": None,
}


def wikitext(name):
    return (WIKI2 / (name + ".wikitext")).read_text(encoding="utf-8")


def iso_universe():
    """ISO 639-1 codes that the dataset's universe keeps (living and constructed languages)."""
    lines = (RAW / "wiki" / "List_of_ISO_639-1_codes.wikitext").read_text(encoding="utf-8").splitlines()
    out, iso3 = set(), {}
    for i, line in enumerate(lines):
        m = re.match(r'\|\s*id="([a-z]{2})"\s*\|\s*(.*?)\s*\|\|\s*<code>\{\{iso639-1\|[a-z]{2}\}\}</code>\s*\|\|\s*(?:colspan="2"\s*\|\s*)?<code>([a-z]{3})</code>', line)
        if not m:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        kind = [p.strip() for p in nxt.split("||")][1].strip() if len(nxt.split("||")) > 1 else ""
        iso3[m.group(3)] = m.group(1)
        if kind in ("Living", "Constructed"):
            out.add(m.group(1))
    return out, iso3


def cwe_universe():
    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    root = ET.parse(io.BytesIO(z.read(name))).getroot()
    out = set()
    for w in root.find(NS + "Weaknesses").findall(NS + "Weakness"):
        if w.get("Status") == "Deprecated" or w.get("Abstraction") == "Pillar":
            continue
        out.add("CWE-" + w.get("ID"))
    return out, root


def salience(title):
    if not title:
        return 0
    path = ROOT / "salience" / "raw" / ("pv_" + title.replace("/", "_") + ".json")
    if not path.exists():
        return 0
    return sum(int(x["views"]) for x in json.loads(path.read_text(encoding="utf-8")).get("items", []))


def load_base(name):
    return yaml.safe_load((RAW / f"base_{name}.yaml").read_text(encoding="utf-8"))


def entry(lid, name, members, out_names, official_count, source, title, synonyms=None):
    return dict(id=lid, name=name, synonyms=synonyms or [], members=sorted(members), disputed=[],
                changes=[], out_of_universe=sorted(out_names), official_count=official_count,
                source=source, salience=salience(title))


def parse_charter_table(country):
    """Rows of the charter table for one state: [(display name, 1-based line in the wikitext)]."""
    lines = wikitext(CHARTER_PAGE).splitlines()
    starts = []
    for i, line in enumerate(lines):
        m = re.match(r'\|rowspan="(\d+)"\|\{\{flagcountry\|([^}]+)\}\}', line)
        if m:
            starts.append((i, int(m.group(1)), m.group(2)))
    for k, (i, n, name) in enumerate(starts):
        if name != country:
            continue
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        rows = []
        for j in range(i + 1, end):
            m = re.match(r'\|\s*"?\[\[([^\]|]+)(?:\|([^\]]*))?\]\]', lines[j])
            if m:
                rows.append(((m.group(2) or m.group(1)).strip(), m.group(1).strip(), j + 1))
        assert len(rows) == n, (country, len(rows), n)
        return rows
    raise KeyError(country)


def links_in(text):
    return [((m.group(2) or m.group(1)).strip()) for m in re.finditer(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", text)]


def country_lists():
    out = []
    # Spain: official languages in the infobox of "Languages of Spain"
    text = wikitext("Languages_of_Spain")
    line = next(l for l in text.splitlines() if re.match(r"\s*\|\s*official\s*=", l))
    names = links_in(line.split("{{efn")[0])
    members, seen = [], set()
    for nm in names:
        code = NAME2CODE[nm]
        if code and code not in seen:
            seen.add(code)
            members.append(code)
    assert len(members) == 5, members
    out.append(entry("spain_official_languages", "Official languages of Spain (Spanish and the co-official languages of its autonomous communities)",
                     members, [], 5, "https://en.wikipedia.org/wiki/Languages_of_Spain", "Languages_of_Spain"))
    # Italy: the twelve languages recognised by Law 482/1999
    text = wikitext("Languages_of_Italy")
    key = "Twelve languages are officially recognized as spoken by [[minority language|linguistic minorities]]:"
    assert key in text, "law 482 sentence not found"
    names, i = [], text.index(key) + len(key)
    while i < len(text):
        if text.startswith("[[", i):
            m = re.match(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", text[i:])
            names.append((m.group(2) or m.group(1)).strip())
            i += m.end()
        elif text.startswith("<ref", i):
            m = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", re.S).match(text, i)
            i = m.end()
        elif text.startswith("{{", i):
            depth, i = 0, i
            while i < len(text):
                if text.startswith("{{", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("}}", i):
                    depth, i = depth - 1, i + 2
                    if depth == 0:
                        break
                else:
                    i += 1
        elif text[i] == ".":
            break
        else:
            i += 1
    members, again, out_names = [], set(), []
    for nm in names:
        code = NAME2CODE[nm]
        if code is None:
            out_names.append(nm)
        elif code not in again:
            again.add(code)
            members.append(code)
    assert len(members) == 9 and len(members) + len(out_names) == 12, (members, out_names)
    out.append(entry("italy_law_482_languages", "Languages recognised as minority languages by Italian Law 482/1999",
                     members, out_names, 12, "https://en.wikipedia.org/wiki/Languages_of_Italy", "Languages_of_Italy"))
    # Vojvodina: Serbian plus the five minority languages of the provincial administration
    text = wikitext("Languages_of_Vojvodina")
    m = re.search(r"there are five recognized minority languages in the official use by the provincial administration in Vojvodina:\s*(.*?)\.", text)
    assert m, "vojvodina sentence not found"
    out_names = [nm for nm in links_in(m.group(1))]
    members, out_u = ["sr"], []
    for nm in out_names:
        code = NAME2CODE[nm]
        if code is None:
            out_u.append(nm)
        else:
            members.append(code)
    assert len(members) == 5 and len(members) + len(out_u) == 6, (members, out_u)
    out.append(entry("vojvodina_official_languages", "Languages in official use by the provincial administration of Vojvodina",
                     members, out_u, 6, "https://en.wikipedia.org/wiki/Languages_of_Vojvodina", "Languages_of_Vojvodina"))
    # Organization of Turkic States: official languages in the infobox
    text = wikitext("Organization_of_Turkic_States")
    line = next(l for l in text.splitlines() if re.match(r"\s*\|\s*official_languages\s*=", l))
    members = []
    for nm in links_in(line):
        members.append(NAME2CODE[nm])
    assert len(members) == 5 and all(members), members
    out.append(entry("ots_official_languages", "Official languages of the Organization of Turkic States",
                     members, [], 5, "https://en.wikipedia.org/wiki/Organization_of_Turkic_States",
                     "Organization_of_Turkic_States"))
    return out


BRANCHES = [  # wikidata item, list id, English name, wikipedia article
    ("Q106085", "north_germanic_languages", "North Germanic languages", "North_Germanic_languages"),
    ("Q1792570", "west_scandinavian_languages", "West Scandinavian languages", "West_Scandinavian_languages"),
    ("Q961559", "nguni_languages", "Nguni languages", "Nguni_languages"),
    ("Q500394", "gallo_romance_languages", "Gallo-Romance languages", "Gallo-Romance_languages"),
    ("Q980498", "southern_bantu_languages", "Southern Bantu languages", "Southern_Bantu_languages"),
    ("Q954321", "gallo_iberian_languages", "Gallo-Iberian languages", "Gallo-Iberian_languages"),
]


def branch_lists(uni):
    data = json.loads((RAW / "wikidata" / "language_ancestors_all.json").read_text(encoding="utf-8"))["results"]["bindings"]
    by = {}
    for b in data:
        qid = b["anc"]["value"].rsplit("/", 1)[-1]
        by.setdefault(qid, set()).add(b["code"]["value"])
    out = []
    for qid, lid, name, page in BRANCHES:
        codes = by[qid]
        members = sorted(c for c in codes if c in uni)
        outcodes = sorted(c for c in codes if c not in uni)
        assert len(members) >= 5, (lid, members)
        out.append(entry(lid, name, members, outcodes, len(codes),
                         "https://www.wikidata.org/wiki/" + qid, page))
    return out


CWE_LISTS = [  # category id in the CWE catalogue, list id, name, wikipedia article
    ("1228", "cwe699_api_errors", "CWE-699 Software Development category: API / Function Errors", "Application_programming_interface"),
    ("1210", "cwe699_audit_logging", "CWE-699 Software Development category: Audit / Logging Errors", "Audit_log"),
    ("840", "cwe699_business_logic", "CWE-699 Software Development category: Business Logic Errors", "Business_logic"),
    ("557", "cwe699_concurrency", "CWE-699 Software Development category: Concurrency Issues", "Concurrency_(computer_science)"),
    ("1214", "cwe699_data_integrity", "CWE-699 Software Development category: Data Integrity Issues", "Data_integrity"),
    ("1218", "cwe699_memory_buffer", "CWE-699 Software Development category: Memory Buffer Errors", "Memory_safety"),
    ("189", "cwe699_numeric", "CWE-699 Software Development category: Numeric Errors", "Integer_overflow"),
    ("399", "cwe699_resource_management", "CWE-699 Software Development category: Resource Management Errors", "Resource_management"),
    ("885", "sfp_risky_values", "SFP Primary Cluster: Risky Values", ""),
    ("897", "sfp_entry_points", "SFP Primary Cluster: Entry Points", "Entry_point"),
    ("899", "sfp_access_control", "SFP Primary Cluster: Access Control", "Access_control"),
    ("906", "sfp_ui", "SFP Primary Cluster: UI", "User_interface"),
]


def cwe_lists():
    uni, root = cwe_universe()
    weak = {w.get("ID") for w in root.find(NS + "Weaknesses").findall(NS + "Weakness")}
    cats = {c.get("ID"): c for c in root.find(NS + "Categories").findall(NS + "Category")}

    def members(cid, seen=None):
        seen = set() if seen is None else seen
        cat = cats.get(cid)
        if cat is None:
            return seen
        for m in cat.findall(f"{NS}Relationships/{NS}Has_Member"):
            mid = m.get("CWE_ID")
            if mid in cats:
                if mid not in seen:
                    seen.add(mid)
                    members(mid, seen)
            else:
                seen.add(mid)
        return seen

    out = []
    for cid, lid, name, page in CWE_LISTS:
        allm = {m for m in members(cid) if m in weak}
        inu = sorted("CWE-" + m for m in allm if "CWE-" + m in uni)
        outu = sorted("CWE-" + m for m in allm if "CWE-" + m not in uni)
        assert len(inu) >= 5, (lid, len(inu))
        out.append(entry(lid, name, inu, outu, len(allm),
                         "https://cwe.mitre.org/data/definitions/%s.html" % cid, page))
    return out


def main():
    uni, _ = iso_universe()
    lang = load_base("language")
    charter = []
    for lid, country in CHARTER:
        rows = parse_charter_table(country)
        members, out_names, seen = [], [], set()
        for display, target, _ in rows:
            key = re.sub(r"\s+language$", "", target)
            code = NAME2CODE[key] if key in NAME2CODE else NAME2CODE[display]
            if code is None:
                out_names.append(display)
            elif code in seen:
                continue
            else:
                seen.add(code)
                members.append(code)
        assert len(members) >= 5, (lid, members)
        charter.append(entry(lid, "Languages protected under the European Charter for Regional or Minority Languages in %s" % country,
                             members, out_names, len(members) + len(out_names),
                             "https://en.wikipedia.org/wiki/" + CHARTER_PAGE, CHARTER_PAGE))
    new_lang = charter + country_lists() + branch_lists(uni)
    have = {x["id"] for x in lang}
    assert not (have & {x["id"] for x in new_lang}), have & {x["id"] for x in new_lang}
    (ROOT / "lists" / "language.yaml").write_text(
        yaml.safe_dump(lang + new_lang, allow_unicode=True, sort_keys=False), encoding="utf-8")

    cwe = load_base("cwe")
    new_cwe = cwe_lists()
    have = {x["id"] for x in cwe}
    assert not (have & {x["id"] for x in new_cwe}), have & {x["id"] for x in new_cwe}
    (ROOT / "lists" / "cwe.yaml").write_text(
        yaml.safe_dump(cwe + new_cwe, allow_unicode=True, sort_keys=False), encoding="utf-8")
    for x in new_lang + new_cwe:
        print("%-28s %3d %3d %8d %s" % (x["id"], len(x["members"]), x["official_count"], x["salience"], x["source"]))


if __name__ == "__main__":
    main()
