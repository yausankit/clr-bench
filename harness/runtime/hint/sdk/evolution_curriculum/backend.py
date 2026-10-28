import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


class InfrastructureError(RuntimeError):
    """No valid score: the evaluator failed before producing a task observation."""


class DockerExecutor:
    def __init__(self, image="python:3.12-slim"):
        self.image = image

    def execute(self, task, code, bundle):
        if task["language"] == "sql":
            # Preserve the original host SQLite engine; Python submissions still run in Docker.
            database = Path(bundle) / task["database_asset"]
            if not database.is_file():
                raise InfrastructureError(f"Missing database asset: {task['database_asset']}")
            process = subprocess.run([sys.executable, str(Path(__file__).with_name("sql_worker.py"))],
                                     input=json.dumps(dict(database=str(database), code=code)), text=True, capture_output=True)
            if process.returncode:
                raise InfrastructureError(f"SQLite worker exited {process.returncode}: {process.stderr[-2000:]}")
            try:
                return json.loads(process.stdout)
            except ValueError as error:
                raise InfrastructureError("SQLite worker returned invalid JSON") from error
        with tempfile.TemporaryDirectory(prefix="evolution-grade-") as temp:
            root = Path(temp)
            (root / "input").mkdir()
            (root / "output").mkdir()
            (root / "input/candidate.txt").write_text(code, encoding="utf-8")
            shutil.copyfile(Path(__file__).with_name("worker.py"), root / "input/worker.py")
            mounts = ["--mount", f"type=bind,src={root / 'input'},dst=/work,readonly",
                      "--mount", f"type=bind,src={root / 'output'},dst=/out"]
            payload = {"data": json.loads((Path(bundle) / task["input_asset"]).read_text())}
            command = ["docker", "run", "-i", "--name", "evolution-grade-" + uuid.uuid4().hex,
                       "--label", "evolution-curriculum=1", "--network", "none", "--read-only",
                       "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "2g",
                       "--pids-limit", "128", "--user", f"{os.getuid()}:{os.getgid()}",
                       "--tmpfs", "/tmp:rw,noexec,size=32m", "--env", "PYTHONDONTWRITEBYTECODE=1",
                       "--env", "PYTHONUTF8=1", *mounts, "--workdir", "/tmp", self.image, "python", "/work/worker.py"]
            try:
                result = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False), text=True, capture_output=True)
            except OSError as error:
                raise InfrastructureError(str(error)) from error
            container_name=command[command.index('--name')+1]
            inspection=subprocess.run(['docker','inspect',container_name],text=True,capture_output=True)
            state={}
            try:
                if inspection.returncode==0: state=json.loads(inspection.stdout)[0]['State']
            finally:
                subprocess.run(['docker','rm','-f',container_name],capture_output=True)
            if state.get('OOMKilled'):
                return dict(ok=False,error='ResourceLimit: candidate exceeded the declared 2 GiB memory budget',execution_resource=dict(container=container_name,state=state,memory='2g'))
            output = root / "output/result.json"
            if result.returncode or not output.exists():
                raise InfrastructureError(f"Container exited {result.returncode}: {result.stderr[-2000:]}")
            try:
                observation = json.loads(output.read_text())
                if not isinstance(observation.get("ok"), bool):
                    raise ValueError("Worker returned no boolean ok field")
                return observation
            except (ValueError, TypeError, AttributeError) as error:
                raise InfrastructureError(f"Invalid worker response: {error}") from error
