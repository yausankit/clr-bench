<div align="center">

# CLR-Bench

### More Rules, Longer Lists? Benchmarking Self-Evolving Agents on a Hidden-Rule Curriculum

**C**urriculum of **L**atent **R**ules

[![Paper](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b.svg)](#citation)
[![Python](https://img.shields.io/badge/python-3.12-3776ab.svg)](requirements.txt)
[![License](https://img.shields.io/badge/license-TBD-lightgrey.svg)](LICENSE)

**English** | [中文](README_zh.md)

</div>

<p align="center">
  <img src="assets/main_figure.png" width="100%" alt="Overview of CLR-Bench">
</p>

## Overview

Self-evolving agents rewrite a persistent state (a playbook, a prompt, a skill library, a memory bank) from feedback.
Do they learn a rule nobody told them, or do they only write down each correction as an exception?

CLR-Bench answers this with **curriculum chains**. Each level adds a hidden rule on top of the earlier ones, for example
*"segments in review queue B8 are not counted."* Behind every opaque label is a **named grouping published on the
Web**, such as the founding member airlines of Star Alliance. The task shows one example (*Lufthansa*); practice
feedback reveals one more member (*Thai Airways*) and one non-member (*ITA Airways*); the test checks members the
agent never saw (*United Airlines*) and look-alike non-members.

- **Practice can be passed by an exception list**, but only an agent that infers the category handles the test.
- **Probe-certified**: the base model knows the members of each grouping, cannot guess it without feedback, and can
  identify it from the evidence once labels are read as named groupings.
- **Diagnostic**: single-cell accuracy and value-level diagnostics separate under-generalization (unseen members left
  in the count) from over-generalization (non-members removed).
- **Extensible**: the CLR-Synth pipeline builds and certifies chains from a new data domain.

## Benchmark at a glance

<p align="center">
  <img src="assets/composition.png" width="85%" alt="Composition of CLR-Bench">
</p>

| | |
|---|---|
| Chains | 20 (two per domain) |
| Domains | travel audit, pharmacy review, web security, system logs, sponsorship, chemical imports, raw materials, port inspections, scholarships, travel grants |
| Levels per chain | 4 (rules accumulate) |
| Hidden rules / practice tasks / test tasks | 80 / 80 / 80 |
| Hidden classes | intergovernmental memberships, standards, airline alliances, stock indices, sports clubs, ... |
| Methods evaluated | ACE, GEPA, Dynamic Cheatsheet, Training-Free GRPO, EvoSkill, ReasoningBank |
| References | frozen agent, raw practice history, + lesson |

## Main results

<p align="center">
  <img src="assets/main_levels.png" width="100%" alt="Test accuracy per level">
</p>

Average test accuracy (%, levels 1-4, 20 chains). *Self*: learning from feedback alone. *+ lesson*: a fixed text in the
update step that states the named-grouping convention without naming any class.

| Method | GPT-6-Luna self | GPT-6-Luna + lesson | GPT-6-Sol self | GPT-6-Sol + lesson |
|---|---:|---:|---:|---:|
| Frozen agent | 47.8 | - | 32.5 | - |
| History (raw practice) | 52.3 | 63.5 | 70.3 | 83.8 |
| ACE | 52.5 | 67.0 | 78.3 | 81.3 |
| Dynamic Cheatsheet | 52.8 | **68.3** | **78.5** | **84.0** |
| GEPA | 49.5 | 66.0 | 58.8 | 64.8 |
| Training-Free GRPO | 48.0 | 49.5 | 35.8 | 31.2 |
| EvoSkill | 46.0 | 42.0 | 52.3 | 70.5 |
| ReasoningBank | 33.5 | 30.0 | 24.8 | 20.8 |

**Findings.**
1. With GPT-6-Luna, the methods barely learn: the best gain at most 5 points over the frozen agent and exclude only
   6-12% of the unseen members, fewer than the raw history (20%). The lesson lifts them by 14.5-16.5 points.
2. Their states record corrections as exceptions: the revealed member appears in 75-98% of the final states, the
   class name almost never.
3. Learning grows with the base model: with GPT-6-Sol, ACE and Dynamic Cheatsheet learn from feedback alone (78%)
   and surpass the raw history.

<p align="center">
  <img src="assets/state_content.png" width="95%" alt="What the state records">
</p>

## Quick start

```bash
pip install -r requirements.txt
python data/unpack_chains.py TR1                     # unpack one chain (or all: no argument)
cd data/chains/TR1
python score_k1_v3.py --version 0 --program L1=controls/reference_L1.py --diagnostics
```

## Repository layout

```
data/            the 20 certified chains used in the paper
  CHAINS.tsv       chain -> dataset, course id, build config, seed, pipeline commit, classes
  PROVENANCE.md    how the final builds were identified; contents of a chain directory
  unpack_chains.py unpack payload.tar.gz files and verify them against MANIFEST.sha256
  chains/<chain>/  CHAIN.json, CONCEPTS.json, prompts/, TRAPS/, controls/, scorer, payload.tar.gz, run_kit/
pipeline/        CLR-Synth (python -m clrsynth): lint, candidates, probes, certification, build, check, verify
  inputs/          per-domain inputs (dataset.py, scenario, universes, lists, salience, chain configs, sources)
  inputs_alt/      inputs of the MN2 and UN2 builds (see data/PROVENANCE.md)
  tools/           frozen calibration, dry run, rebuild_chain.sh (rebuild a released chain and check its manifest)
  tests/           offline tests with a fake endpoint
harness/         evaluation harness
  runtime/{self,hint,test}/  practice harness (feedback alone / +lesson) and test harness: evaluator, feedback,
                   solver loop, transport, local task service (sdk/)
  run_dir/         per-run drivers: stage A (practice), replay plan, stage B (test), scoring, frozen agent, references
  setup_run.py     create the run directory of one chain
  run_condition.sh run a queue of (mode, method) pairs on one chain, end to end
  gateway.py       local gateway to an OpenAI-compatible endpoint (model, reasoning effort, retries, audit)
  summarize.py     aggregate scores over chains (accuracy per level, single cells, inc_u, exc)
  variants.py      update-text variants (lesson parts under a neutral heading, convention at level 1 only, class names)
methods/         adapters for ACE, GEPA, EvoSkill, Dynamic Cheatsheet, ReasoningBank, Training-Free GRPO and the
                 method-free references; UPSTREAM.md, fetch_upstream.sh
prompts/         lesson and its parts, GEPA notes, class-name oracle texts
paper_figures/   plotting and table scripts with the data files they read
```

## Requirements

Python 3.12 (`pip install -r requirements.txt`). Scoring and chain building need only PyYAML. Running methods needs
the upstream ACE, GEPA and EvoSkill code (`methods/fetch_upstream.sh`) and an OpenAI-compatible chat-completions
endpoint for the base model; the paper used GPT-6-Luna and GPT-6-Sol with high reasoning effort. The harness runs
every candidate program in a Docker container without network (`python:3.12-slim`; `docker pull python:3.12-slim`).

## Data

```bash
python data/unpack_chains.py            # all chains; or: python data/unpack_chains.py TR1 UN2
```

The paper uses levels 1-4 and instance version 0 of every chain.

## Build chains

All pipeline commands run from `pipeline/`. Probes call the evaluated model through:

```bash
export CLRSYNTH_ENDPOINT=https://api.example.com/v1   # OpenAI-compatible base URL
export CLRSYNTH_MODEL=gpt-6-luna CLRSYNTH_REASONING=high
export CLRSYNTH_API_KEY_CMD='cat ~/.secrets/key'      # or CLRSYNTH_API_KEY; the key is kept in memory only
cd pipeline
python -m clrsynth lint TR                            # input checks
python -m clrsynth screen inputs/TR/chains/TR1.yaml       # Known probe on every candidate list (run before make-chain)
python -m clrsynth make-chain inputs/TR/chains/TR1.yaml   # slots -> candidates -> probes -> build -> check -> verify-repro
python tools/frozen.py out/TR/TR1                         # frozen-agent calibration on the three versions
```

The paper's four probes map to the code as follows: Known is `clrsynth screen`, and Hidden, Learnable and Solvable
are `P0`, `P1` and `P1H` in `pipeline/clrsynth/probe.py`, run by `make-chain` in the context of the full chain.

`make-chain` is resumable (pinned slots are kept in `out/<dataset>/<chain>/STATE.json`). The SY domain needs the
Synthea sample: `tar -xzf inputs/SY/sources/synthea.tar.gz -C inputs/SY/sources`. Raw source snapshots (`raw/`) are
not shipped; `inputs/<domain>/sources/FETCH.md` documents how each was fetched, and the derived universes, lists and
salience files are included, so chains build without them.

To check that the released chains are reproducible without any model call (rebuild from the pinned slots and compare
every built and input file with the chain's manifest):

```bash
pipeline/tools/rebuild_chain.sh TR1 /tmp/clr_rebuild
```

## Run a method on a chain

```bash
methods/fetch_upstream.sh                                   # ACE, GEPA, EvoSkill into methods/upstream/
export CLRBENCH_API_BASE=https://api.example.com/v1 CLRBENCH_API_KEY=...
python harness/gateway.py --model gpt-6-luna --reasoning high --port 42802 --base-path /CLR &
python data/unpack_chains.py TR1
harness/run_condition.sh TR1 runs/luna "[('self','ace'),('hint','ace'),('self','hist')]" \
    --gateway-url http://localhost:42802/CLR --model gpt-6-luna
```

`mode` is `self` (learning from feedback alone) or `hint` (+lesson: `prompts/lesson.txt` appended to every update
input). Methods: `ace`, `gepa`, `evoskill`, `dc` (Dynamic Cheatsheet), `rb` (ReasoningBank), `tfgrpo` (Training-Free
GRPO); method-free references: `hist` (raw practice history), `histhint` (history + lesson), `histconv` and `histproc`
(history + one part of the lesson), `nameoracle` (class-name oracle); see `methods/README.md`. The frozen agent runs
with `runs/luna/TR1/run_frozen.sh 1 2 3 4`. Other settings:

* `CLRBENCH_GEPA_NOTE=neutral|explicit|none` selects the GEPA format note (default `neutral`, as in the main results).
* Rewarded practice: `CLR_BUNDLE=bundle_k1_v0_rg` (applied to stage A only by `run_condition.sh`).
* Update-text variants: `CLR_VARIANT=lessn|convn|procn|namem|convl1` with the pairs `('hint','ace')` and
  `('hint','dc')` (whole lesson, convention, or procedure under the neutral heading "UPDATE NOTE:"; class names;
  convention at level 1 only). See `harness/variants.py`.
* Other base models: pass `--model` to `run_condition.sh` and the gateway, for example `gpt-6-sol`.

A run directory follows the layout of the paper's runs: stage A writes per-level states to
`runs_nc100_<mode>_v0/rep1/<method>/<course>/L<k>/STATE.json`, stage B replays each state on the test task into
`runs_nc100_test/<mode>/<method>/L<k>/`, and `score_all.py` writes `SCORES_ALL.json`.

## Score

Every chain ships its scorer. To score programs directly:

```bash
cd data/chains/TR1
python score_k1_v3.py --version 0 --program L1=controls/reference_L1.py --program L2=my_L2.py --diagnostics
```

It prints the score per level (passed cells / 5), each cell's result and, with `--diagnostics`, the value-level
diagnostics. To aggregate runs over chains:

```bash
python harness/summarize.py runs/luna                       # accuracy, per level, single cells, inc_u, exc
```

## Regenerate figures and tables

```bash
cd paper_figures
for f in figures/make_*.py; do python "$f"; done            # PDFs into figures/, LaTeX tables into sections/
python figures/build_main_figure.py && sh figures/make_main_figure.sh   # overview figure (headless Chrome, pdfcrop)
```

The scripts read `paper_figures/data/*.json`, the aggregated results of the paper's runs.

## Citation

```bibtex
@article{qiu2026clrbench,
  title  = {More Rules, Longer Lists? Benchmarking Self-Evolving Agents on a Hidden-Rule Curriculum},
  author = {Qiu, Chenjie and Xu, Boyan and Shi, Shaobin and Chen, Bingfeng and Cai, Ruichu and Luo, Dongsheng},
  year   = {2026},
  note   = {arXiv link coming soon}
}
```

## License

To be decided; see `LICENSE`.
