"""Local HTTP task service: serves task prompts, runs submissions through the executor, and records grades."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .backend import DockerExecutor, InfrastructureError
from .export import read, write
from .grading import equal, parse


class ConflictError(ValueError):
    pass


class Evaluator:
    def __init__(self, bundle, output, *, courses=None, levels=None, repeats=3, executor=None, harness_config=None):
        self.bundle, self.output = Path(bundle).resolve(), Path(output).resolve()
        if self.output == self.bundle or self.bundle in self.output.parents:
            raise ValueError("Keep run records outside the immutable dataset bundle")
        tasks = [json.loads(line) for line in (self.bundle / "public/tasks.jsonl").read_text().splitlines()]
        known = {t["course_id"] for t in tasks}
        courses = sorted(known if courses is None else courses)
        levels = sorted([1, 2, 3, 4] if levels is None else levels)
        if not courses or set(courses) - known or not levels or set(levels) - {1, 2, 3, 4} or type(repeats) is not int or repeats < 1:
            raise ValueError("Invalid course, level or repeat selection")
        self.tasks = {t["task_id"]: t for t in tasks if t["course_id"] in courses and t["level"] in levels}
        self.gold = read(self.bundle / "private/gold.json")
        self.executor = executor or DockerExecutor()
        self.lock = threading.RLock()
        self.repeats = repeats
        config = dict(format="evolution-run-v1", courses=courses, levels=levels, repeats=repeats,
                      harness_config=harness_config or {},
                      evaluation_tasks=[k for k, t in self.tasks.items() if t["split"] == "evaluation"])
        if (self.output / "run.json").exists() and read(self.output / "run.json") != config:
            raise ConflictError("Existing run has a different configuration; use a new output directory")
        write(self.output / "run.json", config)

    def task(self, task_id):
        if task_id not in self.tasks:
            raise ValueError("Unknown task or task outside this evaluator's scope")
        return self.tasks[task_id]

    def inspect(self, task_id, table, offset=0, limit=100):
        task = self.task(task_id)
        data = read(self.bundle / task["input_asset"])
        if table not in data:
            return dict(available_fields=list(data), error="Unknown table/input field")
        raw = data[table]
        if not isinstance(raw, list):
            return dict(value=raw)
        return dict(table=table, total=len(raw), offset=offset, records=raw[max(0, offset):max(0, offset) + min(max(1, limit), 100)])

    def grade(self, task_id, text):
        task = self.task(task_id)
        try:
            code = parse(text, task["language"])
        except (ValueError, SyntaxError, TypeError, AttributeError) as error:
            return dict(status="scored", pass_=False, score=0, actually_executed=False,
                        actual=dict(ok=False, error_type="FormatError", error=str(error)))
        actual = self.executor.execute(task, code, self.bundle)
        passed = actual["ok"] and equal(self.gold[task_id]["expected"], actual.get("value"))
        return dict(status="scored", pass_=passed, score=int(passed), actually_executed=True, actual=actual)

    def feedback(self, task_id, text):
        if self.task(task_id)["split"] == "evaluation":
            raise PermissionError("Evaluation feedback is private; submit through evaluate")
        result = self.grade(task_id, text)
        result["expected"] = self.gold[task_id]["expected"]
        return result

    def evaluate(self, task_id, text, repeat=1, state_ref=None, metadata=None):
        if self.task(task_id)["split"] != "evaluation":
            raise ValueError("Only evaluation tasks have cold-evaluation slots")
        if type(repeat) is not int or repeat not in range(1, self.repeats + 1):
            raise ValueError("Repeat outside the configured plan")
        receipt = f"{task_id}.r{repeat}"
        path = self.output / "evaluations" / f"{receipt}.json"
        request = dict(task_id=task_id, text=text, repeat=repeat, state_ref=state_ref, metadata=metadata or {})
        # A persistent slot prevents accidental re-execution after HTTP disconnects.
        # Reusing a slot with another answer is rejected, not counted as another sample.
        with self.lock:
            if path.exists():
                saved = read(path)
                if saved["request"] != request:
                    raise ConflictError("Evaluation slot already has a different submission")
                return dict(receipt=receipt, status="received", feedback="withheld")
            write(path, dict(request=request, status="pending", submitted_at=time.time()))
            try:
                grade = self.grade(task_id, text)
            except Exception as error:
                write(path, dict(request=request, status="missing", reason=type(error).__name__, error=str(error)))
                raise InfrastructureError(f"Evaluation interrupted; slot preserved: {receipt}") from error
            write(path, dict(request=request, **grade, finished_at=time.time()))
        return dict(receipt=receipt, status="received", feedback="withheld")

    def dispatch(self, request):
        operation = request["operation"]
        args = request.get("arguments", {})
        if operation == "tasks":
            return [t for t in self.tasks.values() if all(t.get(k) == v for k, v in args.items())]
        if operation == "inspect_source":
            return self.inspect(**args)
        if operation == "run_candidate":
            task = self.task(args["task_id"])
            return self.executor.execute(task, args["code"], self.bundle)
        if operation == "feedback":
            return self.feedback(**args)
        if operation == "evaluate":
            return self.evaluate(**args)
        raise ValueError("Unknown operation")


def make_server(evaluator, host="127.0.0.1", port=8765):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            if self.path != "/v1":
                self.send_error(404)
                return
            request = None
            started = time.time()
            try:
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                response = {"result": evaluator.dispatch(request)}
                status = 200
            except PermissionError as error:
                status, response = 403, {"error": str(error)}
            except ConflictError as error:
                status, response = 409, {"error": str(error)}
            except (ValueError, KeyError, TypeError) as error:
                status, response = 400, {"error": str(error)}
            except Exception as error:
                status, response = 503, {"error": str(error), "kind": "infrastructure_error"}
            with evaluator.lock, (evaluator.output / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(dict(request=request, response=response, http_status=status, started_at=started, ended_at=time.time()), ensure_ascii=False) + "\n")
            body = json.dumps(response, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass  # The result remains on disk; never repeat model or artifact execution here.

    return ThreadingHTTPServer((host, port), Handler)


def report(output):
    output = Path(output)
    config = read(output / "run.json")
    rows = []
    for task_id in config["evaluation_tasks"]:
        for repeat in range(1, config["repeats"] + 1):
            path = output / "evaluations" / f"{task_id}.r{repeat}.json"
            grade = read(path) if path.exists() else {"status": "unsubmitted"}
            rows.append(dict(task_id=task_id, level=int(task_id.split(".")[1][1:]), repeat=repeat,
                             status=grade["status"], pass_=grade.get("pass_"), reason=grade.get("reason")))
    def summarize(items):
        observed = [r for r in items if r["status"] == "scored"]
        passed = sum(r["pass_"] for r in observed)
        n = len(items)
        return dict(planned=n, observed=len(observed), passed=passed, missing=n-len(observed),
                    percentage=100*passed/len(observed) if observed else None,
                    planned_bounds=[100*passed/n, 100*(passed+n-len(observed))/n] if n else None)
    return dict(overall=summarize(rows), levels={f"L{level}": summarize([r for r in rows if r["level"] == level]) for level in config["levels"]}, slots=rows)
