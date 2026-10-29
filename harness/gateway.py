"""Local model gateway used by the harness. transport.py posts jobs to it; it forwards them to an OpenAI-compatible
endpoint (CLRBENCH_API_BASE, CLRBENCH_API_KEY) with the configured model and reasoning effort, retries transient
errors, and writes an audit log. The paper used GPT-6-Luna and GPT-6-Sol with high reasoning effort."""
import argparse, json, os, shutil, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=42802)
parser.add_argument("--base-path", default="/CLR")
parser.add_argument("--model", default="gpt-6-luna")
parser.add_argument("--reasoning", default="high")
parser.add_argument("--max-tokens", type=int, default=131072)
parser.add_argument("--concurrency", type=int, default=32)
parser.add_argument("--min-free-disk-gb", type=float, default=1.0)
ARGS = parser.parse_args()
LOCAL_PORT = ARGS.port
BASE_PATH = ARGS.base_path
API_BASE = os.environ["CLRBENCH_API_BASE"].rstrip("/")
KEY = os.environ["CLRBENCH_API_KEY"]


class _Response:
    def __init__(self, status, data):
        self.status, self.data = status, data


def _post(body):
    req = urllib.request.Request(API_BASE + "/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            return _Response(r.status, r.read())
    except urllib.error.HTTPError as e:
        return _Response(e.code, e.read())

jobs = {}
records = []
lock = threading.RLock()
slots = threading.Semaphore(ARGS.concurrency)
control = dict(concurrency_limit=ARGS.concurrency, billing_stop=False, reason=None)

def process(job, body, context, role):
    body.update(model=ARGS.model, reasoning_effort=ARGS.reasoning, max_tokens=ARGS.max_tokens)
    network_retries = {"transport": 0, "408": 0, "invalid_prompt": 0}
    attempt = 0
    retry_delay = 60
    while True:
        attempt += 1
        with slots:
            with lock:
                if shutil.disk_usage(".").free < ARGS.min_free_disk_gb * 1e9:
                    control.update(billing_stop=True, reason="free disk below --min-free-disk-gb")
                if control["billing_stop"]:
                    jobs[job] = dict(status="error", error=control["reason"])
                    return
                record = dict(index=len(records)+1, job=job, attempt=attempt,
                    context=context, model=body.get("model"),
                    label=role,
                    reasoning_effort=body.get("reasoning_effort"),
                    max_tokens=body.get("max_tokens"), has_response_format="response_format" in body,
                    response_format_type=body.get("response_format", {}).get("type"),
                    started_at=time.time(), usage=None)
                records.append(record)
            try:
                response = _post(body)
                data = response.data
            except OSError as error:
                with lock:
                    record.update(completed=False, transport_failure=True, error=type(error).__name__, ended_at=time.time())
                network_retries["transport"] += 1
                record["retry_after_seconds"] = retry_delay
                record["retry_count"] = network_retries["transport"]
                time.sleep(retry_delay)
                retry_delay = min(600, retry_delay * 2)
                continue
        with lock:
            record.update(http_status=response.status, ended_at=time.time(),
                          seconds=time.time()-record["started_at"])
            if response.status == 200:
                result = json.loads(data)
                usage = result.get("usage", {})
                record.update(completed=True, usage=usage,
                              finish_reason=result["choices"][0]["finish_reason"])
                jobs[job] = dict(status="complete", result=result)
                return
            error = data.decode(errors="replace")
            record["error"] = error[:1200]
            lowered = error.lower()
            invalid_prompt = response.status == 400 and "invalid_prompt" in lowered
            context_too_large = response.status == 400 and "context_too_large" in lowered
            if response.status == 408:
                record["network_interruption"] = True
                network_retries["408"] += 1
                record["retry_after_seconds"] = retry_delay
                record["retry_count"] = network_retries["408"]
                lock.release()
                time.sleep(retry_delay)
                lock.acquire()
                retry_delay = min(600, retry_delay * 2)
                continue
            if invalid_prompt:
                record["invalid_prompt"] = True
                network_retries["invalid_prompt"] += 1
                if network_retries["invalid_prompt"] == 1:
                    record["retry_after_seconds"] = 30
                    lock.release()
                    time.sleep(30)
                    lock.acquire()
                    continue
                jobs[job] = dict(status="error", error="Upstream HTTP 400 invalid_prompt", no_output=True)
                return
            if context_too_large:
                record["context_too_large"] = True
                jobs[job] = dict(status="error", error="Upstream HTTP 400 context_too_large", no_output=True)
                return
            if response.status == 400 and "response_format" in body and any(
                token in lowered for token in ("response_format", "json_schema", "structured output", "unsupported")):
                jobs[job] = dict(status="error", error=error[:1200], response_format_rejected=True)
                return
            quota = any(token in lowered for token in ("quota", "billing", "insufficient"))
            if quota:
                control.update(billing_stop=True, reason="Explicit quota/billing error: " + error[:1000])
                jobs[job] = dict(status="error", error=control["reason"])
                return
            record["retry_after_seconds"] = retry_delay
            record["retry_count"] = network_retries.get("upstream", 0) + 1
            network_retries["upstream"] = record["retry_count"]
            control["reason"] = "Upstream retry cooldown " + str(retry_delay) + " seconds"
        time.sleep(retry_delay)
        with lock:
            control["reason"] = None
        retry_delay = min(600, retry_delay * 2)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return
    def reply(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def do_GET(self):
        if self.path == BASE_PATH + "/ready":
            return self.reply(200, dict(ready=True, requests=len(records), **control))
        if self.path == BASE_PATH + "/audit":
            return self.reply(200, dict(requests=len(records), records=records, **control))
        job = self.path.rsplit("/", 1)[-1]
        return self.reply(200, jobs.get(job, dict(status="unknown")))
    def do_POST(self):
        job = self.path.rsplit("/", 1)[-1]
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with lock:
            if job not in jobs:
                jobs[job] = dict(status="pending")
                threading.Thread(target=process, args=(job, body, self.headers.get("X-RSI-Context"), self.headers.get("X-RSI-Role")), daemon=True).start()
        return self.reply(202, dict(accepted=True, job=job))

ThreadingHTTPServer(("127.0.0.1", LOCAL_PORT), Handler).serve_forever()  # loopback only
