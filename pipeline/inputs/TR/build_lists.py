"""Build lists/{airline,airport,currency}.yaml from raw/ (Wikidata SPARQL JSON, ISO 4217 page,
Wikipedia wikitext snapshots).  Deterministic: everything is derived from files in raw/.

Run:  python3 build_universes.py && python3 build_salience.py && python3 build_lists.py
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "lists")
sys.path.insert(0, HERE)
import build_universes as bu  # noqa: E402


def rows(name):
    with open(os.path.join(RAW, name + ".json"), encoding="utf-8") as fh:
        d = json.load(fh)
    return [{k: v["value"] for k, v in b.items()} for b in d["results"]["bindings"]]


def universe(name):
    out = []
    with open(os.path.join(HERE, "universes", name + ".tsv"), encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            out.append(dict(zip(head, line.rstrip("\n").split("\t"))))
    return out


def wiki_text(slug):
    path = os.path.join(RAW, "wiki", slug + ".json")
    if not os.path.exists(path):
        return ""
    return json.load(open(path, encoding="utf-8")).get("parse", {}).get("wikitext", "")


def evidence(slug, needle):
    """Line number (1-based) in raw/wiki/<slug>.wiki holding `needle`, or None."""
    text = wiki_text(slug)
    if not text:
        return None
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


def salience_table(name):
    path = os.path.join(HERE, "salience", name + ".tsv")
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8") as fh:
        for r in list(fh)[1:]:
            parts = r.rstrip("\n").split("\t")
            if len(parts) >= 4:
                out[parts[0]] = int(float(parts[3] or 0))
    return out


def emit(name, items):
    sal = salience_table(name)
    out = []
    for it in items:
        it = dict(it)
        it["members"] = sorted(set(it["members"]))
        it["out_of_universe"] = sorted(set(it.get("out_of_universe") or []))
        it["disputed"] = sorted(set(it.get("disputed") or []))
        it.setdefault("changes", [])
        it["official_count"] = len(it["members"]) + len(it["disputed"]) + len(it["out_of_universe"])
        it["salience"] = int(sal.get(it["id"], 0))
        order = ["id", "name", "kind", "parents", "org", "section", "phrase", "word", "synonyms", "wiki", "members", "disputed", "changes",
                 "official_count", "out_of_universe", "source", "salience", "note"]
        out.append({k: it[k] for k in order if k in it})
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".yaml"), "w", encoding="utf-8") as fh:
        yaml.safe_dump(out, fh, allow_unicode=True, sort_keys=False, width=120)
    print(name, len(out), "lists", sum(len(x["members"]) for x in out), "members")
    return out


# ---------------------------------------------------------------- country helpers
EUROZONE = ["Austria", "Belgium", "Croatia", "Cyprus", "Estonia", "Finland", "France", "Germany",
            "Greece", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
            "Portugal", "Slovakia", "Slovenia", "Spain"]
# EU-27 as of the snapshot: Wikidata P463 still carries the pre-Brexit United Kingdom and misses
# Romania; the curated list is the official membership (see REPORT.md, known corrections).
EU27 = ["Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia",
        "Finland", "France", "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia", "Lithuania",
        "Luxembourg", "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
        "Spain", "Sweden"]
GCC = ["Bahrain", "Kuwait", "Oman", "Qatar", "Saudi Arabia", "United Arab Emirates"]
ASEAN = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar", "Philippines", "Singapore",
         "Thailand", "Vietnam"]


def country_list(org_label):
    out = set()
    for r in rows("country_relations"):
        if r.get("memberOfLabel") == org_label:
            out.add(r["countryLabel"])
    return out


def currency_by_country():
    """country (English label as used in the ISO table) -> ISO code."""
    m = {}
    for r in bu.currency_rows():
        locs = r["locations"]
        if not locs:
            continue
        for part in re.split(r",\s*", locs):
            name = re.sub(r"\s*\((?:[A-Z]{2})\)", "", part)
            name = re.sub(r"\s*\(pegged[^)]*\)", "", name)
            name = re.sub(r"\[[^\]]*\]", "", name).strip()
            if name:
                m.setdefault(name, r["code"])
    for c in EUROZONE:
        m[c] = "EUR"
    m["People's Republic of China"] = "CNY"
    m["Democratic Republic of the Congo"] = "CDF"
    m["Republic of the Congo"] = "XAF"
    m["Ivory Coast"] = "XOF"
    return m


def currency_members(countries, c2c, universe_values):
    mem, out = [], []
    for c in countries:
        code = c2c.get(c)
        if code is None:
            out.append(c)
        elif code in universe_values:
            mem.append(code)
        else:
            out.append(code)
    return sorted(set(mem)), sorted(set(out))


def currency_lists():
    uni = universe("currency")
    values = {r["value"] for r in uni}
    c2c = currency_by_country()
    eu = set(EU27)
    g20 = country_list("G20")
    brics = country_list("BRICS")
    arab = country_list("Arab League")
    items = []

    def add(lid, name, countries, source, synonyms=(), note="", org_label=None):
        mem, out = currency_members(countries, c2c, values)
        it = {"id": lid, "name": name, "kind": "currency_org", "org": org_label, "synonyms": list(synonyms),
              "members": mem,
              "out_of_universe": out, "source": source}
        if note:
            it["note"] = note
        items.append(it)

    add("sdr_basket_currencies", "Currencies in the IMF special drawing rights basket",
        [], "IMF SDR basket (USD, EUR, CNY, JPY, GBP)", ["SDR basket"], note="five currencies fixed by the IMF")
    items[-1]["members"] = ["CNY", "EUR", "GBP", "JPY", "USD"]
    add("eu_non_euro_currencies", "Currencies of European Union member states outside the euro area",
        sorted(eu - set(EUROZONE)), "ISO 4217 table (raw/iso4217_page.json) + EU membership (Wikidata P463)",
        ["EU currencies outside the euro"], org_label="European Union")
    add("gcc_currencies", "Currencies of Gulf Cooperation Council member states", GCC,
        "ISO 4217 table + GCC membership", ["GCC currencies"], org_label="Gulf Cooperation Council")
    add("asean_currencies", "Currencies of ASEAN member states", ASEAN,
        "ISO 4217 table + ASEAN membership", ["ASEAN currencies"], org_label="ASEAN")
    add("g20_currencies", "Currencies of G20 member states", sorted(g20),
        "ISO 4217 table + G20 membership (Wikidata P463)", ["G20 currencies"], org_label="G20")
    add("brics_currencies", "Currencies of BRICS member states", sorted(brics),
        "ISO 4217 table + BRICS membership (Wikidata P463)", ["BRICS currencies"], org_label="BRICS")
    add("arab_league_currencies", "Currencies of Arab League member states", sorted(arab),
        "ISO 4217 table + Arab League membership (Wikidata P463)", ["Arab League currencies"], org_label="Arab League")
    for lid, name, org in [("commonwealth_currencies", "Currencies of Commonwealth of Nations member states",
                            "Commonwealth of Nations"),
                           ("oic_currencies", "Currencies of Organisation of Islamic Cooperation member states",
                            "Organisation of Islamic Cooperation"),
                           ("african_union_currencies", "Currencies of African Union member states",
                            "African Union"),
                           ("oas_currencies", "Currencies of Organization of American States member states",
                            "Organization of American States"),
                           ("apec_currencies", "Currencies of APEC member economies",
                            "Asia-Pacific Economic Cooperation")]:
        add(lid, name, sorted(country_list(org)),
            f"ISO 4217 table + {org} membership (Wikidata P463)", org_label=org)
    for lid, word, name in [("dollar_named_currencies", "dollar", "Currencies named dollar"),
                            ("peso_named_currencies", "peso", "Currencies named peso"),
                            ("dinar_named_currencies", "dinar", "Currencies named dinar"),
                            ("franc_named_currencies", "franc", "Currencies named franc"),
                            ("pound_named_currencies", "pound", "Currencies named pound"),
                            ("rupee_named_currencies", "rupee", "Currencies named rupee")]:
        mem = [r["value"] for r in uni if word in r["entity"].lower()]
        items.append({"id": lid, "name": name, "kind": "name_family", "synonyms": [],
                      "members": sorted(mem), "out_of_universe": [],
                      "source": "ISO 4217 table (currency names) in raw/iso4217_page.json"})
    # English Wikipedia concept of each list (used only to rank candidates by salience).
    name_family_wiki = {"dollar_named_currencies": "Dollar", "peso_named_currencies": "Peso",
                        "dinar_named_currencies": "Dinar", "franc_named_currencies": "Franc",
                        "pound_named_currencies": "Pound (currency)", "rupee_named_currencies": "Rupee"}
    wiki_override = {"sdr_basket_currencies": "Special drawing rights",
                     "eu_non_euro_currencies": "European Union"}
    for it in items:
        it["wiki"] = wiki_override.get(it["id"]) or name_family_wiki.get(it["id"]) or it.get("org")
    return emit("currency", items)


# ---------------------------------------------------------------- airlines
GROUPS = [
    ("lufthansa_group", "Lufthansa Group airlines", ["Q62589018"], "Lufthansa Group"),
    ("iag_group", "International Airlines Group airlines", ["Q8774"], "International Airlines Group"),
    ("air_france_klm_group", "Air France-KLM group airlines", ["Q407237"], "Air France-KLM"),
    ("qantas_group", "Qantas Group airlines", ["Q32491"], "Qantas"),
    ("latam_airlines_group", "LATAM Airlines Group airlines", ["Q1321868"], "LATAM Airlines Group"),
    ("ana_group", "ANA Holdings airlines", ["Q11189379"], "All Nippon Airways"),
    ("jal_group", "Japan Airlines group airlines", ["Q213140"], "Japan Airlines"),
    ("hna_group", "HNA Group airlines", ["Q292428", "Q1565713"], "HNA Group"),
    ("air_china_group", "Air China group airlines", ["Q51747"], "Air China"),
    ("tui_group", "TUI Group airlines", ["Q1476472"], "TUI Group"),
    ("dhl_aviation_group", "DHL aviation group airlines", ["Q489815"], "DHL"),
    ("asl_aviation_group", "ASL Aviation Holdings airlines", ["Q61719469"], "ASL Aviation Holdings"),
    ("avianca_group", "Avianca Group airlines", ["Q790788", "Q308911"], "Avianca Group"),
    ("wizz_air_group", "Wizz Air Holdings airlines", ["Q114314826"], "Wizz Air"),
    ("malaysia_aviation_group", "Malaysia Aviation Group airlines", ["Q137477114"], "Malaysia Aviation Group"),
    ("lion_air_group", "Lion Air Group airlines", ["Q57239467", "Q1056794"], "Lion Air"),
    ("egyptair_group", "EgyptAir group airlines", ["Q374740"], "EgyptAir"),
    ("ryanair_group", "Ryanair group airlines", ["Q170614"], "Ryanair Holdings"),
    ("china_eastern_group", "China Eastern group airlines", ["Q291796"], "China Eastern Airlines"),
    ("china_southern_group", "China Southern group airlines", ["Q291090"], "China Southern Airlines"),
    ("cathay_group", "Cathay Pacific group airlines", ["Q32141"], "Cathay Pacific"),
    ("garuda_group", "Garuda Indonesia group airlines", ["Q512468"], "Garuda Indonesia"),
    ("norwegian_group", "Norwegian group airlines", ["Q215392"], "Norwegian Air Shuttle"),
    ("icelandair_group", "Icelandair Group airlines", ["Q3278622"], "Icelandair"),
    ("sas_group", "SAS Group airlines", ["Q1345441"], "SAS Group"),
    ("turkish_airlines_group", "Turkish Airlines group airlines", ["Q4548"], "Turkish Airlines"),
    ("smartwings_group", "Smartwings group airlines", ["Q1853488"], "Smartwings"),
    ("rex_group", "Regional Express Holdings airlines", ["Q7309054"], "Regional Express Holdings"),
    ("volga_dnepr_group", "Volga-Dnepr group airlines", ["Q765297"], "Volga-Dnepr Airlines"),
]

# the group's own flagship airline is part of the group even when Wikidata attaches it to the
# holding company rather than listing it as a subsidiary
GROUP_PARENT_AIRLINES = {
    "qantas_group": ["Qantas Airways"],
    "jal_group": ["Japan Airlines"],
    "air_china_group": ["Air China"],
    "hna_group": ["Hainan Airlines"],
    "lion_air_group": ["Lion Air"],
    "iag_group": ["British Airways"],
    "lufthansa_group": ["Lufthansa"],
    "ana_group": ["All Nippon Airways"],
    "avianca_group": ["Avianca"],
}


def airline_group_lists():
    uni = universe("airline")
    q2v = {r["qid"]: r["value"] for r in uni}
    subs = {}
    for r in rows("group_subsidiaries"):
        subs.setdefault(r["group"].split("/")[-1], set()).add(
            (r["sub"].split("/")[-1], r.get("subLabel", "")))
    for r in rows("airline_relations"):
        if "parent" in r:
            subs.setdefault(r["parent"].split("/")[-1], set()).add(
                (r["item"].split("/")[-1], r.get("itemLabel", "")))
    items = []
    for lid, name, qids, wiki in GROUPS:
        mem, out = set(), set()
        for q in qids:
            for sq, label in subs.get(q, ()):  # noqa: B007
                if sq in q2v:
                    mem.add(q2v[sq])
                else:
                    out.add(label or sq)
        for v in GROUP_PARENT_AIRLINES.get(lid, []):
            if v in q2v.values():
                mem.add(v)
        if len(mem) < 5:
            print("skip group (only %d in universe): %s" % (len(mem), lid))
            continue
        items.append({"id": lid, "name": name, "kind": "group", "parents": qids, "synonyms": [], "wiki": wiki,
                      "members": sorted(mem), "out_of_universe": sorted(out),
                      "source": "Wikidata P355/P749 subsidiary statements of the group item "
                                "(raw/group_subsidiaries.json, raw/airline_relations.json)"})
    return items


# ---------------------------------------------------------------- airports
# country sets that a list is built from; "org:" means the membership recorded in
# raw/country_relations.json (Wikidata P463), "fix" are curated corrections (REPORT.md).
AIRPORT_ORG_LISTS = [
    ("schengen_airports", "Airports in the Schengen Area", "Schengen Area",
     ["Kingdom of Denmark", "realm of the United Kingdom"], "Schengen Area"),
    ("eu_airports", "Airports in the European Union", "curated:EU27", [], "European Union"),
    ("eea_airports", "Airports in the European Economic Area", "curated:EEA", [],
     "European Economic Area"),
    ("arab_league_airports", "Airports in Arab League member states", "Arab League", [], "Arab League"),
    ("asean_airports", "Airports in ASEAN member states", "curated:ASEAN", [], "ASEAN"),
    ("gcc_airports", "Airports in Gulf Cooperation Council member states", "curated:GCC", [],
     "Gulf Cooperation Council"),
    ("nordic_airports", "Airports in the Nordic countries", "Nordic Council", [], "Nordic Council"),
    ("baltic_airports", "Airports in the Baltic states", "Baltic Assembly", [], "Baltic Assembly"),
    ("caricom_airports", "Airports in Caribbean Community member states", "Caribbean Community", [],
     "Caribbean Community"),
    ("opec_airports", "Airports in OPEC member states", "curated:OPEC", [],
     "OPEC"),
    ("visegrad_airports", "Airports in Visegrad Group member states", "curated:VISEGRAD", [],
     "Visegrad Group"),
    ("benelux_airports", "Airports in Benelux Union member states", "curated:BENELUX", [], "Benelux"),
    ("eaeu_airports", "Airports in Eurasian Economic Union member states", "curated:EAEU", [],
     "Eurasian Economic Union"),
    ("sadc_airports", "Airports in Southern African Development Community member states",
     "Southern African Development Community", [], "Southern African Development Community"),
    ("turkic_airports", "Airports in Organization of Turkic States member states",
     "Organization of Turkic States", [], "Organization of Turkic States"),
    ("sco_airports", "Airports in Shanghai Cooperation Organisation member states",
     "Shanghai Cooperation Organisation", [], "Shanghai Cooperation Organisation"),
    ("ecowas_airports", "Airports in ECOWAS member states",
     "Economic Community of West African States", [], "ECOWAS"),
    ("cbss_airports", "Airports in Council of the Baltic Sea States member states",
     "Council of the Baltic Sea States", [], "Council of the Baltic Sea States"),
    ("cplp_airports", "Airports in Community of Portuguese Language Countries member states",
     "Community of Portuguese Language Countries", [], "Community of Portuguese Language Countries"),
    ("bsec_airports", "Airports in Organization of the Black Sea Economic Cooperation member states",
     "Organization of the Black Sea Economic Cooperation", [],
     "Organization of the Black Sea Economic Cooperation"),
    ("eccas_airports", "Airports in Economic Community of Central African States member states",
     "Economic Community of Central African States", [], "Economic Community of Central African States"),
    ("amu_airports", "Airports in Arab Maghreb Union member states", "Arab Maghreb Union", [],
     "Arab Maghreb Union"),
    ("sacu_airports", "Airports in Southern African Customs Union member states",
     "Southern African Customs Union", [], "Southern African Customs Union"),
    ("efta_airports", "Airports in European Free Trade Association member states", "curated:EFTA", [],
     "European Free Trade Association"),
    ("coe_airports", "Airports in Council of Europe member states", "Council of Europe", [],
     "Council of Europe"),
    ("oic_airports", "Airports in Organisation of Islamic Cooperation member states",
     "Organisation of Islamic Cooperation", [], "Organisation of Islamic Cooperation"),
    ("african_union_airports", "Airports in African Union member states", "African Union", [],
     "African Union"),
]
CURATED_ORG = {
    "curated:EU27": "European Union", "curated:EEA": "European Economic Area", "curated:ASEAN": "ASEAN",
    "curated:GCC": "Gulf Cooperation Council", "curated:OPEC": "OPEC",
    "curated:VISEGRAD": "Visegrad Group", "curated:BENELUX": "Benelux",
    "curated:EAEU": "Eurasian Economic Union", "curated:EFTA": "European Free Trade Association",
}
CURATED_COUNTRIES = {
    "EU27": EU27,
    "EEA": EU27 + ["Iceland", "Liechtenstein", "Norway"],
    "ASEAN": ASEAN,
    "GCC": GCC,
    "OPEC": ["Algeria", "Republic of the Congo", "Equatorial Guinea", "Gabon", "Iran", "Iraq",
             "Kuwait", "Libya", "Nigeria", "Saudi Arabia", "Venezuela"],
    "VISEGRAD": ["Czech Republic", "Hungary", "Poland", "Slovakia"],
    "BENELUX": ["Belgium", "Luxembourg", "Netherlands"],
    "EAEU": ["Armenia", "Belarus", "Kazakhstan", "Kyrgyzstan", "Russia"],
    "EFTA": ["Iceland", "Liechtenstein", "Norway", "Switzerland"],
}


def org_countries(spec, drop):
    if spec.startswith("curated:"):
        base = set(CURATED_COUNTRIES[spec.split(":", 1)[1]])
    else:
        base = country_list(spec)
    return sorted(base - set(drop))


def airport_org_lists():
    uni = universe("airport")
    items = []
    for lid, name, spec, drop, wiki in AIRPORT_ORG_LISTS:
        countries = org_countries(spec, drop)
        cset = set(countries)
        mem = [r["value"] for r in uni if r["attr:country"] in cset]
        if len(mem) < 5:
            print("skip airport list (only %d members): %s" % (len(mem), lid))
            continue
        items.append({"id": lid, "name": name, "kind": "airport_org", "org": CURATED_ORG.get(spec, spec),
                      "synonyms": [], "wiki": wiki, "members": sorted(mem), "out_of_universe": [],
                      "source": "country membership (raw/country_relations.json, or the organisation article "
                                "in raw/wiki) joined with airport country (raw/airports.json)"})
    return items


# ---------------------------------------------------------------- airline organisations
ALLIANCE_PAGES = [
    ("star_alliance_members", "Star Alliance member airlines", "Star_Alliance",
     "Members and affiliates", "former"),
    ("oneworld_members", "Oneworld member airlines", "Oneworld",
     "Full members and their affiliates", "former"),
    ("skyteam_members", "SkyTeam member airlines", "SkyTeam",
     "Full members and their member affiliates", "former"),
]
ORG_PAGES = [
    ("a4a_members", "Airlines for America member airlines", "Airlines_for_America", "ATA Airline Members"),
    ("aapa_members", "Association of Asia Pacific Airlines member airlines",
     "Association_of_Asia_Pacific_Airlines", "Members"),
    ("aaco_members", "Arab Air Carriers Organization member airlines",
     "Arab_Air_Carriers_Organization", "Members"),
    ("afraa_members", "African Airlines Association member airlines",
     "African_Airlines_Association", "AFRAA members"),
    ("a4e_members", "Airlines for Europe member airlines", "Airlines_for_Europe", "Airline members"),
]


def _sections(text):
    heads = [(m.start(), m.end(), m.group(2))
             for m in re.finditer(r"(?m)^(==+)\s*(.+?)\s*\1\s*$", text)]
    out = [("", text[:heads[0][0]] if heads else text)]
    for i, (start, end, name) in enumerate(heads):
        stop = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        out.append((re.sub(r"<[^>]+>", "", name).strip(), text[end:stop]))
    return out


def _row_first_links(body):
    out = []
    for row in body.split("\n|-")[1:]:
        m = re.search(r"\[\[([^\]\|#]+)", row)
        if m:
            out.append(m.group(1).strip())
    return out


def airline_org_lists():
    uni = universe("airline")
    title2q = {r["article"].split("/wiki/")[-1].replace("_", " "): r["item"].split("/")[-1]
               for r in rows("airline_sitelinks")}
    q2v = {r["qid"]: r["value"] for r in uni}
    items = []
    for lid, name, slug, secname, skip in ALLIANCE_PAGES:
        text = wiki_text(slug)
        if not text:
            print("missing page", slug)
            continue
        titles = []
        for sec, body in _sections(text):
            if sec != secname or skip in sec.lower():
                continue
            titles = _row_first_links(body)
        mem, out = set(), set()
        for t in titles:
            q = title2q.get(t)
            if q and q in q2v:
                mem.add(q2v[q])
            else:
                out.add(t)
        items.append({"id": lid, "name": name, "kind": "alliance", "section": secname, "synonyms": [],
                      "wiki": slug.replace("_", " "),
                      "members": sorted(mem), "out_of_universe": sorted(out),
                      "source": f"en.wikipedia.org/wiki/{slug.replace('_', ' ')} — section "
                                f"'{secname}' (table rows, one airline per row)"})
    for lid, name, slug, secname in ORG_PAGES:
        text = wiki_text(slug)
        if not text:
            print("missing page", slug)
            continue
        titles = []
        for sec, body in _sections(text):
            if sec != secname:
                continue
            titles = re.findall(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]", body)
        mem, out = set(), set()
        for t in titles:
            t = t.strip()
            q = title2q.get(t)
            if q and q in q2v:
                mem.add(q2v[q])
            elif q:
                out.add(t)
        items.append({"id": lid, "name": name, "kind": "org", "section": secname, "synonyms": [],
                      "wiki": slug.replace("_", " "),
                      "members": sorted(mem), "out_of_universe": sorted(out),
                      "source": f"en.wikipedia.org/wiki/{slug.replace('_', ' ')} — section '{secname}'"})
    return items


FOUNDING = [
    ("star_alliance_founding", "Founding member airlines of Star Alliance",
     ["Air Canada", "Lufthansa", "Scandinavian Airlines", "Thai Airways", "United Airlines"],
     ["Canadian Airlines"], "Star_Alliance", "five founding members of the alliance",
     [{"value": "Scandinavian Airlines", "date": "2024-09-01", "event": "moved from Star Alliance to SkyTeam"}]),
    ("oneworld_founding", "Founding member airlines of Oneworld",
     ["American Airlines", "British Airways", "Cathay Pacific", "Japan Airlines", "Qantas Airways"],
     ["Canadian Airlines"], "Oneworld", "Oneworld was unveiled by its founding members",
     []),
]


def airline_founding_lists():
    uni = {r["value"] for r in universe("airline")}
    items = []
    for lid, name, members, extra_out, slug, phrase, changes in FOUNDING:
        mem = [m for m in members if m in uni]
        out = [m for m in members if m not in uni] + list(extra_out)
        items.append({"id": lid, "name": name, "kind": "founding", "phrase": phrase, "synonyms": [],
                      "wiki": slug.replace("_", " "),
                      "members": sorted(mem), "out_of_universe": sorted(out), "changes": changes,
                      "source": f"en.wikipedia.org/wiki/{slug.replace('_', ' ')} — \"{phrase}\""})
    return items


def flag_carrier_list():
    """Flag-carrying airlines of each country/region, from the table in the 'Flag carrier' article."""
    uni = {r["value"] for r in universe("airline")}
    title2q = {r["article"].split("/wiki/")[-1].replace("_", " "): r["item"].split("/")[-1]
               for r in rows("airline_sitelinks")}
    q2v = {r["qid"]: r["value"] for r in universe("airline")}
    text = wiki_text("Flag_carrier")
    start = text.find("List of flag-carrying airlines")
    body = text[start:] if start >= 0 else text
    mem, out = set(), set()
    for row in body.split("\n|-")[1:]:
        cells = re.split(r"\|\||\n\|", row)
        while cells and not cells[0].strip():
            cells = cells[1:]
        if len(cells) < 2:
            continue
        airline_cell = cells[1]
        links = re.findall(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]", airline_cell)
        for t in links:
            q = title2q.get(t.strip())
            if q and q in q2v:
                mem.add(q2v[q])
            elif q:
                out.add(t.strip())
    return {"id": "flag_carrier_airlines", "name": "Flag-carrying airlines of their countries",
            "kind": "flag", "section": "List of flag-carrying airlines", "synonyms": [],
            "wiki": "Flag carrier", "members": sorted(mem),
            "out_of_universe": sorted(out),
            "source": "en.wikipedia.org/wiki/Flag carrier — section 'List of flag-carrying airlines'"}


def airline_lists():
    items = (airline_group_lists() + airline_org_lists() + airline_founding_lists()
             + airline_country_bloc_lists()
             + [flag_carrier_list()])
    return emit("airline", items)


AIRLINE_BLOCS = [
    ("eu_airlines", "Airlines of European Union member states", "curated:EU27", "European Union"),
    ("asean_airlines", "Airlines of ASEAN member states", "curated:ASEAN", "ASEAN"),
    ("gcc_airlines", "Airlines of Gulf Cooperation Council member states", "curated:GCC",
     "Gulf Cooperation Council"),
    ("arab_league_airlines", "Airlines of Arab League member states", "Arab League", "Arab League"),
    ("oas_airlines", "Airlines of Organization of American States member states",
     "Organization of American States", "Organization of American States"),
]


def airline_country_bloc_lists():
    uni = universe("airline")
    items = []
    for lid, name, spec, wiki in AIRLINE_BLOCS:
        countries = org_countries(spec, [])
        cset = set(countries)
        mem = [r["value"] for r in uni if r["attr:country"] in cset]
        items.append({"id": lid, "name": name, "kind": "bloc", "org": wiki, "synonyms": [], "wiki": wiki,
                      "members": sorted(mem), "out_of_universe": [],
                      "source": "Wikidata P463 country membership (raw/country_relations.json) joined with "
                                "airline country of headquarters (raw/airlines.json)"})
    return items


def airport_lists():
    items = airport_org_lists()
    for it in items:
        it["kind"] = "airport_org"
    return emit("airport", items)


if __name__ == "__main__":
    which = sys.argv[1:] or ["airline", "airport", "currency"]
    if "airline" in which:
        airline_lists()
    if "airport" in which:
        airport_lists()
    if "currency" in which:
        currency_lists()
