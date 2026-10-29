#!/usr/bin/env python3
"""Worker process for x_runner.py: reads {"code": ..., "data": ...} on stdin and prints the run result on stdout.

Part of harness/runtime/test: the test harness: replay of learned states on the test task, and the frozen agent."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import run_candidate

payload = json.load(sys.stdin)
print(json.dumps(run_candidate(payload["code"], payload["data"]), ensure_ascii=False))
