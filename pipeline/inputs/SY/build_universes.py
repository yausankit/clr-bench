"""Build universes/ from the frozen Synthea snapshot (sources/synthea), RxNorm ingredient
responses (raw/rxnav_ingredients) and the NLM MeSH 2025 descriptor file (raw/mesh/desc2025.xml).

Run from the dataset directory:  python3 build_universes.py
Deterministic: every output row is sorted by value.
"""
import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SYN = ROOT / "sources" / "synthea"
PERIOD = ("2015-01-01", "2021-12-31")


def in_period(stamp):
    """The chains' data period; values outside it are not part of this dataset."""
    return PERIOD[0] <= str(stamp)[:10] <= PERIOD[1]


def read_rows(name):
    with (SYN / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean_tag(desc):
    """Split a SNOMED description into (label, semantic tag)."""
    m = re.search(r"\s*\(([a-z /]+)\)?\s*$", desc)
    if m and m.group(1) in {"disorder", "finding", "situation", "procedure", "regime/therapy",
                            "physical object", "person", "event", "substance"}:
        return desc[:m.start()].strip(), m.group(1)
    return desc.strip(), "other"


# ---------------------------------------------------------------- medicine
DOSE_WORDS = (
    ("oral", ("oral", "mouth", "buccal", "sublingual")),
    ("inhaled", ("inhaler", "inhalant", "inhalation", "nebule", "nebulizer")),
    ("injectable", ("injection", "injectable", "syringe", "vial", "pen", "infusion", "intravenous")),
    ("topical", ("topical", "cream", "ointment", "gel", "lotion", "patch", "transdermal")),
    ("ophthalmic", ("ophthalmic", "eye")),
    ("nasal", ("nasal",)),
    ("rectal", ("rectal", "suppository")),
)
DOSE_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:MG|UNT|ML|MCG|G|MG/ML|UNT/ML|MG/ACTUAT|MG/HR)\b", re.I)


def dose_route(desc):
    low = desc.lower()
    hits = [name for name, words in DOSE_WORDS if any(w in low for w in words)]
    return "|".join(sorted(set(hits))) if hits else "?"


def load_ingredients():
    """RxCUI -> tuple of ingredient names from the RxNorm related.json (tty=IN) responses."""
    out = {}
    for p in sorted((ROOT / "raw" / "rxnav_ingredients").glob("*.json")):
        data = json.loads(p.read_text())
        names = []
        for group in data.get("relatedGroup", {}).get("conceptGroup", []) or []:
            for cp in group.get("conceptProperties") or []:
                names.append(cp["name"])
        out[p.stem] = tuple(sorted(set(n for n in names if n != "inert ingredients")))
    return out


def load_mesh_drug_names():
    names = set()
    for _, el in ET.iterparse(ROOT / "raw" / "mesh" / "desc2025.xml", events=("end",)):
        if el.tag != "DescriptorRecord":
            continue
        if any(t.text.startswith(("D", "C")) for t in el.findall("TreeNumberList/TreeNumber")):
            names.add((el.findtext("DescriptorName/String") or "").strip().lower())
        el.clear()
    return names


def medicine_rows():
    rx = load_ingredients()
    with (ROOT / "sources" / "ingredient_by_rxcui.tsv").open("w", encoding="utf-8") as f:
        f.write("rxcui\tingredient\n")
        for code in sorted(rx):
            if rx[code]:
                f.write(f"{code}\t{' / '.join(n[0].upper() + n[1:] for n in rx[code])}\n")
    mesh_drugs = load_mesh_drug_names()
    meds = read_rows("medications.csv")
    routes = {}
    values = {}

    def add(name, desc):
        key = name[0].upper() + name[1:]
        values.setdefault(key, set()).add(desc)
        routes.setdefault(key, set()).add(dose_route(desc))

    for row in meds:
        if not in_period(row["START"]):
            continue
        code, desc = row["CODE"], row["DESCRIPTION"]
        names = rx.get(code, ())
        if names:
            add(" / ".join(names), desc)
            continue
        head = DOSE_RE.split(desc, maxsplit=1)[0].strip()
        head = re.sub(r"^(?:\d+\s+HR\s+|NDA\d+\s+\d+\s+ACTUAT\s+)", "", head, flags=re.I)
        if head and head.lower() in mesh_drugs:
            add(head.lower(), desc)
    rows = ["value\tentity\taliases\tattr:route"]
    for value in sorted(values, key=lambda v: (v.lower(), v)):
        routes_v = "|".join(sorted(r for r in routes[value] if r != "?")) or "?"
        rows.append(f"{value}\t{value}\t{value.lower()}\t{routes_v}")
    (ROOT / "universes" / "medicine.tsv").write_text("\n".join(rows) + "\n")


# ---------------------------------------------------------------- MeSH body systems
MESH_SYSTEM = {
    "C01": "Infections", "C02": "Infections", "C03": "Parasitic diseases", "C04": "Neoplasms",
    "C05": "Musculoskeletal", "C06": "Digestive", "C07": "Stomatognathic", "C08": "Respiratory",
    "C09": "Otorhinolaryngologic", "C10": "Nervous", "C11": "Eye", "C12": "Skin",
    "C13": "Female genital", "C14": "Cardiovascular", "C15": "Hemic and lymphatic",
    "C16": "Congenital", "C17": "Skin", "C18": "Nutritional and metabolic", "C19": "Endocrine",
    "C20": "Immune", "C21": "Environment", "C22": "Animal", "C23": "Pathological conditions",
    "C24": "Occupational", "C25": "Chemically induced", "C26": "Wounds and injuries",
}


def norm(s):
    s = s.lower()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def mesh_systems():
    """SNOMED/MeSH name -> body system, from the MeSH tree numbers of the exact name."""
    byname = {}
    for _, el in ET.iterparse(ROOT / "raw" / "mesh" / "desc2025.xml", events=("end",)):
        if el.tag != "DescriptorRecord":
            continue
        trees = [t.text for t in el.findall("TreeNumberList/TreeNumber")]
        if any(t.startswith("C") for t in trees):
            name = (el.findtext("DescriptorName/String") or "").strip()
            terms = [name] + [t.text for t in el.findall("ConceptList/Concept/TermList/Term/String")]
            systems = sorted({MESH_SYSTEM[t.split(".")[0]] for t in trees if t.startswith("C")})
            for term in terms:
                key = norm(term)
                if key:
                    byname.setdefault(key, set()).update(systems)
        el.clear()
    return byname


def condition_rows():
    systems = mesh_systems()
    seen = {}
    for row in read_rows("conditions.csv"):
        if not in_period(row["START"]):
            continue
        code, desc = row["CODE"], row["DESCRIPTION"]
        label, tag = clean_tag(desc)
        seen.setdefault(code, {}).setdefault((label, tag), 0)
        seen[code][(label, tag)] += 1
    seen = {code: sorted(counts, key=lambda k: (-counts[k], k))[0] for code, counts in seen.items()}
    rows = ["value\tentity\tattr:semantic_tag\tattr:system"]
    for code, (label, tag) in sorted(seen.items()):
        sysnames = systems.get(norm(label), set())
        sysval = "|".join(sorted(sysnames)) if sysnames else "?"
        rows.append(f"{code}\t{label}\t{tag}\t{sysval}")
    (ROOT / "universes" / "condition.tsv").write_text("\n".join(rows) + "\n")


MESH_E = {
    "E01": "Diagnosis", "E02": "Therapeutics", "E03": "Anesthesia and analgesia",
    "E04": "Surgical procedures", "E05": "Investigative techniques", "E06": "Dentistry",
    "E07": "Equipment and supplies",
}


def mesh_e_systems():
    """MeSH descriptor name/term -> MeSH E-tree top-level category (for procedure codes)."""
    byname = {}
    for _, el in ET.iterparse(ROOT / "raw" / "mesh" / "desc2025.xml", events=("end",)):
        if el.tag != "DescriptorRecord":
            continue
        trees = [t.text for t in el.findall("TreeNumberList/TreeNumber")]
        if any(t.startswith("E") for t in trees):
            name = (el.findtext("DescriptorName/String") or "").strip()
            terms = [name] + [t.text for t in el.findall("ConceptList/Concept/TermList/Term/String")]
            systems = sorted({MESH_E[t.split(".")[0]] for t in trees if t.startswith("E") and t.split(".")[0] in MESH_E})
            for term in terms:
                key = norm(term)
                if key:
                    byname.setdefault(key, set()).update(systems)
        el.clear()
    return byname


def procedure_rows():
    systems = mesh_e_systems()
    cw = {}
    cwpath = ROOT / "raw" / "crosswalk" / "procedure.tsv"
    if cwpath.exists():
        cw = {r["code"]: r["mesh_descriptor"] for r in csv.DictReader(cwpath.open(), delimiter="\t")}
    seen = {}
    for row in read_rows("procedures.csv"):
        if not in_period(row["START"]):
            continue
        code, desc = row["CODE"], row["DESCRIPTION"]
        label, tag = clean_tag(desc)
        seen.setdefault(code, {}).setdefault((label, tag), 0)
        seen[code][(label, tag)] += 1
    seen = {code: sorted(counts, key=lambda k: (-counts[k], k))[0] for code, counts in seen.items()}
    rows = ["value\tentity\tattr:semantic_tag\tattr:system"]
    for code, (label, tag) in sorted(seen.items()):
        sysnames = systems.get(norm(cw.get(code, "")), set())
        rows.append(f"{code}\t{label}\t{tag}\t{'|'.join(sorted(sysnames)) if sysnames else '?'}")
    (ROOT / "universes" / "procedure.tsv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    medicine_rows()
    condition_rows()
    procedure_rows()
    for name in ("medicine", "condition", "procedure"):
        n = len((ROOT / "universes" / f"{name}.tsv").read_text().splitlines()) - 1
        print(name, n)
