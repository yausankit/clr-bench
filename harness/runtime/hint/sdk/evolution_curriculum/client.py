"""Client side of the local task service. It never loads hidden answers and makes no model calls."""
import json
import urllib.error
import urllib.request


class RemoteError(RuntimeError):
    def __init__(self, status, payload):
        super().__init__(f"HTTP {status}: {payload}")
        self.status = status
        self.payload = payload


class Client:
    def __init__(self, url="http://127.0.0.1:8765"):
        self.url = url.rstrip("/") + "/v1"

    def call(self, operation, **arguments):
        data = json.dumps(dict(operation=operation, arguments=arguments), ensure_ascii=False).encode()
        request = urllib.request.Request(self.url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=None) as response:
                return json.load(response)["result"]
        except urllib.error.HTTPError as error:
            raise RemoteError(error.code, json.load(error)) from error

    def tasks(self, **filters):
        return self.call("tasks", **filters)

    def tools(self, task_id):
        return TaskTools(self, task_id)

    def feedback(self, task_id, text):
        return self.call("feedback", task_id=task_id, text=text)

    def feedback_pair(self, task_id, text):
        return self.call("feedback_pair", task_id=task_id, text=text)

    def evaluate(self, task_id, text, *, repeat=1, state_ref=None, metadata=None):
        return self.call("evaluate", task_id=task_id, text=text, repeat=repeat, state_ref=state_ref, metadata=metadata)


class TaskTools:
    def __init__(self, client, task_id):
        self.client, self.task_id = client, task_id

    def inspect_source(self, table, offset=0, limit=100):
        return self.client.call("inspect_source", task_id=self.task_id, table=table, offset=offset, limit=limit)

    def run_candidate(self, code):
        return self.client.call("run_candidate", task_id=self.task_id, code=code)

    def public_input(self):
        return self.client.call("public_input", task_id=self.task_id)

    @property
    def definitions(self):
        return [
            {"name": "inspect_source", "description": "Read the original raw input, without derived features or answers: text lines, or JSON tables and fields.",
             "parameters": {"type": "object", "properties": {"table": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}, "required": ["table", "offset", "limit"]}},
            {"name": "run_candidate", "description": "Execute a program that defines solve(data) and returns an int against the current full input; returns output/errors but no correctness feedback.",
             "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}},
        ]
