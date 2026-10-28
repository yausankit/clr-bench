#!/usr/bin/env python3
"""Build the CH universes from the snapshots in raw/.

All generated rows come from the raw files in this directory. A small set of official short
names and category labels is kept here for normalisation. This script never reads another
dataset or another executor's work.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "universes"


def clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.replace("–", "-").replace("—", "-").replace("’", "'")
    return " ".join(s.split())


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(s).lower())


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, delimiter="\t", fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def pdf_text(name: str) -> str:
    r = pypdf.PdfReader(RAW / name)
    return "\n".join((p.extract_text() or "") for p in r.pages)


# Canonical generic name, CAS (identifier only), category, aliases.
CHEM_BASE: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("Aldrin", "309-00-2", "pesticide", ("aldrin",)),
    ("Alpha-hexachlorocyclohexane", "319-84-6", "pesticide", ("alpha hexachlorocyclohexane",)),
    ("Beta-hexachlorocyclohexane", "319-85-7", "pesticide", ("beta hexachlorocyclohexane",)),
    ("Chlordane", "57-74-9", "pesticide", ()),
    ("Chlordecone", "143-50-0", "pesticide", ()),
    ("Chlorpyrifos", "2921-88-2", "pesticide", ()),
    ("Decabromodiphenyl ether", "1163-19-5", "industrial_chemical", ("BDE-209",)),
    ("Dechlorane Plus", "13560-89-9", "industrial_chemical", ()),
    ("Dicofol", "115-32-2", "pesticide", ()),
    ("Dieldrin", "60-57-1", "pesticide", ()),
    ("Endrin", "72-20-8", "pesticide", ()),
    ("Heptachlor", "76-44-8", "pesticide", ()),
    ("Hexabromobiphenyl", "36355-01-8", "industrial_chemical", ()),
    ("Hexabromocyclododecane", "25637-99-4", "industrial_chemical", ("HBCDD",)),
    ("Hexabromodiphenyl ether", "36483-60-0", "industrial_chemical", ()),
    ("Heptabromodiphenyl ether", "68928-80-3", "industrial_chemical", ()),
    ("Hexachlorobenzene", "118-74-1", "persistent_pollutant", ("HCB",)),
    ("Hexachlorobutadiene", "87-68-3", "persistent_pollutant", ("HCBD",)),
    ("Lindane", "58-89-9", "pesticide", ("gamma-hexachlorocyclohexane",)),
    ("Long-chain perfluorocarboxylic acids", "", "industrial_chemical", ()),
    ("Medium-chain chlorinated paraffins", "", "industrial_chemical", ("MCCPs",)),
    ("Methoxychlor", "72-43-5", "pesticide", ()),
    ("Mirex", "2385-85-5", "pesticide", ()),
    ("Pentachlorobenzene", "608-93-5", "persistent_pollutant", ("PeCB",)),
    ("Pentachlorophenol", "87-86-5", "pesticide", ("PCP",)),
    ("Perfluorohexane sulfonic acid", "355-46-4", "industrial_chemical", ("PFHxS",)),
    ("Perfluorooctanoic acid", "335-67-1", "industrial_chemical", ("PFOA",)),
    ("Polychlorinated biphenyls", "1336-36-3", "persistent_pollutant", ("PCBs",)),
    ("Polychlorinated naphthalenes", "70776-03-3", "persistent_pollutant", ("PCNs",)),
    ("Short-chain chlorinated paraffins", "", "industrial_chemical", ("SCCPs",)),
    ("Technical endosulfan", "115-29-7", "pesticide", ("endosulfan",)),
    ("Tetrabromodiphenyl ether", "40088-47-9", "industrial_chemical", ()),
    ("Pentabromodiphenyl ether", "", "industrial_chemical", ()),
    ("Toxaphene", "8001-35-2", "pesticide", ()),
    ("UV-328", "25973-55-1", "industrial_chemical", ()),
    ("DDT", "50-29-3", "pesticide", ("dichlorodiphenyltrichloroethane",)),
    ("Perfluorooctane sulfonic acid", "1763-23-1", "industrial_chemical", ("PFOS",)),
    ("2,3,7,8-Tetrachlorodibenzo-p-dioxin", "1746-01-6", "persistent_pollutant", ("PCDD", "dioxin")),
    ("2,3,7,8-Tetrachlorodibenzofuran", "51207-31-9", "persistent_pollutant", ("PCDF",)),
    ("2,4,5-T", "93-76-5", "pesticide", ("2,4,5-trichlorophenoxyacetic acid",)),
    ("Alachlor", "15972-60-8", "pesticide", ()),
    ("Aldicarb", "116-06-3", "pesticide", ()),
    ("Azinphos-methyl", "86-50-0", "pesticide", ()),
    ("Binapacryl", "485-31-4", "pesticide", ()),
    ("Captafol", "2425-06-1", "pesticide", ()),
    ("Carbofuran", "1563-66-2", "pesticide", ()),
    ("Carbosulfan", "55285-14-8", "pesticide", ()),
    ("Chlordimeform", "6164-98-3", "pesticide", ()),
    ("Chlorobenzilate", "510-15-6", "pesticide", ()),
    ("Dinitro-ortho-cresol", "534-52-1", "pesticide", ("DNOC",)),
    ("Dinoseb", "88-85-7", "pesticide", ()),
    ("1,2-Dibromoethane", "106-93-4", "pesticide", ("EDB", "ethylene dibromide")),
    ("Ethylene dichloride", "107-06-2", "industrial_solvent", ("1,2-dichloroethane",)),
    ("Ethylene oxide", "75-21-8", "industrial_chemical", ()),
    ("Fluoroacetamide", "640-19-7", "pesticide", ()),
    ("HCH", "608-73-1", "pesticide", ("hexachlorocyclohexane",)),
    ("Mercury compounds", "7439-97-6", "heavy_metal_compound", ("mercury",)),
    ("Methamidophos", "10265-92-6", "pesticide", ()),
    ("Monocrotophos", "6923-22-4", "pesticide", ()),
    ("Parathion", "56-38-2", "pesticide", ()),
    ("Phorate", "298-02-2", "pesticide", ()),
    ("Terbufos", "13071-79-9", "pesticide", ()),
    ("Trichlorfon", "52-68-6", "pesticide", ()),
    ("Benomyl", "17804-35-2", "pesticide", ()),
    ("Thiram", "137-26-8", "pesticide", ()),
    ("Fenthion", "55-38-9", "pesticide", ()),
    ("Phosphamidon", "13171-21-6", "pesticide", ()),
    ("Methyl-parathion", "298-00-0", "pesticide", ("parathion-methyl",)),
    ("Commercial octabromodiphenyl ether", "32536-52-0", "industrial_chemical", ("octaBDE",)),
    ("Commercial pentabromodiphenyl ether", "", "industrial_chemical", ("pentaBDE",)),
    ("Polybrominated biphenyls", "59536-65-1", "industrial_chemical", ("PBB",)),
    ("Polychlorinated terphenyls", "61788-33-8", "industrial_chemical", ("PCT",)),
    ("Tetraethyl lead", "78-00-2", "heavy_metal_compound", ()),
    ("Tetramethyl lead", "75-74-1", "heavy_metal_compound", ()),
    ("Tris(2,3-dibromopropyl) phosphate", "126-72-7", "industrial_chemical", ()),
    ("Tributyltin oxide", "56-35-9", "pesticide", ()),
    ("Tributyltin fluoride", "1983-10-4", "pesticide", ()),
    ("Tributyltin methacrylate", "2155-70-6", "pesticide", ()),
    ("Tributyltin benzoate", "4342-36-3", "pesticide", ()),
    ("Tributyltin chloride", "1461-22-9", "pesticide", ()),
    ("Tributyltin linoleate", "24124-25-2", "pesticide", ()),
    ("Tributyltin naphthenate", "85409-17-2", "pesticide", ()),
    ("CFC-11", "75-69-4", "refrigerant", ("trichlorofluoromethane",)),
    ("CFC-12", "75-71-8", "refrigerant", ("dichlorodifluoromethane",)),
    ("CFC-113", "76-13-1", "refrigerant", ()),
    ("CFC-114", "76-14-2", "refrigerant", ()),
    ("CFC-115", "76-15-3", "refrigerant", ()),
    ("Halon-1211", "353-59-3", "refrigerant", ()),
    ("Halon-1301", "75-63-8", "refrigerant", ()),
    ("Halon-2402", "124-73-2", "refrigerant", ()),
    ("CFC-13", "75-72-9", "refrigerant", ()),
    ("CFC-111", "354-56-3", "refrigerant", ()),
    ("CFC-112", "76-12-0", "refrigerant", ()),
    ("CFC-211", "422-78-6", "refrigerant", ()),
    ("CFC-212", "3182-26-1", "refrigerant", ()),
    ("CFC-213", "2354-06-5", "refrigerant", ()),
    ("CFC-214", "29255-31-0", "refrigerant", ()),
    ("CFC-215", "4259-43-2", "refrigerant", ()),
    ("CFC-216", "661-97-2", "refrigerant", ()),
    ("CFC-217", "422-86-6", "refrigerant", ()),
    ("Carbon tetrachloride", "56-23-5", "industrial_solvent", ()),
    ("Methyl chloroform", "71-55-6", "industrial_solvent", ("1,1,1-trichloroethane",)),
    ("HCFC-21", "75-43-4", "refrigerant", ()),
    ("HCFC-22", "75-45-6", "refrigerant", ()),
    ("HCFC-31", "593-70-4", "refrigerant", ()),
    ("HCFC-121", "", "refrigerant", ()),
    ("HCFC-122", "", "refrigerant", ()),
    ("HCFC-123", "306-83-2", "refrigerant", ()),
    ("HCFC-124", "2837-89-0", "refrigerant", ()),
    ("HCFC-131", "", "refrigerant", ()),
    ("HCFC-132", "", "refrigerant", ()),
    ("HCFC-133", "", "refrigerant", ()),
    ("HCFC-141", "", "refrigerant", ()),
    ("HCFC-141b", "1717-00-6", "refrigerant", ()),
    ("HCFC-142", "", "refrigerant", ()),
    ("HCFC-142b", "75-68-3", "refrigerant", ()),
    ("HCFC-151", "", "refrigerant", ()),
    ("HCFC-221", "", "refrigerant", ()),
    ("HCFC-222", "", "refrigerant", ()),
    ("HCFC-223", "", "refrigerant", ()),
    ("HCFC-224", "", "refrigerant", ()),
    ("HCFC-225", "", "refrigerant", ()),
    ("HCFC-225ca", "422-56-0", "refrigerant", ()),
    ("HCFC-225cb", "507-55-1", "refrigerant", ()),
    ("HCFC-226", "", "refrigerant", ()),
    ("HCFC-231", "", "refrigerant", ()),
    ("HCFC-232", "", "refrigerant", ()),
    ("HCFC-233", "", "refrigerant", ()),
    ("HCFC-234", "", "refrigerant", ()),
    ("HCFC-235", "", "refrigerant", ()),
    ("HCFC-241", "", "refrigerant", ()),
    ("HCFC-242", "", "refrigerant", ()),
    ("HCFC-243", "", "refrigerant", ()),
    ("HCFC-244", "", "refrigerant", ()),
    ("HCFC-251", "", "refrigerant", ()),
    ("HCFC-252", "", "refrigerant", ()),
    ("HCFC-253", "", "refrigerant", ()),
    ("HCFC-261", "", "refrigerant", ()),
    ("HCFC-262", "", "refrigerant", ()),
    ("HCFC-271", "", "refrigerant", ()),
    ("Bromochloromethane", "74-97-5", "refrigerant", ()),
    ("Methyl bromide", "74-83-9", "pesticide", ("bromomethane",)),
    ("HFC-134", "359-35-3", "refrigerant", ()),
    ("HFC-134a", "811-97-2", "refrigerant", ()),
    ("HFC-143", "430-66-0", "refrigerant", ()),
    ("HFC-245fa", "460-73-1", "refrigerant", ()),
    ("HFC-365mfc", "406-58-6", "refrigerant", ()),
    ("HFC-227ea", "431-89-0", "refrigerant", ()),
    ("HFC-236cb", "677-56-5", "refrigerant", ()),
    ("HFC-236ea", "431-63-0", "refrigerant", ()),
    ("HFC-236fa", "690-39-1", "refrigerant", ()),
    ("HFC-245ca", "679-86-7", "refrigerant", ()),
    ("HFC-43-10mee", "138495-42-8", "refrigerant", ()),
    ("HFC-32", "75-10-5", "refrigerant", ()),
    ("HFC-125", "354-33-6", "refrigerant", ()),
    ("HFC-143a", "420-46-2", "refrigerant", ()),
    ("HFC-41", "593-53-3", "refrigerant", ()),
    ("HFC-152", "624-72-6", "refrigerant", ()),
    ("HFC-152a", "75-37-6", "refrigerant", ()),
    ("HFC-23", "75-46-7", "refrigerant", ()),
    ("Sarin", "107-44-8", "chemical_agent", ()),
    ("Soman", "96-64-0", "chemical_agent", ()),
    ("Tabun", "77-81-6", "chemical_agent", ()),
    ("VX", "50782-69-9", "chemical_agent", ()),
    ("Sulfur mustard", "505-60-2", "chemical_agent", ("mustard gas",)),
    ("Lewisite 1", "541-25-3", "chemical_agent", ()),
    ("Lewisite 2", "40334-69-8", "chemical_agent", ()),
    ("Lewisite 3", "40334-70-1", "chemical_agent", ()),
    ("HN1", "538-07-8", "chemical_agent", ("nitrogen mustard HN1",)),
    ("HN2", "51-75-2", "chemical_agent", ("nitrogen mustard HN2",)),
    ("HN3", "555-77-1", "chemical_agent", ("nitrogen mustard HN3",)),
    ("Ricin", "9009-86-3", "chemical_agent", ()),
    ("Saxitoxin", "35523-89-8", "chemical_agent", ()),
    ("DF", "676-99-3", "chemical_agent", ("methylphosphonyl difluoride",)),
    ("QL", "57856-11-8", "chemical_agent", ()),
    ("Chlorosarin", "1445-76-7", "chemical_agent", ()),
    ("Chlorosoman", "7040-57-5", "chemical_agent", ()),
    ("Amiton", "78-53-5", "chemical_agent", ()),
    ("PFIB", "382-21-8", "chemical_agent", ("perfluoroisobutene",)),
    ("BZ", "6581-06-2", "chemical_agent", ("3-quinuclidinyl benzilate",)),
    ("Methylphosphonyl dichloride", "676-97-1", "chemical_agent", ()),
    ("Dimethyl methylphosphonate", "756-79-6", "chemical_agent", ()),
    ("Fonofos", "944-22-9", "pesticide", ()),
    ("Arsenic trichloride", "7784-34-1", "chemical_agent", ()),
    ("2,2-Diphenyl-2-hydroxyacetic acid", "76-93-7", "chemical_agent", ()),
    ("Quinuclidin-3-ol", "1619-34-7", "chemical_agent", ()),
    ("Phosgene", "75-44-5", "chemical_agent", ()),
    ("Cyanogen chloride", "506-77-4", "chemical_agent", ()),
    ("Hydrogen cyanide", "74-90-8", "chemical_agent", ()),
    ("Chloropicrin", "76-06-2", "chemical_agent", ()),
    ("Phosphorus oxychloride", "10025-87-3", "chemical_agent", ()),
    ("Phosphorus trichloride", "7719-12-2", "chemical_agent", ()),
    ("Phosphorus pentachloride", "10026-13-8", "chemical_agent", ()),
    ("Trimethyl phosphite", "121-45-9", "chemical_agent", ()),
    ("Triethyl phosphite", "122-52-1", "chemical_agent", ()),
    ("Dimethyl phosphite", "868-85-9", "chemical_agent", ()),
    ("Diethyl phosphite", "762-04-9", "chemical_agent", ()),
    ("Sulfur monochloride", "10025-67-9", "chemical_agent", ()),
    ("Sulfur dichloride", "10545-99-0", "chemical_agent", ()),
    ("Thionyl chloride", "7719-09-7", "chemical_agent", ()),
    ("Ethyldiethanolamine", "139-87-7", "chemical_agent", ()),
    ("Methyldiethanolamine", "105-59-9", "chemical_agent", ()),
    ("Triethanolamine", "102-71-6", "chemical_agent", ()),
    ("Anthracene", "120-12-7", "industrial_chemical", ()),
    ("Atrazine", "1912-24-9", "pesticide", ()),
    ("Benzene", "71-43-2", "industrial_solvent", ()),
    ("Brominated diphenyl ethers", "32534-81-9", "industrial_chemical", ()),
    ("Cadmium compounds", "7440-43-9", "heavy_metal_compound", ("cadmium",)),
    ("C10-13 Chloroalkanes", "85535-84-8", "industrial_chemical", ()),
    ("Chlorfenvinphos", "470-90-6", "pesticide", ()),
    ("Isodrin", "465-73-6", "pesticide", ()),
    ("Di(2-ethylhexyl) phthalate", "117-81-7", "industrial_chemical", ("DEHP",)),
    ("Diuron", "330-54-1", "pesticide", ()),
    ("Fluoranthene", "206-44-0", "industrial_chemical", ()),
    ("Isoproturon", "34123-59-6", "pesticide", ()),
    ("Lead compounds", "7439-92-1", "heavy_metal_compound", ("lead",)),
    ("Naphthalene", "91-20-3", "industrial_chemical", ()),
    ("Nickel compounds", "7440-02-0", "heavy_metal_compound", ("nickel",)),
    ("Nonylphenols", "84852-15-3", "industrial_chemical", ()),
    ("Octylphenols", "140-66-9", "industrial_chemical", ()),
    ("Polyaromatic hydrocarbons", "", "industrial_chemical", ("PAHs",)),
    ("Benzo(a)pyrene", "50-32-8", "industrial_chemical", ()),
    ("Benzo(b)fluoranthene", "205-99-2", "industrial_chemical", ()),
    ("Benzo(k)fluoranthene", "207-08-9", "industrial_chemical", ()),
    ("Benzo(g,h,i)perylene", "191-24-2", "industrial_chemical", ()),
    ("Indeno(1,2,3-cd)pyrene", "193-39-5", "industrial_chemical", ()),
    ("Simazine", "122-34-9", "pesticide", ()),
    ("Tetrachloroethylene", "127-18-4", "industrial_solvent", ("perchloroethylene",)),
    ("Trichloroethylene", "79-01-6", "industrial_solvent", ()),
    ("Tributyltin compounds", "", "pesticide", ()),
    ("Trichlorobenzenes", "12002-48-1", "industrial_solvent", ()),
    ("Trichloromethane", "67-66-3", "industrial_solvent", ("chloroform",)),
    ("Trifluralin", "1582-09-8", "pesticide", ()),
    ("Quinoxyfen", "124495-18-7", "pesticide", ()),
    ("Dioxins and dioxin-like compounds", "", "persistent_pollutant", ()),
    ("Aclonifen", "74070-46-5", "pesticide", ()),
    ("Bifenox", "42576-02-3", "pesticide", ()),
    ("Cybutryne", "28159-98-0", "pesticide", ()),
    ("Cypermethrin", "52315-07-8", "pesticide", ()),
    ("Dichlorvos", "62-73-7", "pesticide", ()),
    ("Heptachlor epoxide", "1024-57-3", "pesticide", ()),
    ("Terbutryn", "886-50-0", "pesticide", ()),
    ("Dichloromethane", "75-09-2", "industrial_solvent", ("methylene chloride",)),
    ("Ephedrine", "299-42-3", "drug_precursor", ()),
    ("Pseudoephedrine", "90-82-4", "drug_precursor", ()),
    ("Norephedrine", "14838-15-4", "drug_precursor", ("phenylpropanolamine",)),
    ("Safrole", "94-59-7", "drug_precursor", ()),
    ("Piperonal", "120-57-0", "drug_precursor", ()),
    ("Anthranilic acid", "118-92-3", "drug_precursor", ()),
    ("N-Acetylanthranilic acid", "89-42-3", "drug_precursor", ()),
    ("Phenylacetic acid", "103-82-2", "drug_precursor", ()),
    ("Acetic anhydride", "108-24-7", "drug_precursor", ()),
    ("1-Phenyl-2-propanone", "103-79-7", "drug_precursor", ("phenylacetone",)),
    ("3,4-Methylenedioxyphenyl-2-propanone", "4676-39-5", "drug_precursor", ()),
    ("Lysergic acid", "82-58-6", "drug_precursor", ()),
    ("Ergometrine", "60-79-7", "drug_precursor", ()),
    ("Ergotamine", "113-15-5", "drug_precursor", ()),
    ("Toluene", "108-88-3", "industrial_solvent", ()),
    ("Xylene", "1330-20-7", "industrial_solvent", ()),
    ("Methanol", "67-56-1", "industrial_solvent", ()),
    ("Acetone", "67-64-1", "industrial_solvent", ()),
]


DESC_CHEM = {
    "pesticide": "Pesticide used to control insects, weeds, fungi, or other agricultural pests.",
    "persistent_pollutant": "Persistent organic pollutant that accumulates in living organisms and the environment.",
    "refrigerant": "Refrigerant or blowing agent used in cooling, insulation, and air-conditioning equipment.",
    "industrial_solvent": "Industrial solvent used in cleaning, degreasing, and chemical manufacturing.",
    "heavy_metal_compound": "Heavy-metal compound used in industrial processes and manufactured products.",
    "chemical_agent": "Highly toxic chemical agent whose production and transfer are tightly controlled.",
    "drug_precursor": "Chemical intermediate used in the manufacture of pharmaceutical products.",
    "industrial_chemical": "Industrial chemical used in manufacturing, coatings, plastics, or other processes.",
}


IARC_GROUPS = {"1": "iarc_group_1_chemicals", "2A": "iarc_group_2a_chemicals", "2B": "iarc_group_2b_chemicals"}
EXCLUDE_IARC = re.compile(r"infection|radiation|exposure|dust|fume|soot|smoke|exhaust|fibre|fiber|process|"
                          r"manufacture|beverage|diet|plant|herb|wood|coal|coke|asphalt|bitumen|rubber|leather|"
                          r"shale|gasification|welding|painting|printing|oil|waste|combustion|solar|ultraviolet", re.I)


def read_iarc_agents() -> list[dict]:
    text = (RAW / "iarc_loc_app.js").read_text(encoding="utf-8", errors="replace")
    out = []
    pat = re.compile(r'\{name:"((?:\\.|[^"\\])*)",group:"([^"]+)",cas:\[([^\]]*)\]')
    for m in pat.finditer(text):
        name = bytes(m.group(1), "utf-8").decode("unicode_escape")
        cas = [x.strip().strip('"') for x in m.group(3).split(",") if x.strip().strip('"')]
        out.append({"name": clean(name), "group": m.group(2), "cas": cas})
    return out


def build_chemical_rows() -> list[dict]:
    rows: dict[str, dict] = {}

    def add(name: str, cas: str, category: str, aliases: tuple[str, ...] = (), source: str = "") -> None:
        name = clean(name).strip(" .")
        if not name:
            return
        key = norm(name)
        cas_clean = re.sub(r"\D", "", cas or "")
        if key in rows:
            rows[key]["aliases"].update(clean(a) for a in aliases if clean(a))
            return
        rows[key] = {"value": name, "cas": cas_clean, "category": category,
                     "aliases": set(clean(a) for a in aliases if clean(a)), "source": source}

    for name, cas, cat, aliases in CHEM_BASE:
        add(name, cas, cat, aliases, "official annex / chemical record")
    for a in read_iarc_agents():
        if a["group"] not in IARC_GROUPS or not a["cas"] or EXCLUDE_IARC.search(a["name"]):
            continue
        cat = "industrial_chemical"
        if re.search(r"lead|cadmium|mercury|nickel|arsenic|beryllium|chromium|cobalt", a["name"], re.I):
            cat = "heavy_metal_compound"
        elif re.search(r"pesticide|insecticide|herbicide|fungicide|DDT|lindane|chlorpyrifos", a["name"], re.I):
            cat = "pesticide"
        add(a["name"], a["cas"][0], cat, (), "IARC Monographs list")

    out = []
    for key in sorted(rows, key=lambda k: (rows[k]["value"].casefold(), k)):
        r = rows[key]
        out.append({"value": r["value"], "entity": r["value"], "attr:category": r["category"],
                    "aliases": "|".join(sorted(r["aliases"])) if r["aliases"] else "",
                    "_cas": r["cas"], "_source": r["source"]})
    return out


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

COUNTRY_ALIASES = {
    "UNITED STATES OF AMERICA": "US", "UNITED STATES": "US", "USA": "US",
    "UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND": "GB", "UNITED KINGDOM": "GB",
    "RUSSIAN FEDERATION": "RU", "RUSSIA": "RU", "KOREA, REPUBLIC OF": "KR", "SOUTH KOREA": "KR",
    "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF": "KP", "NORTH KOREA": "KP",
    "IRAN, ISLAMIC REPUBLIC OF": "IR", "IRAN": "IR", "SYRIAN ARAB REPUBLIC": "SY", "SYRIA": "SY",
    "VIET NAM": "VN", "VIETNAM": "VN", "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "LA", "LAOS": "LA",
    "CZECH REPUBLIC": "CZ", "CZECHIA": "CZ", "TURKEY": "TR", "TURKIYE": "TR",
    "BOLIVIA, PLURINATIONAL STATE OF": "BO", "BOLIVIA": "BO", "VENEZUELA, BOLIVARIAN REPUBLIC OF": "VE",
    "VENEZUELA": "VE", "TANZANIA, UNITED REPUBLIC OF": "TZ", "TANZANIA": "TZ",
    "MOLDOVA, REPUBLIC OF": "MD", "MOLDOVA": "MD", "BRUNEI DARUSSALAM": "BN", "BRUNEI": "BN",
    "PALESTINE, STATE OF": "PS", "PALESTINE": "PS", "HOLY SEE": "VA", "VATICAN CITY": "VA",
    "COTE D'IVOIRE": "CI", "CÔTE D'IVOIRE": "CI", "IVORY COAST": "CI",
    "SWAZILAND": "SZ", "ESWATINI": "SZ", "CABO VERDE": "CV", "CAPE VERDE": "CV",
    "MICRONESIA, FEDERATED STATES OF": "FM", "MICRONESIA": "FM",
}


def build_country_rows() -> tuple[list[dict], dict[str, dict], dict[str, str]]:
    with (RAW / "country_codes.csv").open(encoding="utf-8", newline="") as fh:
        raw = list(csv.DictReader(fh))
    rows, info = [], {}
    for r in raw:
        if r.get("is_independent") != "Yes":
            continue
        code = r["ISO3166-1-Alpha-2"].strip().upper()
        name = clean(r.get("CLDR display name") or r.get("UNTERM English Short") or code)
        if not code or not name:
            continue
        info[code] = r
        rows.append({"value": code, "entity": name, "qid": r.get("wikidata_id", ""),
                     "attr:region": clean(r.get("Region Name", "")) or "?",
                     "attr:subregion": clean(r.get("Sub-region Name", "")) or "?",
                     "attr:continent": clean(r.get("Continent", "")) or "?"})
    rows.sort(key=lambda x: x["value"])
    alias: dict[str, str] = {}
    for r in raw:
        code = r.get("ISO3166-1-Alpha-2")
        if not code:
            continue
        for col in ("CLDR display name", "UNTERM English Short", "UNTERM English Formal", "official_name_en"):
            value = clean(r.get(col, "")).upper()
            if value:
                alias[value] = code
    alias.update(COUNTRY_ALIASES)
    return rows, info, alias


def country_desc(code: str, r: dict) -> str:
    name = clean(r.get("CLDR display name") or r.get("UNTERM English Short") or code)
    sub = clean(r.get("Sub-region Name", ""))
    cap = clean(r.get("Capital", ""))
    if sub and cap and cap.upper() != "N/A":
        return f"{name} is a country in {sub}; its capital is {cap}."
    if sub:
        return f"{name} is a country in {sub}."
    return f"{name} is an independent country."


# ---------------------------------------------------------------------------
# Air carriers
# ---------------------------------------------------------------------------

CARRIER_QID_NAMES = {
    "Q213147": "Korean Air", "Q740844": "S7 Airlines", "Q822130": "Bulgaria Air",
    "Q461631": "Iran Air", "Q83535": "Aerolineas Argentinas", "Q863432": "Biman Bangladesh Airlines",
    "Q387901": "Libyan Airlines", "Q794272": "Azul", "Q1189080": "Flyadeal",
}
DEFUNCT_CARRIERS = {"Czech Airlines", "Go First", "Air Namibia", "LIAT", "Air Malta"}

# Current carriers named on the official alliance and regional-association pages in raw/.
# The Wikidata top-active extraction omits several real members that do not carry an IATA
# code in that snapshot, so this short supplement keeps those official lists usable.
CARRIER_EXTRA: list[tuple[str, str, str, str, str]] = [
    ("KLM", "NL", "Amsterdam", "Netherlands", "skyteam_members.html"),
    ("Atlas Air", "US", "Purchase, New York", "United States", "airlines_for_america_members.html"),
    ("Arajet", "DO", "Santo Domingo", "Dominican Republic", "alta_members.html"),
    ("Aeromexico Connect", "MX", "Mexico City", "Mexico", "alta_members.html"),
    ("Bahamasair", "BS", "Nassau", "Bahamas", "alta_members.html"),
    ("Boliviana de Aviacion", "BO", "Cochabamba", "Bolivia", "alta_members.html"),
    ("Caribbean Airlines", "TT", "Port of Spain", "Trinidad and Tobago", "alta_members.html"),
    ("DHL Aero Expreso", "PA", "Panama City", "Panama", "alta_members.html"),
    ("interCaribbean Airways", "TC", "Providenciales", "Turks and Caicos Islands", "alta_members.html"),
    ("JetSMART", "CL", "Santiago", "Chile", "alta_members.html"),
    ("SANSA", "CR", "San Jose", "Costa Rica", "alta_members.html"),
    ("Sky Airline", "CL", "Santiago", "Chile", "alta_members.html"),
    ("Star Peru", "PE", "Lima", "Peru", "alta_members.html"),
    ("Sunrise Airways", "HT", "Port-au-Prince", "Haiti", "alta_members.html"),
    ("TAG Airlines", "GT", "Guatemala City", "Guatemala", "alta_members.html"),
    ("Total Linhas Aereas", "BR", "Belo Horizonte", "Brazil", "alta_members.html"),
    ("Tropic Air", "BZ", "San Pedro", "Belize", "alta_members.html"),
    ("Wingo", "CO", "Bogota", "Colombia", "alta_members.html"),
]


def build_carrier_rows() -> list[dict]:
    data = json.loads((RAW / "wikidata_top_active_iata_airlines.json").read_text(encoding="utf-8"))
    bindings = data["results"]["bindings"]
    seen: dict[str, dict] = {}
    for r in bindings:
        qid = r["item"]["value"].rstrip("/").split("/")[-1]
        name = CARRIER_QID_NAMES.get(qid, clean(r.get("itemLabel", {}).get("value", "")))
        if not name or re.fullmatch(r"Q\d+", name):
            continue
        name = clean(name).strip(" .")
        if name in DEFUNCT_CARRIERS:
            continue
        seen[qid] = {"value": name, "qid": qid, "iso": r.get("iso", {}).get("value", ""),
                     "country": clean(r.get("countryLabel", {}).get("value", "")),
                     "hq": clean(r.get("hqLabel", {}).get("value", "")),
                     "sitelinks": int(r.get("sitelinks", {}).get("value", "0") or 0)}
    by_value: dict[str, dict] = {}
    for r in sorted(seen.values(), key=lambda x: (-x["sitelinks"], x["qid"])):
        by_value.setdefault(norm(r["value"]), r)
    for name, iso, hq, country, source in CARRIER_EXTRA:
        by_value.setdefault(norm(name), {"value": name, "qid": "", "iso": iso, "country": country,
                                         "hq": hq, "sitelinks": 0, "source": source})
    return sorted(by_value.values(), key=lambda x: (x["value"].casefold(), x["qid"]))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    chem = build_chemical_rows()
    write_tsv(OUT / "chemical.tsv", chem, ["value", "entity", "aliases", "attr:category"])
    with (OUT / "chemical.desc.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["value", "description", "source"])
        for r in chem:
            w.writerow([r["value"], DESC_CHEM[r["attr:category"]], r["_source"]])

    country, info, _ = build_country_rows()
    write_tsv(OUT / "country.tsv", country,
              ["value", "entity", "qid", "attr:region", "attr:subregion", "attr:continent"])
    with (OUT / "country.desc.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["value", "description", "source"])
        for r in country:
            w.writerow([r["value"], country_desc(r["value"], info[r["value"]]), "country_codes.csv"])

    carriers = build_carrier_rows()
    crows: dict[str, dict] = {}
    with (OUT / "country.tsv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            crows[r["value"]] = r
    carrier_rows = []
    for r in carriers:
        c = crows.get(r["iso"])
        carrier_rows.append({"value": r["value"], "entity": r["value"], "qid": r["qid"],
                             "attr:country": r["iso"] or "?",
                             "attr:region": (c.get("attr:region") if c else "") or "?"})
    write_tsv(OUT / "carrier.tsv", carrier_rows, ["value", "entity", "qid", "attr:country", "attr:region"])
    with (OUT / "carrier.desc.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["value", "description", "source"])
        for r in carriers:
            hq = r["hq"] or "an unspecified city"
            country_name = r["country"] or "an unspecified country"
            source = f"Wikidata {r['qid']}" if r["qid"] else f"Official member page {r['source']}"
            w.writerow([r["value"], f"Airline headquartered in {hq}, {country_name}.", source])

    print(f"chemical {len(chem)}; country {len(country)}; carrier {len(carriers)}")
    manifest = []
    for p in sorted(OUT.glob("*.tsv")):
        manifest.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (ROOT / "sources" / "UNIVERSE_SHA256SUMS").write_text("\n".join(manifest) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
