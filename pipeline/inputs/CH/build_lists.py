#!/usr/bin/env python3
"""Build CH lists from the archived official pages and PDFs in raw/."""
from __future__ import annotations

import csv
import json
import re
import sys
import warnings
from pathlib import Path

import yaml
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from pypdf import PdfReader

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "lists"
sys.path.insert(0, str(ROOT))
import build_universes as bu  # noqa: E402


def read_universe(name: str) -> list[dict]:
    with (ROOT / "universes" / f"{name}.tsv").open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


CHEM_ROWS = read_universe("chemical")
COUNTRY_ROWS = read_universe("country")
CARRIER_ROWS = read_universe("carrier")


def norm(s: object) -> str:
    return bu.norm(str(s or ""))


def one_map(rows: list[dict], extra_aliases: dict[str, str] | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in rows:
        out[norm(r["value"])] = r["value"]
        out[norm(r["entity"])] = r["value"]
        for a in (r.get("aliases") or "").split("|"):
            if a.strip():
                out.setdefault(norm(a), r["value"])
    for alias, value in (extra_aliases or {}).items():
        out[norm(alias)] = value
    return out


CHEM_NAME = one_map(CHEM_ROWS)
COUNTRY_NAME = one_map(COUNTRY_ROWS)
CARRIER_NAME = one_map(CARRIER_ROWS)
OFFICIAL_BY_LIST: dict[str, list[tuple[str, str]]] = {}
COUNTRY_QID = {r["qid"].rsplit("/", 1)[-1]: r["value"] for r in COUNTRY_ROWS if r.get("qid")}

COUNTRY_ALIAS = bu.build_country_rows()[2]
CHEM_CAS: dict[str, str] = {}
for row in bu.build_chemical_rows():
    cas = re.sub(r"\D", "", row.get("_cas") or "")
    if cas:
        CHEM_CAS.setdefault(cas, row["value"])

CHEM_OVERRIDES = {
    "2,4,5-t and its salts and esters": "2,4,5-T",
    "dinoseb and its salts and esters": "Dinoseb",
    "dinitro-ortho-cresol (dnoc) and its salts": "Dinitro-ortho-cresol",
    "endosulfan": "Technical endosulfan",
    "hch (mixed isomers)": "HCH (mixed isomers)",
    "pentachlorophenol and its salts and esters": "Pentachlorophenol",
    "perfluorooctane sulfonic acid, its salts and perfluorooctane sulfonyl fluoride": "Perfluorooctane sulfonic acid",
    "polychlorinated biphenyls (pcb)": "Polychlorinated biphenyls",
    "polychlorinated dibenzo-p-dioxins and dibenzofurans (pcdd/pcdf)": "2,3,7,8-Tetrachlorodibenzo-p-dioxin",
    "polychlorinated naphthalenes": "Polychlorinated naphthalenes",
    "short-chain chlorinated paraffins": "Short-chain chlorinated paraffins",
    "perfluorooctanoic acid (pfoa), its salts and pfoa-related compounds": "Perfluorooctanoic acid",
    "perfluorooctane sulfonic acid and its derivatives (pfos)": "Perfluorooctane sulfonic acid",
    "commercial octabromodiphenyl ether": "Hexabromodiphenyl ether",
    "commercial pentabromodiphenyl ether": "Tetrabromodiphenyl ether",
    "polybrominated biphenyls (pbb)": "Hexabromobiphenyl",
    "all tributyltin compounds": "Tributyltin compounds",
    "brominated diphenylethers": "Brominated diphenyl ethers",
    "cadmium and its compounds": "Cadmium compounds",
    "chloroalkanes, c10-13": "C10-13 Chloroalkanes",
    "hexachlorocyclohexane": "HCH (mixed isomers)",
    "lead and its compounds": "Lead compounds",
    "mercury and its compounds": "Mercury compounds",
    "nickel and its compounds": "Nickel compounds",
    "polyaromatic hydrocarbons (pah)": "Polyaromatic hydrocarbons",
    "chlorpyrifos (chlorpyrifos-ethyl)": "Chlorpyrifos",
    "octylphenols ( 6 )": "Octylphenols",
    "polyaromatic hydrocarbons (pah) ( 7 )": "Polyaromatic hydrocarbons",
    "hexabromocyclododecanes (hbcdd)": "Hexabromocyclododecane",
    "heptachlor and heptachlor epoxide": "Heptachlor",
    "1,2-dibromoethane (edb)": "1,2-Dibromoethane",
}


def resolve_chem(name: str, cas: str = "") -> str | None:
    digits = re.sub(r"\D", "", cas or "")
    if digits and digits in CHEM_CAS:
        return CHEM_CAS[digits]
    key = norm(name)
    if key in CHEM_OVERRIDES:
        return CHEM_OVERRIDES[key]
    return CHEM_NAME.get(key)


def resolve_country(name: str) -> str | None:
    raw = str(name).strip()
    if raw.upper() in {r["value"] for r in COUNTRY_ROWS}:
        return raw.upper()
    value = COUNTRY_NAME.get(norm(raw)) or COUNTRY_ALIAS.get(raw.upper())
    if value in {r["value"] for r in COUNTRY_ROWS}:
        return value
    return None


CARRIER_ALIASES = {
    "ANA": "All Nippon Airways", "SWISS": "Swiss International Air Lines", "THAI": "Thai Airways",
    "THAI Airways": "Thai Airways", "United": "United Airlines", "SAS": "Scandinavian Airlines",
    "MEA": "Middle East Airlines - Air Liban", "XiamenAir": "Xiamen Airlines",
    "Gol": "Gol Transportes Aereos", "JetSMART Airlines": "JetSMART",
    "Arajet S.A": "Arajet", "BOA Boliviana de Aviacion": "Boliviana de Aviacion",
    "Cubana de Aviación": "Cubana de Aviacion", "interCaribbean": "interCaribbean Airways",
    "Total Linhas Aéreas": "Total Linhas Aereas", "FedEx": "FedEx Express",
    "JetBlue": "JetBlue Airways", "Southwest": "Southwest Airlines", "UPS": "UPS Airlines",
    "Emirates Airlines": "Emirates", "TAAG Linhas Aereas DE Angola, SA": "TAAG Angola Airlines",
    "Qantas": "Qantas Airways", "China Eastern": "China Eastern Airlines",
}


def resolve_carrier(name: str) -> str | None:
    if name in CARRIER_ALIASES:
        return CARRIER_ALIASES[name]
    return CARRIER_NAME.get(norm(name))


def make_list(lid: str, name: str, official: list[tuple[str, str]], source: str,
              *, universe: str, disputed: set[str] | None = None,
              changes: list[dict] | None = None, synonyms: list[str] | None = None) -> dict:
    OFFICIAL_BY_LIST[lid] = list(official)
    values = set(r["value"] for r in (CHEM_ROWS if universe == "chemical" else COUNTRY_ROWS if universe == "country" else CARRIER_ROWS))
    resolver = resolve_chem if universe == "chemical" else resolve_country if universe == "country" else resolve_carrier
    members, outside = [], []
    for label, hint in official:
        v = resolver(label, hint) if universe == "chemical" else resolver(label)
        if v in values:
            members.append(v)
        else:
            outside.append(label)
    members = sorted(set(members))
    disputed_set = sorted(set(disputed or ()) & values)
    regular = sorted(set(members) - set(disputed_set))
    outside = sorted(set(outside))
    if len(regular) + len(disputed_set) + len(outside) != len(official):
        raise ValueError(f"{lid}: mapped {len(regular)}+{len(disputed_set)}+{len(outside)} != official {len(official)}")
    if len(regular) < 5:
        raise ValueError(f"{lid}: fewer than 5 regular members ({len(regular)})")
    return {
        "id": lid, "name": name, "synonyms": synonyms or [], "members": regular,
        "disputed": disputed_set, "changes": changes or [], "official_count": len(official),
        "out_of_universe": outside, "salience": 0.0, "source": source,
    }


def parse_wfd() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    soup = BeautifulSoup((RAW / "eu_wfd_directive_2013_39.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    all_items, hazard_items = [], []
    for tr in soup.find_all("tr", class_="oj-table"):
        cells = [" ".join(td.get_text(" ", strip=True).split()) for td in tr.find_all("td")]
        if len(cells) != 5 or not re.fullmatch(r"\(\d+\)", cells[0] or ""):
            continue
        name, cas, flag = cells[3], cells[1], (cells[4] if len(cells) > 4 else "")
        if not name:
            continue
        all_items.append((name, cas if cas.lower() != "not applicable" else ""))
        if flag.strip().upper().startswith("X"):
            hazard_items.append((name, cas if cas.lower() != "not applicable" else ""))
    return all_items, hazard_items


def iarc_group(group: str) -> list[tuple[str, str]]:
    return [(a["name"], a["cas"][0] if a["cas"] else "") for a in bu.read_iarc_agents() if a["group"] == group]


def mtcr_names() -> list[str]:
    soup = BeautifulSoup((RAW / "mtcr_partners.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    out = []
    for h in soup.find_all("h4"):
        text = " ".join(h.get_text(" ", strip=True).split())
        m = re.fullmatch(r"(.+?) \(\d{4}\)", text)
        if m:
            out.append(m.group(1))
    return out


def wassenaar_codes() -> list[str]:
    soup = BeautifulSoup((RAW / "wassenaar_home.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    special = {"ea": "ES", "sj": "NO", "hr": "HR", "gb": "GB", "kr": "KR"}
    out = []
    for img in soup.select("div.flags-slider img"):
        src = img.get("src", "")
        m = re.search(r"/([a-z]{2})\.svg", src)
        if m:
            out.append(special.get(m.group(1), m.group(1).upper()))
    return sorted(set(out))


def dedupe(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out, seen = [], set()
    for label, hint in items:
        key = (norm(label), re.sub(r"\D", "", hint or ""))
        if key not in seen:
            seen.add(key)
            out.append((label, hint))
    return out


def wikidata_country_codes(label: str) -> list[str]:
    data = json.loads((RAW / "wikidata_country_group_members.json").read_text(encoding="utf-8"))
    rows = data["results"]["bindings"]
    return sorted({r["iso"]["value"] for r in rows
                   if r.get("orgLabel", {}).get("value") == label and not r.get("end")})


def wikidata_entity_country_codes(filename: str, qid: str, prop: str) -> list[str]:
    data = json.loads((RAW / filename).read_text(encoding="utf-8"))
    entity = data["entities"][qid]
    out = []
    for claim in entity["claims"].get(prop, []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        item = value.get("id") if isinstance(value, dict) else None
        code = COUNTRY_QID.get(item)
        if code and code not in out:
            out.append(code)
    return sorted(out)


STOCKHOLM_A: list[tuple[str, str]] = [
    ("Aldrin", "309-00-2"), ("Alpha-hexachlorocyclohexane", "319-84-6"),
    ("Beta-hexachlorocyclohexane", "319-85-7"), ("Chlordane", "57-74-9"),
    ("Chlordecone", "143-50-0"), ("Chlorpyrifos", "2921-88-2"),
    ("Decabromodiphenyl ether", "1163-19-5"), ("Dechlorane Plus", "13560-89-9"),
    ("Dicofol", "115-32-2"), ("Dieldrin", "60-57-1"), ("Endrin", "72-20-8"),
    ("Heptachlor", "76-44-8"), ("Hexabromobiphenyl", "36355-01-8"),
    ("Hexabromocyclododecane", "25637-99-4"), ("Hexabromodiphenyl ether", "36483-60-0"),
    ("Heptabromodiphenyl ether", "68928-80-3"), ("Hexachlorobenzene", "118-74-1"),
    ("Hexachlorobutadiene", "87-68-3"), ("Lindane", "58-89-9"),
    ("Long-chain perfluorocarboxylic acids", ""),
    ("Medium-chain chlorinated paraffins", ""), ("Methoxychlor", "72-43-5"),
    ("Mirex", "2385-85-5"), ("Pentachlorobenzene", "608-93-5"),
    ("Pentachlorophenol", "87-86-5"), ("Perfluorohexane sulfonic acid", "355-46-4"),
    ("Perfluorooctanoic acid", "335-67-1"), ("Polychlorinated biphenyls", "1336-36-3"),
    ("Polychlorinated naphthalenes", "70776-03-3"),
    ("Short-chain chlorinated paraffins", "85535-84-8"),
    ("Technical endosulfan", "115-29-7"), ("Tetrabromodiphenyl ether", "40088-47-9"),
    ("Pentabromodiphenyl ether", "32534-81-9"), ("Toxaphene", "8001-35-2"),
    ("UV-328", "25973-55-1"),
]


STOCKHOLM_C: list[tuple[str, str]] = [
    ("Hexachlorobenzene", "118-74-1"), ("Hexachlorobutadiene", "87-68-3"),
    ("Pentachlorobenzene", "608-93-5"), ("Polychlorinated biphenyls", "1336-36-3"),
    ("2,3,7,8-Tetrachlorodibenzo-p-dioxin", "1746-01-6"),
    ("Polychlorinated naphthalenes", "70776-03-3"),
]


ROTTERDAM_PESTICIDES: list[tuple[str, str]] = [
    ("2,4,5-T", "93-76-5"), ("Alachlor", "15972-60-8"), ("Aldicarb", "116-06-3"),
    ("Aldrin", "309-00-2"), ("Azinphos-methyl", "86-50-0"), ("Binapacryl", "485-31-4"),
    ("Captafol", "2425-06-1"), ("Carbofuran", "1563-66-2"), ("Carbosulfan", "55285-14-8"),
    ("Chlordane", "57-74-9"), ("Chlordimeform", "6164-98-3"), ("Chlorobenzilate", "510-15-6"),
    ("DDT", "50-29-3"), ("Dieldrin", "60-57-1"), ("Dinitro-ortho-cresol", "534-52-1"),
    ("Dinoseb", "88-85-7"), ("1,2-Dibromoethane (EDB)", "106-93-4"),
    ("Endosulfan", "115-29-7"), ("Ethylene dichloride", "107-06-2"),
    ("Ethylene oxide", "75-21-8"), ("Fluoroacetamide", "640-19-7"),
    ("HCH (mixed isomers)", "608-73-1"), ("Heptachlor", "76-44-8"),
    ("Hexachlorobenzene", "118-74-1"), ("Lindane", "58-89-9"),
    ("Mercury compounds", ""), ("Methamidophos", "10265-92-6"),
    ("Monocrotophos", "6923-22-4"), ("Parathion", "56-38-2"),
    ("Pentachlorophenol", "87-86-5"), ("Phorate", "298-02-2"),
    ("Terbufos", "13071-79-9"), ("Toxaphene", "8001-35-2"),
    ("Trichlorfon", "52-68-6"), ("Dustable powder formulation of benomyl, carbofuran, and thiram", ""),
    ("Fenthion ultra-low-volume formulation", "55-38-9"),
    ("Phosphamidon soluble liquid formulation", "13171-21-6"),
    ("Methyl-parathion emulsifiable concentrate and dust", "298-00-0"),
]


ROTTERDAM_INDUSTRIAL: list[tuple[str, str]] = [
    ("Asbestos (all forms, including actinolite, amosite, anthophyllite, chrysotile, crocidolite, tremolite)", ""),
    ("Commercial octabromodiphenyl ether", ""), ("Commercial pentabromodiphenyl ether", ""),
    ("Decabromodiphenyl ether", "1163-19-5"), ("Hexabromocyclododecane", "25637-99-4"),
    ("Perfluorooctane sulfonic acid", "1763-23-1"), ("Perfluorooctanoic acid", "335-67-1"),
    ("Polybrominated biphenyls (PBB)", "36355-01-8"),
    ("Polychlorinated biphenyls (PCB)", "1336-36-3"),
    ("Polychlorinated terphenyls (PCT)", "61788-33-8"),
    ("Short-chain chlorinated paraffins", "85535-84-8"), ("Tetraethyl lead", "78-00-2"),
    ("Tetramethyl lead", "75-74-1"), ("Tris (2,3-dibromopropyl) phosphate", "126-72-7"),
    ("All tributyltin compounds", ""),
]


ROTTERDAM_ALL: list[tuple[str, str]] = dedupe(ROTTERDAM_PESTICIDES + ROTTERDAM_INDUSTRIAL)
STOCKHOLM_ALL: list[tuple[str, str]] = dedupe(STOCKHOLM_A + STOCKHOLM_C)


def opcw_rows(filename: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup((RAW / filename).read_text(encoding="utf-8", errors="replace"), "lxml")
    out = []
    for tr in soup.find_all("tr"):
        cells = [" ".join(x.get_text(" ", strip=True).split()) for x in tr.find_all(["th", "td"])]
        text = " | ".join(cells)
        for cas in re.findall(r"\b(\d{2,7}-\d{2}-\d)\b", text):
            label = next((c for c in cells if c and not re.search(r"^[\(\d,\s-]+\)?$", c)
                          and "CAS" not in c), "")
            shown = label if label and norm(label) not in {"e", "eg", "exemptions"} else f"CAS {cas}"
            out.append((f"{shown} [CAS {cas}]", cas))
    return dedupe(out)


def montreal_named_substances() -> list[tuple[str, str]]:
    """Rows in Montreal Annexes A/B/C/E/F that carry a common substance designation."""
    reader = PdfReader(RAW / "montreal_handbook_2020.pdf")
    text = "\n".join((reader.pages[i].extract_text() or "") for i in range(48, 53))
    text = text.replace("\u2011", "-").replace("\u2013", "-")
    names = []
    for code in re.findall(r"\b(?:CFC|HCFC|HBFC|HFC)-[A-Za-z0-9-]+", text):
        if code not in names:
            names.append(code)
    names.extend(["Halon-1211", "Halon-1301", "Halon-2402"])
    names.extend(["Carbon tetrachloride", "Methyl chloroform", "Methyl bromide", "Bromochloromethane"])
    return [(name, "") for name in names]


def iarc_group(group: str) -> list[tuple[str, str]]:
    out, seen = [], set()
    for a in bu.read_iarc_agents():
        cas = re.sub(r"\D", "", a["cas"][0]) if a["group"] == group and a["cas"] else ""
        if cas and cas not in seen:
            seen.add(cas)
            out.append((a["name"], a["cas"][0]))
    return out


def stars() -> list[tuple[str, str]]:
    soup = BeautifulSoup((RAW / "staralliance_members.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    meta = soup.find("meta", attrs={"name": "keywords"})
    words = [x.strip() for x in (meta.get("content") if meta else "").split(",")]
    stop = words.index("Star Alliance network")
    return [(x, "") for x in words[:stop] if x and not x.startswith("Star Alliance ")]


def oneworld_members() -> list[tuple[str, str]]:
    return [(x, "") for x in [
        "Alaska Airlines", "American Airlines", "British Airways", "Cathay Pacific",
        "Fiji Airways", "Finnair", "Iberia", "Japan Airlines", "Malaysia Airlines",
        "Oman Air", "Philippine Airlines", "Qantas", "Qatar Airways", "Royal Air Maroc",
        "Royal Jordanian", "SriLankan Airlines",
    ]]


def skyteam_members() -> list[tuple[str, str]]:
    return [(x, "") for x in [
        "Aerolineas Argentinas", "Aeromexico", "Air Europa", "Air France", "China Airlines",
        "China Eastern", "Delta Air Lines", "Garuda Indonesia", "Kenya Airways", "KLM",
        "Korean Air", "Middle East Airlines - Air Liban", "SAS", "Saudia", "TAROM",
        "Vietnam Airlines", "Virgin Atlantic", "Xiamen Airlines",
    ]]


def alta_panel(index: int) -> list[tuple[str, str]]:
    soup = BeautifulSoup((RAW / "alta_members.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    panels = soup.select("[role=tabpanel]")
    names = [(" ".join((im.get("title") or "").split()), "") for im in panels[index].find_all("img")]
    return dedupe([x for x in names if x[0]])


def a4a_members() -> list[tuple[str, str]]:
    soup = BeautifulSoup((RAW / "airlines_for_america_members.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    wanted = {"Air Canada", "Alaska Airlines", "American Airlines", "Atlas Air", "Delta Air Lines",
              "FedEx", "JetBlue", "Southwest", "United Airlines", "UPS"}
    out = []
    for im in soup.find_all("img"):
        alt = " ".join((im.get("alt") or "").split())
        if alt in wanted:
            out.append((alt, ""))
    return dedupe(out)


def a4e_members() -> list[tuple[str, str]]:
    soup = BeautifulSoup((RAW / "a4e_our_members.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    wanted = {
        "Aegean Airlines", "airBaltic", "Air France-KLM Group", "Cargolux", "easyJet",
        "Finnair", "Icelandair", "International Airlines Group (IAG)", "Jet2.com",
        "Lufthansa Group", "Norwegian", "Ryanair Holdings", "Smartwings", "TAP Air Portugal",
        "TUI", "Volotea",
    }
    out = [(alt, "") for im in soup.find_all("img")
           if (alt := " ".join((im.get("alt") or "").split())) in wanted]
    return dedupe(out)


def country_by_codes(codes: list[str]) -> list[tuple[str, str]]:
    return [(c, "") for c in codes]


def eu_1958_members() -> list[str]:
    soup = BeautifulSoup((RAW / "eu_member_states.html").read_text(encoding="utf-8", errors="replace"), "lxml")
    out = []
    for link in soup.select('a[href*="/eu-countries/"]'):
        article = link.find_parent("article")
        if article is None or "EU Member State since 1958" not in article.get_text(" ", strip=True):
            continue
        code = resolve_country(link.get_text(" ", strip=True))
        if code and code not in out:
            out.append(code)
    return sorted(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wfd, wfd_hazard = parse_wfd()
    eu = country_by_codes([
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU",
        "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    ])
    eu_1958 = country_by_codes(eu_1958_members())
    nato = country_by_codes([
        "AL", "BE", "BG", "CA", "HR", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU",
        "IS", "IT", "LV", "LT", "LU", "ME", "NL", "MK", "NO", "PL", "PT", "RO", "SK",
        "SI", "ES", "SE", "TR", "GB", "US",
    ])
    schengen = country_by_codes([
        "AT", "BE", "BG", "HR", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IS",
        "IT", "LV", "LI", "LT", "LU", "MT", "NL", "NO", "PL", "PT", "RO", "SK", "SI",
        "ES", "SE", "CH",
    ])
    commonwealth = country_by_codes(wikidata_country_codes("Commonwealth of Nations"))
    g7 = country_by_codes(wikidata_entity_country_codes("wikidata_g7_entity.json", "Q1764511", "P710"))
    gcc = country_by_codes(wikidata_entity_country_codes("wikidata_gcc_entity.json", "Q217172", "P527"))
    asean = country_by_codes(wikidata_country_codes("ASEAN"))
    arab = country_by_codes(wikidata_country_codes("Arab League"))
    nsg = country_by_codes(wikidata_country_codes("Nuclear Suppliers Group"))
    australia = country_by_codes(wikidata_country_codes("Australia Group"))
    mtcr = [(x, "") for x in mtcr_names()]
    wassenaar = country_by_codes(wassenaar_codes())
    opec_data = json.loads((RAW / "wikidata_opec_members.json").read_text(encoding="utf-8"))
    opec = sorted({r["iso"]["value"] for r in opec_data["results"]["bindings"]
                   if not r.get("end") and r.get("iso", {}).get("value")})
    opcw_all = dedupe(opcw_rows("cwc_schedule_1.html") + opcw_rows("cwc_schedule_2.html")
                      + opcw_rows("cwc_schedule_3.html"))

    chemical = [
        make_list("stockholm_annex_a", "Stockholm Convention Annex A", STOCKHOLM_A,
                  "stockholm_convention_text_2025.pdf Annex A; stockholm_allpops.html",
                  universe="chemical",
                  disputed={"Long-chain perfluorocarboxylic acids", "Medium-chain chlorinated paraffins"},
                  changes=[
                      {"value": "Long-chain perfluorocarboxylic acids", "date": "2025-05-09", "change": "added"},
                      {"value": "Medium-chain chlorinated paraffins", "date": "2025-05-09", "change": "added"},
                  ]),
        make_list("stockholm_annex_c", "Stockholm Convention Annex C", STOCKHOLM_C,
                  "stockholm_convention_text_2025.pdf Annex C", universe="chemical"),
        make_list("rotterdam_pesticides", "Rotterdam Convention Annex III pesticides",
                  ROTTERDAM_PESTICIDES, "rotterdam_convention_text_2025.pdf Annex III pesticide rows",
                  universe="chemical"),
        make_list("rotterdam_industrial", "Rotterdam Convention Annex III industrial chemicals",
                  ROTTERDAM_INDUSTRIAL, "rotterdam_convention_text_2025.pdf Annex III industrial rows",
                  universe="chemical"),
        make_list("rotterdam_annex_iii", "Rotterdam Convention Annex III all chemicals",
                  ROTTERDAM_ALL, "rotterdam_convention_text_2025.pdf Annex III complete chemical table",
                  universe="chemical"),
        make_list("opcw_schedule_1", "Chemical Weapons Convention Schedule 1",
                  opcw_rows("cwc_schedule_1.html"), "cwc_schedule_1.html chemical rows",
                  universe="chemical"),
        make_list("opcw_schedule_2", "Chemical Weapons Convention Schedule 2",
                  opcw_rows("cwc_schedule_2.html"), "cwc_schedule_2.html chemical rows",
                  universe="chemical"),
        make_list("opcw_schedule_3", "Chemical Weapons Convention Schedule 3",
                  opcw_rows("cwc_schedule_3.html"), "cwc_schedule_3.html chemical rows",
                  universe="chemical"),
        make_list("opcw_all_schedules", "Chemical Weapons Convention scheduled chemicals (Schedules 1-3)",
                  opcw_all, "cwc_schedule_1.html; cwc_schedule_2.html; cwc_schedule_3.html chemical rows",
                  universe="chemical"),
        make_list("montreal_all_controlled_substances", "Montreal Protocol controlled substances",
                  montreal_named_substances(),
                  "montreal_handbook_2020.pdf Annexes A, B, C, E and F named substances",
                  universe="chemical"),
        make_list("iarc_group_1", "IARC Group 1 chemical agents", iarc_group("1"),
                  "iarc_loc_app.js group 1 records with CAS numbers", universe="chemical"),
        make_list("iarc_group_2a", "IARC Group 2A chemical agents", iarc_group("2A"),
                  "iarc_loc_app.js group 2A records with CAS numbers", universe="chemical"),
        make_list("iarc_group_2b", "IARC Group 2B chemical agents", iarc_group("2B"),
                  "iarc_loc_app.js group 2B records with CAS numbers", universe="chemical"),
        make_list("iarc_group_3", "IARC Group 3 chemical agents", dedupe(iarc_group("3")),
                  "iarc_loc_app.js group 3 records with CAS numbers", universe="chemical"),
        make_list("wfd_priority", "Water Framework Directive priority substances", wfd,
                  "eu_wfd_directive_2013_39.html Annex I table rows 1-45", universe="chemical"),
        make_list("wfd_hazardous", "Water Framework Directive priority hazardous substances",
                  wfd_hazard, "eu_wfd_directive_2013_39.html Annex I rows marked X",
                  universe="chemical"),
        make_list("montreal_annex_a_group_i", "Montreal Protocol Annex A Group I",
                  [("CFC-11", ""), ("CFC-12", ""), ("CFC-113", ""), ("CFC-114", ""), ("CFC-115", "")],
                  "montreal_handbook_2020.pdf Annex A Group I table", universe="chemical"),
        make_list("stockholm_all_pops", "Stockholm Convention all persistent organic pollutants",
                  STOCKHOLM_ALL, "stockholm_convention_text_2025.pdf Annex A and C; stockholm_allpops.html",
                  universe="chemical"),
    ]

    country = [
        make_list("eu", "European Union member states", eu,
                  "eu_member_states.html EU country index (27)", universe="country"),
        make_list("eu_1958", "EU member states since 1958", eu_1958,
                  "eu_member_states.html country cards marked EU Member State since 1958", universe="country"),
        make_list("nato", "NATO member countries", nato,
                  "nato_member_states.html member country pages (30)", universe="country",
                  disputed={"FI", "SE"},
                  changes=[{"value": "FI", "date": "2023-04-04", "change": "added"},
                           {"value": "SE", "date": "2024-03-07", "change": "added"}]),
        make_list("commonwealth", "Commonwealth of Nations member states", commonwealth,
                  "commonwealth_member_countries.html; Wikidata current membership", universe="country"),
        make_list("g7", "Group of Seven member countries", g7,
                  "wikidata_g7_entity.json P710 participants (7); wikipedia_g7.txt", universe="country"),
        make_list("gcc", "Gulf Cooperation Council member states", gcc,
                  "wikidata_gcc_entity.json P527 members (6); wikipedia_gcc.txt", universe="country"),
        make_list("asean", "ASEAN member states", asean,
                  "Wikidata current association membership; observer and 2025 accession disputed",
                  universe="country", disputed={"AU", "TL"},
                  changes=[{"value": "TL", "date": "2025-10-26", "change": "added"}]),
        make_list("arab_league", "Arab League member states", arab,
                  "Wikidata current Arab League membership", universe="country", disputed={"SY"}),
        make_list("mtcr", "Missile Technology Control Regime partners", mtcr,
                  "mtcr_partners.html partner country headings", universe="country"),
        make_list("nsg", "Nuclear Suppliers Group participating governments", nsg,
                  "Wikidata current Nuclear Suppliers Group membership", universe="country"),
        make_list("australia_group", "Australia Group participants", australia,
                  "Wikidata current Australia Group membership", universe="country"),
        make_list("wassenaar", "Wassenaar Arrangement participating states", wassenaar,
                  "wassenaar_home.html participating-state flags", universe="country"),
        make_list("schengen", "Schengen area countries", schengen,
                  "schengen_area.html Schengen country list", universe="country",
                  disputed={"BG", "RO"},
                  changes=[{"value": "BG", "date": "2025-01-01", "change": "added"},
                           {"value": "RO", "date": "2025-01-01", "change": "added"}]),
        make_list("opec", "OPEC member countries", [(code, "") for code in opec],
                  "wikidata_opec_members.json current membership statements", universe="country",
                  disputed={"GA"},
                  changes=[{"value": "GA", "date": "2025-01-01", "change": "withdrawn"}]),
    ]

    carrier = [
        make_list("star_alliance", "Star Alliance member airlines", stars(),
                  "staralliance_members.html member airline keywords (26)", universe="carrier",
                  changes=[{"value": "Scandinavian Airlines", "date": "2024-08-31", "change": "withdrawn"}]),
        make_list("oneworld", "oneworld member airlines", oneworld_members(),
                  "oneworld_members.html member and future-member cards (16)", universe="carrier",
                  disputed={"Philippine Airlines"},
                  changes=[{"value": "Philippine Airlines", "date": "2025-01-01", "change": "future member"}]),
        make_list("skyteam", "SkyTeam member airlines", skyteam_members(),
                  "skyteam_members.html member airline list (18)", universe="carrier",
                  disputed={"Scandinavian Airlines"},
                  changes=[{"value": "Scandinavian Airlines", "date": "2024-08-31", "change": "withdrawn"}]),
        make_list("alta_full", "ALTA full member airlines", alta_panel(0),
                  "alta_members.html FULL MEMBERS tab", universe="carrier"),
        make_list("alta_associate", "ALTA associate member airlines", alta_panel(1),
                  "alta_members.html ASSOCIATE MEMBERS tab", universe="carrier"),
        make_list("a4a", "Airlines for America member airlines", a4a_members(),
                  "airlines_for_america_members.html member airline logos (10)", universe="carrier"),
        make_list("a4e", "Airlines for Europe member groups and airlines", a4e_members(),
                  "a4e_our_members.html member logo labels (16)", universe="carrier"),
    ]

    payloads = {"chemical": chemical, "country": country, "carrier": carrier}
    for uname, rows in payloads.items():
        with (OUT / f"{uname}.yaml").open("w", encoding="utf-8") as fh:
            yaml.safe_dump(rows, fh, allow_unicode=True, sort_keys=False, width=1000)
        print(f"{uname}: {len(rows)} lists", file=sys.stderr)
        for row in rows:
            print(f"  {row['id']}: members={len(row['members'])} disputed={len(row['disputed'])} "
                  f"official={row['official_count']} outside={len(row['out_of_universe'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
