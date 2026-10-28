import json

from clrsynth.inputs import Dataset, load_chain
from clrsynth.candidates import FieldContext, candidates_for_slot, allocate_slots, Candidate
from clrsynth.probe import judge_p0, judge_p1h, judge_p1, soft_score, parse_json_answer
from clrsynth.lint import lint_dataset


def ctx(toy, field="records.item"):
    cfg = load_chain(toy / "inputs/TOY/chains/TOY1.yaml")
    ds = Dataset(cfg["_inputs_root"], "TOY")
    return ds, cfg, FieldContext(ds, cfg, field)


def test_lint_toy_ok(toy):
    ds, _, _ = ctx(toy)
    assert lint_dataset(ds) == []


def test_lint_catches_problems(toy):
    root = toy / "inputs/TOY"
    u = root / "universes/color.tsv"
    u.write_text("\n".join(l.split("\tattr:zone")[0] if i == 0 else l.rsplit("\t", 1)[0]
                           for i, l in enumerate(u.read_text().splitlines())) + "\n")
    lst = root / "lists/item.yaml"
    lst.write_text(lst.read_text().replace("official_count: 30", "official_count: 31", 1))
    ds = Dataset(toy / "inputs", "TOY")
    errs = "\n".join(lint_dataset(ds))
    assert "no attr:" in errs and "official_count" in errs


def test_lint_entity_count(toy):
    p = toy / "inputs/TOY/dataset.py"
    p.write_text(p.read_text().replace("range(40)", "range(12)"))
    errs = "\n".join(lint_dataset(Dataset(toy / "inputs", "TOY")))
    assert "entities (at least 30" in errs


def test_slot_allocation(toy):
    ds, cfg, _ = ctx(toy)
    fields = [s["field"] for s in allocate_slots(ds, cfg)]
    assert fields == ["records.item", "records.tag", "records.color", "records.item", "records.tag"]


def test_candidates_deterministic_and_valid(toy):
    _, _, fc = ctx(toy)
    a, _ = candidates_for_slot(fc, set(), 1)
    b, _ = candidates_for_slot(fc, set(), 1)
    assert [c.to_dict() for c in a] == [c.to_dict() for c in b] and a
    for c in a:
        assert len(set(c.pool())) == 12 and len(c.N_t) == 7
        assert len(fc.comp(c.A, c.C)) >= 2
        assert c.A in fc.member_sets[c.C] and all(m in fc.member_sets[c.C] for m in c.P_M)
        assert not any(v in fc.member_sets[c.C] for v in [c.N_p, *c.N_t])
        comp_union = set().union(*[fc.member_sets[l] for l in c.comp_A])
        assert sum(t in comp_union for t in c.N_t) >= 3
        assert c.checks["H2"]["pass"] and c.checks["H4"]["pass"]


def test_candidates_respect_excluded(toy):
    _, _, fc = ctx(toy)
    first, _ = candidates_for_slot(fc, set(), 1, limit=1)
    pool = set(first[0].pool())
    second, _ = candidates_for_slot(fc, pool, 4, tried={first[0].C}, limit=3)
    for c in second:
        assert not (set(c.pool()) & pool) and c.C != first[0].C


def test_attribute_list_never_a_candidate(toy):
    _, _, fc = ctx(toy, "records.tag")
    assert "tag_fours" in fc.attr_lists and "tag_fours" not in fc.c_order()


CAND = Candidate(field="f", universe="u", C="c", C_name="c", A="a", P_M=["m0", "m1", "m2"], N_p="np",
                 N_t=[f"t{i}" for i in range(7)], comp_A=[], checks={}, salience=0)


def test_p0_rules():
    only_a = {"L1": ["a"]}
    assert judge_p0(CAND, 1, [only_a] * 3)["pass"]
    assert not judge_p0(CAND, 1, [{"L1": ["a", "m0", "m1", "m2"]}, only_a, only_a])["pass"]
    assert not judge_p0(CAND, 1, [{"L1": ["a", "m0"]}, {"L1": ["a", "m0"]}, only_a])["pass"]
    lump = {"L1": ["a", "m0", "t0", "t1"]}
    assert judge_p0(CAND, 1, [lump, lump, only_a])["pass"]


def test_soft_score_and_p1h():
    good = {"L1": {"category": "x", "values": ["a", "m0", "m1", "m2"]}}
    assert soft_score(CAND, 0, {"a", "m0", "m1", "m2"}) == 1.0
    assert soft_score(CAND, 0, {"a", "m0"}) == 7 / 9
    assert judge_p1h(CAND, 1, [(v, good) for v in range(3) for _ in range(2)], "soft", set())["pass"]
    bad = {"L1": {"category": "x", "values": ["a", *[f"t{i}" for i in range(7)]]}}
    rows = [(0, bad), (0, bad)] + [(v, good) for v in (1, 2) for _ in range(2)]
    assert not judge_p1h(CAND, 1, rows, "soft", set())["pass"]
    assert judge_p1h(CAND, 1, [(v, good) for v in range(3) for _ in range(2)], "strict", set())["pass"]


def test_p1_band():
    band = [1 / 6, 2 / 3]
    lit = {"L1": {"category": "x", "values": ["a", "m0"]}}
    full = {"L1": {"category": "x", "values": ["a", "m0", "m1", "m2"]}}
    lump = {"L1": {"category": "x", "values": ["a", "m0", "m1", "m2", "t0", "t1"]}}
    rows = lambda obj: [(v, obj) for v in range(3) for _ in range(2)]
    r = judge_p1(CAND, 1, rows(lit), band)
    assert r["pass"] and abs(r["mean_g"] - 1 / 3) < 1e-3
    assert not judge_p1(CAND, 1, rows(full), band)["pass"]          # too easy without the lesson
    assert not judge_p1(CAND, 1, rows(lump), band)["pass"]          # lumping the family is no generalization
    assert not judge_p1(CAND, 1, rows({"L1": {"values": ["a"]}}), band)["pass"]   # nothing recoverable


def test_changed_values():
    from clrsynth.check import changed_values
    a = {"rows": [{"x": "p", "y": 1}, {"x": "q", "y": 2}]}
    b = {"rows": [{"x": "p", "y": 1}, {"x": "r", "y": 2}]}
    assert changed_values(a, b) == 1 and changed_values(a, a) == 0
    assert changed_values(a, {"rows": []}) is None
    assert changed_values("l1\nl2\nl3", "l1\nzz\nl3") == 1


def test_parse_json_answer():
    assert parse_json_answer('blah ```json\n{"L1": ["x"]}\n``` end') == {"L1": ["x"]}
    assert parse_json_answer('answer: {"L2": []}') == {"L2": []}
    assert parse_json_answer("no json") is None


def test_value_descriptions_in_prompt_and_lint(toy):
    from clrsynth.chain import Chain
    ds, cfg, fc = ctx(toy, "records.color")
    assert ds.universes["color"].desc["C07"] == "toy shade number 7"
    cand = candidates_for_slot(fc, set(), 1, limit=1)[0][0]
    chain = Chain(ds, cfg, [{"level": 1, "field": "records.color", "cand": cand}])
    prompt = chain.prompt(1, "test", chain.public_example(1)["data"])
    line = next(l for l in prompt.splitlines() if l.startswith(f"- {cand.A} "))
    assert line.endswith(f"; toy shade number {int(cand.A[1:])}")   # code values: "- v — entity; description"
    d = toy / "inputs/TOY/universes/color.desc.tsv"
    d.write_text(d.read_text().replace("toy shade number 4\n", "listed in color evens\n"))
    errs = "\n".join(lint_dataset(Dataset(toy / "inputs", "TOY")))
    assert "'C04' names list color_evens" in errs
    d.write_text(d.read_text().replace("toy shade number 5\n", "第五号玩具颜色\n"))
    assert "must be in English" in "\n".join(lint_dataset(Dataset(toy / "inputs", "TOY")))
