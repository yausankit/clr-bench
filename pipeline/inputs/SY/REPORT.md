# REPORT — SY: health-plan pharmacy review (Synthea synthetic records)

Business: a health plan's utilisation-review unit totals, per patient, the records its desk must
process — every medication fill, diagnosis and procedure counts 1; practice = largest patient, test =
sum over all patients. Answer format JSON, `solve(data) -> int`.

## Universes
- `medicine`: 107 values; attr:route=oral:55/injectable:35/?:14/inhaled:4/topical:4
- `condition`: 176 values; attr:semantic_tag=other:84/finding:44/disorder:43/situation:4/person:1; attr:system=?:121/Pathological conditions:19/Respiratory:10/Nervous:7/Nutritional and metabolic:7/Musculoskeletal:7/Skin:7/Cardiovascular:6/Infections:6/Digestive:3/Otorhinolaryngologic:3/Congenital:2/Immune:2/Neoplasms:2/Endocrine:1/Hemic and lymphatic:1/Chemically induced:1
- `procedure`: 165 values; attr:semantic_tag=other:96/procedure:64/regime/therapy:4/physical object:1; attr:system=Diagnosis:73/?:47/Investigative techniques:47/Surgical procedures:31/Therapeutics:25/Anesthesia and analgesia:1/Dentistry:1
- Medicine values are RxNorm ingredients (combo = "A / B"), route from the Synthea dose form;
  conditions/procedures are SNOMED codes with the Synthea description as `entity`; the condition
  system and procedure system attributes come from the MeSH C/E tree of the mapped descriptor.

## Lists
Table: `id members/official salience source`; source A=ATC/DDD, D/C/E=MeSH tree section,
PA=MeSH pharmacological action, S=SNOMED CT is-a expansion. Salience = pageviews 2025-10..2026-09.
- `medicine`: 35 lists (A 7, D 20, PA 8)
  atc_b01 5/62 11k A; atc_c01 5/65 10k A; atc_j01 8/83 0 A; atc_l01 9/37 18k A; atc_n02 5/30 233k A; atc_n06 5/70 16k A; atc_s01 9/106 190k A
  mesh_d_d02_033_alcohols 5/177 110k D; mesh_d_d02_065_amides 6/267 76k D; mesh_d_d02_092_amines 9/350 130k D
  mesh_d_d02_455_426_559_389_benzene_derivatives 5/348 377k D; mesh_d_d02_455_426_559_847_polycyclic_aromatic_hydrocarbons 6/119 77k D
  mesh_d_d02_455_426_559_hydrocarbons_aromatic 11/468 77k D; mesh_d_d02_455_426_hydrocarbons_cyclic 14/572 16k D
  mesh_d_d02_455_hydrocarbons 15/797 173k D; mesh_d_d02_886_sulfur_compounds 8/442 8k D; mesh_d_d03_132_alkaloids 7/159 159k D
  mesh_d_d03_383_129_azoles 5/225 18k D; mesh_d_d03_383_621_piperidines 5/59 82k D; mesh_d_d03_383_heterocyclic_compounds_1_ring 20/786 64k D
  mesh_d_d03_633_100_heterocyclic_compounds_2_ring 16/605 64k D; mesh_d_d03_633_heterocyclic_compounds_fused_ring 21/799 64k D
  mesh_d_d04_210_500_steroids 9/268 182k D; mesh_d_d04_615_polycyclic_aromatic_hydrocarbons 9/149 77k D; mesh_d_d04_polycyclic_compounds 20/564 4k D
  mesh_d_d09_carbohydrates 7/679 269k D; mesh_d_d12_644_peptides 5/806 370k D; mesh_pa_adjuvants_anesthesia 5/19 17k PA
  mesh_pa_analgesics_opioid 7/40 257k PA; mesh_pa_anti_arrhythmia_agents 5/54 34k PA; mesh_pa_anti_bacterial_agents 9/209 11k PA
  mesh_pa_antihypertensive_agents 5/111 28k PA; mesh_pa_antineoplastic_agents_hormonal 5/26 6k PA; mesh_pa_narcotics 6/32 109k PA
  mesh_pa_vasodilator_agents 5/96 75k PA
- `condition`: 52 lists (C 12, S 40)
  mesh_c_c01_infections 6/785 187k C; mesh_c_c05_musculoskeletal_diseases 7/381 18k C; mesh_c_c08_381_lung_diseases 6/111 0 C
  mesh_c_c08_respiratory_tract_diseases 10/254 51k C; mesh_c_c10_nervous_system_diseases 6/921 5k C; mesh_c_c14_cardiovascular_diseases 6/470 220k C
  mesh_c_c18_452_metabolic_diseases 7/307 33k C; mesh_c_c23_550_pathologic_processes 7/459 177k C
  mesh_c_c23_888_592_neurologic_manifestations 5/242 150k C; mesh_c_c23_888_852_signs_and_symptoms_respiratory 5/30 0 C
  mesh_c_c23_888_signs_and_symptoms 13/414 0 C; mesh_c_c23_pathological_conditions_signs_and_symptoms 19/963 0 C; snomed_106098005 7/2613 74k S
  snomed_106147001 11/1769 0 S; snomed_111273006 5/252 0 S; snomed_118185001 5/1255 103k S; snomed_118240005 12/2347 0 S; snomed_118436003 7/1109 0 S
  snomed_125605004 8/2464 67k S; snomed_125610000 6/2058 0 S; snomed_126643005 6/1652 0 S; snomed_1269101009 6/1170 7k S; snomed_128126004 5/839 19k S
  snomed_128272009 7/1948 242k S; snomed_128524007 5/502 0 S; snomed_129134004 8/332 59k S; snomed_129681004 5/397 24k S; snomed_19829001 5/1300 0 S
  snomed_198609003 5/1171 25k S; snomed_22253000 10/1270 144k S; snomed_248982007 7/2217 0 S; snomed_250132005 5/636 3k S; snomed_2704003 11/2314 25k S
  snomed_271860004 8/2685 3k S; snomed_275498002 5/525 36k S; snomed_27624003 9/2702 96k S; snomed_279001004 9/1042 34k S; snomed_300855001 6/2448 9k S
  snomed_301186004 10/1869 59k S; snomed_301282008 5/467 223 S; snomed_312225001 6/2314 0 S; snomed_312608009 5/771 15k S; snomed_363059001 5/974 25k S
  snomed_363176004 7/2590 0 S; snomed_365523001 5/428 80k S; snomed_414029004 5/2328 161k S; snomed_699697007 10/1455 0 S
  snomed_700010002 7/2423 43k S; snomed_74627003 5/449 226k S; snomed_82271004 5/2571 35k S; snomed_82423001 6/190 70k S; snomed_844005 6/2570 0 S
- `procedure`: 18 lists (E 11, S 7)
  mesh_e_e01_370_225_500_cytological_techniques 5/89 0 E; mesh_e_e01_370_225_clinical_laboratory_techniques 15/244 23k E
  mesh_e_e01_370_350_diagnostic_imaging 7/191 76k E; mesh_e_e01_370_388_diagnostic_techniques_surgical 5/47 0 E
  mesh_e_e01_370_diagnostic_techniques_and_procedures 34/746 0 E; mesh_e_e02_therapeutics 19/736 25k E
  mesh_e_e04_502_minimally_invasive_surgical_procedures 5/58 4k E; mesh_e_e04_520_obstetric_surgical_procedures 5/25 109k E
  mesh_e_e04_surgical_procedures_operative 24/579 0 E; mesh_e_e05_478_immunologic_techniques 5/94 0 E; mesh_e_e05_investigative_techniques 22/1211 7k E
  snomed_118669005 10/2098 71k S; snomed_14734007 7/1409 37k S; snomed_16310003 5/1275 74k S; snomed_225365006 6/1271 0 S; snomed_445536008 5/670 22k S
  snomed_5880005 8/2926 40k S; snomed_86273004 5/1559 64k S

## Same-partition check (§8.2)
- 0 lists equal a class of a single-valued attribute (lint notes empty).
- 6 condition lists equal a class of the multi-valued `attr:system`: mesh_c_c01_infections, mesh_c_c05_musculoskeletal_diseases, mesh_c_c08_respiratory_tract_diseases, mesh_c_c14_cardiovascular_diseases, mesh_c_c18_452_metabolic_diseases, mesh_c_c23_pathological_conditions_signs_and_symptoms
  They stay in `lists/condition.yaml` as competitors but never C; so do snomed_844005 and snomed_445536008 (no competitor).
- C-capable lists per field: medicine 35, condition 45, procedure 17.

## Scenario card
- 97 rule templates (35/45/17 per field), one per C-capable list; each names one list and gives
  >=2 distinct plausible ids. Rule text names the record type that carries the field and matches
  `total()`'s per-record exclusion ("A medication whose ingredient belongs to X...", "...diagnosis
  whose code...", "...procedure whose code..."). One confirmation per template: SCENARIO_CHECK.tsv.
- Label nouns: review tag, audit lane, desk slot, queue tag, batch lane, ledger mark, routing lane, intake mark.

## dataset.py
- Entities = patients; 45 sampled per world from 681 eligible patients (>=3 records of every kind in
  2015-2021). Records are filtered to 2015-01-01..2021-12-31 before eligibility and rendering.
- Example world (seed 20266089, step "report"): 45 patients, positions medications.ingredient 838,
  conditions.code 600, procedures.code 2105 (min per patient 3/4/4); totals sum 3543, max 360, min 18.
- `total()` counts every in-period row and skips excluded (field, position); `reference()` uses only
  rendered rows (no file reads), `render()` emits patients/medications/conditions/procedures JSON.

## Chains
- `chains/SY1.yaml` .. `SY5.yaml`: seeds 20266089..20266093, period 2015-2021, snapshot 2026-10-16,
  5 slots (medicine 2, condition 2, procedure 1 — procedure has 165 values but one slot is enough),
  probe criterion soft, all 99 templates listed on every chain.

## Self-checks
- Lint: `clrsynth lint SY --inputs-root ../inputs` -> `lint OK: SY` (re-run after every build).
- Dry run: `tools/dryrun.py ../inputs SY`: 5/5 slots had candidates (8 reported each) and all
  instances built; `build_instances 105.2s, diagnostics 165`, no PlacementError.
- Reproducibility: build_universes.py + build_lists.py + build_salience.py run twice; every generated
  file compared byte-for-byte with `cmp` (see PROGRESS.md for the run log).
- SPOTCHECK.tsv: 1050 rows = 105 lists x (5 members + 5 non-members);
  verify_spotcheck.py re-opened each cited raw line/entry for 1285 claims: 0 errors, 0 count issues.
- check_dataset.py: determinism, >=30 entities, >=3 positions per field per entity, set_value visible,
  total int and decreasing, reference == total, isolated import -- all pass.

## Known issues / deviations
- The Synthea nov-2021 CSV spans 1919-2021; the chains declare 2015-2021, so universes and worlds are
  filtered to that period (before filtering: 127/202/170 values).
- `raw/crosswalk/procedure.tsv` is a derived SNOMED->MeSH table (column `basis`), not a download, and is
  documented in `sources/FETCH.md`; every MeSH-based procedure member is still checked in SPOTCHECK.tsv.
- `changes`/`disputed` are empty: the classifications are point-in-time snapshots (MeSH 2025, ATC current,
  SNOMED 20250201) and no historical membership list was available.
- `attr:system` is `?` for 47/165 procedures and 121/176 conditions.  Lists with <5 in-universe members
  after the period filter were dropped; salience = first related Wikipedia hit, else 0 (see FETCH.md).
Reproduce: `cd inputs/SY && python3 build_universes.py && python3 build_lists.py && python3 build_salience.py && python3 ../../work/make_scenario.py`, then lint from `code/` (see `sources/FETCH.md`).
