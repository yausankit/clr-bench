# Provenance of the released chains

## Which builds are final

Every chain-construction run wrote its chains to its own build directory (`FIN_<domain>_<attempt>/run/out/<domain>/`),
and several domains were built more than once. The evaluation runs of the paper did not pick builds by name: they read
a single mapping file, `baselines_final/CHAINS.tsv`, that lists for each of the 20 chain names the build directory it
was evaluated on. Every evaluation condition reported in the paper (explicit-feedback main runs, references, variants,
rewarded practice, other base models) copied its per-chain run directory from that mapping. We therefore took exactly
the 20 directories listed there. Two further checks confirm the choice:

* the `bundle_k1_v0/` task files of every chain are byte-identical (SHA-256 over all files) to the copies inside the
  evaluation run directories of the paper's main runs;
* every file shipped here passes the chain's own `MANIFEST.sha256`, written by the pipeline at build time
  (`python data/unpack_chains.py`), and rebuilding the chain from its pinned slots reproduces all built files
  byte for byte (`pipeline/tools/rebuild_chain.sh <chain>`).

`data/CHAINS.tsv` records the mapping: chain name, dataset, course id inside the files, the build id and chain config
under `pipeline/`, the seed, the build run, and the pipeline commit it was built with.

## Notes on individual chains

* **UN2** is the chain built as `UN1` (course id `CLR_UN1`, seed 20266101) by a separate UN build that used an earlier
  input layout (nationality / sponsor / university fields). Its inputs are in `pipeline/inputs_alt/UN/`. It shares the
  `nasdaq_100` and `g20` classes with UN1. The task files keep the original course id `CLR_UN1`; the directory name
  `UN2` is the chain's name in the paper.
* **MN2** comes from an MN build whose `lists/country.yaml` predates a later membership correction; none of its classes
  (G7, SkyTeam, Yttrium group, G20) uses a corrected list. Its inputs are in `pipeline/inputs_alt/MN/`.
* **TR1, TR2, WS1, WS2** were built with pipeline commit `0718590`; the other 16 chains with `b6568da`, which only adds
  one lint rule (Roman numerals in list names). The released `pipeline/` is `b6568da`.

## Levels and versions

The pipeline builds five levels (L1-L5) and three instance versions (v0, v1, v2) per chain, and certifies the frozen
agent on all three. The paper evaluates levels 1-4 on version 0 only. This release ships all five levels of version 0
(L5 is unused by the paper) and omits versions 1 and 2, which `pipeline/` regenerates deterministically
(`python -m clrsynth build`).

## What each chain directory holds

| File | Content |
|---|---|
| `CHAIN.json` | the five slots: trap field, opaque label, hidden class `C` and its name, revealed example `A`, practice member `P_M`, practice non-member `N_p`, test non-members `N_t`, competing lists, check results |
| `CONCEPTS.json` | the hidden classes with their members |
| `STATE.json` | probe history of the construction run (Hidden/Learnable/Solvable verdicts per round) and the pinned slots |
| `ZERO_CHECK.json` | the build checks (H1-H6 and others) |
| `MANIFEST.sha256` | hashes of every built file and every input file |
| `TRAPS/`, `prompts/` | trap definitions and the rendered practice/test prompts per level |
| `controls/` | reference programs per level and two control programs (`L-all`, `L-lit`) used by the checks |
| `frozen/FROZEN.json` | frozen-agent calibration scores per version and level |
| `score_k1_v3.py`, `harness_k1_test/` | the scorer (5 scored cells per level, value-level diagnostics) |
| `payload.tar.gz` | `bundle_k1_v0/` (practice and test task files: public view, hidden inputs, expected answers), `test_k1_v0.json`, `practice_views_v0.json`, `diagnostics.json`, `bundle_k1_v0_rg/` (rewarded-practice files) |
| `run_kit/` | per-chain files of the evaluation run directory (config template with seeds, assembly audit, frozen replay plan, explicit-feedback value table, rewarded-practice build report) |
