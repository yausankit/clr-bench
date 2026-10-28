# Scripts as run for the paper (reference)

These are the driver scripts and patches that produced the paper's runs, with machine-specific paths replaced by
variables (`CLRBENCH_RUNS`: the directory holding the run roots; `PYTHON`). They are kept to document each condition
exactly; for new runs use `harness/setup_run.py` and `harness/run_condition.sh`.

* In the original layout, `baselines_fb/<chain>` is the per-chain run directory under explicit practice feedback.
  `harness/setup_run.py` creates the same directory: the patches in `patches/` (`patch_feedback.py`,
  `patch_extra*.py`, `patch_gepa*.py`) are already applied to `harness/runtime` and `methods/`.
* `run_fb.sh` and `run_gepa3.sh` first called an internal assembly tool (`baseline_tool_v4/assemble.py`) that copied
  the harness from earlier experiment trees; `setup_run.py` replaces it. `baselines_final/CHAINS.tsv` corresponds to
  `data/CHAINS.tsv` (chain directories are `data/chains/<chain>`).
* The canonical GEPA note is now selected by `CLRBENCH_GEPA_NOTE` (default `neutral`); the `sed` edits of the note in
  `run_learn2.sh`, `run_rg.sh` and `run_variant*.sh` did the same on the original files.
* Rewarded practice (`run_rg.sh`): the evaluator change it relied on is built into `harness/runtime/*/evaluator.py`;
  set `CLR_BUNDLE=bundle_k1_v0_rg` for stage A only.

| Script | Condition |
|---|---|
| `run_fb.sh` | ACE, GEPA, DC, self and +lesson, explicit feedback (main runs; the other three methods via `run_learn2.sh`) |
| `run_extra.sh` ... `run_extra6.sh` | references: history, lesson in prompt, history + lesson, class-name oracle, lesson parts, web lookup |
| `run_learn2.sh` | any queue of (mode, method) pairs on any base model (used for GPT-6-Sol) |
| `run_variant2.sh` | text in the update step under a neutral heading: whole lesson, convention, procedure, class names |
| `run_variant3.sh` | convention in the update step at level 1 only |
| `run_variant.sh`, `run_webm.sh` | convention / web lookup / hypothesize guideline in the update step |
| `run_rg.sh` | rewarded practice |
| `run_gepa3.sh` | GEPA without a note and with the neutral note |
| `run_models.sh`, `run_sonnet.sh` | other base models (frozen agent, class-name oracle, ACE/DC) |
| `retention.py`, `agg_extra.py`, `agg_final.py` | aggregation used for the paper's data files |
