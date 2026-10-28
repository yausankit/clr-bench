"""A chain under construction: slots with candidates, labels, background values,
instance placement over the dataset interface, and prompt rendering."""
import copy
import json
from itertools import product

from .inputs import rng_for, seeded_order
from .candidates import Candidate

FEEDBACK = ("[FEEDBACK] The submitted program was wrong on the example input. The expected answer "
            "applies the L{j} rule to {obj} whose {fname} is {mv} in the same way as to {obj} whose "
            "{fname} is {a}, and does not apply it to {obj} whose {fname} is {np}.")
HINT_TITLE = "VERIFIED LESSON (correct, from the task designers):"
HINT = ('When a level rule applies to a labelled class and the report gives only one example value, the class '
        'is a real-world category that the label does not name: a named grouping that exists in this domain, '
        'such as an organisation, an alliance, an official list or a standard classification. Feedback that '
        'another value is treated like the example, and that some other value is not, tells you which '
        'category it is: choose the best-known named grouping that contains the example and the confirmed '
        'value and excludes the rejected one. Do not construct a category from a property you read in the '
        'descriptions, such as a region, a type of government, a climate or a size. Write that category by '
        'name into your notes together with the label. Then apply the rule to every value the report '
        'describes that belongs to that grouping, using each description only to identify what the value is '
        'and your knowledge of the grouping to decide membership, including values that never appeared in '
        'feedback, and leave out values that are not in the grouping. Before coding, go through every '
        'described value, decide membership for each one, and hard-code the complete member set.')

P0_QUESTION = ("Question: for each of the five level rules L1-L5, list which values from the Value reference "
               "(for that rule's field) belong to that rule's label. Answer only with JSON of the form "
               '{"L1": [...], "L2": [...], "L3": [...], "L4": [...], "L5": [...]}.')
CATEGORY_NOTE = ("Each label in the field notes stands for a real-world category of values; a note gives one member "
                 "of that category, and the label's name does not say which category it is.")
PAIR_NOTE = ("Some hidden test inputs are the example input below with one or two field values changed; each is "
             "judged by the same rules.")
P1_LOW, P1_HIGH = 1 / 6, 2 / 3   # default band for P1: feedback alone makes the class partly, not fully, recoverable
P1H_QUESTION = ("Question: for each of the five level rules L1-L5, write the category you think the label "
                "stands for, and list the values from the Value reference (for that rule's field) that belong "
                'to it. Answer only with JSON of the form {"L1": {"category": "...", "values": [...]}, ..., '
                '"L5": {"category": "...", "values": [...]}}.')


def p0_question(levels):
    """P0_QUESTION for the levels present (identical text for L1-L5)."""
    if list(levels) == [1, 2, 3, 4, 5]:
        return P0_QUESTION
    names = ", ".join(f"L{l}" for l in levels)
    form = ", ".join(f'"L{l}": [...]' for l in levels)
    return (f"Question: for each of the level rules {names}, list which values from the Value reference (for that "
            f"rule's field) belong to that rule's label. Answer only with JSON of the form {{{form}}}.")


def p1h_question(levels):
    if list(levels) == [1, 2, 3, 4, 5]:
        return P1H_QUESTION
    names = ", ".join(f"L{l}" for l in levels)
    form = ", ".join(f'"L{l}": {{"category": "...", "values": [...]}}' for l in levels)
    return (f"Question: for each of the level rules {names}, write the category you think the label stands for, "
            f"and list the values from the Value reference (for that rule's field) that belong to it. Answer only "
            f"with JSON of the form {{{form}}}.")


CONTRACT = {
    "json": "Write one Python 3 program in a single code block. Define solve(data), where data is the parsed JSON "
            "input (a dict), and return the answer as an int.",
    "text": "Write one Python 3 program in a single code block. Define solve(text), where text is the whole input "
            "as one string, and return the answer as an int.",
    "files": "Write one Python 3 program in a single code block. Define solve(files), where files is a dict mapping "
             "each file path to that file's text, and return the answer as an int.",
}
CODE_CHARS = "ABCDEFGHJKMNPQRSTVWXYZ"


def Dataset_default_nouns():
    return ["tenant class", "review tag", "routing bucket", "ledger code", "audit lane",
            "handling class", "queue tag", "settlement lane", "dispatch band"]


class PlacementError(Exception):
    pass


def split_field(field):
    table, _, name = field.rpartition(".")
    return (table or "records").replace("_", " "), name


def singular(noun):
    if noun.endswith("ies"):
        return noun[:-3] + "y"
    if noun.endswith(("sses", "uses", "xes", "ches", "shes")):
        return noun[:-2]          # classes, statuses, boxes, matches
    if noun.endswith("s") and not noun.endswith("ss"):
        return noun[:-1]          # raises, licenses, records
    return noun


def article(word):
    return "An" if word[:1].lower() in "aeiou" else "A"


class Chain:
    def __init__(self, dataset, cfg, slots):
        """slots: list of {level, field, cand: Candidate}."""
        self.ds = dataset
        self.cfg = cfg
        self.seed = cfg["seed"]
        self.slots = sorted(slots, key=lambda s: s["level"])
        self.mod = dataset.module
        self.fmt = self.mod.ANSWER_FORMAT
        self.fields = [spec["field"] for spec in cfg["fields"]]
        self.labels = self._labels()
        self.background = self._background()
        self._public = {}

    # ---------- static pieces ----------
    def _labels(self):
        import re
        nouns = seeded_order(self.ds.label_nouns(), self.seed, "label-nouns")
        out = {}
        used_codes, used_nouns = set(), set()
        stop = {"a", "an", "the", "of", "in", "and", "at", "for", "to", "on", "by"}
        data_words = self.data_words()
        nouns = [n for n in nouns if not ({w.lower() for w in n.split()} & data_words)] or \
            [n for n in seeded_order(Dataset_default_nouns(), self.seed, "label-nouns")
             if not ({w.lower() for w in n.split()} & data_words)]
        for i, s in enumerate(self.slots):
            c = s["cand"]
            lst = {l.id: l for l in self.ds.lists.get(c.universe, [])}.get(c.C)
            texts = [c.C.replace("_", " "), c.C_name] + (lst.synonyms if lst else [])
            c_words = {w.lower() for t in texts for w in re.findall(r"[A-Za-z]+", t)} - stop
            noun = next((n for n in nouns if n not in used_nouns
                         and not ({w.lower() for w in n.split()} & c_words)), None)
            if noun is None:
                noun = next(n for n in nouns if not ({w.lower() for w in n.split()} & c_words))
            used_nouns.add(noun)
            rng = rng_for(self.seed, "label-code", s["level"])
            shape = i % 3
            while True:
                if shape == 0:
                    code = f"{rng.choice(CODE_CHARS)}{rng.randint(2, 9)}"
                elif shape == 1:
                    code = f"{rng.randint(11, 98)}"
                else:
                    code = f"{rng.choice(CODE_CHARS)}-{rng.randint(10, 99)}"
                if code not in used_codes:
                    used_codes.add(code)
                    break
            out[s["level"]] = f"{noun} {code}"
        return out

    def data_words(self):
        """Words a reader would take for the data's own objects: table and field names, the entity noun and
        every key in a rendered example. A label must not use them ("in host 39" reads as a host id)."""
        import re
        words = set()

        def add(text):
            for w in re.findall(r"[A-Za-z]+", str(text).replace("_", " ")):
                words.add(w.lower())
                words.add(w.lower().rstrip("s"))
        for f in self.mod.TRAP_FIELDS:
            add(f)
        add(getattr(self.mod, "ENTITY_NOUN", ""))
        add(getattr(self.mod, "ENTITY_NOUN_PLURAL", ""))
        world = self.mod.base_world(self.seed, "label-words")
        example = self.mod.render(world, list(self.mod.entities(world))[:2])

        def keys(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    add(k)
                    keys(v)
            elif isinstance(x, list):
                for v in x:
                    keys(v)
        if isinstance(example, str):
            for k in re.findall(r"([A-Za-z_]+)=", example):
                add(k)
        else:
            keys(example)
        return words - {"a", "an", "the", "of", "id", "s"}

    def _background(self):
        out = {}
        for f in self.fields:
            fslots = [s for s in self.slots if s["field"] == f]
            u = self.ds.universes[self.ds.universe_of(f)]
            lists = {l.id: l for l in self.ds.lists.get(u.name, [])}
            banned = set(u.multi)
            for s in fslots:
                c = s["cand"]
                lst = lists[c.C]
                banned |= set(lst.members) | set(lst.disputed) | set(c.pool())
                banned |= {str(ch.get("value")) for ch in lst.changes}
            pool_n = sum(len(s["cand"].pool()) for s in fslots)
            need = max(16 - pool_n, 10)
            choices = [v for v in seeded_order(u.values, self.seed, "background", f) if v not in banned]
            if len(choices) < need:
                raise PlacementError(f"{f}: only {len(choices)} safe background values")
            out[f] = sorted(choices[:need])
        return out

    def slot(self, level):
        return next(s for s in self.slots if s["level"] == level)

    def value_reference(self, f):
        vals = set(self.background[f])
        for s in self.slots:
            if s["field"] == f:
                vals |= set(s["cand"].pool())
        return sorted(vals)

    # ---------- rule programs ----------
    def ref_sets(self, k):
        return {s["level"]: set(s["cand"].members()) for s in self.slots if s["level"] <= k}

    def variant(self, k, j, values):
        sets = self.ref_sets(k)
        sets[j] = set(values)
        return sets

    def lit(self, k):
        return {s["level"]: {s["cand"].A} for s in self.slots if s["level"] <= k}

    def all_described(self, k):
        return {s["level"]: set(s["cand"].pool()) for s in self.slots if s["level"] <= k}

    def excluded_positions(self, assign, sets):
        by_field = {}
        for lvl, vals in sets.items():
            by_field.setdefault(self.slot(lvl)["field"], set()).update(vals)
        return {(f, p) for (f, p), v in assign.items() if v in by_field.get(f, ())}

    # ---------- instances ----------
    def make_instance(self, step, placements, agg, requirements, extra=2, accept=None):
        """placements: list of (field, value). Each value sits on its own entity.
        requirements: list of (name, sets) programs whose answer must differ from reference(level sets).
        Returns dict with data, expected, entities, assignment."""
        ref_level_sets = requirements[0][1] if requirements and requirements[0][0] == "__ref__" else None
        reqs = [r for r in requirements if r[0] != "__ref__"]
        rng = rng_for(self.seed, "place", step)
        for attempt in range(400):
            world = self.mod.base_world(self.seed, f"{step}#{attempt}" if attempt else step)
            ents = list(self.mod.entities(world))
            pos = {f: {} for f in self.fields}
            for f in self.fields:
                for e, p in self.mod.slots(world, f):
                    pos[f].setdefault(e, []).append(p)
            order = ents[:]
            rng.shuffle(order)
            chosen, used, ok = [], set(), True
            for f, v in placements:
                e = next((x for x in order if x not in used and pos[f].get(x)), None)
                if e is None:
                    ok = False
                    break
                used.add(e)
                n = min(len(pos[f][e]), 1 + (attempt // 40) % 3)
                chosen.append((f, v, e, sorted(rng.sample(pos[f][e], n))))
            if not ok:
                raise PlacementError(f"{step}: not enough entities for {len(placements)} placements")
            extras = [x for x in order if x not in used][:extra]
            inst_ents = sorted(used | set(extras))
            assign = {}
            for f in self.fields:
                bg = self.background[f]
                for e in inst_ents:
                    for p in pos[f].get(e, []):
                        assign[(f, p)] = bg[rng.randrange(len(bg))]
            for f, v, e, ps in chosen:
                for p in ps:
                    assign[(f, p)] = v
            # every placed position must count toward its entity
            if any(self.mod.total(world, e, set()) - self.mod.total(world, e, {(f, p)}) <= 0
                   for f, v, e, ps in chosen for p in ps):
                continue
            for (f, p), v in sorted(assign.items()):
                self.mod.set_value(world, f, p, v)
            answers = {}

            def answer(sets):
                excl = self.excluded_positions(assign, sets)
                totals = [self.mod.total(world, e, excl) for e in inst_ents]
                return max(totals) if agg == "max" else sum(totals)
            ref = answer(ref_level_sets) if ref_level_sets is not None else None
            answers["reference"] = ref
            good = True
            for name, sets in reqs:
                a = answer(sets)
                answers[name] = a
                if a == ref:
                    good = False
                    break
            if not good:
                continue
            data = self.mod.render(world, inst_ents)
            excl = self.excluded_positions(assign, ref_level_sets) if ref_level_sets is not None else set()
            out = {"data": data, "expected": ref, "entities": inst_ents, "answers": answers,
                    "ref_totals": [self.mod.total(world, e, excl) for e in inst_ents],
                    "placements": [{"field": f, "value": v, "entity": e, "positions": ps}
                                   for f, v, e, ps in chosen],
                    "_world": (world, assign)}
            if accept is None or accept(out):
                return out
        raise PlacementError(f"{step}: no placement satisfies {len(reqs)} requirements")

    def make_single_view(self, base, step, place, level_sets, reqs, extra=None):
        """Practice view as a minimal pair of the public example `base`: the same input with one background value
        set to `place`'s value, nothing else changed, placed where the maximum moves so every program in `reqs`
        answers differently from the reference. h-X uses m_v ('only A' must differ: the one changed record is the
        culprit); h-N uses N_p ('all described' must differ: the changed record still counts)."""
        world0, assign0 = base["_world"]
        ents = base["entities"]
        f, val = place
        bg = set(self.background[f])
        extra = list(extra or [])
        rank = {e: -self.mod.total(world0, e, set()) for e in ents}
        owner = {(f, p): e for e, p in self.mod.slots(world0, f) if e in rank}
        order = sorted(((g, p) for (g, p), v in assign0.items() if g == f and v in bg and (g, p) in owner),
                       key=lambda x: (rank[owner[x]], str(x)))
        tries = 0
        for pos in order:
          for pos2 in ([None] if not extra else [x for x in order if x != pos]):
            tries += 1
            if tries > 300:
                raise PlacementError(f"{step}: no placement in 300 tries")
            world = copy.deepcopy(world0)
            assign = dict(assign0)
            assign[pos] = val
            self.mod.set_value(world, pos[0], pos[1], val)
            if pos2 is not None:
                assign[pos2] = extra[0][1]
                self.mod.set_value(world, pos2[0], pos2[1], extra[0][1])

            def answer(sets):
                excl = self.excluded_positions(assign, sets)
                return max(self.mod.total(world, e, excl) for e in ents)
            ref = answer(level_sets)
            answers = {"reference": ref}
            ok = True
            for name, sets in reqs:
                answers[name] = answer(sets)
                ok = ok and answers[name] != ref
            if not ok:
                continue
            excl = self.excluded_positions(assign, level_sets)
            placements = base["placements"] + [{"field": f, "value": val, "entity": owner[pos], "positions": [pos[1]]}]
            changes = [{"field": f, "from": assign0[pos], "to": val}]
            if pos2 is not None:
                placements.append({"field": f, "value": extra[0][1], "entity": owner[pos2], "positions": [pos2[1]]})
                changes.append({"field": f, "from": assign0[pos2], "to": extra[0][1]})
            return {"data": self.mod.render(world, ents), "expected": ref, "entities": ents,
                    "answers": answers, "ref_totals": [self.mod.total(world, e, excl) for e in ents],
                    "placements": placements, "changes": changes}
        raise PlacementError(f"{step}: no placement found")

    def a_placements(self, k):
        return [(s["field"], s["cand"].A) for s in self.slots if s["level"] <= k]

    # ---------- prompts ----------
    def entity_nouns(self):
        noun = getattr(self.mod, "ENTITY_NOUN", "entity")
        plural = getattr(self.mod, "ENTITY_NOUN_PLURAL", noun[:-1] + "ies" if noun.endswith("y") else noun + "s")
        return noun, plural

    def quote(self, v):
        return v if v.lstrip("-").isdigit() else f"'{v}'"

    def a_sentence(self, s):
        obj, fname = split_field(s["field"])
        one = singular(obj)
        return f"{article(one)} {one} whose {fname} is {self.quote(s['cand'].A)} is in {self.labels[s['level']]}."

    def rule_sentence(self, s):
        obj, _ = split_field(s["field"])
        return f"L{s['level']}: From this level on, {obj} in {self.labels[s['level']]} are not counted."

    def input_description(self, example):
        custom = getattr(self.mod, "INPUT_FORMAT", None)
        if custom:
            return custom.strip()
        if self.fmt == "json" and isinstance(example, dict):
            lines = ["The top-level JSON object has these keys:"]
            for key in sorted(example):
                val = example[key]
                rows = list(val.values()) if isinstance(val, dict) else val
                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    cols = sorted({c for r in rows for c in r})
                    lines.append(f"- {key}: rows with {', '.join(cols)}")
                else:
                    lines.append(f"- {key}")
            return "\n".join(lines)
        if self.fmt == "files":
            return "The input maps file paths to file contents; see the example."
        return "The input is plain text; see the example."

    def serialize(self, data):
        if self.fmt == "text":
            return data if isinstance(data, str) else str(data)
        return json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True)

    def summary_sentence(self, split):
        _, plural = self.entity_nouns()
        if split == "practice":
            return f"Return the largest total among the {plural} in the input, as an int."
        return f"Return the sum of the totals of all {plural} in the input, as an int."

    def prompt(self, k, split, example):
        parts = []
        if self.ds.business():
            parts.append(self.ds.business())
        parts.append(CONTRACT[self.fmt])
        parts.append("Input:\n" + self.input_description(example))
        parts.append(self.mod.TASK.strip() + "\n" + self.summary_sentence(split))
        active = [s for s in self.slots if s["level"] <= k]
        if active:
            parts.append("Field notes:\n" + "\n".join("- " + self.a_sentence(s) for s in active) + "\n"
                         + CATEGORY_NOTE)
            parts.append("Level rules:\n" + "\n".join(self.rule_sentence(s) for s in active))
        if split == "practice":
            parts.append(PAIR_NOTE)
        ref = ["Value reference:"]
        for f in self.fields:
            ref.append(f"{f}:")
            u = self.ds.universes[self.ds.universe_of(f)]
            code = self.ds.value_form(f) == "code"
            for v in self.value_reference(f):
                d = u.desc.get(v)
                if code:
                    ref.append(f"- {v} — {u.entity[v]}" + (f"; {d}" if d else ""))
                else:
                    ref.append(f"- {v}" + (f" — {d}" if d else ""))
        parts.append("\n".join(ref))
        parts.append("Example input:\n" + self.serialize(example))
        return "\n\n".join(parts) + "\n"

    def feedback(self, s, v):
        obj, fname = split_field(s["field"])
        c = s["cand"]
        return FEEDBACK.format(j=s["level"], obj=obj, fname=fname, mv=self.quote(c.P_M[v]),
                               a=self.quote(c.A), np=self.quote(c.N_p))

    def public_example(self, k):
        """The level's public example, regenerated until every practice view can be built from it: h-X_j (each trap,
        each version: one value set to m_v) and h-XN_j (each trap, each version: one value set to m_v, one to N_p)."""
        if k not in self._public:
            pairs = {}

            def accept(inst):
                pairs.clear()
                try:
                    for s in [s for s in self.slots if s["level"] <= k]:
                        j, c, f = s["level"], s["cand"], s["field"]
                        for v in range(3):
                            pairs[(j, v)] = self.make_single_view(inst, f"L{k}/hX/{j}/v{v}", (f, c.P_M[v]),
                                                                  self.ref_sets(k),
                                                                  [("a", self.variant(k, j, {c.A}))])
                            # m_v and N_p together: the only-A program fails it too, so the first feedback also
                            # shows that N_p still counts; an over-inclusive program fails it as well
                            pairs[(j, "N", v)] = self.make_single_view(
                                inst, f"L{k}/hXN/{j}/v{v}", (f, c.P_M[v]), self.ref_sets(k),
                                [("a", self.variant(k, j, {c.A})), ("c", self.variant(k, j, set(c.pool())))],
                                extra=[(f, c.N_p)])
                except PlacementError:
                    return False
                return True
            inst = self.make_instance(f"L{k}/public", self.a_placements(k), "max",
                                      [("__ref__", self.ref_sets(k))], accept=accept)
            self._public[k] = (inst, dict(pairs))
        return self._public[k][0]

    def pair_view(self, k, j, v, both=False):
        """h-X_j (m_v only) or, with both=True, h-XN_j (m_v and N_p) for version v."""
        self.public_example(k)
        return self._public[k][1][(j, "N", v) if both else (j, v)]

    def probe_prompts(self, unpinned_levels, kinds=("P0", "P1H", "P1")):
        """P0 on the last level's test prompt; P1H (feedback + lesson) and P1 (feedback only) on its practice prompt
        for each unpinned slot and version. `kinds` picks a subset (certify asks P0 first, then the others)."""
        k = max(s["level"] for s in self.slots)
        levels = [s["level"] for s in self.slots]
        example = self.public_example(k)["data"]
        test_prompt = self.prompt(k, "test", example)
        practice_prompt = self.prompt(k, "practice", example)
        q0, q1 = p0_question(levels), p1h_question(levels)
        out = [{"kind": "P0", "level": None, "version": None, "sample": i,
                "prompt": test_prompt + "\n" + q0} for i in range(3)] if "P0" in kinds else []
        for j in unpinned_levels:
            s = self.slot(j)
            for v in range(3):
                for i in range(2):
                    if "P1H" in kinds:
                        out.append({"kind": "P1H", "level": j, "version": v, "sample": i,
                                    "prompt": practice_prompt + "\n" + self.feedback(s, v) + "\n\n" + HINT_TITLE
                                    + "\n" + HINT + "\n\n" + q1})
                    if "P1" in kinds and self.cfg["probe"].get("p1_band", [P1_LOW, P1_HIGH]):
                        out.append({"kind": "P1", "level": j, "version": v, "sample": i,
                                    "prompt": practice_prompt + "\n" + self.feedback(s, v) + "\n\n" + q1})
        return out
