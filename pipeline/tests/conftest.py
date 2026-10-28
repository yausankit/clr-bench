import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_toy  # noqa: E402


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def toy(tmp_path):
    make_toy.write(tmp_path / "inputs")
    return tmp_path


@pytest.fixture
def fake(toy):
    procs = []

    def start(**env):
        port = free_port()
        e = {**os.environ, "FAKE_STATE": str(toy / "out" / "TOY" / "TOY1" / "STATE.json"),
             "FAKE_LISTS": str(toy / "inputs" / "TOY" / "lists"), **env}
        p = subprocess.Popen([sys.executable, str(REPO / "tests" / "fake_endpoint.py"), str(port)], env=e)
        procs.append(p)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        return {"CLRSYNTH_ENDPOINT": f"http://127.0.0.1:{port}/v1", "CLRSYNTH_MODEL": "fake",
                "CLRSYNTH_API_KEY": "x"}
    yield start
    for p in procs:
        p.kill()


def run_make_chain(toy, env, **kw):
    e = {**os.environ, **env, "PYTHONPATH": str(REPO)}
    return subprocess.run([sys.executable, "-m", "clrsynth", "make-chain", str(toy / "inputs/TOY/chains/TOY1.yaml"),
                           "--out-root", str(toy)], env=e, capture_output=True, text=True, **kw)
