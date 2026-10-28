# MN dataset delivery report
## Universes
- country: 194 values; attributes region, subregion; 194 one-line descriptions in `country.desc.tsv`.
- carrier: 452 values; attributes country; 452 one-line descriptions in `carrier.desc.tsv`.
- material: 118 values; attributes category, state; 118 one-line descriptions in `material.desc.tsv`.
## Lists
Legend: usable/official (out=outside universe, disp=disputed); views=12-month pageviews; WD=Wikidata, WP=Wikipedia, PTJ=Periodic-Table-JSON, IATA=IATA roster.
| id | usable / official | views | source |
|---|---:|---:|---|
| african_union_members | 54 / 54 | 382745 | WD Q7159 |
| apec_members | 19 / 21 (2 out) | 215960 | WD Q170481 |
| arab_league_members | 21 / 22 (1 out) | 386459 | WD Q7172 |
| asean_members | 11 / 12 (1 disp) | 946505 | WD Q7768 |
| brics_members | 10 / 10 | 1491124 | WD Q243630 |
| commonwealth_members | 55 / 55 | 1422475 | WD Q7785 |
| eu_members | 26 / 26 | 2455194 | WD Q458 |
| eurozone_members | 20 / 21 (1 disp) | 516397 | WP Eurozone |
| g20_members | 19 / 21 (2 out) | 746828 | WD Q19771 |
| g7_members | 7 / 7 | 802164 | WD Q1764511 |
| gcc_members | 6 / 6 | 767528 | WP Gulf_Cooperation_Council |
| nato_members | 29 / 30 (1 disp) | 2129009 | WD Q7184 |
| oecd_members | 36 / 36 | 329 | WD Q41550 |
| oic_members | 55 / 56 (1 out) | 209910 | WD Q47543 |
| opec_members | 13 / 13 | 7991 | WD Q7795 |
| schengen_members | 27 / 29 (2 disp) | 1141441 | WP Schengen_Area |
| a4a | 10 / 10 | 15267 | WP Airlines_for_America |
| a4e_airlines | 44 / 44 | 3639 | WP Airlines_for_Europe |
| aaco | 35 / 36 (1 disp) | 4900 | WP Arab_Air_Carriers'_Organization |
| aapa | 17 / 17 | 1412 | WP Association_of_Asia_Pacific_Airlines |
| afraa | 46 / 46 | 3355 | WP African_Airlines_Association |
| air_france_klm_airlines | 5 / 5 | 27811 | WP Airlines_for_Europe |
| iag_airlines | 5 / 5 | 236588 | WP International_Airlines_Group |
| iata_airlines | 381 / 381 | 141222 | IATA roster |
| lufthansa_group_airlines | 6 / 6 | 68079 | WP Airlines_for_Europe |
| oneworld | 12 / 16 (4 disp) | 471950 | WP Oneworld |
| skyteam | 18 / 19 (1 disp) | 434984 | WP SkyTeam |
| skytrax_five_star | 10 / 10 | 59462 | WP Skytrax |
| star_alliance | 25 / 26 (1 disp) | 633554 | WP Star_Alliance |
| value_alliance | 5 / 5 | 18250 | WP Value_Alliance |
| boron_group | 6 / 6 | 28370 | PTJ |
| carbon_group | 6 / 6 | 27225 | PTJ |
| cerium_group | 7 / 7 | 547616 | WP Rare-earth_element |
| chalcogens | 6 / 6 | 60610 | PTJ |
| heavy_rare_earths | 10 / 10 | 547616 | WP Rare-earth_element |
| lanthanides | 15 / 15 | 127208 | WP Lanthanide |
| lanthanides_and_actinides | 30 / 30 | 613 | WP Inner_transition_metal |
| light_rare_earths | 5 / 5 | 547616 | WP Rare-earth_element |
| metals_of_antiquity | 7 / 7 | 48685 | WP Metals_of_antiquity |
| noble_metals | 7 / 7 | 79931 | WP Noble_metal |
| period_3_elements | 8 / 8 | 9748 | PTJ |
| period_4_elements | 18 / 18 | 9759 | PTJ |
| period_5_elements | 18 / 18 | 8750 | WP Period_5_element |
| period_6_elements | 32 / 32 | 12207 | WP Period_6_element |
| platinum_group_metals | 6 / 6 | 54429 | WP Platinum_group |
| pnictogens | 6 / 6 | 49507 | PTJ |
| precious_metals | 8 / 8 | 112117 | WP Precious_metal |
| rare_earth_elements | 17 / 17 | 547616 | WP Rare-earth_element |
| yttrium_group | 10 / 10 | 547616 | WP Rare-earth_element |
## Partition, spotcheck, and templates
Single-attribute partitions: `african_union_members` equals `attr:region=Africa`; `lanthanides` equals `attr:category=lanthanide`. Both remain competing lists but do not count; non-partition counts are country 15/16, carrier 14/14, material 18/19.
SPOTCHECK: 490 rows = 49 lists x (5 members + 5 non-members); `build_spotcheck.py` verified every row against a concrete `raw/` locator with 0 unresolved or mismatched values.
| template | field | effect | plausible lists | rule summary |
|---|---|---|---:|---|
| origin_intergovernmental_group | origin_country | exclude_record | 11 | A purchase lot whose origin country belongs to the named intergovernmental or economic association on the audit note is not counted. |
| origin_political_cooperation_group | origin_country | exclude_record | 10 | A purchase lot whose origin country belongs to the named political, security or regional cooperation association on the compliance note is not counted. |
| origin_producer_group | origin_country | exclude_record | 4 | A purchase lot whose origin country belongs to the named commodity-producer or regional country association on the commodity note is not counted. |
| carrier_alliance | carrier | exclude_record | 4 | A purchase lot whose carrier belongs to the named airline alliance on the logistics note is not counted. |
| carrier_association | carrier | exclude_record | 6 | A purchase lot whose carrier belongs to the named airline industry association on the logistics note is not counted. |
| carrier_rating_or_owner | carrier | exclude_record | 4 | A purchase lot whose carrier is named in the airline rating or corporate airline group cited by the logistics note is not counted. |
| material_element_group | material | exclude_record | 6 | A purchase lot whose material belongs to the named scientific grouping of related elements on the materials note is not counted. |
| material_metal_group | material | exclude_record | 4 | A purchase lot whose material belongs to the named technical or historical group of metals on the materials note is not counted. |
| material_periodic_group | material | exclude_record | 13 | A purchase lot whose material belongs to the named periodic-table classification on the materials note is not counted. |
Rule/plausible consistency: all 9 templates were checked one by one; every plausible id exists in that field and each rule wording covers exactly the named class family (9/9 consistent).
## Dataset and chains
`dataset.py`: 36 factories, 72 purchase orders, 252 lots; 252 positions for each of `lots.origin_country`, `lots.carrier`, and `lots.material`; 7-entity render 6,011 chars; sample F001/F002/F003 totals 7/9/7; `ANSWER_FORMAT=json`.
Chains: `MN1` seed 20266105 and `MN2` seed 20266106; period 2025-01-01..2026-10-16; snapshot 2026-10-16; field order origin_country(2 slots), carrier(2), material(1); slots=5; probe=soft.
## Checks
Lint: `lint OK: MN`; notes only: `african_union_members equals attr:region=Africa (kept only as a competing list)` and `lanthanides equals attr:category=lanthanide (kept only as a competing list)`.
`check_dataset.py`: `check_dataset OK: entities=36, lots=252`.
Dryrun: `build_instances 6.9s, diagnostics 165`; every slot had candidates and all instances built.
Pre-screen: country 11/14 candidates pass (need 10), carrier 10/13 (need 10), material 6/12 (need 5), all three thresholds met.
## Known issues
`raw/failures/restcountries.json` is a retained HTTP 301 failure; it was not used, and the mledoze country snapshot supplied country/region/subregion data.
The screen population omits attribute-equal or structurally non-overlapping lists (for example ASEAN, lanthanides, chalcogens); this is why screened totals are below full list totals. All deliverables remain above the required pass counts.
Exploratory source pages and two unused pageview snapshots are retained under `raw/` for provenance and are covered by `sources/SHA256SUMS`; build scripts do not consume them.
## Delivery checklist
- [x] Universes follow section 1 (no identifier attributes), and every universe has a description file.
- [x] Lists follow section 2 (no attribute-value lists, at least two per field, at least five members, counts reconcile).
- [x] Salience is merged into all three universes.
- [x] Scenario card follows section 4 (slot limits; templates and plausibles are consistent).
- [x] dataset.py follows section 5, and check_dataset.py passes completely.
- [x] Two chain configurations follow section 6.
- [x] Two-pass reproduction cmp/sha256 checks are byte-identical.
- [x] All seven section 8 self-checks pass, including pre-screen.
- [x] Report is complete.
