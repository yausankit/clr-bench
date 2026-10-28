"""TR round 3: append airlines in member states of 16 closed-membership organisations.

Existing airline.yaml entries are preserved byte-for-byte.  Each new list joins an
organisation's current official member-state table (wikitext snapshot in raw/wiki/<slug>.wiki)
with the airline headquarters country in universes/airline.tsv, whose source is
raw/airlines.json.  The script only reads raw snapshots and the existing universe/salience;
run it twice and compare the output.
"""
import os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "wiki")
LISTS = os.path.join(HERE, "lists", "airline.yaml")
UNIVERSE = os.path.join(HERE, "universes", "airline.tsv")
SALIENCE = os.path.join(HERE, "salience", "airline.tsv")

# id, display name, organisation, wiki title, member countries, source-section line range,
# source member count, evidence aliases for country names that use templates/ISO codes.
SPECS = [
 ("oic_airlines", "Airlines of Organisation of Islamic Cooperation member states",
  "Organisation of Islamic Cooperation", "Organisation of Islamic Cooperation",
  "Algeria|Benin|Burkina Faso|Cameroon|Chad|Comoros|Djibouti|Egypt|Gabon|Gambia|Guinea|Guinea-Bissau|Ivory Coast|Libya|Mali|Mauritania|Morocco|Mozambique|Niger|Nigeria|Senegal|Sierra Leone|Somalia|Sudan|Togo|Tunisia|Uganda|Afghanistan|Azerbaijan|Bahrain|Bangladesh|Brunei|Indonesia|Iran|Iraq|Jordan|Kazakhstan|Kuwait|Kyrgyzstan|Lebanon|Malaysia|Maldives|Oman|Pakistan|Palestine|Qatar|Saudi Arabia|Syria|Tajikistan|Turkey|Turkmenistan|United Arab Emirates|Uzbekistan|Yemen|Albania|Guyana|Suriname",
  (89, 168), 57, {"Gambia": ["Gambia", "GMB"]}),
 ("apec_airlines", "Airlines of Asia-Pacific Economic Cooperation member economies",
  "Asia-Pacific Economic Cooperation", "Asia Pacific Economic Cooperation",
  "Australia|Brunei|Canada|Chile|China|Hong Kong|Indonesia|Japan|Malaysia|Mexico|New Zealand|Papua New Guinea|Peru|Philippines|Russia|Singapore|South Korea|Taiwan|Thailand|United States|Vietnam",
  (193, 310), 21, {"China": ["China", "CHN"], "Hong Kong": ["Hong Kong", "HKG"]}),
 ("g20_airlines", "Airlines of Group of Twenty member states",
  "Group of Twenty", "G20",
  "Argentina|Australia|Brazil|Canada|China|France|Germany|India|Indonesia|Italy|Japan|Mexico|Russia|Saudi Arabia|South Africa|South Korea|Turkey|United Kingdom|United States",
  (171, 344), 19, {"China": ["China", "CHN"]}),
 ("oecd_airlines", "Airlines of OECD member states",
  "Organisation for Economic Co-operation and Development", "OECD",
  "Australia|Austria|Belgium|Canada|Chile|Colombia|Costa Rica|Czech Republic|Denmark|Estonia|Finland|France|Germany|Greece|Hungary|Iceland|Ireland|Israel|Italy|Japan|Latvia|Lithuania|Luxembourg|Mexico|Netherlands|New Zealand|Norway|Poland|Portugal|Slovakia|Slovenia|South Korea|Spain|Sweden|Switzerland|Turkey|United Kingdom|United States",
  (542, 641), 38, {}),
 ("nato_airlines", "Airlines of NATO member states",
  "North Atlantic Treaty Organization", "NATO",
  "Albania|Belgium|Bulgaria|Canada|Croatia|Czech Republic|Denmark|Estonia|Finland|France|Germany|Greece|Hungary|Iceland|Italy|Latvia|Lithuania|Luxembourg|Montenegro|Netherlands|North Macedonia|Norway|Poland|Portugal|Romania|Slovakia|Slovenia|Spain|Sweden|Turkey|United Kingdom|United States",
  (219, 253), 32, {}),
 ("brics_airlines", "Airlines of BRICS member states",
  "BRICS", "BRICS",
  "Brazil|China|Egypt|Ethiopia|India|Indonesia|Iran|Russia|South Africa|United Arab Emirates",
  (273, 292), 10, {"China": ["China", "CHN"]}),
 ("bsec_airlines", "Airlines of Black Sea Economic Cooperation member states",
  "Organization of the Black Sea Economic Cooperation", "Organization of the Black Sea Economic Cooperation",
  "Albania|Armenia|Azerbaijan|Bulgaria|Georgia|Greece|Moldova|North Macedonia|Romania|Russia|Serbia|Turkey|Ukraine",
  (30, 161), 13, {}),
 ("cis_airlines", "Airlines of Commonwealth of Independent States member states",
  "Commonwealth of Independent States", "Commonwealth of Independent States",
  "Armenia|Azerbaijan|Belarus|Kazakhstan|Kyrgyzstan|Moldova|Russia|Tajikistan|Uzbekistan",
  (152, 232), 9, {}),
 ("eco_airlines", "Airlines of Economic Cooperation Organization member states",
  "Economic Cooperation Organization", "Economic Cooperation Organization",
  "Afghanistan|Azerbaijan|Iran|Kazakhstan|Kyrgyzstan|Pakistan|Tajikistan|Turkey|Turkmenistan|Uzbekistan",
  (150, 221), 10, {}),
 ("aladi_airlines", "Airlines of Latin American Integration Association member states",
  "Latin American Integration Association", "Latin American Integration Association",
  "Argentina|Bolivia|Brazil|Chile|Colombia|Cuba|Ecuador|Mexico|Paraguay|Panama|Peru|Uruguay|Venezuela",
  (86, 208), 13, {}),
 ("pacific_alliance_airlines", "Airlines of Pacific Alliance member states",
  "Pacific Alliance", "Pacific Alliance",
  "Chile|Colombia|Mexico|Peru",
  (188, 193), 4, {}),
 ("comesa_airlines", "Airlines of Common Market for Eastern and Southern Africa member states",
  "Common Market for Eastern and Southern Africa", "Common Market for Eastern and Southern Africa",
  "Djibouti|Eritrea|Ethiopia|Somalia|Egypt|Libya|Sudan|Tunisia|Comoros|Madagascar|Mauritius|Seychelles|Burundi|Kenya|Malawi|Rwanda|Uganda|Eswatini|Zambia|Zimbabwe|Democratic Republic of the Congo",
  (50, 112), 21, {"Djibouti": ["DJI"], "Eritrea": ["ERI"], "Ethiopia": ["ETH"], "Somalia": ["SOM"],
   "Egypt": ["EGY"], "Libya": ["LBY"], "Sudan": ["SDN"], "Tunisia": ["TUN"], "Comoros": ["COM"],
   "Madagascar": ["MDG"], "Mauritius": ["MUS"], "Seychelles": ["SYC"], "Burundi": ["BDI"],
   "Kenya": ["KEN"], "Malawi": ["MWI"], "Rwanda": ["RWA"], "Uganda": ["UGA"], "Eswatini": ["SWZ"],
   "Zambia": ["ZMB"], "Zimbabwe": ["ZWE"], "Democratic Republic of the Congo": ["COD"]}),
 ("cen_sad_airlines", "Airlines of Community of Sahel-Saharan States member states",
  "Community of Sahel-Saharan States", "Community of Sahel–Saharan States",
  "Benin|Burkina Faso|Central African Republic|Chad|Comoros|Djibouti|Egypt|Eritrea|The Gambia|Ghana|Guinea|Guinea-Bissau|Ivory Coast|Libya|Mali|Mauritania|Morocco|Niger|Nigeria|Senegal|Sierra Leone|Somalia|Sudan|Togo|Tunisia",
  (121, 343), 25, {"Benin": ["BEN"], "Burkina Faso": ["BFA"], "Central African Republic": ["CAF"],
   "Chad": ["CHA"], "Comoros": ["COM"], "Djibouti": ["DJI"], "Egypt": ["EGY"], "Eritrea": ["ERI"],
   "The Gambia": ["GAM"], "Ghana": ["GHA"], "Guinea": ["GIN"], "Guinea-Bissau": ["GNB"],
   "Ivory Coast": ["CIV"], "Libya": ["LBA", "LBY"], "Mali": ["MLI"], "Mauritania": ["MRT"],
   "Morocco": ["MAR"], "Niger": ["NIG"], "Nigeria": ["NGA"], "Senegal": ["SEN"],
   "Sierra Leone": ["SLE"], "Somalia": ["SOM"], "Sudan": ["SUD"], "Togo": ["TOG"], "Tunisia": ["TUN"]}),
 ("saarc_airlines", "Airlines of South Asian Association for Regional Cooperation member states",
  "South Asian Association for Regional Cooperation", "South Asian Association for Regional Cooperation",
  "Afghanistan|Bangladesh|Bhutan|India|Maldives|Nepal|Pakistan|Sri Lanka",
  (178, 180), 8, {}),
 ("mgc_airlines", "Airlines of Mekong-Ganga Cooperation member states",
  "Mekong-Ganga Cooperation", "Mekong–Ganga Cooperation",
  "India|Thailand|Myanmar|Cambodia|Laos|Vietnam",
  (21, 30), 6, {}),
 ("opec_airlines", "Airlines of OPEC member states",
  "Organization of the Petroleum Exporting Countries", "OPEC",
  "Algeria|Republic of the Congo|Equatorial Guinea|Gabon|Iran|Iraq|Kuwait|Libya|Nigeria|Saudi Arabia|Venezuela",
  (313, 433), 11, {}),
]
ALIAS = {"China": "People's Republic of China", "Gambia": "The Gambia"}
SCAN_ALIAS = {"People's Republic of China": ["China", "CHN"],
              "The Gambia": ["Gambia", "GMB"]}

def blocks(path):
    text = open(path, encoding="utf-8").read()
    out = []
    for p in re.split(r"(?m)^(?=- id: )", text):
        if not p.strip(): continue
        m = re.match(r"- id: (\S+)", p)
        if not m: raise RuntimeError("unparsed YAML block: " + p[:60])
        out.append((m.group(1), p if p.endswith("\n") else p + "\n"))
    return out

def rows():
    with open(UNIVERSE, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, line.rstrip("\n").split("\t"))) for line in fh]

def salience():
    out = {}
    if os.path.exists(SALIENCE):
        for line in list(open(SALIENCE, encoding="utf-8"))[1:]:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4: out[p[0]] = int(float(p[3] or 0))
    return out

def wiki_slug(title):
    return re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")

def section(slug, lo, hi):
    lines = open(os.path.join(RAW, slug + ".wiki"), encoding="utf-8").read().splitlines()
    return "\n".join(lines[lo - 1:hi - 1])

def dump(item):
    return yaml.safe_dump([item], allow_unicode=True, sort_keys=False, width=130)

def main():
    uni = rows(); sal = salience()
    by_country = {}
    for r in uni: by_country.setdefault(r["attr:country"], []).append(r["value"])
    existing = blocks(LISTS)
    ids = {x[0] for x in existing}
    new_ids = {s[0] for s in SPECS}
    if len(new_ids) != len(SPECS): raise RuntimeError("duplicate new id")
    if len(ids) != len(existing): raise RuntimeError("duplicate ids in airline.yaml")
    out = [p for i, p in existing if i not in new_ids]
    for lid, name, org, title, country_text, (lo, hi), official_count, aliases in SPECS:
        countries = [ALIAS.get(c, c) for c in country_text.split("|")]
        if len(countries) != len(set(countries)) or len(countries) != official_count:
            raise RuntimeError(f"{lid}: country count {len(countries)} != {official_count}")
        section_text = section(wiki_slug(title), lo, hi)
        for c in countries:
            needles = aliases.get(c, SCAN_ALIAS.get(c, [c]))
            if not any(re.search(r"(?<![A-Za-z])" + re.escape(x) + r"(?![A-Za-z])", section_text) for x in needles):
                raise RuntimeError(f"{lid}: {c} not in raw/wiki/{wiki_slug(title)}.wiki lines {lo}-{hi}")
        members = sorted(v for c in countries for v in by_country.get(c, []))
        represented = sorted(set(countries) & set(by_country))
        if len(members) < 10 or len(represented) < 4:
            raise RuntimeError(f"{lid}: only {len(members)} members / {len(represented)} countries")
        item = {"id": lid, "name": name, "kind": "bloc", "org": org, "synonyms": [],
                "wiki": title, "members": members, "disputed": [], "changes": [],
                "official_count": len(members), "out_of_universe": [],
                "source": f"current member-state list in raw/wiki/{wiki_slug(title)}.wiki lines {lo}-{hi} "
                          f"({official_count} official member countries) joined with airline country of headquarters "
                          f"(raw/airlines.json, carried in universes/airline.tsv)",
                "salience": sal.get(lid, 0),
                "note": f"{official_count} official member countries in the source table; {len(represented)} represented in the airline universe"}
        out.append(dump(item))
    with open(LISTS, "w", encoding="utf-8") as fh:
        fh.write("".join(out))
    print("appended", len(SPECS), "airline lists")

if __name__ == "__main__": main()
