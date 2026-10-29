"""Dynamic Cheatsheet, ReasoningBank, and Training-Free GRPO helpers used by the test harness to put a learned state
into the solver prompt (for example ReasoningBank's retrieval)."""
import copy
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from rb_memory_instruction import SUCCESSFUL_SI as RB_SUCCESSFUL_SI
from rb_memory_instruction import FAILED_SI as RB_FAILED_SI



ROOT = Path(__file__).resolve().parent
DEST = ROOT.parent
RB_RETRIEVAL_INSTRUCTION = ("Below are some memory items that I accumulated from past interaction from the environment "
                            "that may be helpful to solve the task. You can use it when you feel it\u2019s relevant. "
                            "In each step, please first explicitly discuss if you want to use each memory item or not, "
                            "and then take action.")

_model = None
_model_lock = threading.RLock()


def _read(path):
    return json.loads(Path(path).read_text())


def _dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def _compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _config():
    path = DEST / "CONFIG.json"
    return _read(path) if path.exists() else {}


def _context(method, sid, task_id, phase):
    return dict(method=method, sample=sid, level=int(task_id.split(".")[1][1:]),
                split="evaluation", phase=phase)


def _feedback_text(feedback):
    parts = [str(feedback.get("verdict", ""))]
    if feedback.get("expected") is not None:
        parts.append("Expected result: " + _compact(feedback["expected"]))
    if feedback.get("actual") is not None:
        parts.append("Actual result: " + _compact(feedback["actual"]))
    return "\n".join(part for part in parts if part)


def _embedding_model_path():
    configured = _config().get("embedding_model")
    return Path(configured) if configured else ROOT / "sentence-transformers_all-MiniLM-L6-v2"


def _embedding_model():
    global _model
    with _model_lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer
            path = _embedding_model_path()
            _model = SentenceTransformer(str(path), device="cpu")
            _model.max_seq_length = 256
        return _model


def embed_texts(texts):
    items = list(texts)
    if not items:
        return []
    with _model_lock:
        vectors = _embedding_model().encode(items, normalize_embeddings=True,
                                            show_progress_bar=False, convert_to_numpy=True)
    return [[float(value) for value in row] for row in vectors]


def _render_memory_item(item):
    lines = []
    if item.get("title"):
        lines.append("### " + item["title"])
    if item.get("description"):
        lines.append("Description: " + item["description"])
    if item.get("content"):
        lines.append("Content: " + item["content"])
    return "\n".join(lines)


def memory_section(task_prompt, experiences, k=None):
    """Retrieve the top-k trajectories (paper default k=1), then expand their items."""
    from sentence_transformers import util
    if not experiences:
        return ""
    if k is None:
        k = int(_config().get("rb_top_k", 1))
    missing = [item for item in experiences if not item.get("query_embedding")]
    if missing:
        vectors = embed_texts([item.get("query", "") for item in missing])
        for item, vector in zip(missing, vectors):
            item["query_embedding"] = vector
    query = embed_texts([task_prompt])[0]
    scores = util.cos_sim(query, [item["query_embedding"] for item in experiences])[0].tolist()
    order = sorted(range(len(experiences)), key=lambda index: scores[index], reverse=True)[:max(1, k)]
    items = [memory_item for index in order for memory_item in experiences[index].get("memory_items", [])]
    rendered = [_render_memory_item(item) for item in items]
    return "\n\n" + RB_RETRIEVAL_INSTRUCTION + "\n\n" + "\n\n".join(text for text in rendered if text)


def _parse_memory_items(raw):
    raw = raw.strip()
    if not raw:
        return []
    starts = [match.start() for match in re.finditer(r"^# Memory Item\b.*$", raw, re.M)]
    blocks = [raw[start:end].strip() for start, end in zip(starts, starts[1:] + [len(raw)])] if starts else []
    items = []
    for block in blocks:
        values = {}
        for name in ("Title", "Description", "Content"):
            match = re.search(r"^##\s*" + name + r"\s*:?\s*(.*?)(?=^##\s*|\Z)", block, re.M | re.S)
            values[name.lower()] = re.sub(r"\s+", " ", match.group(1)).strip() if match else ""
        if any(values.values()):
            items.append(values)
    if items:
        return items
    return [dict(title="Memory item %d" % (index + 1), description="", content=part.strip())
            for index, part in enumerate(re.split(r"\n\s*\n", raw)) if part.strip()]


def dc_update(native, sid, level, state, history, folder):
    folder = Path(folder)
    trace = history[-1]
    prompt = (ROOT / "dc_curator.txt").read_text()
    feedback = _feedback_text(trace["feedback"])
    prompt = prompt.replace("[[PREVIOUS_CHEATSHEET]]", state.get("text") or "(empty)")
    prompt = prompt.replace("[[QUESTION]]", trace["task_prompt"])
    prompt = prompt.replace("[[MODEL_ANSWER]]", trace["assistant_final"] + "\n\nEXECUTION FEEDBACK:\n" + feedback)
    prompt = prompt
    response = native.call(_context("dc", sid, trace["task_id"], "curator"), "curator", prompt, "", kind="text")
    raw = response["text"].strip()
    if "<cheatsheet>" in raw and "</cheatsheet>" in raw:
        cheatsheet = raw.split("<cheatsheet>", 1)[1].split("</cheatsheet>", 1)[0].strip()
    else:
        cheatsheet = state.get("text", "")
    new = dict(text=cheatsheet)
    _dump(folder / "UPDATE.json", dict(method="dc", implementation="official_DC_Cu_curator",
        before=state, after=new, changed=new != state, source_task_id=trace["task_id"],
        feedback_received=trace["feedback"], response_file=response["folder"]))
    return new


def rb_update(native, sid, level, state, history, folder):
    folder = Path(folder)
    trace = history[-1]
    passed = bool(trace["feedback"]["pass_"])
    system = RB_SUCCESSFUL_SI if passed else RB_FAILED_SI
    outcome = "succeeded" if passed else "failed"
    prompt = ("**Query:** " + trace["task_prompt"] + "\n\n**Trajectory:**\n" + trace["assistant_final"] +
              "\n\nThe task " + outcome + " because: " + _feedback_text(trace["feedback"]))
    prompt = prompt
    response = native.call(_context("rb", sid, trace["task_id"], "extract_success" if passed else "extract_failure"),
                           "extract_success" if passed else "extract_failure", prompt, system, kind="text")
    memory_items = _parse_memory_items(response["text"])
    experiences = copy.deepcopy(state.get("experiences", []))
    next_id = int(state.get("next_global_id", 1))
    added = None
    if memory_items:
        added = dict(id="RB%d" % next_id, task_id=trace["task_id"], query=trace["task_prompt"],
                     status="success" if passed else "fail", memory_items=memory_items,
                     query_embedding=embed_texts([trace["task_prompt"]])[0])
        experiences.append(added)
        next_id += 1
    new = dict(experiences=experiences, next_global_id=next_id)
    _dump(folder / "UPDATE.json", dict(method="rb", implementation="official_ReasoningBank_extraction",
        before=state, after=new, changed=new != state, source_task_id=trace["task_id"],
        status="success" if passed else "failure", added=added, consolidation="append",
        feedback_received=trace["feedback"], response_file=response["folder"]))
    return new


_TF = yaml.safe_load((ROOT / "tfgrpo_prompts.yaml").read_text())


def _tf_render(name, **values):
    text = _TF[name]
    for key, value in values.items():
        text = text.replace("{{ " + key + " }}", str(value))
    return text


def _json_array(text):
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.S | re.I)
    if match:
        text = match.group(1).strip()
    value = json.loads(text)
    if not isinstance(value, list):
        raise ValueError("Expected a JSON array")
    return value


def _experience_view(experiences):
    if not experiences:
        return "None"
    return "\n".join("[%s]. %s" % (key, value) for key, value in experiences.items())


def _format_experiences_and_operations(experiences, operations):
    if not operations:
        return "No batch operations."
    rows = []
    for key, content in experiences.items():
        related = [op for op in operations if op.get("id") == key]
        row = "Experience %s:\nContent: %s\n" % (key, content)
        if related:
            row += "Related Operations:\n" + "\n".join(json.dumps(op, ensure_ascii=False, indent=2) for op in related)
        else:
            row += "No related operations."
        rows.append(row)
    without_id = [op for op in operations if not op.get("id")]
    if without_id:
        rows.append("Operations without specific Experience ID:\n" +
                    "\n".join(json.dumps(op, ensure_ascii=False, indent=2) for op in without_id))
    return "\n\n".join(rows)


def _apply_operations(experiences, operations):
    result = copy.deepcopy(experiences)
    next_id = int(max([int(key[1:]) for key in result if re.fullmatch(r"G\d+", key)] or [-1])) + 1
    for op in operations:
        operation = str(op.get("operation", "ADD")).upper()
        target = op.get("id")
        content = str(op.get("content", "")).strip()
        if not content and operation != "DELETE":
            continue
        if operation == "ADD":
            result["G%d" % next_id] = content
            next_id += 1
        elif operation == "UPDATE":
            if target in result:
                result[target] = content
            else:
                result["G%d" % next_id] = content
                next_id += 1
        elif operation == "DELETE" and target in result:
            del result[target]
    return result, next_id


def _reindex_experiences(experiences):
    return {"G%d" % index: content for index, content in enumerate(experiences.values())}


def _summary_call(parent_native, index, folder, ctx, question, trajectory, answer, critique):
    from solver import Native
    system = _tf_render("SINGLE_ROLLOUT_SUMMARY_TEMPLATE_SP",
                        agent_objective=AGENT_OBJECTIVE, learning_objective=LEARNING_OBJECTIVE)
    prompt = _tf_render("SINGLE_ROLLOUT_SUMMARY_TEMPLATE_UP", question=question,
                        trajectory=trajectory, answer=answer, critique=critique)
    prompt = prompt
    native = Native(parent_native.client, Path(folder) / ("summary%d" % (index + 1)))
    return native.call(ctx, "summary%d" % (index + 1), prompt, system, kind="text")["text"]


AGENT_OBJECTIVE = """input: A task asking for a Python program that defines solve(data) and returns one integer for a JSON report
output: A complete Python program implementing solve(data)"""
LEARNING_OBJECTIVE = """Help the agent discover reusable, hidden rules for class membership and program construction, extracting concise guidelines from contrasting correct and incorrect execution attempts."""


def tfgrpo_update(native, sid, level, state, history, folder):
    folder = Path(folder)
    trace = history[-1]
    group = trace.get("group") or []
    scores = [float(bool(item["feedback"]["pass_"])) for item in group]
    average = sum(scores) / len(scores) if scores else 0.0
    if len(group) < 2 or average <= 0.0 or average >= 1.0:
        new = copy.deepcopy(state)
        reason = ("all-correct group filter" if average >= 1.0 and group else
                  "all-wrong group filter" if group else "no group sampled")
        _dump(folder / "UPDATE.json", dict(method="tfgrpo", implementation="official_Training_Free_GRPO",
            changed=False, skipped="本组无优势信号、未更新", skip_reason=reason,
            group_size=len(group), group_rewards=scores, group_average=average))
        return new

    ctx = _context("tfgrpo", sid, trace["task_id"], "experience_update")
    question = trace["task_prompt"]
    answer = _compact(trace["feedback"].get("expected"))
    summaries = []
    with ThreadPoolExecutor(max_workers=min(4, len(group))) as pool:
        futures = []
        for index, item in enumerate(group):
            trajectory = _compact([dict(assistant_final=item["assistant_final"],
                                        execution_feedback=item["feedback"].get("verdict", ""))])
            futures.append(pool.submit(_summary_call, native, index, folder, ctx, question,
                                       trajectory, answer, item["feedback"].get("verdict", "")))
        summaries = [future.result() for future in futures]

    formatted = "\n\n".join("Attempt %d (Reward %s):\n%s" % (index + 1, scores[index], summary)
                            for index, summary in enumerate(summaries))
    system = _tf_render("SINGLE_QUERY_GROUP_ADVANTAGE_SP", agent_objective=AGENT_OBJECTIVE,
                        learning_objective=LEARNING_OBJECTIVE,
                        num_experiences=int(os.environ.get("TFGRPO_NUM_EXPERIENCES", "1")))
    prompt = _tf_render("SINGLE_QUERY_GROUP_ADVANTAGE_UP", question=question, answer=answer,
                        trajectories=formatted)
    prompt = prompt
    critique = native.call(ctx, "group_advantage", prompt, system, kind="text")["text"]
    match = re.search(r"<Experiences>\s*(.*?)\s*</Experiences>", critique, re.S | re.I)
    extracted = match.group(1).strip() if match else ""

    experiences = copy.deepcopy(state.get("experiences", {}))
    operations = []
    if extracted:
        system = _tf_render("GROUP_EXPERIENCE_UPDATE_TEMPLATE_SP", agent_objective=AGENT_OBJECTIVE,
                            learning_objective=LEARNING_OBJECTIVE)
        prompt = _tf_render("GROUP_EXPERIENCE_UPDATE_TEMPLATE_UP",
                            existing_experiences=_experience_view(experiences), new_experiences=extracted)
        prompt = prompt
        response = native.call(ctx, "group_update", prompt, system, kind="text")["text"]
        operations = _json_array(response)

    if operations:
        system = _tf_render("BATCH_EXPERIENCE_UPDATE_TEMPLATE_SP", agent_objective=AGENT_OBJECTIVE,
                            learning_objective=LEARNING_OBJECTIVE)
        prompt = _tf_render("BATCH_EXPERIENCE_UPDATE_TEMPLATE_UP",
                            experiences_and_operations=_format_experiences_and_operations(experiences, operations))
        prompt = prompt
        response = native.call(ctx, "batch_update", prompt, system, kind="text")["text"]
        operations = _json_array(response)

    experiences, _ = _apply_operations(experiences, operations)
    experiences = _reindex_experiences(experiences)
    new = dict(experiences=experiences, next_global_id=len(experiences))
    _dump(folder / "UPDATE.json", dict(method="tfgrpo", implementation="official_Training_Free_GRPO",
        changed=new != state, group_size=len(group), group_rewards=scores, group_average=average,
        official_partial_correct_filter=True, summaries=summaries, critique=critique,
        extracted=extracted, operations=operations, before=state, after=new,
        source_task_id=trace["task_id"]))
    return new


def sample_group(env_url, sid, level, replicate, attempt, state, folder, size=4, temperature=0.7):
    import solver as solver_module
    from solver import Native, solve
    from evolution_curriculum.client import Client
    folder = Path(folder)
    task_id = f"{sid}.L{level}.evaluation"
    original_completion = solver_module.completion

    def rollout_completion(messages, **kwargs):
        kwargs["temperature"] = temperature
        return original_completion(messages, **kwargs)

    def one(index):
        subfolder = folder / ("g%d" % (index + 1))
        native = Native(Client(env_url), subfolder)
        ctx = dict(method="tfgrpo", sample=sid, level=level,
                   phase=f"PB3-rep{replicate}-a{attempt}-g{index + 1}", split="evaluation", task_id=task_id)
        task, result = solve(native, ctx, copy.deepcopy(state), subfolder)
        return dict(index=index + 1, task_id=task_id, task_prompt=task["prompt"],
                    assistant_final=result["text"], response_folder=result["folder"])

    for index in range(size):
        (folder / ("g%d" % (index + 1))).mkdir(parents=True, exist_ok=True)
    solver_module.completion = rollout_completion
    try:
        with ThreadPoolExecutor(max_workers=min(size, 8)) as pool:
            return list(pool.map(one, range(size)))
    finally:
        solver_module.completion = original_completion
