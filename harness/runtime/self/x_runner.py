"""Run one candidate program on one input in an isolated container and return its answer (answer format: json).

Part of harness/runtime/self: the practice harness for learning from feedback alone (self)."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FORMAT = "json"
DRIVER = """import json, sys
sys.path.insert(0, sys.argv[1])
import candidate
raw = open(sys.argv[2], encoding="utf-8").read()
data = raw if %r == "text" else json.loads(raw)
value = candidate.solve(data)
if type(value) is not int:
    print("solve must return an int, got " + type(value).__name__, file=sys.stderr)
    sys.exit(3)
print(value)
"""


def extract_code(text):
    """Code from a reply: the last fenced block if any (with or without a language tag), else the text."""
    blocks = re.findall(r"```[ \t]*(?:python|py)?[ \t]*\n(.*?)```", text, flags=re.S)
    return blocks[-1] if blocks else text


def run_candidate(code, data, timeout=10, env=None):
    with tempfile.TemporaryDirectory(prefix="clr-candidate-") as folder:
        root = Path(folder)
        (root / "candidate.py").write_text(extract_code(code), encoding="utf-8")
        (root / "driver.py").write_text(DRIVER % FORMAT, encoding="utf-8")
        name = "input.txt" if FORMAT == "text" else "input.json"
        payload = data if FORMAT == "text" else json.dumps(data, ensure_ascii=False)
        (root / name).write_text(payload, encoding="utf-8")
        try:
            res = subprocess.run([sys.executable, str(root / "driver.py"), str(root), str(root / name)],
                                 text=True, capture_output=True, timeout=timeout, env=env, cwd=folder)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error_type": "TimeoutExpired", "error": f"candidate exceeded {timeout} seconds",
                    "stdout": ""}
        if res.returncode:
            kind = "FormatError" if res.returncode == 3 else "ProcessError"
            return {"ok": False, "error_type": kind, "error": res.stderr[-2000:], "stdout": res.stdout[-2000:]}
        return {"ok": True, "value": int(res.stdout.strip().splitlines()[-1]), "stdout": res.stdout}
