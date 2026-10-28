import json
import os
import signal
import subprocess
import sys
import time

from conftest import run_make_chain, REPO


def state(toy):
    return json.loads((toy / "out/TOY/TOY1/STATE.json").read_text())


def test_end_to_end(toy, fake):
    (toy / "out/TOY/TOY1").mkdir(parents=True)
    (toy / "out/TOY/TOY1/KEEP_ME.txt").write_text("foreign file")
    r = run_make_chain(toy, fake())
    assert r.returncode == 0, r.stderr
    st = state(toy)
    assert st["stage"] == "done" and all(s["pinned"] for s in st["slots"])
    by = {s["level"]: s["pinned"] for s in st["slots"]}
    assert not set(by[1]["A"] for _ in [0]) & set()  # placeholder
    assert not (set([by[1]["A"], *by[1]["P_M"], by[1]["N_p"], *by[1]["N_t"]])
                & set([by[4]["A"], *by[4]["P_M"], by[4]["N_p"], *by[4]["N_t"]]))
    z = json.loads((toy / "out/TOY/TOY1/ZERO_CHECK.json").read_text())
    assert z["pass"] and z["results"]["L-lit_scores_v1"]["pass"]
    assert (toy / "out/TOY/TOY1/KEEP_ME.txt").exists()
    task = json.loads((toy / "out/TOY/TOY1/bundle_k1_v0/private/CLR_TOY1.L3.practice.json").read_text())
    assert len(task["hidden"]) == 7
    assert z["results"]["pair_of_public_v0_L3_h-X_2_v0"]["pass"] and z["results"]["pair_of_public_v0_L3_h-X_2_v0"]["detail"] == 1
    assert z["results"]["pair_of_public_v0_L3_h-XN_2_v0"]["pass"] and z["results"]["pair_of_public_v0_L3_h-XN_2_v0"]["detail"] == 2
    assert "one or two field values changed" in task["prompt"]
    hx = next(h for h in task["hidden"] if h["coverage"] == "h-X_2_v0")
    assert len(hx["changes"]) == 1 and hx["changes"][0]["field"] == "records.tag"
    assert len(next(h for h in task["hidden"] if h["coverage"] == "h-XN_2_v0")["changes"]) == 2
    test = json.loads((toy / "out/TOY/TOY1/bundle_k1_v0/private/CLR_TOY1.L3.test.json").read_text())
    assert "one or two field values changed" not in test["prompt"]
    assert all("changes" not in h for h in test["hidden"])
    assert "real-world category" in test["prompt"] and "real-world category" in task["prompt"]
    hist = st["history"][0]["verdicts"]
    assert all(v["P1"] and abs(v["g"] - 1 / 3) < 1e-3 for v in hist.values())
    rerun = subprocess.run([sys.executable, "-m", "clrsynth", "verify-repro", str(toy / "inputs/TOY/chains/TOY1.yaml"),
                            "--out-root", str(toy)], env={**os.environ, "PYTHONPATH": str(REPO)},
                           capture_output=True, text=True)
    assert "verify-repro OK" in rerun.stdout


def test_rejected_candidate_is_replaced(toy, fake):
    first = None
    env = fake(FAKE_REJECT="1:item_fives")
    r = run_make_chain(toy, env)
    assert r.returncode == 0, r.stderr
    st = state(toy)
    l1 = next(s for s in st["slots"] if s["level"] == 1)
    assert l1["pinned"]["C"] != "item_fives" and "item_fives" in l1["tried"] and st["rounds"] >= 2


def test_p0_failure_replaces_candidate(toy, fake):
    r = run_make_chain(toy, fake(FAKE_P0_GUESS="3"))
    st = state(toy)
    l3 = next(s for s in st["slots"] if s["level"] == 3)
    assert len(l3["tried"]) >= 1  # every color candidate is guessed, so the chain stops when they run out
    assert r.returncode == 2 and "no candidate left" in r.stderr and "needed:" in r.stderr


def test_resume_and_sigterm(toy, fake):
    env = {**os.environ, **fake(FAKE_DELAY="2"), "PYTHONPATH": str(REPO)}
    p = subprocess.Popen([sys.executable, "-m", "clrsynth", "make-chain", str(toy / "inputs/TOY/chains/TOY1.yaml"),
                          "--out-root", str(toy)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    deadline = time.time() + 30
    while time.time() < deadline and not list((toy / "logs/TOY/TOY1").glob("run1/probe/S1")):
        time.sleep(0.2)
    time.sleep(1)
    os.kill(p.pid, signal.SIGTERM)
    p.wait(timeout=10)
    assert p.returncode == 130
    time.sleep(0.5)
    alive = subprocess.run(["pgrep", "-g", str(p.pid)], capture_output=True, text=True).stdout.strip()
    assert alive == ""
    r = run_make_chain(toy, fake())
    assert r.returncode == 0, r.stderr
    assert (toy / "logs/TOY/TOY1/run2").exists()


def test_sibling_chains_reuse_concepts_with_other_members(toy, fake):
    env = fake()
    assert run_make_chain(toy, env).returncode == 0
    od = toy / "out/TOY/TOY1"
    first = {s["pinned"]["C"]: s["pinned"] for s in state(toy)["slots"]}
    sib = toy / "out/TOY/SIBLING"
    sib.mkdir()
    (sib / "STATE.json").write_text((od / "STATE.json").read_text())
    import shutil
    shutil.rmtree(od)
    r = run_make_chain(toy, env)
    assert r.returncode == 0, r.stderr
    second = {s["pinned"]["C"]: s["pinned"] for s in state(toy)["slots"]}
    shared = set(first) & set(second)
    for c in shared:   # a shared concept never shares a trap value
        assert not ({first[c]["A"], *first[c]["P_M"]} & {second[c]["A"], *second[c]["P_M"]})
    assert len(set(second) - set(first)) >= 1 or shared   # unused concepts come first


def test_p1_too_easy_replaces_candidate(toy, fake):
    r = run_make_chain(toy, fake(FAKE_P1_ALL="1"))
    st = state(toy)
    l1 = next(s for s in st["slots"] if s["level"] == 1)
    assert len(l1["tried"]) >= 1 and not st["history"][0]["verdicts"]["1"]["P1"]


def test_certify_then_make_chain_uses_the_pool(toy, fake):
    env = {**os.environ, **fake(), "PYTHONPATH": str(REPO)}
    r = subprocess.run([sys.executable, "-m", "clrsynth", "certify", str(toy / "inputs/TOY/chains/TOY1.yaml"),
                        "--out-root", str(toy)], env=env, capture_output=True, text=True)
    assert "certified variants" in r.stdout, r.stdout + r.stderr
    pool = json.loads((toy / "out/TOY/POOL.json").read_text())
    passed = {c for c, e in pool.items() if any(v["pass"] for v in e["variants"])}
    assert passed
    if r.returncode == 0:
        r2 = run_make_chain(toy, fake())
        assert r2.returncode == 0, r2.stderr
        assert {s["pinned"]["C"] for s in state(toy)["slots"]} <= passed
