# Method adapters

`harness/setup_run.py` overlays these files onto the harness copies of a run directory:
`self/` -> `harness_self_v0/` (learning from feedback alone), `hint/` -> `harness_hint_v0/` (+lesson: the lesson is
appended, under "VERIFIED LESSON (correct, from the task designers):", to every update input), `test/` ->
`harness_k1_test/` (test replay of learned states), and `shared/` -> all three.

| Method (paper name) | Key | Update function | File |
|---|---|---|---|
| ACE | `ace` | `ace_update` (official Reflector and Curator) | `*/methods_r3.py` |
| GEPA | `gepa` | `gepa_update` (official `gepa.optimize`, one candidate proposal per practice attempt, plus the format note) | `*/methods_r3.py` |
| EvoSkill | `evoskill` | `evoskill_update` (official proposer/builder prompts and schema; text-parsed proposals) | `*/methods_r3.py`, `shared/proposal_compat_r3.py` |
| Dynamic Cheatsheet (DC-Cu) | `dc` | `dc_update` | `*/evo_methods.py`, `shared/dc_curator.txt` |
| ReasoningBank | `rb` | `rb_update`, `memory_section` | `*/evo_methods.py`, `shared/rb_memory_instruction.py` |
| Training-Free GRPO | `tfgrpo` | `tfgrpo_update`, `sample_group` | `*/evo_methods.py`, `shared/tfgrpo_prompts.yaml`, `harness/runtime/*/run_*_tfgrpo.py` |
| Frozen agent | `frozen` | none (empty state, same solver prompt) | `harness/run_dir/run_frozen.sh` |
| History reference | `hist` | `hist_update`: every earlier practice program with its feedback, verbatim in the solver prompt | `self/methods_r3.py`, `harness/runtime/*/common.py` |
| History + lesson / convention / procedure | `histhint`, `histconv`, `histproc` | `hist_update` plus a fixed text in the solver prompt | same |
| Class-name oracle | `nameoracle` | `oracle_update`; one line per label from `prompts/class_names/<chain>.txt` | same |

How the learned state enters the solver prompt is in `persona()` of `harness/runtime/*/common.py`.
The GEPA format note is selected with `CLRBENCH_GEPA_NOTE` (`neutral`, the paper's main results; `explicit`; `none`,
the original GEPA). Upstream sources and versions: `UPSTREAM.md`; clone them with `./fetch_upstream.sh`.
