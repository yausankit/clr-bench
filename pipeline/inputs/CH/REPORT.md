# CH dataset report
Snapshot 2026-10-16; generated 2026-10-22. URLs and retrieval details are in `sources/FETCH.md`.
## Universes
- `chemical.tsv`: 654 values; attributes `category` (pesticide, industrial solvent, refrigerant, heavy-metal compound, chemical agent, industrial chemical).
- `country.tsv`: 195 values; attributes `region`, `subregion`, `continent`.
- `carrier.tsv`: 239 values; attributes `country`, `region`. All three universes have complete `*.desc.tsv` files and no identifier attribute.
## Lists

| id | members | official_count | salience | source key |
|---|---:|---:|---:|---|
| stockholm_annex_a | 33 | 35 | 1476 | Stockholm 2025 PDF Annex A |
| stockholm_annex_c | 6 | 6 | 28368 | Stockholm 2025 PDF Annex C |
| rotterdam_pesticides | 37 | 38 | 7005 | Rotterdam 2025 PDF Annex III pesticides |
| rotterdam_industrial | 14 | 15 | 7005 | Rotterdam 2025 PDF Annex III industrial |
| rotterdam_annex_iii | 51 | 53 | 7005 | Rotterdam 2025 PDF Annex III all |
| opcw_schedule_1 | 17 | 33 | 59528 | OPCW Schedule 1 page |
| opcw_schedule_2 | 9 | 13 | 59528 | OPCW Schedule 2 page |
| opcw_schedule_3 | 17 | 17 | 59528 | OPCW Schedule 3 page |
| opcw_all_schedules | 43 | 63 | 59528 | OPCW Schedules 1-3 union |
| montreal_all_controlled_substances | 78 | 79 | 108853 | Montreal 2020 handbook named annex rows |
| iarc_group_1 | 57 | 64 | 11223 | IARC `loc_app` Group 1 |
| iarc_group_2a | 76 | 80 | 3533 | IARC `loc_app` Group 2A |
| iarc_group_2b | 283 | 291 | 3968 | IARC `loc_app` Group 2B |
| iarc_group_3 | 25 | 438 | 997 | IARC `loc_app` Group 3 |
| wfd_priority | 41 | 45 | 6917 | EU WFD 2013/39 Annex I |
| wfd_hazardous | 18 | 21 | 6917 | EU WFD Annex I hazardous rows |
| montreal_annex_a_group_i | 5 | 5 | 108853 | Montreal handbook Annex A Group I |
| stockholm_all_pops | 36 | 36 | 28368 | Stockholm Annexes A and C |
| eu | 27 | 27 | 2427987 | EU member-state index |
| eu_1958 | 6 | 6 | 27130 | EU country cards marked since 1958 |
| nato | 30 | 32 | 2087661 | NATO member page |
| commonwealth | 55 | 55 | 1410547 | Commonwealth member page; Wikidata |
| g7 | 7 | 7 | 808964 | Wikidata Q1764511 `P710` |
| gcc | 6 | 6 | 760907 | Wikidata Q217172 `P527` |
| asean | 10 | 12 | 933074 | Wikidata current membership |
| arab_league | 20 | 22 | 379074 | Wikidata current membership |
| mtcr | 35 | 35 | 42351 | MTCR partner headings |
| nsg | 48 | 48 | 27313 | Wikidata current membership |
| australia_group | 40 | 40 | 13483 | Wikidata current membership |
| wassenaar | 42 | 42 | 27588 | Wassenaar participating-state flags |
| schengen | 27 | 29 | 1116871 | European Commission Schengen list |
| opec | 12 | 13 | 880838 | Wikidata current membership |
| star_alliance | 26 | 26 | 630113 | Star Alliance member keywords |
| oneworld | 15 | 16 | 467145 | oneworld member cards |
| skyteam | 17 | 18 | 430553 | SkyTeam member list |
| alta_full | 24 | 24 | 0 | ALTA full-member tab |
| alta_associate | 11 | 11 | 0 | ALTA associate-member tab |
| a4a | 10 | 10 | 15028 | Airlines for America logos |
| a4e | 10 | 16 | 3587 | Airlines for Europe logo labels |

Every row satisfies `members + disputed + out_of_universe = official_count`; lint verifies this. Salience is the 12-month English Wikipedia pageview total used only for ordering.

## Self-checks

- Partition check: 0 of 18 chemical lists, 0 of 14 country lists, and 0 of 7 carrier lists equal a single-valued attribute class.
- `SPOTCHECK.tsv`: 39 lists × (5 members + 5 non-members) = 390 rows; every member cites a raw file plus line/table/page, every non-member records the scanned source and absence, `unverified=0`.
- Dataset check: `ANSWER_FORMAT=json`; `reference()` reads only rendered data and agrees with `total()`.
- Dryrun: all five slots have candidates and all instances build; 165 diagnostics, exit 0.

## Scenario templates

| template | field | consistency confirmation |
|---|---|---|
| chem_pops | lines.substance | pollutant/prior-consent wording matches the Stockholm and Rotterdam annex `plausible` sets |
| chem_weapons | lines.substance | chemical-weapons schedule wording matches OPCW Schedules 1/2/3 and their union |
| chem_hazard | lines.substance | cancer-hazard wording matches IARC Groups 1/2A/2B/3 |
| chem_water | lines.substance | water-pollution wording matches WFD priority and hazardous lists |
| chem_ozone | lines.substance | international chemical-control wording matches Montreal A-I, Montreal named substances, and OPCW Schedule 3 |
| country_europe | declarations.exporter_country | European common-market/travel wording matches EU, EU-1958, and Schengen |
| country_control | declarations.exporter_country | security/export-control wording matches NATO, MTCR, NSG, Australia Group, and Wassenaar |
| country_regional | declarations.exporter_country | regional/intergovernmental wording matches Commonwealth, G7, GCC, ASEAN, Arab League, and OPEC |
| carrier_alliance | shipments.air_carrier | global-alliance wording matches Star Alliance, oneworld, and SkyTeam |
| carrier_americas | shipments.air_carrier | Americas airline-association wording matches ALTA full/associate and A4A |
| carrier_europe | shipments.air_carrier | national/regional airline-association wording matches A4A and A4E |

All 11 template rows were checked against their `plausible` sets. Label nouns (`review batch`, `clearance stamp`, `intake folder`) name no data object, field, class, or rank.

## Dataset and chains

- `dataset.py`: 40 importers; 3 declarations per importer; one shipment per declaration; 1-3 lines per shipment. Positions: substance 235, exporter country 120, air carrier 120; seven-importer sample is 5,044 characters.
- `CH1.yaml`/`CH2.yaml`: seeds 20266102/20266103; period 2025-2026; snapshot 2026-10-16; five slots; soft probes; field order substance (2), country (2), carrier (1); all 11 templates listed.

## Verification

- `clrsynth lint CH --inputs-root ../inputs`: `lint OK: CH`.
- `check_dataset.py`: `ok: 40 entities; positions=lines.substance:235, declarations.exporter_country:120, shipments.air_carrier:120; sample_chars=5044`.
- `tools/dryrun.py ../inputs CH`: five slots built, 165 diagnostics, exit 0; rejected lists are not needed because every slot has candidates.
- Reproduction: two full runs of `build_universes.py`, `build_lists.py`, `build_salience.py`, `build_spotcheck.py`, and `clrsynth salience` produced the same 52 generated files; every pair passed `cmp`.

## Prescreen

- `lines.substance`: 6/14 passing lists (required 6): `iarc_group_1`, `opcw_schedule_1`, `opcw_schedule_3`, `rotterdam_pesticides`, `stockholm_all_pops`, `stockholm_annex_a`.
- `declarations.exporter_country`: 8/12 passing (required 6): `commonwealth`, `eu`, `eu_1958`, `g7`, `gcc`, `nato`, `opec`, `schengen`.
- `shipments.air_carrier`: 4/6 passing (required 3): `a4a`, `oneworld`, `skyteam`, `star_alliance`. All soft-score means are ≥0.8 in `screen_run/out/CH/SCREEN.json`.

## Known issues

- Pageviews returned raw monthly JSON for 37 of 39 concepts; the two ALTA titles returned HTTP 404 and retain `pageviews_12m=0`, `note=raw response missing`.
- The first G7 Wikidata attempt used the wrong entity (Q132610, Siocon); it is archived but unused. G7/GCC use Q1764511 `P710` and Q217172 `P527`.
- `gcc_member_states.html` is a 404, `mercosur_states_parties.html` is a Cloudflare block, `eu_drug_precursors.html` is empty, and the exploratory `wikidata_g7_gcc_oecd.json` is unused.
