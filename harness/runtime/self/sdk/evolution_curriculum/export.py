"""Export tasks from a chain's task files into the format the task service serves; it does not regenerate tasks."""
import ast
import json
import shutil
from pathlib import Path

SPLITS = ("learning", "validation1", "validation2", "evaluation")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def export_pilot(project, output, database_dir=None):
    project, output = Path(project).resolve(), Path(output).resolve()
    frozen = project / "experiments/cross_dataset12_20260920"
    source = project / "experiments/cross_dataset_wikiskill12_20260920/data"
    cases = read(frozen / "MANIFEST.json")["courses"]
    database_dir = Path(database_dir) if database_dir else project / "experiments/relational_staircase8_20260920/rounds/r02/source/databases"
    # Read the two literal system prompts without importing historical controllers.
    personas = {}
    for node in ast.parse((frozen / "tasks.py").read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("SQL_PERSONA", "PY_PERSONA"):
                    personas[target.id] = ast.literal_eval(node.value)
    required = [database_dir / (c["db"] + ".sqlite") for c in cases.values() if c["kind"] == "sql"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Provide the original BIRD databases with --database-dir: {path}")
    if output.exists():
        raise FileExistsError(f"Export to a new directory; existing bundles are not overwritten: {output}")
    (output / "public").mkdir(parents=True)
    (output / "private/references").mkdir(parents=True)
    (output / "assets/databases").mkdir(parents=True)
    tasks, gold, courses = [], {}, []
    for sid, case in sorted(cases.items()):
        courses.append({"course_id": sid, "dataset": case["dataset"], "title": case["title"], "language": case["kind"], "levels": [1, 2, 3, 4]})
        db = None
        if case["kind"] == "sql":
            db = f"assets/databases/{case['db']}.sqlite"
            shutil.copyfile(database_dir / (case["db"] + ".sqlite"), output / db)
        for split in SPLITS:
            raw = f"assets/raw/{sid}/{split}.json"
            (output / raw).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / split / sid / "RAW.json", output / raw)
            for level in range(1, 5):
                folder = source / split / sid / f"L{level}"
                task_id = f"{sid}.L{level}.{split}"
                task = dict(task_id=task_id, course_id=sid, dataset=case["dataset"], level=level, split=split,
                            language=case["kind"], title=case["title"],
                            system=personas["SQL_PERSONA" if case["kind"] == "sql" else "PY_PERSONA"],
                            prompt=(folder / "PROMPT.md").read_text(encoding="utf-8"),
                            input_asset=raw, database_asset=db,
                            output_contract="SQLite SELECT/WITH scalar" if db else "Python solve(data) scalar",
                            feedback_policy="receipt_only" if split == "evaluation" else "execution_and_correctness")
                tasks.append(task)
                ext = "sql" if db else "py"
                ref = f"private/references/{task_id}.{ext}"
                shutil.copyfile(folder / f"reference.{ext}", output / ref)
                gold[task_id] = dict(expected=read(folder / "CASE.json")["expected"], reference=ref)
    (output / "public/tasks.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks), encoding="utf-8")
    write(output / "public/courses.json", courses)
    write(output / "private/gold.json", gold)
    provenance = read(frozen / "PROVENANCE.json")
    for record in provenance["sources"].values():
        record.pop("database_path", None)
    write(output / "provenance.json", provenance)
    manifest = dict(format="evolution-curriculum-v1", courses=len(courses), tasks=len(tasks),
                    splits=list(SPLITS), levels=[1, 2, 3, 4], evaluation_tasks=48,
                    recommended_evaluation_repeats=3, generated_model_calls=0,
                    construction="Frozen author-annotated relational curriculum; exported without regeneration",
                    upstream_data_terms="Underlying source dataset terms continue to apply; no new data license is granted.")
    write(output / "manifest.json", manifest)
    return manifest
