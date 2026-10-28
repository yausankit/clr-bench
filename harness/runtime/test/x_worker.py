#!/usr/bin/env python3
"""stdin: {"code": ..., "data": ...}; stdout: run_candidate result."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import run_candidate

payload = json.load(sys.stdin)
print(json.dumps(run_candidate(payload["code"], payload["data"]), ensure_ascii=False))
