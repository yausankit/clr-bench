#!/usr/bin/env python3
"""Extract the ADD_SY_a5 official medicine lists from the stored raw sources.

The output is raw/add/r5/manifests/official_members.json.  Every entry records
the exact source term and a page/cell/line reference that can be checked against
the file under raw/add/r5/.  No network access is used.
"""
import csv
import html
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "add" / "r5"
OUT = RAW / "manifests" / "official_members.json"
SPEC = ROOT / "add_lists_spec_r5.tsv"


def squish(value):
    return " ".join(str(value or "").split())


def xml_text(element):
    return squish("".join(element.itertext()))


def table_rows(path, wanted_label):
    root = ET.parse(path).getroot()
    for table in root.iter("table-wrap"):
        label = xml_text(table.find("label")) if table.find("label") is not None else ""
        if label == wanted_label:
            return [[xml_text(cell) for cell in row.findall("th") + row.findall("td")]
                    for row in table.iter("tr")]
    raise SystemExit(f"{path}: table {wanted_label!r} not found")


def line_of(path, needle, start=0):
    pattern = squish(needle).lower()
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if number >= start and pattern in squish(html.unescape(line)).lower():
            return number
    return start or 1


def pdf_pages(path, pages):
    with pdfplumber.open(path) as pdf:
        return {number: pdf.pages[number - 1].extract_text() or "" for number in pages}


def clean_threshold(name):
    value = squish(name)
    value = re.sub(r"\s*\((?:>|<|as |e\.g\.|non-|sustained|long-term|oral|parenteral).*\)$", "", value,
                   flags=re.I)
    value = re.sub(r"\s+>.*$", "", value)
    value = re.sub(r"\s+as\s+.*$", "", value, flags=re.I)
    return value.strip(" .;")


def drug_name(name):
    value = clean_threshold(name)
    value = re.sub(r"^(?:Iron supplements\s*/\s*)", "", value, flags=re.I)
    value = re.sub(r"\s*\((?:crushable|non-crushable|prolonged-release|modified-release)\)$", "",
                   value, flags=re.I)
    return squish(value)


def entry(term, raw, evidence):
    return {"term": squish(term), "raw": str(raw), "evidence": squish(evidence)}


def beers_table_6():
    path = RAW / "sources" / "beers_2023.xml"
    rows = table_rows(path, "TABLE 6")
    official = []
    for index, cells in enumerate(rows[1:], 2):
        if len(cells) < 2 or not cells[0]:
            continue
        name = drug_name(cells[0])
        official.append(entry(name, path.relative_to(ROOT),
                              f"TABLE 6 row {index}, first cell: {name}"))
    return official


def eu7_table_1():
    path = RAW / "sources" / "eu7_pim_2015.xml"
    rows = table_rows(path, "Table 1")
    official, seen = [], set()
    for index, cells in enumerate(rows[1:], 2):
        if len(cells) < 2 or not cells[0]:
            continue
        name = drug_name(cells[0])
        key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        official.append(entry(name, path.relative_to(ROOT),
                              f"Table 1 row {index}, PIM cell: {cells[0]}"))
    return official


STOPP_L = [
    "morphine", "oxycodone", "fentanyl", "buprenorphine", "diamorphine", "methadone",
    "tramadol", "pethidine", "pentazocine", "paracetamol", "lidocaine", "gabapentin",
    "pregabalin",
]


def stopp_section_l():
    path = RAW / "sources" / "stopp_start_v3_supplement.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "Section L: Analgesic Drugs")
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
               if line.startswith("Section M:"))
    text = "\n".join(lines[start:end])
    official = []
    for name in STOPP_L:
        if name.lower() not in text.lower():
            raise SystemExit(f"STOPP section L does not name {name}")
        official.append(entry(name, path.relative_to(ROOT),
                              f"Section L, line {line_of(path, name, start + 1)}: Analgesic Drugs"))
    return official


class DrugList(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = self.in_row = False
        self.in_generic = False
        self.generic = ""
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and attrs.get("id") == "druglist":
            self.in_table = True
        if self.in_table and tag == "tr":
            self.in_row, self.generic = True, ""
        if self.in_table and self.in_row and tag == "td" and "dgeneric" in attrs.get("class", ""):
            self.in_generic = True

    def handle_data(self, data):
        if self.in_generic:
            self.generic += data

    def handle_endtag(self, tag):
        if tag == "td" and self.in_generic:
            self.rows.append(squish(self.generic))
            self.in_generic = False
        if tag == "tr":
            self.in_row = False
        if tag == "table" and self.in_table:
            self.in_table = False


def credible_composite():
    path = RAW / "sources" / "crediblemeds_qt_2013.html"
    parser = DrugList()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    official = []
    for name in parser.rows:
        if not name:
            continue
        official.append(entry(name, path.relative_to(ROOT),
                              f"table#druglist, generic-name cell, line {line_of(path, name)}: {name}"))
    return official


def markdown_rows(path):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if not parts or all(set(part) <= {"-", ":"} for part in parts):
            continue
        rows.append((number, parts))
    return rows


def fda_column(column_name):
    path = RAW / "sources" / "fda_cyp_transporter_examples.md"
    rows = markdown_rows(path)
    header_number, header = rows[0]
    column = header.index(column_name)
    official = []
    for number, parts in rows[1:]:
        if len(parts) <= column or not parts[column]:
            continue
        name = re.sub(r"\s+\d+$", "", parts[0]).strip()
        official.append(entry(name, path.relative_to(ROOT),
                              f"Table 1 line {number}, column {column_name}: {parts[column]}"))
    return official


WHO = {
    "who_eml_2023_s3_antiallergics": {
        "pages": [7], "heading": "3. ANTIALLERGICS AND MEDICINES USED IN ANAPHYLAXIS",
        "terms": ["dexamethasone", "epinephrine (adrenaline)", "hydrocortisone", "loratadine",
                  "cetirizine", "fexofenadine", "prednisolone", "prednisone"],
    },
    "who_eml_2023_s8_2_4_hormones": {
        "pages": [36, 37], "heading": "8.2.4 Hormones and antihormones",
        "terms": ["abiraterone", "enzalutamide", "anastrozole", "bicalutamide", "flutamide",
                  "nilutamide", "dexamethasone", "hydrocortisone", "leuprorelin", "goserelin",
                  "triptorelin", "methylprednisolone", "prednisolone", "prednisone", "tamoxifen"],
    },
    "who_eml_2023_s12_2_antiarrhythmics": {
        "pages": [41], "heading": "12.2 Antiarrhythmic medicines",
        "terms": ["bisoprolol", "carvedilol", "metoprolol", "digoxin", "epinephrine (adrenaline)",
                  "lidocaine", "verapamil", "amiodarone"],
    },
    "who_eml_2023_s12_4_heart_failure": {
        "pages": [43], "heading": "12.4 Medicines used in heart failure",
        "terms": ["bisoprolol", "carvedilol", "metoprolol", "digoxin", "enalapril", "furosemide",
                  "bumetanide", "torasemide", "hydrochlorothiazide", "chlorothiazide",
                  "chlorthalidone", "indapamide", "losartan", "spironolactone", "dopamine"],
    },
}


def who_sections():
    path = RAW / "sources" / "who_eml_2023.pdf"
    out = {}
    for lid, spec in WHO.items():
        pages = pdf_pages(path, spec["pages"])
        text = "\n".join(pages.values())
        if spec["heading"].lower() not in text.lower():
            raise SystemExit(f"{lid}: heading not found in PDF pages {spec['pages']}")
        official = []
        for term in spec["terms"]:
            compact = re.sub(r"[^a-z0-9]+", " ", term.lower()).strip()
            if compact not in re.sub(r"[^a-z0-9]+", " ", text.lower()):
                raise SystemExit(f"{lid}: term {term!r} not found in section text")
            page = next(number for number, page_text in pages.items()
                        if compact in re.sub(r"[^a-z0-9]+", " ", page_text.lower()))
            official.append(entry(term, path.relative_to(ROOT),
                                  f"page {page}, section {spec['heading']}: {term}"))
        out[lid] = official
    return out


def niosh_names(pages):
    path = RAW / "sources" / "niosh_hazardous_drugs_2024.pdf"
    out, seen = [], set()
    with pdfplumber.open(path) as pdf:
        for pageno in pages:
            page = pdf.pages[pageno - 1]
            words = [w for w in page.extract_words()
                     if w["x0"] < 170 and 145 < w["top"] < 710]
            lines = []
            for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
                if lines and abs(word["top"] - lines[-1][0]) < 2:
                    lines[-1][1].append(word["text"])
                else:
                    lines.append([word["top"], [word["text"]]])
            drug, last = [], None
            for top, parts in lines:
                text = " ".join(parts)
                if text.startswith(("*", "†", "Table")):
                    break
                if text == "Drug":
                    continue
                if last is not None and top - last > 14 and drug:
                    name = " ".join(drug)
                    if name not in seen:
                        seen.add(name)
                        out.append(name)
                    drug = []
                drug.extend(parts)
                last = top
            if drug:
                name = " ".join(drug)
                if name not in seen:
                    seen.add(name)
                    out.append(name)
    return out


def niosh_table(number, pages):
    path = RAW / "sources" / "niosh_hazardous_drugs_2024.pdf"
    names = niosh_names(pages)
    return [entry(name, path.relative_to(ROOT),
                  f"Table {number}, pages {pages[0]}-{pages[-1]}, drug column: {name}")
            for name in names]


ATC_L02 = ["L02AA", "L02AB", "L02AE", "L02AX", "L02BA", "L02BB", "L02BG", "L02BX"]


def atc_l02():
    official = []
    for code in ATC_L02:
        path = RAW / "sources" / f"class_{code}.html"
        text = path.read_text(encoding="latin-1", errors="replace")
        for match in re.finditer(r"<td>[A-Z0-9]{7}&nbsp;</td><td><a [^>]*>([^<]+)</a>", text):
            name = html.unescape(match.group(1)).strip()
            line = text.count("\n", 0, match.start()) + 1
            official.append(entry(name, path.relative_to(ROOT),
                                  f"{code} line {line}: {name}"))
    return official


RXCLASS = [
    ("rxclass_chloride_channel_interactions", "Chloride Channel Interactions",
     "N0000000156", "MEDRT", "MOA", "rxclass_selected_chloride_channel_interactions.json"),
    ("rxclass_adrenal_cortical_effect", "Adrenal Cortical Activity Alteration",
     "N0000008291", "MEDRT", "PE", "rxclass_selected_adrenal_cortical_effect.json"),
    ("rxclass_norepinephrine_effect", "Norepinephrine Activity Alteration",
     "N0000009765", "MEDRT", "PE", "rxclass_selected_norepinephrine_effect.json"),
    ("rxclass_serotonin_effect", "Serotonin Activity Alteration",
     "N0000009844", "MEDRT", "PE", "rxclass_selected_serotonin_effect.json"),
    ("rxclass_nervous_system_effect", "Nervous System Activity Alteration",
     "N0000009759", "FDASPL", "PE", "rxclass_selected_nervous_system_effect.json"),
    ("rxclass_transcription_factor_activity", "Transcription Factor Activity",
     "N0000000242", "FDASPL", "MOA", "rxclass_selected_transcription_factor_activity.json"),
    ("rxclass_cyp3a_inhibitors", "Cytochrome P450 3A Inhibitors",
     "N0000190114", "FDASPL", "MOA", "rxclass_selected_cyp3a_inhibitors.json"),
    ("rxclass_hormone_receptor_interactions", "Hormone Receptor Interactions",
     "N0000000257", "FDASPL", "MOA", "rxclass_selected_hormone_receptor_interactions.json"),
    ("rxclass_membrane_transporter_interactions", "Membrane Transporter Interactions",
     "N0000188367", "FDASPL", "MOA", "rxclass_selected_membrane_transporter_interactions.json"),
    ("rxclass_cellular_structure_effect", "Cellular Structure Alteration",
     "N0000008346", "MEDRT", "PE", "rxclass_selected_cellular_structure_effect.json"),
    ("rxclass_decreased_protein_synthesis", "Decreased Protein Synthesis",
     "N0000008841", "MEDRT", "PE", "rxclass_selected_decreased_protein_synthesis.json"),
]


def rxclass_lists():
    out = {}
    for lid, name, class_id, source, rel, filename in RXCLASS:
        path = RAW / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        members = payload.get("drugMemberGroup", {}).get("drugMember", [])
        official, seen = [], set()
        for index, member in enumerate(members, 1):
            term = squish(member["minConcept"]["name"])
            key = term.lower().replace("-", " ")
            if key in seen:
                continue
            seen.add(key)
            official.append(entry(term, path.relative_to(ROOT),
                                  f"drugMember #{index}, minConcept.name: {term}"))
        url = (f"https://rxnav.nlm.nih.gov/REST/rxclass/classMembers.json?"
               f"classId={class_id}&relaSource={source}")
        out[lid] = (name, f"NLM RxClass {rel} {source} class {class_id} — {url}", official)
    return out


SEARCH = {
    "beers_2023_t6_renal": "Beers criteria",
    "eu7_pim_2015_t1": "Potentially inappropriate medication",
    "stopp_start_v3_section_l": "STOPP/START criteria",
    "crediblemeds_composite_qt_2013": "QT prolongation",
    "fda_cyp_moderate_sensitive_substrates": "CYP3A4",
    "fda_transporter_substrates": "Membrane transport protein",
    "who_eml_2023_s3_antiallergics": "Anaphylaxis",
    "who_eml_2023_s8_2_4_hormones": "Hormone therapy",
    "who_eml_2023_s12_2_antiarrhythmics": "Antiarrhythmic agent",
    "who_eml_2023_s12_4_heart_failure": "Heart failure",
    "niosh_2024_table_1": "Hazardous drug",
    "niosh_2024_table_2": "Hazardous drug",
    "atc_l02": "Hormone therapy",
    "rxclass_chloride_channel_interactions": "Chloride channel",
    "rxclass_adrenal_cortical_effect": "Adrenal cortex",
    "rxclass_norepinephrine_effect": "Norepinephrine",
    "rxclass_serotonin_effect": "Serotonin",
    "rxclass_nervous_system_effect": "Nervous system",
    "rxclass_transcription_factor_activity": "Transcription factor",
    "rxclass_cyp3a_inhibitors": "CYP3A4",
    "rxclass_hormone_receptor_interactions": "Hormone receptor",
    "rxclass_membrane_transporter_interactions": "Membrane transport protein",
    "rxclass_cellular_structure_effect": "Cell structure",
    "rxclass_decreased_protein_synthesis": "Protein biosynthesis",
}


def main():
    beers = beers_table_6()
    eu7 = eu7_table_1()
    stopp = stopp_section_l()
    credible = credible_composite()
    cyp_mod = fda_column("CYP Mod SENS SUB")
    transporter = fda_column("TRNSP SUB")
    who = who_sections()
    niosh1 = niosh_table(1, range(18, 25))
    niosh2 = niosh_table(2, range(26, 34))
    atc = atc_l02()
    rx = rxclass_lists()

    expected = {
        "beers_2023_t6_renal": 24,
        "eu7_pim_2015_t1": 67,
        "stopp_start_v3_section_l": 13,
        "crediblemeds_composite_qt_2013": 150,
    }
    actual = {
        "beers_2023_t6_renal": len(beers),
        "eu7_pim_2015_t1": len(eu7),
        "stopp_start_v3_section_l": len(stopp),
        "crediblemeds_composite_qt_2013": len(credible),
    }
    if actual != expected:
        raise SystemExit(f"unexpected fixed-table counts: {actual}")
    if len(niosh1) != 106 or len(niosh2) != 130:
        raise SystemExit(f"NIOSH counts changed: {len(niosh1)}, {len(niosh2)}")
    if len(atc) != 35:
        raise SystemExit(f"ATC L02 count changed: {len(atc)}")

    payload = []
    fixed = [
        ("beers_2023_t6_renal", "Beers 2023 Table 6 renal-function precautions",
         "American Geriatrics Society 2023 Beers Criteria, Table 6 — medications that should be "
         "avoided or have their dosage reduced with varying levels of kidney function — "
         "https://pmc.ncbi.nlm.nih.gov/articles/PMC12478568/", beers),
        ("eu7_pim_2015_t1", "EU(7)-PIM list 2015",
         "EU(7)-PIM list for older people, Table 1 — PIM according to the EU(7)-PIM list — "
         "https://doi.org/10.1007/s00228-015-1860-9", eu7),
        ("stopp_start_v3_section_l", "STOPP/START v3, STOPP Section L: Analgesic Drugs",
         "STOPP/START criteria for potentially inappropriate prescribing in older people: "
         "version 3, STOPP Section L — https://doi.org/10.1007/s41999-023-00777-y", stopp),
        ("crediblemeds_composite_qt_2013", "CredibleMeds composite QT-drug list",
         "CredibleMeds, Composite List of All QTDrugs and the List of Drugs to Avoid for Patients "
         "with Congenital LQTS (archived 2013) — https://crediblemeds.org/", credible),
        ("fda_cyp_moderate_sensitive_substrates", "FDA moderate-sensitive CYP substrates",
         "FDA, Examples of Drugs that Interact with CYP Enzymes and Transporter Systems, Table 1, "
         "CYP Mod SENS SUB — https://www.fda.gov/drugs/drug-interactions-labeling/"
         "healthcare-professionals-fdas-examples-drugs-interact-cyp-enzymes-and-transporter-systems",
         cyp_mod),
        ("fda_transporter_substrates", "FDA transporter substrates",
         "FDA, Examples of Drugs that Interact with CYP Enzymes and Transporter Systems, Table 1, "
         "TRNSP SUB — https://www.fda.gov/drugs/drug-interactions-labeling/"
         "healthcare-professionals-fdas-examples-drugs-interact-cyp-enzymes-and-transporter-systems",
         transporter),
        ("who_eml_2023_s3_antiallergics", "WHO EML 2023 antiallergics and anaphylaxis",
         "WHO Model List of Essential Medicines, 23rd list (2023), section 3 — "
         "https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02", who["who_eml_2023_s3_antiallergics"]),
        ("who_eml_2023_s8_2_4_hormones", "WHO EML 2023 hormones and antihormones",
         "WHO Model List of Essential Medicines, 23rd list (2023), section 8.2.4 — "
         "https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02", who["who_eml_2023_s8_2_4_hormones"]),
        ("who_eml_2023_s12_2_antiarrhythmics", "WHO EML 2023 antiarrhythmic medicines",
         "WHO Model List of Essential Medicines, 23rd list (2023), section 12.2 — "
         "https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02", who["who_eml_2023_s12_2_antiarrhythmics"]),
        ("who_eml_2023_s12_4_heart_failure", "WHO EML 2023 medicines used in heart failure",
         "WHO Model List of Essential Medicines, 23rd list (2023), section 12.4 — "
         "https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02", who["who_eml_2023_s12_4_heart_failure"]),
        ("niosh_2024_table_1", "NIOSH 2024 hazardous drugs, Table 1",
         "NIOSH List of Hazardous Drugs in Healthcare Settings, 2024, Table 1 — "
         "https://www.cdc.gov/niosh/docs/2025-103/", niosh1),
        ("niosh_2024_table_2", "NIOSH 2024 hazardous drugs, Table 2",
         "NIOSH List of Hazardous Drugs in Healthcare Settings, 2024, Table 2 — "
         "https://www.cdc.gov/niosh/docs/2025-103/", niosh2),
        ("atc_l02", "ATC L02 endocrine therapy",
         "WHO ATC/DDD index L02 ENDOCRINE THERAPY — "
         "https://atcddd.fhi.no/atc_ddd_index/?code=L02&showdescription=no", atc),
    ]
    for lid, name, source, official in fixed:
        payload.append({"id": lid, "name": name, "source": source, "search": SEARCH[lid],
                        "official": official})
    for lid, (name, source, official) in rx.items():
        payload.append({"id": lid, "name": name, "source": source, "search": SEARCH[lid],
                        "official": official})

    if len(payload) != 24:
        raise SystemExit(f"expected 24 lists, got {len(payload)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    SPEC.write_text(
        "id\tname\tsource\tsearch\n" + "".join(
            f"{item['id']}\t{item['name']}\t{item['source']}\t{item['search']}\n"
            for item in payload), encoding="utf-8")
    for item in payload:
        print(f"{item['id']}\t{len(item['official'])}")


if __name__ == "__main__":
    main()
