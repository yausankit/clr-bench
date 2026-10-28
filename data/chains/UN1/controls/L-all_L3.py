"""Deterministic synthetic scholarship review world for CLR-Synth."""
import csv
import hashlib
import json
import random
from pathlib import Path

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["applicants.nationality", "applications.sponsor_company", "references.country"]
TASK = "Each application counts once for its funding programme unless a rule excludes that application."
ENTITY_NOUN = "funding programme"
ENTITY_NOUN_PLURAL = "funding programmes"

def _rng(seed, step, name):
    return random.Random(int(hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest(), 16))

def _values(name):
    path = Path(__file__).resolve().parent / "universes" / f"{name}.tsv"
    with path.open(encoding="utf-8", newline="") as f:
        return [r["value"] for r in csv.DictReader(f, delimiter="\t")]

def base_world(seed: int, step: str) -> dict:
    """A reproducible 36-programme world; trap facts are independent by application."""
    university = _values("university")
    country = _values("country")
    company = _values("sponsor_company")
    ru = _rng(seed, step, "application-university")
    rc = _rng(seed, step, "applicant-nationality")
    rs = _rng(seed, step, "sponsor-company")
    rr = _rng(seed, step, "reference-university")
    rrc = _rng(seed, step, "reference-country")
    rn = _rng(seed, step, "application-counts")
    projects = []
    applicants, references, applications = [], [], []
    for i in range(36):
        project_id = f"P{i+1:02d}"
        projects.append({"project_id": project_id})
        for j in range(4 + rn.randint(0, 4)):
            n = i * 10 + j + 1
            app_id = f"A{n:03d}"
            person_id = f"C{n:03d}"
            ref_id = f"R{n:03d}"
            applicants.append({"applicant_id": person_id, "nationality": rc.choice(country)})
            references.append({"reference_id": ref_id, "university": rr.choice(university),
                               "country": rrc.choice(country)})
            applications.append({
                "application_id": app_id, "project_id": project_id,
                "applicant_id": person_id, "reference_id": ref_id,
                "university": ru.choice(university), "sponsor_company": rs.choice(company),
            })
    return {"projects": projects, "applicants": applicants,
            "references": references, "applications": applications}

def entities(world) -> list[str]:
    return sorted(x["project_id"] for x in world["projects"])

def slots(world, field: str) -> list[tuple[str, str]]:
    if field == "applications.university" or field == "applications.sponsor_company":
        return sorted((r["project_id"], r["application_id"]) for r in world["applications"])
    if field == "references.country":
        by_id = {r["reference_id"]: r for r in world["references"]}
        return sorted((app["project_id"], by_id[app["reference_id"]]["reference_id"])
                      for app in world["applications"])
    if field == "applicants.nationality":
        by_id = {a["applicant_id"]: a for a in world["applicants"]}
        return sorted((r["project_id"], by_id[r["applicant_id"]]["applicant_id"])
                      for r in world["applications"])
    raise KeyError(field)

def set_value(world, field: str, pos: str, value: str) -> None:
    if field == "applications.university":
        row = next(r for r in world["applications"] if r["application_id"] == pos)
        row["university"] = value
    elif field == "applications.sponsor_company":
        row = next(r for r in world["applications"] if r["application_id"] == pos)
        row["sponsor_company"] = value
    elif field == "applicants.nationality":
        row = next(r for r in world["applicants"] if r["applicant_id"] == pos)
        row["nationality"] = value
    elif field == "references.country":
        row = next(r for r in world["references"] if r["reference_id"] == pos)
        row["country"] = value
    else:
        raise KeyError(field)

def total(world, entity: str, excluded: set[tuple[str, str]]) -> int:
    people = {x["applicant_id"]: x for x in world["applicants"]}
    count = 0
    for app in world["applications"]:
        if app["project_id"] != entity:
            continue
        person = people[app["applicant_id"]]
        if (("applications.university", app["application_id"]) in excluded or
            ("applications.sponsor_company", app["application_id"]) in excluded or
            ("applicants.nationality", person["applicant_id"]) in excluded or
            ("references.country", app["reference_id"]) in excluded):
            continue
        count += 1
    return count

def render(world, entity_ids: list[str]):
    selected = set(entity_ids)
    people = {x["applicant_id"]: x for x in world["applicants"]}
    refs = {x["reference_id"]: x for x in world["references"]}
    out = {"programmes": []}
    for project in sorted((x for x in world["projects"] if x["project_id"] in selected),
                          key=lambda x: x["project_id"]):
        records = []
        for app in sorted((x for x in world["applications"] if x["project_id"] == project["project_id"]),
                          key=lambda x: x["application_id"]):
            p, ref = people[app["applicant_id"]], refs[app["reference_id"]]
            records.append({"application_id": app["application_id"],
                "applicant": {"applicant_id": p["applicant_id"], "nationality": p["nationality"]},
                "university": app["university"], "sponsor_company": app["sponsor_company"],
                "reference": {"university": ref["university"], "country": ref["country"]}})
        out["programmes"].append({"project_id": project["project_id"], "applications": records})
    return out

def reference(data, excluded: dict[str, set[str]]) -> dict[str, int]:
    result = {}
    for programme in data["programmes"]:
        value = 0
        for app in programme["applications"]:
            if (app["university"] in excluded.get("applications.university", set()) or
                app["sponsor_company"] in excluded.get("applications.sponsor_company", set()) or
                app["applicant"]["nationality"] in excluded.get("applicants.nationality", set()) or
                app["reference"]["country"] in excluded.get("references.country", set())):
                continue
            value += 1
        result[programme["project_id"]] = value
    return result

def values(data, field: str) -> list[str]:
    out = []
    for programme in data["programmes"]:
        for app in programme["applications"]:
            if field == "applications.university": out.append(app["university"])
            elif field == "applications.sponsor_company": out.append(app["sponsor_company"])
            elif field == "applicants.nationality": out.append(app["applicant"]["nationality"])
            elif field == "references.country": out.append(app["reference"]["country"])
    return out


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'applicants.nationality': ['AL', 'CH', 'FR', 'ID', 'IL', 'JP', 'ME', 'MH', 'OM', 'SV', 'TC', 'US'], 'applications.sponsor_company': ['3M', 'Acciona', 'Apple Inc.', 'Chevron Corporation', 'Constellation Energy', 'ExxonMobil', 'Ferrovial', 'Paychex', 'Sherwin-Williams', 'Truist Financial', 'United Parcel Service', 'Warehouses De Pauw'], 'references.country': ['BB', 'CK', 'EG', 'GE', 'LA', 'LB', 'MM', 'MY', 'PE', 'PH', 'SS', 'TW']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
