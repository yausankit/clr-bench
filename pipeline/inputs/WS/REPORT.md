# REPORT — WS (Web Security Audit), executor DS_WS_a9

Deliverable: `inputs/WS/` (generated from scratch; no prior-round or other-executor artifacts read).
Snapshot 2026-10-16, chain seeds 20266086–20266090. `clrsynth lint WS` → `lint OK: WS`.

## Universes
| universe | values | attributes | raw source |
|---|---|---|---|
| cwe | 934 | abstraction (Base/Class/Variant/Compound) | MITRE CWE 4.20 XML (2026-04-30), non-Pillar, non-Deprecated |
| tld | 1285 | kind (generic/country-code/infrastructure), continent, country | IANA root zone 2026101900 + IANA root DB + ISO 3166-1 alpha-2 page |
| language | 177 | family (27), script (25) | Wikipedia List of ISO 639-1 codes (Living/Constructed); Glottolog languoid.csv; Wikidata P282 |

No identifier attributes. Every value is a real 2026 value (xn-- IDNs and the retired `su` are excluded from tld).
`universes/*.tsv` are generated only by `build_cwe.py`, `build_tld.py`, `build_language.py` from `raw/`.

## Lists
| universe | lists | usable lists (not equal to a single-valued attribute class) | members | official_count | lists with salience > 0 |
|---|---|---|---|---|---|
| cwe | 56 | 56 | 5–381 | 5–382 | 47 |
| tld | 24 | 24 | 5–56 | 5–56 | 24 |
| language | 21 | 20 | 5–24 | 5–24 | 21 |

Full table (id, members, disputed, out_of_universe, official_count, salience, source): `LISTS.tsv`.
Compacted inventory, `id (members/official_count/salience/source-domain)`:
- cwe (56): cwe1000_284 (183/184/56304/cwe.mitre.org); cwe1000_435 (15/16/0/cwe.mitre.org); cwe1000_664 (381/382/12206/cwe.mitre.org); cwe1000_682 (13/14/0/cwe.mitre.org); cwe1000_691 (84/85/53249/cwe.mitre.org); cwe1000_693 (103/104/0/cwe.mitre.org); cwe1000_697 (21/22/0/cwe.mitre.org); cwe1000_703 (58/59/23350/cwe.mitre.org); cwe1000_707 (144/145/0/cwe.mitre.org); cwe1000_710 (195/196/17333/cwe.mitre.org); owasp2017_a01 (9/9/31/cwe.mitre.org); owasp2017_a02 (9/9/31/cwe.mitre.org); owasp2017_a03 (14/14/31/cwe.mitre.org); owasp2021_a01 (39/40/31/cwe.mitre.org); owasp2021_a02 (30/30/31/cwe.mitre.org); owasp2021_a03 (32/32/31/cwe.mitre.org); owasp2021_a04 (46/46/31/cwe.mitre.org); owasp2021_a05 (26/26/31/cwe.mitre.org); owasp2021_a07 (32/32/31/cwe.mitre.org); owasp2021_a08 (10/10/31/cwe.mitre.org); owasp2025_a01 (39/40/31/cwe.mitre.org); owasp2025_a02 (15/15/31/cwe.mitre.org); owasp2025_a03 (5/5/31/cwe.mitre.org); owasp2025_a04 (32/32/31/cwe.mitre.org); owasp2025_a05 (37/37/31/cwe.mitre.org); owasp2025_a06 (38/39/31/cwe.mitre.org); owasp2025_a07 (36/36/31/cwe.mitre.org); owasp2025_a08 (14/14/31/cwe.mitre.org); owasp2025_a09 (5/5/31/cwe.mitre.org); owasp2025_a10 (23/24/31/cwe.mitre.org); bad_coding_practices (60/60/0/cwe.mitre.org); audit (6/6/72428/cwe.mitre.org); authenticate_actors (28/28/100494/cwe.mitre.org); authorize_actors (59/60/31595/cwe.mitre.org); cross_cutting (8/9/0/cwe.mitre.org); encrypt_data (38/38/144393/cwe.mitre.org); identify_actors (12/12/17239/cwe.mitre.org); limit_access (8/8/56304/cwe.mitre.org); limit_exposure (6/6/0/cwe.mitre.org); manage_user_sessions (6/6/14296/cwe.mitre.org); validate_inputs (39/39/15608/cwe.mitre.org); verify_message_integrity (9/10/57227/cwe.mitre.org); cisq_reliability (32/34/962/cwe.mitre.org); cisq_maintainability (28/28/962/cwe.mitre.org); cisq_security (33/34/962/cwe.mitre.org); cisq_efficiency (15/15/962/cwe.mitre.org); sfp_memory_access (19/19/24445/cwe.mitre.org); sfp_information_leak (92/92/3042/cwe.mitre.org); sfp_tainted_input (135/136/22784/cwe.mitre.org); sfp_authentication (40/40/100494/cwe.mitre.org); sfp_privilege (12/12/36152/cwe.mitre.org); sfp_malware (11/11/245782/cwe.mitre.org); sfp_predictability (15/15/0/cwe.mitre.org); sfp_exposed_data (73/73/80984/cwe.mitre.org); sfp_path_traversal (43/43/261/cwe.mitre.org); sfp_tainted_input_command (85/86/308077/cwe.mitre.org)
- tld (24): eu_member_cctlds (27/27/678362/en.wikipedia.org); schengen_cctlds (29/29/1141441/en.wikipedia.org); eea_cctlds (30/30/322322/en.wikipedia.org); eurozone_cctlds (21/21/516397/en.wikipedia.org); eu_candidate_cctlds (9/9/166670/en.wikipedia.org); nato_cctlds (32/32/2129009/en.wikipedia.org); oecd_cctlds (38/38/583168/en.wikipedia.org); g7_cctlds (8/8/35922/en.wikipedia.org); g20_cctlds (20/21/746828/en.wikipedia.org); commonwealth_cctlds (56/56/1422475/en.wikipedia.org); asean_cctlds (11/11/946505/en.wikipedia.org); gcc_cctlds (6/6/767528/en.wikipedia.org); brics_cctlds (10/10/1491124/en.wikipedia.org); mercosur_cctlds (5/5/429384/en.wikipedia.org); caricom_cctlds (15/15/123057/en.wikipedia.org); african_union_cctlds (54/55/382745/en.wikipedia.org); apec_cctlds (21/21/215960/en.wikipedia.org); pif_cctlds (18/18/43071/en.wikipedia.org); cplp_cctlds (9/9/84216/en.wikipedia.org); arab_league_cctlds (22/22/386459/en.wikipedia.org); saarc_cctlds (8/8/238879/en.wikipedia.org); eaeu_cctlds (5/5/160582/en.wikipedia.org); sica_cctlds (8/8/30645/en.wikipedia.org); five_eyes_cctlds (5/5/538347/en.wikipedia.org)
- language (21): romance_languages (13/14/623532/www.wikidata.org); germanic_languages (15/15/493448/www.wikidata.org); slavic_languages (12/14/275497/www.wikidata.org); celtic_languages (6/6/363141/www.wikidata.org); indo_iranian_languages (18/22/208782/www.wikidata.org); finno_ugric_languages (5/5/114463/www.wikidata.org); semitic_languages (5/5/464842/www.wikidata.org); bantu_languages (22/22/195462/www.wikidata.org); indo_aryan_languages (13/16/373323/www.wikidata.org); west_germanic_languages (8/8/288674/www.wikidata.org); south_slavic_languages (6/8/66934/www.wikidata.org); balto_slavic_languages (14/16/106795/www.wikidata.org); italic_languages (13/15/183631/www.wikidata.org); un_official_languages (6/6/84973/en.wikipedia.org); eu_official_languages (24/24/89530/en.wikipedia.org); au_working_languages (6/6/1501/en.wikipedia.org); nordic_council_languages (5/5/85440/en.wikipedia.org); osce_official_languages (6/6/113133/en.wikipedia.org); india_eighth_schedule (15/22/71971/en.wikipedia.org); south_africa_official (10/12/194478/en.wikipedia.org); zimbabwe_official (8/16/54004/en.wikipedia.org)
Members+disputed+out_of_universe = official_count for every list (lint-enforced). Salience = en-wiki pageviews of the list's article, 2025-10-01..2026-09-30, raw JSON in `salience/raw/`, rebuilt by `build_salience.py`; 9 CWE lists have no matching article (salience 0).

## Same-partition check (guide §8.2)
Lists whose member set equals one class of a single-valued attribute: cwe 0; tld 0; language 1 (`finno_ugric_languages` = attr:family=Uralic). It is kept only as a competing list (lint note) and is not usable as C. Usable lists per field: cwe 56, tld 24, language 20. Candidate lists produced: cwe 55, tld 23, language 18 (slots need 21/21/11).

## SPOTCHECK (guide §8.3)
`SPOTCHECK.tsv`: 1010 rows = 101 lists × (5 members + 5 non-members). Every row cites raw file and line / JSON binding; `build_spotcheck.py` asserts membership while extracting, and an independent `verify_spotcheck.py` re-checked 1376 line references and every negative claim: 0 problems, 0 member-token mismatches. Examples: `eu_member_cctlds de` → ISO page line 934 (DE .de Germany) + EU page line 266 (`| {{flag|Germany}}`); `romance_languages fr` → ISO 639-1 line 970 + Wikidata binding (line 22460 region); `cwe1000_284 CWE-270` → Weakness line 91286 + ChildOf line 91289, chain 270→269→284.

## Scenario templates (guide §8.4)
| template | field | rule (mean) | plausible lists (all same theme) |
|---|---|---|---|
| cwe_category | findings.cwe | named weakness category or cluster of the CWE catalogue | 12 CWE-699 categories + 10 CWE-1000 subtrees + 10 SFP clusters |
| cwe_owasp | findings.cwe | named OWASP Top Ten category | 20 OWASP 2017/2021/2025 categories |
| cwe_cisq | findings.cwe | named CISQ quality measure | 4 CISQ measures |
| tld_organisation | hosts.tld | ccTLDs on the named organisation's published member or candidate roster | all 24 rosters |
| tld_union | hosts.tld | ccTLDs of a member country of the named union/bloc | 17 political/economic unions |
| tld_bloc | hosts.tld | ccTLDs of a member country of the named regional or intergovernmental bloc | 10 regional/intergovernmental blocs |
| lang_family | findings.language | language of the named genealogical family | 13 branch lists |
| lang_institution | findings.language | official/working language of the named institution | 5 institutional regimes |
| lang_schedule | findings.language | language in the named country's official-language schedule | India / South Africa / Zimbabwe schedules |
Every template's `plausible` ids belong to its stated theme, and every candidate C has at least one competitor from the same theme (lint requires >=2 plausible ids). Label nouns (audit lane, reporting band, review line, scan queue, client folio) contain no data word and no banned rank word.

## dataset.py
36 sites → 180 hosts → 270 scans → 360 findings. Positions per entity: cwe/language 8–12 each, tld 4–6; site totals 8–12 (sum 360). `TRAP_FIELDS = [findings.cwe, hosts.tld, findings.language]`; `ENTITY_NOUN = site`. Each rule excludes exactly the record carrying the value: a finding (cwe/language) or a host (tld, together with its scans/findings) — the wording "A host whose tld …" / "hosts in … are not counted" matches `total()`. `set_value` also rewrites a host's hostname suffix. `check_dataset.py`: determinism, entity count, positions, set_value→render, total int/decrease, reference==total — all pass.

## Chains
`chains/WS1.yaml` … `WS5.yaml`, seeds 20266086–20266090, period 2025–2026, snapshot 2026-10-16, `slots: 5`, `probe: {criterion: soft}`. Round-robin allocation: L1 findings.cwe, L2 hosts.tld, L3 findings.language, L4 findings.cwe, L5 hosts.tld.

## Reproducibility (guide §7)
`build_salience.py`, `build_cwe.py`, `build_tld.py`, `build_language.py` run twice: `diff -r` on universes/lists/salience → identical. `clrsynth salience WS` rewrites the three list files byte-identically (idempotent). `build_spotcheck.py` is deterministic.

## Section 8 self-checks
1. `clrsynth lint WS --inputs-root inputs` → `lint OK: WS` (only note: finno_ugric attr-equal, competing only).
2. Same-partition: see above (0 / 0 / 1 attr-equal).
3. `SPOTCHECK.tsv`: 1010 rows, 1376 references re-checked, 0 problems.
4. Templates: 9 rows above, rule and plausible consistent by theme.
5. `check_dataset.py` → OK.
6. `tools/dryrun.py inputs WS` → exit 0, all 5 slots have candidates, `build_instances` OK, 165 diagnostics.

## Decisions and known issues
- `sites.tld` → `hosts.tld`: the guide's Frozen counterexample requires the path's table to be the record the rule excludes; the TLD sits on hosts, so "hosts … are not counted" excludes that host's findings.
- `findings.status` was replaced by `findings.language` under the card's fallback clause ("if fewer than 11 theme-clear lists, switch to another real field with ≥100 values and clear groups"). Status groups are disjoint standard increments (RFC 4918/6585/8297/…) and vendor sets (Cloudflare/nginx/IIS), so a member shares at most a near-universal registry with another list and candidate construction fails; the pilot card also records all five status lists failing. ISO 639-1 + genealogical/institutional groups give 177 values and 20 usable lists with real nesting/overlap.
- `findings.status` and `findings.method` are therefore not chain fields; method (<100 values) was dropped as the card allows.
- Rejected as candidate C (remain competing lists): cwe1000_682 (no member in two competing lists), arab_league_cctlds (H2), celtic_languages (no member in two competing lists), indo_iranian_languages (H2).
- 9 CWE lists have salience 0 (no matching English Wikipedia article; kept, per guide).
- `raw/` keeps every fetched file (IANA, CWE zip, Glottolog zip, Wikidata JSON, 50+ Wikipedia wikitexts, pageview JSON).

## Delivery checklist
- [x] universes conform (natural attributes only)
- [x] lists conform (no attribute-value lists; ≥2 usable per field; ≥5 members; counts reconcile)
- [x] salience merged
- [x] scenario conforms (slot limits, templates consistent)
- [x] dataset.py conforms, check_dataset.py all pass
- [x] chain configs (5)
- [x] two-run build cmp identical
- [x] six self-checks pass
- [x] report written
