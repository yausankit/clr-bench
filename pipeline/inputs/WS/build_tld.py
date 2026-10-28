#!/usr/bin/env python3
"""Build universes/tld.tsv and lists/tld.yaml from raw/ (IANA root zone + ISO 3166-1 + Wikipedia rosters)."""
import html, re, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI = RAW / "wiki"

# ---- organization rosters: (list id, page file, name, ISO alpha-2 codes, official count, notes) ----
ROSTERS = [
    ("eu_member_cctlds", "Member_state_of_the_European_Union", "European Union member states",
     "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE", 27),
    ("schengen_cctlds", "Schengen_Area", "Schengen Area participating states",
     "AT BE BG HR CZ DK EE FI FR DE GR HU IS IT LV LI LT LU MT NL NO PL PT RO SK SI ES SE CH", 29),
    ("eea_cctlds", "European_Economic_Area", "European Economic Area contracting parties",
     "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL NO PT RO SK SI ES SE IS LI", 30),
    ("eurozone_cctlds", "Eurozone", "Eurozone member states",
     "AT BE BG HR CY EE FI FR DE GR IE IT LV LT LU MT NL PT SK SI ES", 21),
    ("eu_candidate_cctlds", "Enlargement_of_the_European_Union", "European Union candidate countries",
     "AL BA GE MD ME MK RS TR UA", 9),
    ("nato_cctlds", "NATO", "NATO member states",
     "AL BE BG CA HR CZ DK EE FI FR DE GR HU IS IT LV LT LU ME NL MK NO PL PT RO SK SI ES SE TR GB US", 32),
    ("oecd_cctlds", "OECD", "OECD member states",
     "AU AT BE CA CL CO CR CZ DK EE FI FR DE GR HU IS IE IL IT JP KR LV LT LU MX NL NZ NO PL PT SK SI ES SE CH TR GB US", 38),
    ("g7_cctlds", "Group_of_Seven", "Group of Seven members",
     "CA FR DE IT JP GB US EU", 8),
    ("g20_cctlds", "G20", "G20 members",
     "AR AU BR CA CN FR DE IN ID IT JP MX RU SA ZA KR TR GB US EU", 21),
    ("commonwealth_cctlds", "Commonwealth_of_Nations", "Commonwealth of Nations member states",
     "AG AU BD BB BZ BW BN CM CA CY DM SZ FJ GA GM GH GD GY IN JM KE KI LS MW MY MV MT MU MZ NA NR NZ NG PK PG RW KN LC VC WS SC SL SG SB ZA LK TZ BS TG TO TT TV UG GB VU ZM", 56),
    ("asean_cctlds", "ASEAN", "ASEAN member states",
     "BN KH ID LA MY MM PH SG TH TL VN", 11),
    ("gcc_cctlds", "Gulf_Cooperation_Council", "Gulf Cooperation Council member states",
     "BH KW OM QA SA AE", 6),
    ("brics_cctlds", "BRICS", "BRICS member states",
     "BR CN EG ET IN ID IR RU ZA AE", 10),
    ("mercosur_cctlds", "Mercosur", "Mercosur full member states",
     "AR BO BR PY UY", 5),
    ("caricom_cctlds", "Caribbean_Community", "Caribbean Community member states",
     "AG BS BB BZ DM GD GY HT JM MS KN LC VC SR TT", 15),
    ("african_union_cctlds", "African_Union", "African Union member states",
     "DZ AO BJ BW BF BI CM CV CF TD KM CD CG DJ EG GQ ER SZ ET GA GM GH GN GW CI KE LS LR LY MG MW ML MR MU MA MZ NA NE NG RW ST SN SC SL SO ZA SS SD TZ TG TN UG ZM ZW EH", 55),
    ("apec_cctlds", "Asia-Pacific_Economic_Cooperation", "APEC member economies",
     "AU BN CA CL CN HK ID JP MY MX NZ PG PE PH RU SG KR TW TH US VN", 21),
    ("pif_cctlds", "Pacific_Islands_Forum", "Pacific Islands Forum member states",
     "AU CK FJ PF KI MH FM NR NC NZ NU PW PG WS SB TO TV VU", 18),
    ("cplp_cctlds", "Community_of_Portuguese_Language_Countries", "CPLP member states",
     "AO BR CV GQ GW MZ PT ST TL", 9),
    ("arab_league_cctlds", "Arab_League", "Arab League member states",
     "DZ BH KM DJ EG IQ JO KW LB LY MR MA OM PS QA SA SO SD SY TN AE YE", 22),
    ("saarc_cctlds", "South_Asian_Association_for_Regional_Cooperation", "SAARC member states",
     "AF BD BT IN MV NP PK LK", 8),
    ("eaeu_cctlds", "Eurasian_Economic_Union", "Eurasian Economic Union member states",
     "AM BY KZ KG RU", 5),
    ("sica_cctlds", "Central_American_Integration_System", "SICA member states",
     "BZ CR DO GT HN NI PA SV", 8),
    ("five_eyes_cctlds", "Five_Eyes", "Five Eyes member states",
     "US GB CA AU NZ", 5),
]

CONT_ORDER = ["Africa", "Europe", "Asia", "North America", "South America", "Oceania"]
CONT_OVERRIDE = {"RU": "Europe", "TR": "Asia", "KZ": "Asia", "EG": "Africa", "ID": "Asia",
                 "CY": "Europe", "AM": "Asia", "AZ": "Asia", "GE": "Asia", "CO": "South America"}


def parse_tlds():
    out = []
    for line in (RAW / "tlds-alpha-by-domain.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line.lower())
    return out


def parse_root_db():
    txt = (RAW / "iana_root_db.html").read_text(encoding="utf-8")
    rows = re.findall(r"<tr>(.*?)</tr>", txt, re.S)[1:]
    out = {}
    for r in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        if len(tds) < 3:
            continue
        cell = lambda x: html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
        tld = cell(tds[0]).lstrip(".")
        out[tld.lower()] = cell(tds[2])
    return out


def parse_iso():
    txt = (WIKI / "ISO_3166-1_alpha-2.wikitext").read_text(encoding="utf-8").splitlines()
    out = {}
    for i, l in enumerate(txt, 1):
        mm = re.match(r'\|\s*id="([A-Z]{2})"\s*\|\s*\[\[ISO 3166-2:[A-Z]{2}\|\{\{mono\|[A-Z]{2}\}\}\]\]\s*\|\|\s*(.*?)\s*\|\|', l)
        if not mm:
            continue
        code, rest = mm.group(1), mm.group(2)
        name = re.sub(r"<!--.*?-->", "", rest)
        name = re.sub(r"\{\{sort\|[^|]+\|([^}]+)\}\}", r"\1", name)
        name = re.sub(r"\{\{[^}]*\}\}", "", name)
        name = re.sub(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", lambda x: x.group(2) or x.group(1), name).strip()
        tlds = [t.lstrip(".").lower() for t in re.findall(r"\[\[(\.\w+)\]\]", l)]
        out[code] = (name, tlds, i)
    return out


def parse_continents():
    txt = (WIKI / "List_of_sovereign_states_and_dependent_territories_by_continent.wikitext").read_text(encoding="utf-8").splitlines()
    cur, cont = None, {}
    for l in txt:
        m = re.match(r"^== *([A-Za-z ]+) *==$", l)
        if m:
            cur = m.group(1).strip()
            continue
        m = re.match(r'\|\s*style="vertical-align:top[^"]*"\s*\|\s*\{\{anchor\|([^}]+)\}\}.*?\{\{flag\|([^}|]+)', l)
        if m and cur in CONT_ORDER:
            cont.setdefault(m.group(2).strip(), set()).add(cur)
    return cont



def _salience():
    import csv as _csv
    path = ROOT / "salience" / "tld.tsv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return {r["concept_id"]: int(float(r["pageviews_12m"] or 0))
                for r in _csv.DictReader(fh, delimiter="\t")}

def main():
    tlds = parse_tlds()
    rootdb = parse_root_db()
    iso = parse_iso()
    cont_by_name = parse_continents()

    # country name -> continent, mapped through ISO names (plus a few Wikipedia spellings)
    name_alias = {"Czech Republic": "Czechia", "Turkey": "Türkiye", "United States": "United States of America",
                  "United Kingdom": "United Kingdom of Great Britain and Northern Ireland",
                  "Cape Verde": "Cabo Verde", "East Timor": "Timor-Leste", "Nauru": "Nauru",
                  "Russia": "Russian Federation", "South Korea": "Korea, Republic of",
                  "North Korea": "Korea, Democratic People's Republic of", "Vietnam": "Viet Nam",
                  "Laos": "Lao People's Democratic Republic", "Brunei": "Brunei Darussalam",
                  "Bolivia": "Bolivia, Plurinational State of", "Venezuela": "Venezuela, Bolivarian Republic of",
                  "Iran": "Iran, Islamic Republic of", "Moldova": "Moldova, Republic of",
                  "Tanzania": "Tanzania, United Republic of", "Syria": "Syrian Arab Republic",
                  "DR Congo": "Congo, Democratic Republic of the", "Republic of the Congo": "Congo",
                  "Micronesia": "Micronesia, Federated States of", "Palestine": "Palestine, State of",
                  "Vatican City": "Holy See", "Taiwan": "Taiwan, Province of China", "Macau": "Macao",
                  "The Bahamas": "Bahamas", "Bahamas": "Bahamas", "Cabo Verde": "Cabo Verde",
                  "Côte d'Ivoire": "Côte d'Ivoire", "Ivory Coast": "Côte d'Ivoire",
                  "São Tomé and Príncipe": "Sao Tome and Principe", "Timor-Leste": "Timor-Leste"}
    iso_by_name = {}
    for code, (name, tlds_, line) in iso.items():
        iso_by_name[name] = code
    for alias, target in name_alias.items():
        if target in iso_by_name:
            iso_by_name[alias] = iso_by_name[target]

    continent = {}
    for country, conts in cont_by_name.items():
        code = iso_by_name.get(country)
        if not code:
            continue
        pick = [c for c in CONT_ORDER if c in conts]
        continent[code] = CONT_OVERRIDE.get(code) or (pick[0] if pick else "?")

    # universe
    excluded = {"su"}  # Soviet Union: delegated but its entity no longer exists
    rows = []
    kind_of = {}
    for t in tlds:
        if t.startswith("xn--") or t in excluded:
            continue
        typ = rootdb.get(t, "")
        kind = "country-code" if typ == "Country Code" else ("infrastructure" if typ == "Special Use" else "generic")
        kind_of[t] = kind
        country, cont = "?", "?"
        if kind == "country-code":
            if len(t) == 2:
                code = {"uk": "GB", "ac": "AC"}.get(t, t.upper())
                if code in iso:
                    country = iso[code][0]
                    cont = continent.get(code, "?")
                elif t == "eu":
                    country, cont = "European Union", "Europe"
                elif t == "ac":
                    country, cont = "Ascension Island", "Africa"
        if t == "arpa":
            kind = "infrastructure"
        if kind == "country-code":
            entity = "%s country-code top-level domain" % country if country != "?" else "country-code top-level domain"
        elif kind == "infrastructure":
            entity = "Address and Routing Parameter Area top-level domain"
        else:
            entity = "generic top-level domain"
        rows.append((t, entity, kind, cont, country))
    rows.sort()

    (ROOT / "universes").mkdir(exist_ok=True)
    with (ROOT / "universes" / "tld.tsv").open("w", encoding="utf-8") as fh:
        fh.write("value\tentity\tattr:kind\tattr:continent\tattr:country\n")
        for t, entity, kind, cont, country in rows:
            fh.write("%s\t%s\t%s\t%s\t%s\n" % (t, entity, kind, cont, country))

    universe = {t for t, *_ in rows}
    tld_for_code = {}
    for code, (name, tlds_, line) in iso.items():
        pick = [x for x in tlds_ if x in universe]
        if code == "GB" and "uk" in universe:
            pick = ["uk"] + [x for x in pick if x != "uk"]
        if pick:
            tld_for_code[code] = pick[0]
    tld_for_code["EU"] = "eu"

    extra_out = {"g20_cctlds": ["African Union"]}
    lists = []
    for lid, page, name, codes, official in ROSTERS:
        codes = codes.split()
        members, out = [], []
        for code in codes:
            t = tld_for_code.get(code)
            if code == "EH":
                t = None
            if t and t in universe:
                members.append(t)
            else:
                out.append(code)
        out.extend(extra_out.get(lid, []))
        if len(members) < 5:
            print("SKIP", lid, len(members), file=sys.stderr)
            continue
        lists.append({
            "id": lid, "name": name, "synonyms": [],
            "members": sorted(members, key=lambda x: (len(x), x)),
            "disputed": [], "changes": [], "out_of_universe": sorted(out),
            "official_count": official,
            "source": "https://en.wikipedia.org/wiki/" + page,
        })

    (ROOT / "lists").mkdir(exist_ok=True)
    sal = _salience()
    for x in lists:
        x["salience"] = sal.get(x["id"], 0)
    (ROOT / "lists" / "tld.yaml").write_text(
        yaml.safe_dump(lists, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("universe", len(rows), "lists", len(lists))
    for x in lists:
        print(x["id"], len(x["members"]), x["official_count"], x["out_of_universe"])


if __name__ == "__main__":
    main()
