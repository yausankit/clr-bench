"""Candidate construction (v2 spec section 2): one candidate per natural list C."""
from dataclasses import dataclass, asdict

from .inputs import seeded_order, period_bounds

N_T = 7


def attribute_class_lists(universe, lists):
    """Lists whose member set equals one class of a single-valued attribute."""
    out = {}
    single = universe.single_valued_attrs()
    for lst in lists:
        members = set(lst.members) & set(universe.values)
        for a in single:
            classes = {}
            for v in universe.values:
                vals = universe.attrs[v].get(a)
                if vals:
                    classes.setdefault(next(iter(vals)), set()).add(v)
            for cls, vs in classes.items():
                if vs == members:
                    out[lst.id] = f"attr:{a}={cls}"
    return out


def unstable_values(lst, cfg):
    start, snapshot = period_bounds(cfg)
    out = set()
    for ch in lst.changes:
        date = str(ch.get("date", ""))
        if date and date[:4] >= str(start)[:4] and date <= snapshot:
            out.add(str(ch.get("value")))
    return out


@dataclass
class Candidate:
    field: str
    universe: str
    C: str
    C_name: str
    A: str
    P_M: list
    N_p: str
    N_t: list
    comp_A: list
    checks: dict
    salience: float

    def pool(self):
        return [self.A, *self.P_M, self.N_p, *self.N_t]

    def members(self):
        return [self.A, *self.P_M]

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Candidate(**d)


class FieldContext:
    """Everything about one trap field that candidate construction needs."""

    def __init__(self, dataset, cfg, field_name):
        self.field = field_name
        self.uname = dataset.universe_of(field_name)
        self.universe = dataset.universes[self.uname]
        self.lists = dataset.lists.get(self.uname, [])
        self.by_id = {l.id: l for l in self.lists}
        self.cfg = cfg
        self.seed = cfg["seed"]
        values = set(self.universe.values)
        self.member_sets = {l.id: frozenset(l.members & values) for l in self.lists}
        self.attr_lists = attribute_class_lists(self.universe, self.lists)
        self.dataset = dataset
        spec = next((f for f in cfg["fields"] if f["field"] == field_name), {})
        chain_templates = [str(t) for t in spec.get("templates") or []]
        scen = [t for t in dataset.templates if t.field == field_name]
        order = chain_templates + [t.id for t in scen if t.id not in chain_templates]
        self.templates = [next(t for t in scen if t.id == tid) for tid in order if any(t.id == tid for t in scen)]

    def comp(self, value, c_id):
        c_set = self.member_sets[c_id]
        return sorted(l for l, s in self.member_sets.items()
                      if value in s and l != c_id and s != c_set)

    def c_order(self):
        """Lists named in the field's templates, highest salience first (stable in template order)."""
        seen, ids = set(), []
        for t in self.templates:
            for lid in t.plausible:
                if lid in self.by_id and lid not in seen and lid not in self.attr_lists:
                    seen.add(lid)
                    ids.append(lid)
        return sorted(ids, key=lambda lid: -self.by_id[lid].salience)

    def salience_sum(self, ids):
        return sum(self.by_id[i].salience for i in ids)


def build_candidate(fc, c_id, excluded, level, fixed=None):
    """Construct the candidate for list C, or return (None, reason). fixed=(A, P_M) keeps a certified choice of
    members and only rebuilds N_p and N_t around `excluded` (clrsynth certify pools)."""
    u = fc.universe
    C = fc.by_id[c_id]
    c_set = fc.member_sets[c_id]
    unstable = unstable_values(C, fc.cfg)
    blocked = set(excluded) | u.multi
    E_C = sorted(v for v in c_set if v not in C.disputed and v not in unstable and v not in blocked)
    if len(E_C) < 4:
        return None, f"{c_id}: fewer than 4 eligible members"
    comp = {v: fc.comp(v, c_id) for v in E_C}
    seed = fc.seed
    if fixed is not None and not ({fixed[0], *fixed[1]} <= set(E_C)):
        return None, f"{c_id}: certified members are excluded here"
    ranked = seeded_order(E_C, seed, "A", fc.field, c_id)
    ranked = sorted(ranked, key=lambda v: (-len(comp[v]), -fc.salience_sum(comp[v])))
    A = fixed[0] if fixed is not None else ranked[0]
    if len(comp[A]) < 2:
        return None, f"{c_id}: no member belongs to two competing lists"
    comp_A = set(comp[A])

    def attr_key(v):
        return tuple(sorted((a, tuple(sorted(s))) for a, s in u.attrs[v].items()))

    chosen = list(fixed[1]) if fixed is not None else []
    rest = [v for v in E_C if v != A]
    for i in range(0 if fixed is not None else 3):
        if not rest:
            return None, f"{c_id}: fewer than three members besides A"
        used_lists = set().union(*[set(comp[m]) | {c_id} for m in chosen]) if chosen else set()
        used_attrs = {attr_key(m) for m in chosen} | {attr_key(A)}
        order = seeded_order(rest, seed, "m", fc.field, c_id, i)
        order = sorted(order, key=lambda v: (len(set(comp[v]) & comp_A),
                                             len(set(comp[v]) & used_lists),
                                             attr_key(v) in used_attrs))
        chosen.append(order[0])
        rest.remove(order[0])
    P_M = chosen

    disputed = set(C.disputed) | unstable
    nonmembers = sorted(v for v in u.values
                        if v not in c_set and v not in disputed and v not in blocked)
    if len(nonmembers) < N_T + 1:
        return None, f"{c_id}: too few non-members"

    def np_score(v):
        hits = [l for l, s in fc.member_sets.items()
                if l != c_id and A in s and v in s and any(m in s for m in P_M)]
        return len(hits), fc.salience_sum(hits)
    order = seeded_order(nonmembers, seed, "Np", fc.field, c_id)
    order = sorted(order, key=lambda v: tuple(-x for x in np_score(v)))
    N_p = order[0]

    comp_ranked = sorted(comp_A, key=lambda l: (-fc.by_id[l].salience, l))
    t_vals, covered = [], set()
    pools = {l: seeded_order([v for v in fc.member_sets[l] if v in nonmembers and v != N_p],
                             seed, "t", fc.field, c_id, l) for l in comp_ranked}
    progress = True
    while (len(t_vals) < 3 or len(covered) < 2) and progress:
        progress = False
        for l in comp_ranked:
            pick = next((v for v in pools[l] if v not in t_vals), None)
            if pick is not None:
                t_vals.append(pick)
                covered.add(l)
                progress = True
            if len(t_vals) >= 3 and len(covered) >= 2:
                break
    for v in seeded_order(nonmembers, seed, "t-fill", fc.field, c_id):
        if len(t_vals) >= N_T:
            break
        if v != N_p and v not in t_vals:
            t_vals.append(v)
    t_vals = t_vals[:N_T]

    checks = {}
    pool = [A, *P_M, N_p, *t_vals]
    checks["H1"] = _h1(fc, c_id, A, P_M, N_p, t_vals, unstable)
    h2_lists = [l for l in comp_A if any(t in fc.member_sets[l] for t in t_vals)]
    checks["H2"] = {"pass": len(h2_lists) >= 2, "lists": sorted(h2_lists)}
    checks["H6"] = {"pass": not (set(pool) & set(excluded)), "excluded": len(excluded)}
    t_vals, h4 = _h4_repair(fc, c_id, A, P_M, N_p, t_vals, nonmembers, comp_A)
    checks["H4"] = h4
    if t_vals is not None:
        h2_lists = [l for l in comp_A if any(t in fc.member_sets[l] for t in t_vals)]
        checks["H2"] = {"pass": len(h2_lists) >= 2, "lists": sorted(h2_lists)}
    failed = [k for k, v in checks.items() if not v["pass"]]
    if failed or t_vals is None:
        return None, f"{c_id}: failed {','.join(failed) or 'H4'}"
    return Candidate(field=fc.field, universe=fc.uname, C=c_id, C_name=C.name, A=A, P_M=P_M,
                     N_p=N_p, N_t=t_vals, comp_A=sorted(comp_A), checks=checks,
                     salience=C.salience), None


def _h1(fc, c_id, A, P_M, N_p, N_t, unstable):
    c_set = fc.member_sets[c_id]
    C = fc.by_id[c_id]
    bad = []
    for v in [A, *P_M]:
        if v not in c_set or v in C.disputed or v in unstable or v in fc.universe.multi:
            bad.append(v)
    for v in [N_p, *N_t]:
        if v in c_set or v in C.disputed or v in unstable or v in fc.universe.multi:
            bad.append(v)
    if len(set([A, *P_M, N_p, *N_t])) != 12:
        bad.append("duplicate values")
    return {"pass": not bad, "bad": bad}


def _leaks(fc, members, nonmembers):
    """(attr, value) pairs that every member has and no non-member has: a surface feature that would
    separate the classes without knowing C (v4 symmetry (e), v2 H4')."""
    out = []
    for a in fc.universe.attr_names:
        shared = None
        for v in members:
            vals = set(fc.universe.attrs[v].get(a, set())) - {"?"}
            shared = vals if shared is None else shared & vals
        for val in sorted(shared or ()):
            if not any(val in fc.universe.attrs[v].get(a, set()) for v in nonmembers):
                out.append((a, val))
    return out


def _h4_repair(fc, c_id, A, P_M, N_p, N_t, nonmembers, comp_A):
    members = [A, *P_M]
    leaks = _leaks(fc, members, [N_p, *N_t])
    if not leaks:
        return N_t, {"pass": True, "repaired": []}
    t_vals = list(N_t)
    repaired = []
    for a, val in leaks:
        if not _leaks(fc, members, [N_p, *t_vals]):
            break
        sharer = next((v for v in seeded_order(nonmembers, fc.seed, "H4", fc.field, c_id, a, val)
                       if v != N_p and v not in t_vals and val in fc.universe.attrs[v].get(a, set())), None)
        if sharer is None:
            return None, {"pass": False, "leaks": [list(x) for x in leaks]}
        needed = set()
        for l in sorted(comp_A):
            hit = next((t for t in t_vals if t in fc.member_sets[l]), None)
            if hit:
                needed.add(hit)
        replace = next((t for t in reversed(t_vals) if t not in needed), t_vals[-1])
        t_vals[t_vals.index(replace)] = sharer
        repaired.append({"attr": a, "value": val, "out": replace, "in": sharer})
    leaks = _leaks(fc, members, [N_p, *t_vals])
    return (t_vals if not leaks else None), {"pass": not leaks, "repaired": repaired,
                                             "leaks": [list(x) for x in leaks]}


def candidates_for_slot(fc, excluded, level, tried=(), limit=8, avoid=None):
    """avoid: {C: values} a sibling chain already used as A and P_M for C; this chain builds C from other
    members, so chains that share a concept never share a trap."""
    out, reasons = [], []
    order = fc.c_order()
    order = [c for c in order if c not in (avoid or {})] + [c for c in order if c in (avoid or {})]  # reuse last
    for c_id in order:
        if c_id in tried:
            continue
        cand, why = build_candidate(fc, c_id, set(excluded) | set((avoid or {}).get(c_id, ())), level)
        if cand:
            out.append(cand)
            if len(out) >= limit:
                break
        else:
            reasons.append(why)
    return out, reasons


def allocate_slots(dataset, cfg):
    """v2 spec 2.4: round-robin over fields in config order, cap 2 per field (1 if <100 values)."""
    caps = {}
    order = []
    for spec in cfg["fields"]:
        f = spec["field"]
        u = dataset.universes[dataset.universe_of(f)]
        caps[f] = 1 if len(u.values) < 100 else 2
        order.append(f)
    slots, used = [], {f: 0 for f in order}
    total = int(cfg.get("slots", 5))
    while len(slots) < total:
        progressed = False
        for f in order:
            if len(slots) < total and used[f] < caps[f]:
                used[f] += 1
                slots.append(f)
                progressed = True
        if not progressed:
            raise ValueError(f"fields can fill only {len(slots)} of {total} slots; add a trap field")
    return [{"level": i + 1, "field": f} for i, f in enumerate(slots)]


def build_variants(fc, c_id, k_max, excluded=()):
    """Up to k_max candidates for list C with pairwise disjoint A and P_M: variant k avoids the A and P_M of
    variants 0..k-1, so sibling chains can share C without sharing a trap value."""
    out, avoid, reasons = [], set(), []
    for _ in range(k_max):
        cand, why = build_candidate(fc, c_id, set(excluded) | avoid, 1)
        if not cand:
            reasons.append(why)
            break
        out.append(cand)
        avoid |= {cand.A, *cand.P_M}
    return out, reasons

