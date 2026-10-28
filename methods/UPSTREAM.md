# Upstream method code

The adapters in this directory call or reproduce six published self-evolving methods. No upstream repository is
vendored here. ACE, GEPA and EvoSkill are imported at run time from `methods/upstream/` (create it with
`methods/fetch_upstream.sh`). Dynamic Cheatsheet, ReasoningBank and Training-Free GRPO are re-implemented in
`evo_methods.py` around their official prompt files, which are copied verbatim into `methods/shared/`.

| Method | Upstream | How it is used | Local changes to upstream code |
|---|---|---|---|
| ACE | https://github.com/ace-agent/ace (pyproject version 0.1.0) | Reflector and Curator modules imported from `upstream/ace` (`ace_update` in `methods_r3.py`) | none |
| GEPA | https://github.com/gepa-ai/gepa (pyproject version 0.1.4) | `gepa.optimize` imported from `upstream/gepa/src` (`gepa_update`) | none; our adapter appends a fixed format note to the reflection input (`CLRBENCH_GEPA_NOTE`, default `neutral`) |
| EvoSkill | https://github.com/sentient-agi/EvoSkill (pyproject version 0.1.0) | proposer/generator prompts and the `skill_proposer` schema read from `upstream/EvoSkill/src` (`evoskill_update`, `proposal_compat_r3.py`) | none; `proposal_compat_r3.py` parses the proposal from plain text instead of structured output |
| Dynamic Cheatsheet (DC-Cu) | https://github.com/suzgunmirac/dynamic-cheatsheet | official DC-Cu curator prompt `shared/dc_curator.txt`; execution feedback (expected/actual) appended after `[[MODEL_ANSWER]]` | re-implemented (`dc_update` in `evo_methods.py`) |
| ReasoningBank | official ReasoningBank prompts (Google LLC, Apache-2.0 header kept in `shared/rb_memory_instruction.py`); repository URL not recorded | success/failure extraction prompts, top-1 retrieval by cosine similarity with `sentence-transformers/all-MiniLM-L6-v2` | re-implemented (`rb_update`); binary pass/fail replaces the LLM judge |
| Training-Free GRPO | https://github.com/TencentCloudADP/youtu-agent (training-free GRPO) | official rollout-summary, group-advantage, group-update and batch-update prompts in `shared/tfgrpo_prompts.yaml`; G=4 rollouts at temperature 0.7 | re-implemented (`tfgrpo_update`, `run_nc100_course_tfgrpo.py`); experiences are extracted only from groups with mixed outcomes |

**Commits.** The ACE, GEPA and EvoSkill snapshots used for the paper were downloaded on 2026-09-18 without git
metadata, so the exact commits were not recorded. All files of the three snapshots are unmodified since download.
`fetch_upstream.sh` clones the repositories and checks out the last commit on or before 2026-09-18; pin a commit with
`ACE_REF`, `GEPA_REF` or `EVOSKILL_REF` if you know it.
