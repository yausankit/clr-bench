"""Frozen calibration: a non-learning model answers each level's test prompt once (up to 2 rounds of execution
feedback on the prompt's example input, no counterexamples); the final program is scored on all three versions.
usage: python tools/frozen.py <chain out dir> [--levels 1,2,3,4,5]
Endpoint settings come from the same CLRSYNTH_* environment variables as make-chain."""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clrsynth.probe import Endpoint


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("--levels", default="1,2,3,4,5")
    a = p.parse_args()
    od = Path(a.out).resolve()
    sys.path.insert(0, str(od / "harness_k1_test"))
    from runner import run_candidate, extract_code
    meta = json.loads((od / "CHAIN.json").read_text())
    course = meta["course_id"]
    ep = Endpoint()
    levels = [int(x) for x in a.levels.split(",")]
    fdir = od / "frozen"
    fdir.mkdir(exist_ok=True)

    def solve(k):
        task = json.loads((od / f"bundle_k1_v0/private/{course}.L{k}.test.json").read_text())
        messages = task["prompt"]
        transcript = []
        prompt = messages
        code = ""
        for turn in range(3):
            reply = ep.complete(prompt)
            code = extract_code(reply)
            res = run_candidate(code, task["public"], timeout=30)
            transcript.append({"prompt": prompt, "reply": reply, "example_run": res})
            if res.get("ok"):
                break
            prompt = (messages + "\n\nYour previous program:\n```python\n" + code + "\n```\n\nRunning it on the "
                      f"example input failed: {res.get('error_type')}: {res.get('error', '')[-1500:]}\n"
                      "Fix the program and reply with the complete corrected program.")
        (fdir / f"L{k}.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=1))
        (fdir / f"L{k}.py").write_text(code)
        return k, code

    with ThreadPoolExecutor(max_workers=len(levels)) as pool:
        programs = dict(pool.map(solve, levels))
    summary = {"model": ep.model, "reasoning": ep.reasoning, "versions": {}}
    for v in range(3):
        tests = json.loads((od / f"test_k1_v{v}.json").read_text())
        row = {}
        for k in levels:
            cells = [t for t in tests if t["level"] == k]
            passed = [run_candidate(programs[k], t["data"], timeout=60).get("value") == t["expected"] for t in cells]
            row[f"L{k}"] = {"score": round(sum(passed) / 5, 2),
                            "cells": {t["cell"]: ok for t, ok in zip(cells, passed)}}
        summary["versions"][f"v{v}"] = row
    (fdir / "FROZEN.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    for v, row in summary["versions"].items():
        print(v, " ".join(f"{k}={r['score']:.2f}" for k, r in row.items()))


if __name__ == "__main__":
    main()
