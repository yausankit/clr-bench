# CLR-Bench: Curriculum of Latent Rules

CLR-Bench tests whether self-evolving LLM agents learn hidden rules from corrective feedback. Each of its 20 chains
(10 data domains, two chains each) has four levels. Level *k* adds a rule over a field with an opaque label ("segments
in review queue B8 are not counted"); behind each label is a hidden class, a named grouping published on the Web
(for example, founding member airlines of Star Alliance). The task gives one example member and a factual
description of every value, but never names the class.

At every level the agent first **practices**: it writes a program for a related task (largest entity total), may
submit up to three programs, and receives every failing hidden input back as a counterexample that says whether each
changed value belongs to the label like the example. A self-evolving method updates its state after every attempt.
The state then writes the **test** program (sum of entity totals), scored on five hidden cells: clean cells with only
example values, and one single cell per rule with its unseen members and test non-members. Applying each rule only to
its example gives the frozen staircase 80/60/40/20%; gains above it come from generalizing a rule to unseen members
while keeping non-members. Value-level diagnostics report inc_u (unseen members treated as members) and exc
(non-members treated as non-members).

The chains are built by **CLR-Synth**, a pipeline that turns a domain (entities, value universes with descriptions,
and libraries of published lists) into a certified chain. Each candidate class is probed with the evaluated model
in the context of the full chain: Hidden (`P0`: not recovered from the label and example alone), Learnable (`P1`:
practice feedback alone assigns 1/6 to 2/3 of the unseen members) and Solvable (`P1H`: feedback plus the lesson gives
a soft score of at least 0.8); see `pipeline/clrsynth/probe.py` and `makechain.py`. `clrsynth screen` pre-screens
candidate lists before chains are built.

Paper: arXiv link TBD.

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
  experiment_scripts/  the scripts and patches as run for the paper (reference)
methods/         adapters for ACE, GEPA, EvoSkill, Dynamic Cheatsheet, ReasoningBank, Training-Free GRPO and the
                 method-free references; UPSTREAM.md, fetch_upstream.sh
prompts/         lesson and its parts, GEPA notes, class-name oracle texts, web-lookup texts
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

The paper uses levels 1-4 and instance version 0 of every chain. Each chain directory also contains L5, which the
pipeline builds and certifies but the paper does not use.

## Build chains

All pipeline commands run from `pipeline/`. Probes call the evaluated model through:

```bash
export CLRSYNTH_ENDPOINT=https://api.example.com/v1   # OpenAI-compatible base URL
export CLRSYNTH_MODEL=gpt-6-luna CLRSYNTH_REASONING=high
export CLRSYNTH_API_KEY_CMD='cat ~/.secrets/key'      # or CLRSYNTH_API_KEY; the key is kept in memory only
cd pipeline
python -m clrsynth lint TR                            # input checks
python -m clrsynth screen inputs/TR/chains/TR1.yaml       # optional pre-screen of candidate lists (run before make-chain)
python -m clrsynth make-chain inputs/TR/chains/TR1.yaml   # slots -> candidates -> probes -> build -> check -> verify-repro
python tools/frozen.py out/TR/TR1                         # frozen-agent calibration on the three versions
```

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
GRPO); method-free references: `hist` (history), `histhint`, `histconv`, `histproc`, `oracle`, `nameoracle`
(class-name oracle), `nameproc`, `webonly`, `histweb`, `histwebng` (see `methods/README.md`). The frozen agent runs
with `runs/luna/TR1/run_frozen.sh 1 2 3 4`. Other settings:

* `CLRBENCH_GEPA_NOTE=neutral|explicit|none` selects the GEPA format note (default `neutral`, as in the main results).
* Rewarded practice: `CLR_BUNDLE=bundle_k1_v0_rg` (applied to stage A only by `run_condition.sh`).
* Variants of the update text (lesson parts under a neutral heading, convention at level 1 only, class names in the
  update step) are documented by the scripts in `harness/experiment_scripts/`.

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

The scripts read `paper_figures/data/*.json`, the aggregated results of the paper's runs. Some table captions were
edited by hand in the paper, so regenerated captions can differ from the published ones; the numbers are the same.

## License

To be decided; see `LICENSE`.
