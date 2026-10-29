"""Adapters for ACE, GEPA, and EvoSkill in the + lesson condition: identical to methods/self/methods_r3.py except that
the lesson (HINT_NC100.txt) is appended, under "VERIFIED LESSON (correct, from the task designers):", to every update
input. harness/variants.py swaps this text and heading for the update-text variants."""
from concurrent.futures import ThreadPoolExecutor
"""Small-budget evolution from own public history, never hidden test feedback.

ACE uses official Reflector/Curator modules; GEPA uses the official optimizer;
EvoSkill retains the declared proposer/builder/Pareto adaptation. AFlow runs in
its own native container through aflow_entry.py (see AFLOW_INTEGRATION below).
"""
import ast
import copy
import importlib
import json
import os
from pathlib import Path
import random
import re
import runpy
import sys
import threading

from common import OLD
from proposal_compat_r3 import parse_proposal_with_metadata
from solver import solve
from evo_methods import dc_update, rb_update, tfgrpo_update

HINT_TEXT = (Path(__file__).resolve().parents[1] / "HINT_NC100.txt").read_text().rstrip("\n")




def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n")


def json_object(text):
    text = text.strip()
    if text.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n?```", text, re.S)
        if not match:
            raise ValueError("Expected a single JSON object")
        text = match.group(1)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def released_ids(sid, level, history):
    ids = []
    for trace in history:
        task_id = trace["task_id"]
        match = re.fullmatch(re.escape(sid) + r"\.L([1-5])\.evaluation", task_id)
        if match is None or int(match.group(1)) > level:
            raise ValueError("History contains a different course or future task")
        if task_id not in ids:
            ids.append(task_id)
    if not ids:
        raise ValueError("An evolution update requires released public history")
    if ids != sorted(ids, key=lambda value: int(value.split(".")[1][1:])):
        raise ValueError("History must be ordered by level")
    return ids


def context(method, sid, task_id, phase="update"):
    return dict(method=method, sample=sid,
                level=int(task_id.split(".")[1][1:]),
                split="evaluation", phase=phase)


def score_of(feedback):
    score = float(feedback["score"])
    if score != float(bool(feedback["pass_"])):
        raise ValueError("Public development must use full-contract binary pass score")
    return score


class PublicDevelopment:
    """Actual state-conditioned solves; prior formal grades are never a cache.

    Exact repeats of the same candidate and historical task reuse this search's
    own already-completed solve/grade. This is not another model sampling draw.
    """
    def __init__(self, native, method, sid, level, history, folder):
        self.native, self.method, self.sid = native, method, sid
        self.ids = released_ids(sid, level, history)
        self.folder, self.serial = Path(folder), 0
        self.cache = []
        self.lock = threading.RLock()
        public = native.client.tasks(course_id=sid)
        actual_ids = {task["task_id"] for task in public}
        if actual_ids != set(self.ids):
            raise ValueError("Development endpoint must expose exactly released history")

    def _reserve(self, task_ids):
        plans = []
        with self.lock:
            for task_id in task_ids:
                self.serial += 1
                plans.append((task_id, self.folder / f"{self.serial:03d}-{task_id}"))
        return plans

    def evaluate_one(self, task_id, state, folder=None):
        if task_id not in self.ids:
            raise PermissionError("Candidate evaluation outside released history")
        if folder is None:
            folder = self._reserve([task_id])[0][1]
        with self.lock:
            cached = next((copy.deepcopy((trace, origin)) for cached_id, cached_state, trace, origin in self.cache
                           if cached_id == task_id and cached_state == state), None)
        if cached is not None:
            trace, origin = cached
            dump(folder / "REUSE.json", dict(source=origin,
                 reason="same candidate and public task, own saved observation"))
            return score_of(trace["feedback"]), trace
        ctx = context(self.method, self.sid, task_id, "development")
        task, output = solve(self.native, ctx, copy.deepcopy(state), folder)
        if task["task_id"] != task_id:
            raise ValueError("Solver returned a different historical task")
        feedback = self.native.client.feedback(task_id, output["text"])
        trace = dict(task_id=task_id, task_prompt=task["prompt"],
                     assistant_final=output["text"], feedback=feedback,
                     candidate_state=copy.deepcopy(state),
                     feedback_scope="past_public_input_only")
        dump(folder / "TRACE.json", trace)
        dump(folder / "GRADE.json", feedback)
        with self.lock:
            self.cache.append((task_id, copy.deepcopy(state), copy.deepcopy(trace),
                               str(folder / "TRACE.json")))
        return score_of(feedback), trace

    def evaluate_many(self, task_ids, state):
        plans = self._reserve(list(task_ids))
        with ThreadPoolExecutor(max_workers=max(1, len(plans))) as pool:
            rows = list(pool.map(lambda item: self.evaluate_one(item[0], state, item[1]), plans))
        return rows

    def evaluate(self, state):
        rows = self.evaluate_many(self.ids, state)
        return [row[0] for row in rows], [row[1] for row in rows]


_ace_lock = threading.RLock()


def ace_update(native, sid, level, state, history, folder):
    folder = Path(folder)
    ids = released_ids(sid, level, history)
    trace = history[-1]
    ctx = context("ace", sid, ids[-1])
    sys.path.insert(0, str(Path(OLD) / "upstream/ace"))
    rm = importlib.import_module("ace.core.reflector")
    cm = importlib.import_module("ace.core.curator")
    from playbook_utils import update_bullet_counts, get_playbook_stats

    def bridge(client, provider, model, question, role, call_id, **kwargs):
        result = native.call(ctx, role, question,
            "You are the ACE " + role + ". Follow the requested JSON schema. "
            "Learn from already-released execution feedback. Return valid JSON only.",
            kind="text")
        return result["text"], dict(native=result["folder"],
                                    provider="own-public-history", model="gpt-6-luna")

    question = trace["task_prompt"] + "\nFEEDBACK CONTRACT: This is your own " \
        "submitted program and its released execution feedback. " \
        "bullets_used is the current playbook for comparison, " \
        "not proof that a prior bullet caused the result. reasoning_trace is submitted " \
        "executable source. Wrong submissions receive every failing input, each with its expected and actual results."
    question += released_reference_blocks(history) + "\nOWN_HISTORY_WITH_VERDICTS:\n" + compact(history) + "\nVERIFIED LESSON (correct, from the task designers):\n" + HINT_TEXT
    feedback = trace["feedback"]
    # Official modules store their bridge at module scope; serialize that scope.
    with _ace_lock:
        old_r, old_c = rm.timed_llm_call, cm.timed_llm_call
        rm.timed_llm_call = cm.timed_llm_call = bridge
        try:
            reflector = rm.Reflector(None, "portable", "gpt-6-luna", 16384)
            curator = cm.Curator(None, "portable", "gpt-6-luna", 16384)
            reflection, tags, rinfo = reflector.reflect(
                question=question, reasoning_trace=trace["assistant_final"],
                predicted_answer=feedback["actual"] if isinstance(feedback["actual"],str) else compact(feedback["actual"]),
                ground_truth=compact(feedback.get("expected")) + reference_block(trace),
                environment_feedback=feedback["verdict"] if not feedback["pass_"] else compact(feedback), bullets_used=state["memory"],
                use_ground_truth=True, use_json_mode=True,
                call_id=f"{sid}-L{level}", log_dir=str(folder))
            counted = update_bullet_counts(state["memory"], tags)
            memory, next_id, operations, cinfo = curator.curate(
                current_playbook=counted, recent_reflection=reflection,
                question_context=question, current_step=len(history), total_samples=3,
                token_budget=12000, playbook_stats=get_playbook_stats(counted),
                use_ground_truth=True, use_json_mode=True,
                call_id=f"{sid}-L{level}", log_dir=str(folder),
                next_global_id=state.get("next_global_id", 1))
        finally:
            rm.timed_llm_call, cm.timed_llm_call = old_r, old_c
    new = dict(memory=memory, next_global_id=next_id)
    dump(folder / "UPDATE.json", dict(method="ace", before=state, after=new,
        changed=new != state, source_task_id=ids[-1], reflection=reflection,
        tags=tags, operations=operations, reflector=rinfo, curator=cinfo,
        off_policy=False, tags_are_causal_attribution=False))
    return new


class FileLogger:
    """GEPA logging without process-wide stdout or stderr replacement."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def log(self, message):
        with self.lock, self.path.open("a") as stream:
            print(message, file=stream)


class GEPAAdapter:
    propose_new_texts = None

    def __init__(self, development, history):
        self.development, self.history = development, copy.deepcopy(history)

    def evaluate(self, batch, candidate, capture_traces=False):
        from gepa.core.adapter import EvaluationBatch
        rows = self.development.evaluate_many(batch, {"text": candidate["policy"]})
        return EvaluationBatch(outputs=[row[1]["assistant_final"] for row in rows],
            scores=[row[0] for row in rows],
            trajectories=[row[1] for row in rows] if capture_traces else None,
            num_metric_calls=len(batch))

    def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
        return {name: [dict(t, **({"Reference program (correct)": h["reference_program"]} if h.get("reference_solution_provided") else {})) for t in list(eval_batch.trajectories or []) for h in [next(x for x in self.history if x["task_id"] == t["task_id"])]] + [dict(
            own_public_history=self.history,
            note="Historical grades are from this method's own formal programs. Candidate scores come from fresh development on all tests at each level; wrong submissions receive every failing input, each with its expected and actual results.")]
            for name in components_to_update}


# GEPA note appended to every reflection input (see prompts/gepa_note*.txt). The paper's main results use
# 'neutral'; 'explicit' names the test aggregation; 'none' is the original GEPA without a note.
_GEPA_NOTES = {"neutral": "\n\nNote on the policy: it will also be used for this level's test task, which has the same records and rules but may ask for a different output (for example a different aggregation over the entities). Keep the policy about which records count and which rules apply; do not state the output aggregation or format, and let each task's own instructions decide them.",
               "explicit": "\n\nNote on the policy: it will also be used for this level's test task, which has the same records and rules but may ask for a different output (for example the sum over all entities instead of the largest total). Keep the policy about which records count and which rules apply; do not state the output aggregation or format, and let each task's own instructions decide them.",
               "none": ""}
GEPA_FORMAT_NOTE = _GEPA_NOTES[os.environ.get("CLRBENCH_GEPA_NOTE", "neutral")]


def gepa_update(native, sid, level, state, history, folder):
    folder = Path(folder)
    sys.path.insert(0, str(Path(OLD) / "upstream/gepa/src"))
    from gepa import optimize
    from gepa.utils.stop_condition import MaxCandidateProposalsStopper
    development = PublicDevelopment(native, "gepa", sid, level, history,
                                    folder / "executions")
    initial_scores, _ = development.evaluate({"text": state["text"]})
    if all(value >= 1.0 for value in initial_scores):
        dump(folder / "UPDATE.json", dict(method="gepa", changed=False,
            skipped="perfect_strict_development", initial_scores=initial_scores,
            task_ids=development.ids, validation_is_independent=False))
        return copy.deepcopy(state)
    serial = 0
    ctx = context("gepa", sid, development.ids[-1])

    def reflector(prompt):
        nonlocal serial
        serial += 1
        return native.call(ctx, f"reflect{serial}",
            (prompt if isinstance(prompt, str) else compact(prompt)) + released_reference_blocks(history) + GEPA_FORMAT_NOTE + "\nVERIFIED LESSON (correct, from the task designers):\n" + HINT_TEXT,
            "Optimize the persistent policy from supplied public experience. "
            "Preserve GEPA output delimiters exactly.", kind="text")["text"]

    result = optimize(seed_candidate={"policy": state["text"]},
        trainset=development.ids, valset=development.ids,
        adapter=GEPAAdapter(development, history), reflection_lm=reflector,
        candidate_selection_strategy="pareto", frontier_type="instance",
        skip_perfect_score=True, reflection_minibatch_size=1, perfect_score=1.0,
        use_merge=True, stop_callbacks=MaxCandidateProposalsStopper(2),
        run_dir=str(folder / "search"), logger=FileLogger(folder / "search/run_log.txt"),
        display_progress_bar=False, use_cloudpickle=False, write_agent_state=False,
        cache_evaluation=False, seed=level, raise_on_exception=True,
        acceptance_criterion="strict_improvement")
    dump(folder / "SEARCH_RESULT.json", result.to_dict())
    candidate = {"text": result.best_candidate["policy"]}
    selected_scores, _ = development.evaluate(candidate)
    # Strict improvement keeps the incumbent on ties, including noisy search ties.
    improved = sum(selected_scores) > sum(initial_scores)
    new = candidate if improved else copy.deepcopy(state)
    dump(folder / "UPDATE.json", dict(method="gepa", changed=new != state,
        mechanism="official_GEPA_search", proposals_limit=2, reflection_calls=serial,
        initial_scores=initial_scores, proposed_best_scores=selected_scores,
        selected_scores=selected_scores if improved else initial_scores,
        task_ids=development.ids, validation_is_independent=False,
        donor_scores_used_as_candidate_scores=False))
    return new


def validate_files(files):
    if not isinstance(files, dict):
        raise ValueError("Skill files must be a mapping")
    for name, content in files.items():
        if not isinstance(name, str) or not isinstance(content, str):
            raise ValueError("Skill file paths and contents must be strings")
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Skill file escapes its directory")
        if Path(name).suffix == ".py":
            ast.parse(content)
    if files and not any(Path(name).name == "SKILL.md" for name in files):
        raise ValueError("A skill directory requires SKILL.md")
    return files


def pareto_indices(nodes):
    return [i for i, node in enumerate(nodes) if not any(
        all(a >= b for a, b in zip(other["scores"], node["scores"])) and
        any(a > b for a, b in zip(other["scores"], node["scores"]))
        for j, other in enumerate(nodes) if j != i)]


def evoskill_update(native, sid, level, state, history, folder):
    folder = Path(folder)
    development = PublicDevelopment(native, "evoskill", sid, level, history,
                                    folder / "executions")
    initial = {"files": copy.deepcopy(state["files"])}
    scores, traces = development.evaluate(initial)
    base = Path(OLD) / "upstream/EvoSkill"
    proposer = runpy.run_path(str(base / "src/agent_profiles/skill_proposer/prompt.py"))[
        "SKILL_PROPOSER_SYSTEM_PROMPT"]
    proposer += "\nThe required Brainstorming skill follows inline.\n" + (
        base / ".claude/skills/brainstorming/SKILL.md").read_text() + \
        "\nReturn the specified structured proposal using either JSON or your official " \
        "explicit <proposal> fields. The formal traces are this method's own " \
        "previous executions; candidate development is scored separately."
    builder = """Implement the proposed reusable skill as a complete files mapping.
Return the upstream ToolGeneratorResponse JSON object with generated_skill containing
ONLY a JSON string encoding {"files":{"skill-name/SKILL.md":"complete content", "skill-name/scripts/helper.py":"optional complete source"}} and reasoning explaining implementation choices.
Include every retained parent file. SKILL.md has name/description YAML frontmatter,
when to use it, and actionable steps. Optional standard-library Python helpers
define synchronous run(data,args) returning JSON-serializable results. Helpers have
no gold answers, model API, network, or external files. The solver can read_skill(path)
and run_skill(path,args). Describe invocation precisely. Use actual input keys from
public experience, preserve the task's final program contract, and avoid hardcoding
public answers. Wrong submissions receive every failing input, each with its expected and actual results. Strict binary scores are supplied."""
    schemas = Path(OLD) / 'upstream/EvoSkill/src/schemas'
    proposer_model = runpy.run_path(str(schemas / 'skill_proposer.py'))['SkillProposerResponse']
    builder_model = runpy.run_path(str(schemas / 'tool_generator.py'))['ToolGeneratorResponse']
    def strict_schema(model):
        schema = model.model_json_schema()
        schema['additionalProperties'] = False
        schema['required'] = list(schema.get('properties', {}))
        return schema
    proposer_format = dict(type='json_schema', json_schema=dict(name='SkillProposerResponse', strict=True, schema=strict_schema(proposer_model)))
    builder_format = dict(type='json_schema', json_schema=dict(name='ToolGeneratorResponse', strict=True, schema=strict_schema(builder_model)))
    nodes = [dict(state=initial, scores=scores, traces=traces, parent=None)]
    records = []
    search_history = copy.deepcopy(state.get("search_history", []))
    rng = random.Random(1200 + level)
    ctx = context("evoskill", sid, development.ids[-1])
    for iteration in (1, 2):
        parent_index = rng.choice(pareto_indices(nodes))
        parent = nodes[parent_index]
        if all(score >= 1.0 for score in parent["scores"]):
            records.append(dict(iteration=iteration, skipped="perfect_strict_development"))
            break
        target = folder / f"candidate{iteration}"
        record = dict(iteration=iteration, parent=parent_index, valid=False, changed=False)
        try:
            response = native.call(ctx, f"proposer{iteration}", compact(dict(
                current_files=parent["state"]["files"],
                own_public_history=history, history=search_history,
                selected_parent_public_development=parent["traces"])) + released_reference_blocks(history) + "\nVERIFIED LESSON (correct, from the task designers):\n" + HINT_TEXT, proposer, kind="text", response_format=proposer_format)
            parsed = parse_proposal_with_metadata(response["text"],
                schema_file=base / "src/schemas/skill_proposer.py")
            proposal = parsed["proposal"]
            dump(target / "PROPOSAL_PARSE.json", parsed)
            dump(target / "PROPOSAL.json", proposal)
            response = native.call(ctx, f"builder{iteration}", compact(dict(
                proposal=proposal, parent_files=parent["state"]["files"],
                own_public_history=history)) + "\nVERIFIED LESSON (correct, from the task designers):\n" + HINT_TEXT, builder, kind="text", response_format=builder_format)
            builder_output = json_object(response["text"])
            candidate = {"files": validate_files(json_object(builder_output["generated_skill"])["files"])}
            dump(target / "STATE.json", candidate)
            record.update(valid=True, changed=candidate != parent["state"])
        except (ValueError, TypeError, KeyError, SyntaxError) as error:
            record["invalid_output"] = str(error)
            candidate = None
        # Keep infrastructure/solver failures outside the model-output parser catch.
        if candidate is not None and record["changed"]:
            candidate_scores, candidate_traces = development.evaluate(candidate)
            record["scores"] = candidate_scores
            nodes.append(dict(state=candidate, scores=candidate_scores,
                              traces=candidate_traces, parent=parent_index))
        records.append(record)
        search_history.append(copy.deepcopy(record))
        dump(target / "UPDATE.json", record)
    best = max(range(len(nodes)), key=lambda index: sum(nodes[index]["scores"]))
    improved = sum(nodes[best]["scores"]) > sum(scores)
    selected = best if improved else 0
    new = {**copy.deepcopy(nodes[selected]["state"]), "search_history": search_history}
    dump(folder / "SEARCH_NODES.json", nodes)
    dump(folder / "UPDATE.json", dict(method="evoskill", implementation="adapted",
        changed=new["files"] != state["files"], candidates=records,
        frontier=pareto_indices(nodes), selected_node=selected,
        initial_scores=scores, selected_scores=nodes[selected]["scores"],
        task_ids=development.ids, validation_is_independent=False,
        donor_scores_used_as_candidate_scores=False))
    return new


def update(method, native, sid, level, state, history, folder):
    """Run the update step of `method` after one practice attempt and return the new state."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    released_ids(sid, level, history)
    dump(Path(folder) / "OWN_HISTORY.json", history)
    return {"ace": ace_update, "gepa": gepa_update, "evoskill": evoskill_update,
            "dc": dc_update, "rb": rb_update, "tfgrpo": tfgrpo_update}[
        method](native, sid, level, copy.deepcopy(state), copy.deepcopy(history), Path(folder))


def reference_block(trace):
    return "\nREFERENCE PROGRAM (correct):\n" + trace["reference_program"] if trace.get("reference_solution_provided") else ""

def released_reference_blocks(history):
    return "".join(reference_block(t) for t in history)
