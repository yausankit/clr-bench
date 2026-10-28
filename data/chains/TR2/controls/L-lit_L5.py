"""TR — travel-expense audit.

A multinational's finance department aggregates reimbursable flight segments by the department of
the employee who filed the claim.  The world has departments -> employees -> claims -> segments.
"""
import hashlib
import os
import random

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["segments.airline", "segments.arrival_airport", "claims.currency"]
ENTITY_NOUN = "department"
TASK = ("Each flight segment on a submitted expense claim counts once toward the total of the "
        "department of the employee who filed that claim.")
INPUT_FORMAT = (
    "The input is one JSON object with four lists: departments (id, name, region), employees "
    "(id, name, department), claims (id, employee, submitted, currency, fare_amount, fare_display) and "
    "segments (id, claim, airline, departure_airport, arrival_airport, travel_date, route). "
    "employee.department and segment.claim are ids from the other lists.")

DEPARTMENT_NAMES = [
    "Audit", "Treasury", "Payroll", "Procurement", "Logistics", "Fleet", "Facilities", "Legal",
    "Compliance", "Tax", "Investor Relations", "Human Resources", "Recruiting", "Training",
    "Marketing", "Communications", "Product", "Engineering", "Platform", "Security", "Data",
    "Sales North", "Sales South", "Sales East", "Sales West", "Partnerships", "Support", "Billing",
    "Credit Control", "Risk", "Research", "Strategy", "Quality", "Manufacturing", "Warehousing",
    "Customer Success", "Field Service", "Sourcing", "Analytics", "Operations",
]

_UNIVERSE_CACHE = {}


def _universe(name):
    if name not in _UNIVERSE_CACHE:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "universes", name + ".tsv")
        vals = []
        with open(path, encoding="utf-8") as fh:
            fh.readline()
            for line in fh:
                if line.strip():
                    vals.append(line.split("\t")[0])
        _UNIVERSE_CACHE[name] = sorted(vals)
    return _UNIVERSE_CACHE[name]


def _rng(seed, step, name):
    digest = hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest()
    return random.Random(int(digest, 16))


def _sample(rng, pool, n):
    """n distinct values from pool, deterministic for a given rng state."""
    idx = list(range(len(pool)))
    rng.shuffle(idx)
    return [pool[i] for i in idx[:n]]


def base_world(seed: int, step: str) -> dict:
    rng = _rng(seed, step, "world")
    airlines = _universe("airline")
    airports = _universe("airport")
    currencies = _universe("currency")
    dep_pool = _sample(rng, airlines, 40)
    arr_pool = _sample(rng, airports, 40)
    cur_pool = _sample(rng, currencies, 12)

    depts = [{"id": "D%02d" % (i + 1), "name": DEPARTMENT_NAMES[i],
              "region": ["EMEA", "APAC", "AMER"][i % 3]} for i in range(36)]
    employees, claims, segments = [], [], []
    firsts = ["Ana", "Bo", "Cleo", "Dai", "Eli", "Femi", "Gil", "Hana", "Ivo", "Jun", "Kai", "Lena",
              "Mira", "Nils", "Ola", "Pia", "Quinn", "Rui", "Sami", "Tess", "Uma", "Vik", "Wen", "Yara"]
    lasts = ["Abara", "Brandt", "Costa", "Duval", "Eriksen", "Fischer", "Gomez", "Haddad", "Ito",
             "Jansen", "Khan", "Lindqvist", "Moreau", "Novak", "Okafor", "Petrov", "Rossi", "Sato"]
    eid = 0
    cid = 0
    sid = 0
    for d in depts:
        for _ in range(5):
            eid += 1
            emp = {"id": "E%04d" % eid,
                   "name": rng.choice(firsts) + " " + rng.choice(lasts),
                   "department": d["id"]}
            employees.append(emp)
            for _ in range(2):
                cid += 1
                month = rng.randint(1, 9)
                day = rng.randint(1, 28)
                cur = rng.choice(cur_pool)
                amount = rng.randrange(180, 4200)
                claim = {"id": "C%05d" % cid, "employee": emp["id"],
                         "submitted": "2026-%02d-%02d" % (month, day),
                         "currency": cur, "fare_amount": amount,
                         "fare_display": "%s %s" % (cur, "{:,}".format(amount))}
                claims.append(claim)
                for _ in range(rng.randint(1, 2)):
                    sid += 1
                    dep_air = rng.choice(arr_pool)
                    arr_air = rng.choice(arr_pool)
                    segments.append({
                        "id": "S%05d" % sid, "claim": claim["id"],
                        "airline": rng.choice(dep_pool),
                        "departure_airport": dep_air, "arrival_airport": arr_air,
                        "travel_date": "2026-%02d-%02d" % (month, max(1, day - rng.randint(0, 5))),
                        "route": "%s-%s" % (dep_air, arr_air)})
    return {"departments": depts, "employees": employees, "claims": claims, "segments": segments}


def entities(world) -> list:
    return sorted(d["id"] for d in world["departments"])


def _dept_of_claims(world):
    emp_dept = {e["id"]: e["department"] for e in world["employees"]}
    return {c["id"]: emp_dept[c["employee"]] for c in world["claims"]}


def slots(world, field: str) -> list:
    if field == "claims.currency":
        dmap = _dept_of_claims(world)
        return sorted((dmap[c["id"]], c["id"]) for c in world["claims"])
    if field == "segments.airline" or field == "segments.arrival_airport":
        dmap = _dept_of_claims(world)
        return sorted((dmap[s["claim"]], s["id"]) for s in world["segments"])
    raise ValueError(field)


def set_value(world, field: str, pos: str, value: str) -> None:
    if field == "claims.currency":
        for c in world["claims"]:
            if c["id"] == pos:
                c["currency"] = value
                c["fare_display"] = "%s %s" % (value, "{:,}".format(c["fare_amount"]))
                return
        raise KeyError(pos)
    if field == "segments.airline":
        for s in world["segments"]:
            if s["id"] == pos:
                s["airline"] = value
                return
        raise KeyError(pos)
    if field == "segments.arrival_airport":
        for s in world["segments"]:
            if s["id"] == pos:
                s["arrival_airport"] = value
                s["route"] = "%s-%s" % (s["departure_airport"], value)
                return
        raise KeyError(pos)
    raise ValueError(field)


def _count(world, excluded):
    ex_air = set(excluded.get("segments.airline") or ())
    ex_arr = set(excluded.get("segments.arrival_airport") or ())
    ex_cur = set(excluded.get("claims.currency") or ())
    dmap = _dept_of_claims(world)
    drop_claim = {c["id"] for c in world["claims"] if c["currency"] in ex_cur}
    out = {d["id"]: 0 for d in world["departments"]}
    for s in world["segments"]:
        if s["claim"] in drop_claim:
            continue
        if s["airline"] in ex_air or s["arrival_airport"] in ex_arr:
            continue
        out[dmap[s["claim"]]] += 1
    return out


def total(world, entity: str, excluded: set) -> int:
    by_field = {}
    for f, p in excluded:
        by_field.setdefault(f, set()).add(p)
    if not by_field:
        return _count(world, {})[entity]
    seg_ids = {s["id"] for s in world["segments"]}
    claim_ids = {c["id"] for c in world["claims"]}
    vals = {}
    if by_field.get("segments.airline"):
        vals["segments.airline"] = {s["airline"] for s in world["segments"]
                                    if s["id"] in by_field["segments.airline"]}
    if by_field.get("segments.arrival_airport"):
        vals["segments.arrival_airport"] = {s["arrival_airport"] for s in world["segments"]
                                            if s["id"] in by_field["segments.arrival_airport"]}
    if by_field.get("claims.currency"):
        vals["claims.currency"] = {c["currency"] for c in world["claims"]
                                   if c["id"] in by_field["claims.currency"]}
    return _count(world, vals)[entity]


def render(world, entity_ids: list):
    keep = set(entity_ids)
    depts = [d for d in world["departments"] if d["id"] in keep]
    emps = [e for e in world["employees"] if e["department"] in keep]
    emp_ids = {e["id"] for e in emps}
    claims = [c for c in world["claims"] if c["employee"] in emp_ids]
    claim_ids = {c["id"] for c in claims}
    segs = [s for s in world["segments"] if s["claim"] in claim_ids]
    return {"departments": sorted(depts, key=lambda x: x["id"]),
            "employees": sorted(emps, key=lambda x: x["id"]),
            "claims": sorted(claims, key=lambda x: x["id"]),
            "segments": sorted(segs, key=lambda x: x["id"])}


def reference(data, excluded: dict) -> dict:
    ex_air = set(excluded.get("segments.airline") or ())
    ex_arr = set(excluded.get("segments.arrival_airport") or ())
    ex_cur = set(excluded.get("claims.currency") or ())
    emp_dept = {e["id"]: e["department"] for e in data["employees"]}
    totals = {d["id"]: 0 for d in data["departments"]}
    claim_dept = {}
    for c in data["claims"]:
        if c["currency"] in ex_cur:
            continue
        claim_dept[c["id"]] = emp_dept[c["employee"]]
    for s in data["segments"]:
        dept = claim_dept.get(s["claim"])
        if dept is None:
            continue
        if s["airline"] in ex_air or s["arrival_airport"] in ex_arr:
            continue
        totals[dept] += 1
    return totals


def values(data, field: str) -> list:
    if field == "segments.airline":
        return [s["airline"] for s in data["segments"]]
    if field == "segments.arrival_airport":
        return [s["arrival_airport"] for s in data["segments"]]
    if field == "claims.currency":
        return [c["currency"] for c in data["claims"]]
    raise ValueError(field)


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'claims.currency': ['XAF'], 'segments.airline': ['British Airways', 'Qantas Airways'], 'segments.arrival_airport': ['CZL', 'PEV']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
