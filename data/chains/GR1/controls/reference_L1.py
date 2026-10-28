"""Synthetic conference travel grant world for GR."""
import csv
import hashlib
import json
import random
from pathlib import Path

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["applicants.nationality", "trips.airline", "applicants.university"]
TASK = "Each eligible itinerary segment contributes one to the total for its funding call."
ENTITY_NOUN = "funding call"
ENTITY_NOUN_PLURAL = "funding calls"
INPUT_FORMAT = "A JSON object containing batches, each with its applicant records and itinerary segment records."


def _rng(seed, step, name):
    return random.Random(int(hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest(), 16))


def _values(universe):
    path = Path(__file__).resolve().parent / "universes" / f"{universe}.tsv"
    with path.open(encoding="utf-8", newline="") as f:
        return sorted(row["value"] for row in csv.DictReader(f, delimiter="\t"))


def base_world(seed: int, step: str) -> dict:
    countries = _values("country")
    airlines = _values("airline")
    universities = _values("university")
    r_nat = _rng(seed, step, "applicant_nationality")
    r_uni = _rng(seed, step, "applicant_university")
    r_air = _rng(seed, step, "trip_airline")
    r_vol = _rng(seed, step, "itinerary_volume")
    r_amt = _rng(seed, step, "reimbursement_amount")
    applicants = {}
    batches = {}
    for b in range(40):
        bid = f"FC{b + 1:03d}"
        app_ids = []
        trips = []
        volume = 4 + r_vol.randrange(9)
        per_applicant = [1, 1, 1, 1]
        for _ in range(volume - 4):
            per_applicant[r_vol.randrange(4)] += 1
        trip_n = 0
        for a in range(4):
            aid = f"{bid}-A{a + 1}"
            app_ids.append(aid)
            applicants[aid] = {
                "id": aid,
                "nationality": countries[r_nat.randrange(len(countries))],
                "university": universities[r_uni.randrange(len(universities))],
            }
            for _ in range(per_applicant[a]):
                trip_n += 1
                tid = f"{bid}-T{trip_n:02d}"
                trips.append({
                    "id": tid,
                    "applicant_id": aid,
                    "airline": airlines[r_air.randrange(len(airlines))],
                    "reimbursement_usd": r_amt.randint(70, 1800),
                })
        batches[bid] = {"id": bid, "applicant_ids": app_ids, "trips": trips}
    return {"applicants": applicants, "batches": batches}


def entities(world) -> list[str]:
    return sorted(world["batches"])


def slots(world, field: str) -> list[tuple[str, str]]:
    out = []
    if field in ("applicants.nationality", "applicants.university"):
        for bid in sorted(world["batches"]):
            for aid in world["batches"][bid]["applicant_ids"]:
                out.append((bid, aid))
    elif field == "trips.airline":
        for bid in sorted(world["batches"]):
            for trip in sorted(world["batches"][bid]["trips"], key=lambda x: x["id"]):
                out.append((bid, trip["id"]))
    return sorted(out)


def set_value(world, field: str, pos: str, value: str) -> None:
    if field == "applicants.nationality":
        world["applicants"][pos]["nationality"] = value
    elif field == "applicants.university":
        world["applicants"][pos]["university"] = value
    elif field == "trips.airline":
        for batch in world["batches"].values():
            for trip in batch["trips"]:
                if trip["id"] == pos:
                    trip["airline"] = value
                    return
        raise KeyError(pos)
    else:
        raise KeyError(field)


def total(world, entity: str, excluded: set[tuple[str, str]]) -> int:
    batch = world["batches"][entity]
    count = 0
    for trip in batch["trips"]:
        aid = trip["applicant_id"]
        if ("trips.airline", trip["id"]) in excluded:
            continue
        if ("applicants.nationality", aid) in excluded or ("applicants.university", aid) in excluded:
            continue
        count += 1
    return count


def render(world, entity_ids: list[str]):
    batches = []
    for bid in sorted(set(entity_ids)):
        src = world["batches"][bid]
        applicants = [dict(world["applicants"][aid]) for aid in src["applicant_ids"]]
        trips = [dict(x) for x in sorted(src["trips"], key=lambda x: x["id"])]
        batches.append({"id": bid, "applicants": applicants, "trips": trips})
    return {"batches": batches}


def values(data, field: str) -> list[str]:
    out = []
    for batch in data.get("batches", []):
        if field == "applicants.nationality":
            out.extend(a["nationality"] for a in batch["applicants"])
        elif field == "applicants.university":
            out.extend(a["university"] for a in batch["applicants"])
        elif field == "trips.airline":
            out.extend(t["airline"] for t in batch["trips"])
    return out


def reference(data, excluded: dict[str, set[str]]) -> dict[str, int]:
    result = {}
    ex_nat = set(excluded.get("applicants.nationality", set()))
    ex_uni = set(excluded.get("applicants.university", set()))
    ex_air = set(excluded.get("trips.airline", set()))
    for batch in data.get("batches", []):
        apps = {a["id"]: a for a in batch["applicants"]}
        count = 0
        for trip in batch["trips"]:
            applicant = apps[trip["applicant_id"]]
            if trip["airline"] in ex_air or applicant["nationality"] in ex_nat or applicant["university"] in ex_uni:
                continue
            count += 1
        result[str(batch["id"])] = count
    return result


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'applicants.nationality': ['BD', 'GB', 'GM', 'VC']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
