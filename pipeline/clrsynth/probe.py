"""Probe requests (OpenAI-compatible chat completions) and judging of the three in-chain probes:
  Hidden (P0): label and example only; no sample may recover the class.
  Learnable (P1): practice feedback alone; the model must assign between 1/6 and 2/3 of the unseen members.
  Solvable (P1H): feedback and the lesson; soft score of at least 0.8 on average and 0.6 in every rotation.
The soft score is the share of pool values whose membership the model gets right."""
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


class ProbeError(Exception):
    pass


class Endpoint:
    def __init__(self, stop_flag=None):
        self.url = os.environ.get("CLRSYNTH_ENDPOINT", "").rstrip("/")
        self.model = os.environ.get("CLRSYNTH_MODEL", "")
        self.reasoning = os.environ.get("CLRSYNTH_REASONING", "high")
        self.concurrency = int(os.environ.get("CLRSYNTH_CONCURRENCY", "8"))
        self.max_tokens = int(os.environ.get("CLRSYNTH_MAX_TOKENS", "65536"))
        if not self.url or not self.model:
            raise ProbeError("set CLRSYNTH_ENDPOINT and CLRSYNTH_MODEL")
        cmd = os.environ.get("CLRSYNTH_API_KEY_CMD")
        key = os.environ.get("CLRSYNTH_API_KEY", "")
        if cmd:
            key = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True).stdout.strip()
        self._key = key
        self.stop_flag = stop_flag or (lambda: False)

    def complete(self, prompt):
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.max_tokens}
        if self.reasoning and self.reasoning != "none":
            body["reasoning_effort"] = self.reasoning
        data = json.dumps(body).encode()
        wait = 60
        while True:
            if self.stop_flag():
                raise ProbeError("stopped")
            req = urllib.request.Request(self.url + "/chat/completions", data=data,
                                         headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {self._key}"})
            try:
                with urllib.request.urlopen(req, timeout=3600) as resp:
                    out = json.loads(resp.read().decode())
                return out["choices"][0]["message"].get("content") or ""
            except urllib.error.HTTPError as e:
                text = e.read().decode(errors="replace")[:500]
                if e.code in (408, 429) or e.code >= 500:
                    if "quota" in text.lower() and e.code == 429 and "exceeded" in text.lower():
                        raise ProbeError(f"quota error {e.code}: {text}")
                else:
                    raise ProbeError(f"HTTP {e.code}: {text}")
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
                pass
            for _ in range(wait):
                if self.stop_flag():
                    raise ProbeError("stopped")
                time.sleep(1)
            wait = min(wait * 2, 600)

    def run_all(self, prompts):
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            return list(pool.map(self.complete, prompts))


def parse_json_answer(text):
    """Last top-level JSON object in the reply (fenced or bare)."""
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    candidates = blocks[::-1] + [text[i:] for i in [m.start() for m in re.finditer(r"\{", text)]]
    for c in candidates:
        try:
            obj, _ = json.JSONDecoder().raw_decode(c.strip())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def norm(v):
    return str(v).strip().strip("'\"").strip()


def listed(obj, level, with_category=False):
    if not isinstance(obj, dict):
        return set()
    entry = obj.get(f"L{level}")
    if with_category and isinstance(entry, dict):
        entry = entry.get("values")
    if not isinstance(entry, list):
        return set()
    return {norm(x) for x in entry}


def judge_p0(cand, level, samples):
    """samples: list of parsed objects. Pass: each m_i listed in at most 1 counted sample; no sample lists
    exactly A∪P_M. A sample listing >=2 N_t values does not count toward m_i listings."""
    members = {cand.A, *cand.P_M}
    counts = {m: 0 for m in cand.P_M}
    exact = 0
    for obj in samples:
        got = listed(obj, level)
        if got == members:
            exact += 1
        if len(got & set(cand.N_t)) >= 2:
            continue
        for m in cand.P_M:
            if m in got:
                counts[m] += 1
    ok = exact == 0 and all(c <= 1 for c in counts.values())
    return {"pass": ok, "m_counts": counts, "exact": exact}


def soft_score(cand, version, got):
    shown = {cand.A, cand.P_M[version], cand.N_p}
    pool = [v for v in [*cand.P_M, *cand.N_t] if v not in shown]
    members = set(cand.P_M)
    right = sum((v in got) == (v in members) for v in pool)
    return right / len(pool)


def judge_p1h(cand, level, samples, criterion, other_pool_values):
    """samples: list of (version, parsed)."""
    members = {cand.A, *cand.P_M}
    rows = []
    for v, obj in samples:
        got = listed(obj, level, with_category=True)
        rows.append({"version": v, "values": sorted(got), "soft": soft_score(cand, v, got),
                     "exact": got == members, "foreign": sorted(got & other_pool_values)})
    by_v = {}
    for r in rows:
        by_v.setdefault(r["version"], []).append(r)
    if criterion == "strict":
        ok = (sum(r["exact"] and not r["foreign"] for r in rows) >= 5
              and all(any(r["exact"] for r in by_v.get(v, [])) for v in range(3)))
    else:
        mean = sum(r["soft"] for r in rows) / len(rows)
        ok = mean >= 0.8 and all(sum(r["soft"] for r in by_v.get(v, [])) / max(len(by_v.get(v, [])), 1) >= 0.6
                                 for v in range(3))
    return {"pass": ok, "samples": rows,
            "mean_soft": round(sum(r["soft"] for r in rows) / len(rows), 4)}


def generalization(cand, version, got):
    """Share of the two members never shown in this version that the answer lists; 0 when it lists two or more
    non-members (lumping the whole family is no generalization)."""
    if len(got & set(cand.N_t)) >= 2:
        return 0.0
    unseen = [m for m in cand.P_M if m != cand.P_M[version]]
    return sum(m in got for m in unseen) / len(unseen)


def judge_p1(cand, level, samples, band):
    """P1: feedback without the lesson. Pass when the mean generalization lies in the band [low, high]: the class
    can be partly recovered from feedback alone (a self-learning method can gain something), but not fully
    (the verified lesson still helps)."""
    rows = [{"version": v, "values": sorted(listed(obj, level, with_category=True)),
             "g": generalization(cand, v, listed(obj, level, with_category=True))} for v, obj in samples]
    mean = sum(r["g"] for r in rows) / len(rows)
    low, high = band
    return {"pass": low - 1e-9 <= mean <= high + 1e-9, "samples": rows, "mean_g": round(mean, 4),
            "band": [round(low, 4), round(high, 4)]}

