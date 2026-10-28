#!/usr/bin/env python3
"""Build universes/language.tsv and lists/language.yaml from raw/ (ISO 639-1 list, Glottolog, Wikidata, Wikipedia)."""
import csv, io, json, re, zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI = RAW / "wiki"

BRANCHES = [  # wikidata item, list id, English name
    ("Q19814", "romance_languages", "Romance languages"),
    ("Q21200", "germanic_languages", "Germanic languages"),
    ("Q23526", "slavic_languages", "Slavic languages"),
    ("Q25293", "celtic_languages", "Celtic languages"),
    ("Q33514", "indo_iranian_languages", "Indo-Iranian languages"),
    ("Q79890", "finno_ugric_languages", "Finno-Ugric languages"),
    ("Q34049", "semitic_languages", "Semitic languages"),
    ("Q33146", "bantu_languages", "Bantu languages"),
    ("Q33577", "indo_aryan_languages", "Indo-Aryan languages"),
    ("Q26721", "west_germanic_languages", "West Germanic languages"),
    ("Q146665", "south_slavic_languages", "South Slavic languages"),
    ("Q147356", "balto_slavic_languages", "Balto-Slavic languages"),
    ("Q131848", "italic_languages", "Italic languages"),
]

ORG_LISTS = [  # id, name, page, codes, official count
    ("un_official_languages", "Official languages of the United Nations",
     "Official_languages_of_the_United_Nations", "ar zh en fr ru es", 6),
    ("eu_official_languages", "Official languages of the European Union",
     "Languages_of_the_European_Union",
     "bg hr cs da nl en et fi fr de el hu ga it lv lt mt pl pt ro sk sl es sv", 24),
    ("au_working_languages", "Working languages of the African Union",
     "Languages_of_the_African_Union", "ar en fr pt es sw", 6),
    ("nordic_council_languages", "Working languages of the Nordic Council",
     "Nordic_Council", "da fi is no sv", 5),
    ("osce_official_languages", "Official languages of the OSCE",
     "Organization_for_Security_and_Co-operation_in_Europe", "en fr de it ru es", 6),
]

STATE_LISTS = [  # id, name, page, in-universe codes, out-of-universe names, official count
    ("india_eighth_schedule", "Languages in the Eighth Schedule to the Constitution of India",
     "List_of_official_languages_by_country_and_territory", "as bn gu hi kn ks ml mr ne or pa sd ta te ur",
     ["Bodo", "Dogri", "Konkani", "Maithili", "Manipuri", "Sanskrit", "Santali"], 22),
    ("south_africa_official", "Official languages of South Africa",
     "List_of_official_languages_by_country_and_territory",
     "af en nr st ss ts tn ve xh zu", ["Northern Sotho", "South African Sign Language"], 12),
    ("zimbabwe_official", "Official languages of Zimbabwe",
     "List_of_official_languages_by_country_and_territory",
     "en ny nd sn st tn ve xh",
     ["Kalanga", "Khoisan", "Nambya", "Ndau", "Shangani", "Sign language", "Sena", "Tonga"], 16),
]

FAMILY_FIX = {  # macrolanguages missing from Glottolog's iso639P3code column
    "ar": "Afro-Asiatic", "az": "Turkic", "zh": "Sino-Tibetan", "et": "Uralic", "gn": "Tupian",
    "iu": "Eskimo-Aleut", "kr": "Nilo-Saharan", "kg": "Atlantic-Congo", "mg": "Austronesian",
    "ms": "Austronesian", "oj": "Algic", "or": "Indo-European", "om": "Afro-Asiatic",
    "fa": "Indo-European", "qu": "Quechuan", "sc": "Indo-European", "sw": "Atlantic-Congo",
    "yi": "Indo-European",
}

SCRIPT_PRIORITY = ["Latin", "Cyrillic", "Arabic", "Han", "Devanagari", "Bengali", "Ethiopic", "Greek",
                   "Hebrew", "Armenian", "Georgian", "Hangul", "Kana", "Thai", "Tamil", "Telugu",
                   "Kannada", "Malayalam", "Gujarati", "Gurmukhi", "Odia", "Sinhala", "Myanmar",
                   "Khmer", "Lao", "Tibetan", "Mongolian", "Syriac", "Thaana", "Tifinagh", "Cherokee"]


def norm_script(label):
    if not label:
        return "?"
    low = label.lower()
    table = [("latin", "Latin"), ("cyrillic", "Cyrillic"), ("arabic", "Arabic"), ("han", "Han"),
             ("chinese", "Han"), ("devanagari", "Devanagari"), ("bengali", "Bengali"),
             ("geʽez", "Ethiopic"), ("ge'ez", "Ethiopic"), ("ethiopic", "Ethiopic"), ("greek", "Greek"),
             ("hebrew", "Hebrew"), ("armenian", "Armenian"), ("georgian", "Georgian"),
             ("hangul", "Hangul"), ("korean", "Hangul"), ("kana", "Kana"), ("japanese", "Kana"),
             ("thai", "Thai"), ("tamil", "Tamil"), ("telugu", "Telugu"), ("kannada", "Kannada"),
             ("malayalam", "Malayalam"), ("gujarati", "Gujarati"), ("gurmukhi", "Gurmukhi"),
             ("oriya", "Odia"), ("odia", "Odia"), ("sinhala", "Sinhala"), ("myanmar", "Myanmar"),
             ("burmese", "Myanmar"), ("khmer", "Khmer"), ("lao", "Lao"), ("tibetan", "Tibetan"),
             ("mongolian", "Mongolian"), ("syriac", "Syriac"), ("thaana", "Thaana"),
             ("tifinagh", "Tifinagh"), ("cherokee", "Cherokee")]
    for pat, name in table:
        if pat in low:
            return name
    return "?"



def _salience():
    import csv as _csv
    path = ROOT / "salience" / "language.tsv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return {r["concept_id"]: int(float(r["pageviews_12m"] or 0))
                for r in _csv.DictReader(fh, delimiter="\t")}

def main():
    lines = (WIKI / "List_of_ISO_639-1_codes.wikitext").read_text(encoding="utf-8").splitlines()
    rows = []
    for i, l in enumerate(lines):
        m = re.match(r'\|\s*id="([a-z]{2})"\s*\|\s*(.*?)\s*\|\|\s*<code>\{\{iso639-1\|[a-z]{2}\}\}</code>\s*\|\|\s*(?:colspan="2"\s*\|\s*)?<code>([a-z]{3})</code>', l)
        if not m:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        parts = [p.strip() for p in nxt.split("||")]
        typ = parts[1].strip() if len(parts) > 1 else ""
        name = re.sub(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", lambda x: x.group(2) or x.group(1), m.group(2))
        name = re.sub(r"<[^>]+>", "", name).replace("&nbsp;", " ").strip()
        rows.append(dict(code=m.group(1), name=name, iso3=m.group(3), kind=typ, line=i + 1))

    universe_rows = [r for r in rows if r["kind"] in ("Living", "Constructed")]

    z = zipfile.ZipFile(RAW / "glottolog_languoid.csv.zip")
    g = list(csv.DictReader(io.TextIOWrapper(z.open("languoid.csv"), encoding="utf-8")))
    fam_name = {x["id"]: x["name"] for x in g}
    by_iso = {x["iso639P3code"]: x for x in g if x["iso639P3code"]}

    scripts = json.load(open(RAW / "wikidata" / "language_scripts.json", encoding="utf-8"))["results"]["bindings"]
    script_of = {}
    for b in scripts:
        if "scriptLabel" in b:
            script_of.setdefault(b["code"]["value"], []).append(b["scriptLabel"]["value"])

    uni = {}
    for r in universe_rows:
        code = r["code"]
        fam = "?"
        if r["iso3"] in by_iso:
            fam = fam_name.get(by_iso[r["iso3"]]["family_id"], "?")
        if fam == "Artificial Language":
            fam = "Constructed"
        if fam in ("?", None) and code in FAMILY_FIX:
            fam = FAMILY_FIX[code]
        if code in FAMILY_FIX and fam == "?":
            fam = FAMILY_FIX[code]
        norms = [norm_script(s) for s in script_of.get(code, [])]
        norms = [s for s in norms if s != "?"]
        pick = next((s for s in SCRIPT_PRIORITY if s in norms), norms[0] if norms else "?")
        uni[code] = dict(code=code, name=r["name"], family=fam, script=pick)

    (ROOT / "universes").mkdir(exist_ok=True)
    with (ROOT / "universes" / "language.tsv").open("w", encoding="utf-8") as fh:
        fh.write("value\tentity\tattr:family\tattr:script\n")
        for code in sorted(uni):
            r = uni[code]
            fh.write("%s\t%s\t%s\t%s\n" % (code, r["name"].replace("\t", " "), r["family"], r["script"]))

    branches = json.load(open(RAW / "wikidata" / "language_ancestors_all.json", encoding="utf-8"))["results"]["bindings"]
    by_branch = {}
    for b in branches:
        by_branch.setdefault(b["anc"]["value"].rsplit("/", 1)[-1], set()).add(b["code"]["value"])

    lists = []
    for qid, lid, name in BRANCHES:
        codes = by_branch.get(qid, set())
        members = sorted(c for c in codes if c in uni)
        out = sorted(c for c in codes if c not in uni)
        if len(members) < 5:
            continue
        lists.append(dict(id=lid, name=name, synonyms=[], members=members, disputed=[], changes=[],
                          out_of_universe=out, official_count=len(codes),
                          source="https://www.wikidata.org/wiki/" + qid))
    for lid, name, page, codes, official in ORG_LISTS:
        codes = codes.split()
        members = sorted(c for c in codes if c in uni)
        out = sorted(c for c in codes if c not in uni)
        lists.append(dict(id=lid, name=name, synonyms=[], members=members, disputed=[], changes=[],
                          out_of_universe=out, official_count=official,
                          source="https://en.wikipedia.org/wiki/" + page))
    for lid, name, page, codes, out_names, official in STATE_LISTS:
        codes = codes.split()
        members = sorted(c for c in codes if c in uni)
        out = sorted(c for c in codes if c not in uni) + sorted(out_names)
        lists.append(dict(id=lid, name=name, synonyms=[], members=members, disputed=[], changes=[],
                          out_of_universe=out, official_count=official,
                          source="https://en.wikipedia.org/wiki/" + page))

    (ROOT / "lists").mkdir(exist_ok=True)
    sal = _salience()
    for x in lists:
        x["salience"] = sal.get(x["id"], 0)
    (ROOT / "lists" / "language.yaml").write_text(
        yaml.safe_dump(lists, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("universe", len(uni), "lists", len(lists))
    for x in lists:
        print(x["id"], len(x["members"]), x["official_count"], x["out_of_universe"])


if __name__ == "__main__":
    main()
