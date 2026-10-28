"""Fake chat-completions endpoint for tests. It reads the chain's STATE.json to know the current candidates.
FAKE_REJECT=<level>:<C> makes P1H fail whenever that level's current candidate is C.
FAKE_P0_GUESS=<level> makes P0 list A∪P_M for that level (P0 failure).
P1 (feedback, no lesson) lists A and P_M[0]: mean generalization 1/3, inside the default band.
FAKE_P1_ALL=<level> makes P1 list every member for that level (too easy: P1 failure).
Without a STATE.json (clrsynth certify probes one-slot chains before any chain exists) the fake answers from the
lists in FAKE_LISTS: P0 lists nothing, P1 lists A, m_v and one more member, P1H lists the whole class."""
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def state():
    return json.loads(open(os.environ["FAKE_STATE"]).read())


def knowledge_answer(prompt):
    import glob
    import yaml
    m = re.search(r"applies the L(\d) rule to \S+ whose \S+ is '?([^' ]+)'? in the same way as to \S+ whose \S+ is "
                  r"'?([^' ]+?)'?, and does not apply it to \S+ whose \S+ is '?([^' ]+?)'?\.", prompt)
    screen = re.search(r"Known: an? \S+ whose \S+ is '?([^' ]+?)'? is in the class\. Feedback: an? \S+ whose \S+ is "
                       r"'?([^' ]+?)'? is treated the same way, and an? \S+ whose \S+ is '?([^' ]+?)'? is not\.", prompt)
    if screen:
        a, mv, np_ = screen.groups()
        lvl = None
    elif not m:
        return {"L1": []}                      # P0: nothing guessed
    else:
        lvl, mv, a, np_ = m.groups()
    for f in sorted(glob.glob(os.path.join(os.environ["FAKE_LISTS"], "*.yaml"))):
        for lst in yaml.safe_load(open(f)) or []:
            mem = [str(x) for x in lst.get("members") or []]
            if a in mem and mv in mem and np_ not in mem:
                ref = set(re.findall(r"^- (\S+)", prompt, flags=re.M))
                members = sorted(x for x in mem if x in ref)
                if lvl is None:
                    return {"category": lst["id"], "values": members}
                if "VERIFIED LESSON" in prompt:
                    return {f"L{lvl}": {"category": lst["id"], "values": members}}
                extra = [x for x in members if x not in (a, mv)][:1]
                return {f"L{lvl}": {"category": "?", "values": [a, mv, *extra]}}
    return {f"L{lvl}": {"category": "?", "values": [a]}}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = body["messages"][0]["content"]
        assert "temperature" not in body
        delay = float(os.environ.get("FAKE_DELAY", "0"))
        if delay:
            time.sleep(delay)
        if not os.path.exists(os.environ["FAKE_STATE"]):
            return self.reply(knowledge_answer(prompt))
        st = state()
        cur = {s["level"]: (s.get("current") or s.get("pinned")) for s in st["slots"]}
        reject = os.environ.get("FAKE_REJECT", "")
        guess = os.environ.get("FAKE_P0_GUESS", "")
        m = re.search(r"applies the L(\d) rule", prompt)
        if m:
            j = int(m.group(1))
            ans = {}
            p1 = "VERIFIED LESSON" not in prompt
            for lvl, c in cur.items():
                vals = [c["A"], *c["P_M"]]
                if p1 and os.environ.get("FAKE_P1_ALL") != str(lvl):
                    vals = [c["A"], c["P_M"][0]]
                if reject and reject == f"{lvl}:{c['C']}":
                    vals = [c["A"], c["N_p"], *c["N_t"]]
                ans[f"L{lvl}"] = {"category": c["C"], "values": vals}
        else:
            ans = {f"L{lvl}": ([c["A"], *c["P_M"]] if guess == str(lvl) else [c["A"]]) for lvl, c in cur.items()}
        self.reply(ans)

    def reply(self, ans):
        out = {"choices": [{"message": {"content": "```json\n" + json.dumps(ans) + "\n```"}}]}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H)
    srv.serve_forever()
