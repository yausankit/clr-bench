# SP sports sponsorship settlement dataset
**Universes:** `club` — 151 values; `attr:country` has 36 distinct values and 0 `?`; 151 descriptions (max 96 chars).
`co_sponsor` — 692 values; `attr:country` has 32 distinct values and 0 `?`; 692 descriptions (max 134 chars).
`market_country` — 249 values; `attr:region` has 6 distinct values and 2 `?`; 249 descriptions (max 89 chars).
**Same-partition check:** no list equals a single-valued attribute partition; 12/12 club, 12/12 co-sponsor and 10/10 country lists are distinct.
**Spotcheck:** 340/340 PASS (5 members + 5 non-members for each of 34 lists); every row cites a parsed table/list cell or Wikidata binding in `raw/` and is programmatically checked by `build_spotcheck.py`.
**Lists** (`id | members | official_count | salience | source`):
| ucl_winners | 24 | 24 | 2868927 | WP:List_of_European_Cup_and_UEFA_Champions_League_finals |
| uel_winners | 31 | 31 | 368555 | WP:List_of_UEFA_Cup_and_Europa_League_finals |
| cup_winners_cup_winners | 32 | 32 | 72997 | WP:List_of_UEFA_Cup_Winners'_Cup_finals |
| club_world_cup_winners | 12 | 12 | 166290 | WP:List_of_FIFA_Club_World_Cup_finals |
| super_league_founders | 12 | 12 | 252664 | WP:European_Super_League |
| g14_members | 14 | 14 | 16098 | WP:G-14 |
| club_world_cup_2025_participants | 32 | 32 | 834544 | WP:2025_FIFA_Club_World_Cup |
| ucl_2024_25_league_phase | 36 | 36 | 919359 | WP:2024–25_UEFA_Champions_League |
| premier_league_1992_93 | 21 | 22 | 197583 | WP:1992–93_FA_Premier_League |
| laliga_1929 | 10 | 10 | 15744 | WP:1929_La_Liga |
| bundesliga_1963_64 | 16 | 16 | 13484 | WP:1963–64_Bundesliga |
| seriea_1929_30 | 18 | 18 | 8804 | WP:1929–30_Serie_A |
| cac_40 | 40 | 40 | 158140 | WP:CAC_40 |
| ibex_35 | 35 | 35 | 82519 | WP:IBEX_35 |
| ftse_mib | 40 | 40 | 64853 | WP:FTSE_MIB |
| dax | 40 | 40 | 292182 | WP:DAX |
| aex | 25 | 25 | 61365 | WP:AEX_index |
| bel_20 | 20 | 20 | 23473 | WP:BEL_20 |
| euro_stoxx_50 | 50 | 50 | 139169 | WP:EURO_STOXX_50 |
| dow_jones | 30 | 30 | 1175407 | WP:Dow_Jones_Industrial_Average |
| sp_100 | 100 | 100 | 233543 | WP:S&P_100 |
| nasdaq_100 | 100 | 100 | 1966641 | WP:Nasdaq-100 |
| sp_500 | 155 | 500 | 8918578 | WP:List_of_S&P_500_companies |
| stoxx_europe_600 | 461 | 461 | 70340 | WP:STOXX_Europe_600 |
| eu_members | 27 | 27 | 678362 | WD:Q458 |
| nato_members | 32 | 32 | 2129009 | WD:Q7184 |
| g7_members | 7 | 7 | 802164 | WD:Q1764511 |
| g20_members | 19 | 21 | 746828 | WD:Q19771 |
| oecd_members | 38 | 38 | 583168 | WD:Q41550 |
| opec_members | 13 | 13 | 891426 | WD:Q7795 |
| asean_members | 10 | 10 | 946505 | WD:Q7768 |
| african_union_members | 54 | 55 | 382745 | WD:Q7159 |
| commonwealth_members | 56 | 56 | 1422475 | WD:Q7785 |
| apec_members | 21 | 21 | 215960 | WD:Q170481 |
**Template consistency** (`id | rule => plausible | result`):
| club_rule_ucl | A club that has won the top European club cup is left out. => ucl_winners,uel_winners,cup_winners_cup_winners | OK |
| club_rule_uel | A club that has won the second-tier European club cup is left out. => uel_winners,cup_winners_cup_winners,ucl_winners | OK |
| club_rule_cwc | A club that has won the former European cup-winners' competition is left out. => cup_winners_cup_winners,uel_winners,ucl_winners | OK |
| club_rule_world | A club that has won the world club championship is left out. => club_world_cup_winners,ucl_winners,club_world_cup_2025_participants | OK |
| club_rule_esl | A club named as a founder of the breakaway European league is left out. => super_league_founders,ucl_winners,g14_members | OK |
| club_rule_g14 | A club in the former G-14 group is left out. => g14_members,super_league_founders,ucl_winners | OK |
| club_rule_cwc25 | A club entered in the 2025 world club championship is left out. => club_world_cup_2025_participants,club_world_cup_winners,ucl_2024_25_league_phase | OK |
| club_rule_ucl25 | A club in the 2024-25 Champions League league phase is left out. => ucl_2024_25_league_phase,club_world_cup_2025_participants,ucl_winners | OK |
| club_rule_pl92 | A club in the first Premier League season is left out. => premier_league_1992_93,laliga_1929,bundesliga_1963_64 | OK |
| club_rule_laliga | A club in the first La Liga season is left out. => laliga_1929,seriea_1929_30,premier_league_1992_93 | OK |
| club_rule_bundesliga | A club in the first Bundesliga season is left out. => bundesliga_1963_64,premier_league_1992_93,seriea_1929_30 | OK |
| club_rule_seriea | A club in the 1929-30 Serie A season is left out. => seriea_1929_30,laliga_1929,bundesliga_1963_64 | OK |
| company_rule_cac | A company in the French large-cap equity index is left out. => cac_40,euro_stoxx_50,stoxx_europe_600 | OK |
| company_rule_ibex | A company in the Spanish large-cap equity index is left out. => ibex_35,euro_stoxx_50,stoxx_europe_600 | OK |
| company_rule_mib | A company in the Italian large-cap equity index is left out. => ftse_mib,euro_stoxx_50,stoxx_europe_600 | OK |
| company_rule_dax | A company in the German large-cap equity index is left out. => dax,euro_stoxx_50,stoxx_europe_600 | OK |
| company_rule_aex | A company in the Dutch large-cap equity index is left out. => aex,euro_stoxx_50,stoxx_europe_600 | OK |
| company_rule_bel | A company in the Belgian large-cap equity index is left out. => bel_20,euro_stoxx_50,stoxx_europe_600 | OK |
| company_rule_euro | A company in the euro-area blue-chip equity index is left out. => euro_stoxx_50,stoxx_europe_600,cac_40 | OK |
| company_rule_dow | A company in the oldest United States industrial equity index is left out. => dow_jones,sp_100,sp_500 | OK |
| company_rule_sp100 | A company in the large United States blue-chip equity index is left out. => sp_100,sp_500,dow_jones | OK |
| company_rule_nasdaq | A company in the technology-heavy United States equity index is left out. => nasdaq_100,sp_500,sp_100 | OK |
| company_rule_sp500 | A company in the broad United States large-cap equity index is left out. => sp_500,sp_100,dow_jones | OK |
| company_rule_stoxx | A company in the broad European blue-chip equity index is left out. => stoxx_europe_600,euro_stoxx_50,dax | OK |
| country_rule_eu | A country that is a European Union member state is left out. => eu_members,nato_members,oecd_members | OK |
| country_rule_nato | A country that is a NATO member state is left out. => nato_members,eu_members,oecd_members | OK |
| country_rule_g7 | A country in the Group of Seven is left out. => g7_members,g20_members,oecd_members | OK |
| country_rule_g20 | A country in the Group of Twenty is left out. => g20_members,g7_members,oecd_members | OK |
| country_rule_oecd | A country in the OECD is left out. => oecd_members,eu_members,g20_members | OK |
| country_rule_opec | A country in OPEC is left out. => opec_members,african_union_members,g20_members | OK |
| country_rule_asean | A country in ASEAN is left out. => asean_members,apec_members,commonwealth_members | OK |
| country_rule_au | A country in the African Union is left out. => african_union_members,commonwealth_members,opec_members | OK |
| country_rule_commonwealth | A country in the Commonwealth of Nations is left out. => commonwealth_members,african_union_members,asean_members | OK |
| country_rule_apec | A country in APEC is left out. => apec_members,asean_members,g20_members | OK |
**Dataset:** 40 sponsor brands, 305 activations for `step=check`; every trap field has 305 positions (7.63 per entity); sample total is 305 and the 7-entity JSON render is 8395 chars. `check_dataset.py` passes all assertions; `dataset.py` performs no file I/O at import or in `reference()`.
**Chains:** `SP1` seed 20266106 and `SP2` seed 20266107; `period={2026,2026}`, `snapshot=2026-10-16`, `slots=5`, `probe=soft`; field order is `club` (12 templates), `co_sponsor` (12), `market_country` (10).
**Validation:** `clrsynth lint SP --inputs-root ../inputs` -> `lint OK: SP`; `clrsynth salience SP` -> 12/12, 12/12 and 10/10 lists matched; `tools/dryrun.py` built all 5 slots and 165 diagnostics; two builds produced 52 byte-identical derived files (`diff -qr` status 0).
**Pre-screen:** `screen_run/out/SP/SCREEN.json`; all three fields clear the required minima.
- `activations.club`: 11/12 lists pass (minimum 6): ucl_winners, uel_winners, cup_winners_cup_winners, club_world_cup_winners, super_league_founders, g14_members, club_world_cup_2025_participants, premier_league_1992_93, laliga_1929, bundesliga_1963_64, seriea_1929_30.
- `activations.co_sponsor`: 7/11 lists pass (minimum 6): aex, cac_40, dax, ftse_mib, bel_20, dow_jones, nasdaq_100.
- `activations.market_country`: 10/10 lists pass (minimum 3): african_union_members, apec_members, asean_members, eu_members, g7_members, nato_members, opec_members, oecd_members, commonwealth_members, g20_members.
**Known issues:** The 51 Wikipedia pages are exact revisions at or before 2026-10-16T23:59:59Z (oldids are in `FETCH.md`); Wikidata/ISO metadata and pageviews were fetched on 2026-10-22, with salience using 12 complete monthly buckets from 2025-10 through 2026-09.
The S&P 500 page has 503 security rows but 500 companies after collapsing Alphabet, Fox and News Corp dual-class rows; the list therefore records 500 companies (155 in-universe + 345 out-of-universe). The STOXX Europe 600 table has 467 data rows: five duplicate title rows collapse to 462 titles and one duplicate Campari QID collapses to 461 distinct companies, which is the recorded `official_count`.
Disputed/recent changes are explicit where applicable: NATO marks Finland (2023-04-04) and Sweden (2024-03-07) as joins; historical fixed lists have no membership changes. No pipeline code was modified.
**Delivery checklist**
- [x] universes follow section 1 (no identifier attributes); every universe has `*.desc.tsv`.
- [x] lists follow section 2 (no attribute values; ≥2 per field; ≥5 members; counts reconcile).
- [x] salience is merged into `lists/` and reproducible from `salience/raw/`.
- [x] scenario card obeys slot limits; every rule agrees with its `plausible` lists.
- [x] `dataset.py` follows section 5 and `check_dataset.py` passes.
- [x] both chain configurations follow section 6.
- [x] two-run reproduction is byte-identical (`cmp`/`diff -qr`).
- [x] all seven section-8 checks pass, including the required pre-screen counts.
- [x] this report is complete and copied to `../REPORT.md`.
