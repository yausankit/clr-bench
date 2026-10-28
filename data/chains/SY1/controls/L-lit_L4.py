"""Synthetic health-plan review dataset (Synthea Nov-2021 CSV snapshot).

Entities are patients.  Each patient owns three kinds of records: medication fills, diagnoses and
procedures.  Every record counts one towards the patient's review total.  The three trap fields are
the medication ingredient, the diagnosis SNOMED code and the procedure SNOMED code.

Each patient's file is a seed-chosen sample of MIN_PER_FIELD..MAX_PER_FIELD records per table, so the
rendered input stays small (the full Synthea histories are much longer).
"""
import csv
import hashlib
import random
from pathlib import Path

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["medications.ingredient", "conditions.code", "procedures.code"]
TASK = ("Every record in a patient's file adds one to that patient's review total: each medication "
        "fill, each diagnosis and each procedure counts one.")
ENTITY_NOUN = "patient"
INPUT_FORMAT = ("The top-level JSON object has keys patients (ids), medications, conditions and "
                "procedures.  Each record row carries the patient id and its trap field: medications "
                "have ingredient, conditions and procedures have code (and a description).")

ROOT = Path(__file__).resolve().parent
FIELDS = ("medications.ingredient", "conditions.code", "procedures.code")
TABLES = {"medications.ingredient": "medications", "conditions.code": "conditions",
          "procedures.code": "procedures"}
_CACHE = {}
PERIOD = ("2015-01-01", "2021-12-31")
MIN_PER_FIELD = 3
MAX_PER_FIELD = 6
DATE_KEY = {"medications": "start", "conditions": "onset", "procedures": "date"}
VALUE_KEY = {"medications": "ingredient", "conditions": "code", "procedures": "code"}


def _in_period(stamp):
    return PERIOD[0] <= str(stamp)[:10] <= PERIOD[1]


def _rng(seed, step):
    return random.Random(int(hashlib.sha256(f"{seed}/{step}".encode()).hexdigest(), 16))


def _read(name):
    with (ROOT / "sources" / "synthea" / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _data():
    if _CACHE:
        return _CACHE
    ing = {}
    with (ROOT / "sources" / "ingredient_by_rxcui.tsv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            ing[row["rxcui"]] = row["ingredient"]
    meds = []
    for r in _read("medications.csv"):
        name = ing.get(r["CODE"])
        if not name or not _in_period(r["START"]):
            continue
        meds.append({"patient": r["PATIENT"], "start": r["START"][:10], "ingredient": name,
                     "dispenses": r.get("DISPENSES") or ""})
    conds = [{"patient": r["PATIENT"], "onset": r["START"][:10], "code": r["CODE"],
              "description": r["DESCRIPTION"]} for r in _read("conditions.csv") if _in_period(r["START"])]
    procs = [{"patient": r["PATIENT"], "date": r["START"][:10], "code": r["CODE"],
              "description": r["DESCRIPTION"]} for r in _read("procedures.csv") if _in_period(r["START"])]
    per = {}
    for table, rows in (("medications", meds), ("conditions", conds), ("procedures", procs)):
        for r in rows:
            per.setdefault(r["patient"], {}).setdefault(table, 0)
            per[r["patient"]][table] += 1
    eligible = sorted(p for p, c in per.items()
                      if c.get("medications", 0) >= 3 and c.get("conditions", 0) >= 3
                      and c.get("procedures", 0) >= 3)
    by = {"medications": {}, "conditions": {}, "procedures": {}}
    for table, rows in (("medications", meds), ("conditions", conds), ("procedures", procs)):
        for r in rows:
            by[table].setdefault(r["patient"], []).append(r)
    ent = {}
    for name in ("medicine", "condition", "procedure"):
        with (ROOT / "universes" / f"{name}.tsv").open(newline="", encoding="utf-8") as f:
            ent[name] = {r["value"]: r["entity"] for r in csv.DictReader(f, delimiter="\t")}
    _CACHE.update({"eligible": eligible, "by": by, "entity": ent})
    return _CACHE


def _thin(rows, rng, table):
    """Keep MIN_PER_FIELD..MAX_PER_FIELD rows of one table for one patient (earliest-first)."""
    order = lambda r: (r[DATE_KEY[table]], r[VALUE_KEY[table]])
    if len(rows) <= MIN_PER_FIELD:
        return sorted(rows, key=order)
    k = rng.randint(MIN_PER_FIELD, min(MAX_PER_FIELD, len(rows)))
    return sorted(rng.sample(rows, k), key=order)


def base_world(seed: int, step: str) -> dict:
    """A world: a seed-chosen sample of 45 patients, each with 3-6 records per table."""
    data = _data()
    rng = _rng(seed, step)
    sample = rng.sample(data["eligible"], min(45, len(data["eligible"])))
    patients = {}
    out = {"patients": patients, "medications": {}, "conditions": {}, "procedures": {}}
    counts = {"medications": 0, "conditions": 0, "procedures": 0}
    prefix = {"medications": "M", "conditions": "C", "procedures": "P"}
    for pid in sorted(sample):
        patients[pid] = {"id": pid}
        for table in ("medications", "conditions", "procedures"):
            rows = _thin(data["by"][table].get(pid, []),
                         _rng(seed, f"{step}/{pid}/{table}"), table)
            for row in rows:
                counts[table] += 1
                rid = f"{prefix[table]}{counts[table]:05d}"
                out[table][rid] = {"id": rid, "patient": pid, **row}
    return out


def entities(world):
    return sorted(world["patients"])


def slots(world, field):
    table = TABLES[field]
    return sorted((r["patient"], rid) for rid, r in world[table].items())


def set_value(world, field, pos, value):
    row = world[TABLES[field]][pos]
    if field == "medications.ingredient":
        row["ingredient"] = value
    else:
        row["code"] = value
        name = "condition" if field == "conditions.code" else "procedure"
        row["description"] = _data()["entity"][name][value]


def _value(world, field, pos):
    row = world[TABLES[field]][pos]
    return row["ingredient"] if field == "medications.ingredient" else row["code"]


def total(world, entity, excluded):
    skip = set(excluded)
    n = 0
    for field in FIELDS:
        table = TABLES[field]
        for rid, row in world[table].items():
            if row["patient"] == entity and (field, rid) not in skip:
                n += 1
    return n


def render(world, entity_ids):
    keep = set(entity_ids)
    return {"patients": [{"id": p} for p in sorted(keep)],
            "medications": [{k: r[k] for k in ("id", "patient", "start", "ingredient", "dispenses")}
                            for rid, r in sorted(world["medications"].items()) if r["patient"] in keep],
            "conditions": [{k: r[k] for k in ("id", "patient", "onset", "code", "description")}
                           for rid, r in sorted(world["conditions"].items()) if r["patient"] in keep],
            "procedures": [{k: r[k] for k in ("id", "patient", "date", "code", "description")}
                           for rid, r in sorted(world["procedures"].items()) if r["patient"] in keep]}


def reference(data, excluded):
    out = {p["id"]: 0 for p in data["patients"]}
    excl = {f: set(v) for f, v in (excluded or {}).items()}
    for row in data["medications"]:
        if row["ingredient"] not in excl.get("medications.ingredient", ()):
            out[row["patient"]] += 1
    for row in data["conditions"]:
        if row["code"] not in excl.get("conditions.code", ()):
            out[row["patient"]] += 1
    for row in data["procedures"]:
        if row["code"] not in excl.get("procedures.code", ()):
            out[row["patient"]] += 1
    return out


def values(data, field):
    key, col = {"medications.ingredient": ("medications", "ingredient"),
                "conditions.code": ("conditions", "code"),
                "procedures.code": ("procedures", "code")}[field]
    return [row[col] for row in data[key]]


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'conditions.code': ['195662009', '75498004'], 'medications.ingredient': ['Morphine'], 'procedures.code': ['11466000']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
