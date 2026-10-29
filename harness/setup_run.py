#!/usr/bin/env python3
"""Create the run directory for one chain: the layout the harness scripts expect.

usage: python harness/setup_run.py CHAIN [--out runs/CHAIN] [--gateway-url http://localhost:42802/CLR]
                                   [--model gpt-6-luna] [--python PYTHON] [--embedding-model NAME_OR_PATH]
                                   [--levels 1,2,3,4] [--concurrency 8]

The run directory gets
  CONFIG.json, AUDIT.json, REPLAY_PLAN_K1_FROZEN.json         from data/chains/CHAIN/run_kit (paths filled in)
  HINT_NC100.txt, LESSON_CONV.txt, LESSON_PROC.txt            the lesson and its parts (prompts/)
  CLASS_NAMES.txt                                             class names behind the labels, for the class-name oracle (prompts/)
  bundle_k1_v0/, bundle_k1_v0_rg/                             task files (rewarded practice: practice files replaced)
  harness_self_v0/   practice harness, learning from feedback alone (self)
  harness_hint_v0/   practice harness, lesson appended to every update input (+lesson)
  harness_k1_test/   test harness (frozen agent and replay of learned states on the test task)
  run_stage_a.py, build_replay_plan.py, run_stage_b.py, score_all.py, and run_frozen.sh.
Each harness copy is harness/runtime/<arm> plus the method adapters in methods/<arm> and methods/shared.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARMS = {"harness_self_v0": "self", "harness_hint_v0": "hint", "harness_k1_test": "test"}


def copytree(src, dst):
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("chain")
    p.add_argument("--out")
    p.add_argument("--gateway-url", default="http://localhost:42802/CLR")
    p.add_argument("--model", default="gpt-6-luna")
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    p.add_argument("--levels", default="1,2,3,4")
    p.add_argument("--concurrency", type=int)
    a = p.parse_args()

    chain = REPO / "data/chains" / a.chain
    if not (chain / "CHAIN.json").exists():
        raise SystemExit(f"unknown chain {a.chain}")
    if not (chain / "bundle_k1_v0").exists():
        subprocess.run([sys.executable, str(REPO / "data/unpack_chains.py"), a.chain], check=True)
    out = Path(a.out or REPO / "runs" / a.chain).resolve()
    out.mkdir(parents=True, exist_ok=True)
    kit = chain / "run_kit"

    cfg = json.loads((kit / "CONFIG.json").read_text())
    cfg.pop("_note", None)
    m = re.match(r"https?://[^/:]+:(\d+)(/.*)?$", a.gateway_url)
    if not m:
        raise SystemExit("--gateway-url must look like http://HOST:PORT/BASE_PATH")
    cfg.update(chain=str(chain), gateway_url=a.gateway_url, gateway_port=int(m.group(1)),
               gateway_base_path=m.group(2) or "", model=a.model, python=a.python,
               embedding_model=a.embedding_model, methods_root=str(REPO / "methods"), levels=[int(x) for x in a.levels.split(",")])
    if a.concurrency:
        cfg["concurrency"] = a.concurrency
    (out / "CONFIG.json").write_text(json.dumps(cfg, indent=2) + "\n")

    for f in ("AUDIT.json", "REPLAY_PLAN_K1_FROZEN.json"):
        shutil.copy(kit / f, out / f)
    texts = {"HINT_NC100.txt": "prompts/lesson.txt", "LESSON_CONV.txt": "prompts/lesson_convention.txt",
             "LESSON_PROC.txt": "prompts/lesson_procedure.txt",
             "CLASS_NAMES.txt": f"prompts/class_names/{a.chain}.txt"}
    for dst, src in texts.items():
        shutil.copy(REPO / src, out / dst)

    copytree(chain / "bundle_k1_v0", out / "bundle_k1_v0")
    copytree(chain / "bundle_k1_v0", out / "bundle_k1_v0_rg")
    copytree(chain / "bundle_k1_v0_rg", out / "bundle_k1_v0_rg")

    for name, arm in ARMS.items():
        h = out / name
        copytree(REPO / "harness/runtime" / arm, h)
        copytree(REPO / "methods" / arm, h)
        copytree(REPO / "methods/shared", h)
        xr = h / "x_runner.py"
        s = xr.read_text()
        s = re.sub(r'^FORMAT = "\w+"$', f'FORMAT = "{cfg["format"]}"', s, count=1, flags=re.M)
        s = re.sub(r"\(answer format: \w+\)", f"(answer format: {cfg['format']})", s, count=1)
        xr.write_text(s)
        if arm in ("self", "hint"):
            shutil.copy(kit / "PRACTICE_VALUES.json", h / "PRACTICE_VALUES.json")
    shutil.copy(kit / "REPLAY_PLAN_K1_FROZEN.json", out / "harness_k1_test/REPLAY_PLAN_K1_FROZEN.json")

    for f in sorted((REPO / "harness/run_dir").iterdir()):
        if f.is_file():
            shutil.copy(f, out / f.name)
    (out / "run_frozen.sh").chmod(0o755)
    print(f"run directory ready: {out}")


if __name__ == "__main__":
    main()
