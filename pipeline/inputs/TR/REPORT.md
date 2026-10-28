# TR input report

Snapshot 2026-10-16; seed 20266093; five chains use seeds 20266093..20266097. ANSWER_FORMAT=json, practice=max, test=sum; entity = department.

## Universes
- airline: 1147 values; attrs: country, region; no identifier attributes.
- airport: 6675 values; attrs: country, region; no identifier attributes.
- currency: 155 values; attrs: region; no identifier attributes.

## Lists (members / official_count / salience ; source)
Source keys: wdP355/P749 = Wikidata subsidiary statements; wp:<article> = article membership section; wdP463+cty = country membership joined to value's country; iso+wdP463 = ISO 4217 table joined to issuing-country membership; iso4217 = ISO 4217 table row.

### airline (30 lists)
- lufthansa_group(12/19/68079;wdP355/P749); iag_group(7/10/236588;wdP355/P749); air_france_klm_group(5/7/27811;wdP355/P749); qantas_group(8/8/455159;wdP355/P749)
- latam_airlines_group(7/8/82335;wdP355/P749); ana_group(5/7/398734;wdP355/P749); jal_group(7/8/320185;wdP355/P749); hna_group(9/11/30410;wdP355/P749)
- air_china_group(7/10/357626;wdP355/P749); tui_group(6/6/162796;wdP355/P749); dhl_aviation_group(5/5/388648;wdP355/P749); asl_aviation_group(5/5/13198;wdP355/P749)
- avianca_group(8/17/33386;wdP355/P749); lion_air_group(5/6/116554;wdP355/P749); star_alliance_members(25/26/633554;wp:Star Alliance); oneworld_members(15/15/471950;wp:Oneworld)
- skyteam_members(15/19/434984;wp:SkyTeam); a4a_members(9/9/15267;wp:Airlines for America); aapa_members(16/16/1412;wp:Association of Asia Pacific Airlines); aaco_members(26/28/242;wp:Arab Air Carriers Organization)
- afraa_members(34/38/3355;wp:African Airlines Association); a4e_members(37/37/3639;wp:Airlines for Europe); star_alliance_founding(5/6/633554;wp:Star Alliance); oneworld_founding(5/6/471950;wp:Oneworld)
- eu_airlines(198/198/2455194;wdP463+cty); asean_airlines(95/95/946505;wdP463+cty); gcc_airlines(29/29/767528;wdP463+cty); arab_league_airlines(93/93/386459;wdP463+cty)
- oas_airlines(266/266/218695;wdP463+cty); flag_carrier_airlines(115/125/289484;wp:Flag carrier)

### airport (27 lists)
- schengen_airports(573/573/1141441;wdP463+cty); eu_airports(499/499/2455194;wp:European Union); eea_airports(581/581/322322;wp:European Economic Area); arab_league_airports(225/225/386459;wdP463+cty)
- asean_airports(378/378/946505;wp:ASEAN); gcc_airports(44/44/767528;wp:Gulf Cooperation Council); nordic_airports(181/181/85440;wdP463+cty); baltic_airports(10/10/17836;wdP463+cty)
- caricom_airports(112/112/123057;wdP463+cty); opec_airports(250/250/891426;wp:OPEC); visegrad_airports(30/30/1614;wp:Visegrad Group); benelux_airports(12/12/217337;wp:Benelux)
- eaeu_airports(11/11/160582;wp:Eurasian Economic Union); sadc_airports(335/335/69472;wdP463+cty); turkic_airports(26/26/209108;wdP463+cty); sco_airports(418/418/346826;wdP463+cty)
- ecowas_airports(152/152/213051;wdP463+cty); cbss_airports(229/229/12662;wdP463+cty); cplp_airports(329/329/84216;wdP463+cty); bsec_airports(48/48/26541;wdP463+cty)
- eccas_airports(205/205/22222;wdP463+cty); amu_airports(82/82/33254;wdP463+cty); sacu_airports(110/110/24570;wdP463+cty); efta_airports(89/89/153397;wp:European Free Trade Association)
- coe_airports(673/673/261776;wdP463+cty); oic_airports(807/807/209910;wdP463+cty); african_union_airports(814/814/382745;wdP463+cty)

### currency (18 lists)
- sdr_basket_currencies(5/5/68657;iso+wdP463); eu_non_euro_currencies(6/7/2455194;iso+wdP463); gcc_currencies(6/6/767528;iso+wdP463); asean_currencies(10/10/946505;iso+wdP463)
- g20_currencies(17/17/746828;iso+wdP463); brics_currencies(10/10/1491124;iso+wdP463); arab_league_currencies(21/22/386459;iso+wdP463); commonwealth_currencies(43/46/1422475;iso+wdP463)
- oic_currencies(42/45/209910;iso+wdP463); african_union_currencies(41/42/382745;iso+wdP463); oas_currencies(28/29/218695;iso+wdP463); apec_currencies(20/20/215960;iso+wdP463)
- dollar_named_currencies(22/22/365805;iso4217); peso_named_currencies(8/8/86229;iso4217); dinar_named_currencies(8/8/86757;iso4217); franc_named_currencies(10/10/48264;iso4217)
- pound_named_currencies(9/9/55313;iso4217); rupee_named_currencies(6/6/73401;iso4217)

## Partition check
- 0 lists equal any single-valued attribute class in any field (checked attr:country and attr:region for airline/airport, attr:region for currency).
- Lists differing from every attribute class: airline 30/30, airport 27/27, currency 18/18.

## Spotcheck
- SPOTCHECK.tsv: 750 rows = 75 lists x (5 members + 5 non-members); NO EVIDENCE/PRESENT rows: 0.
- Every row cites a raw file with a line number (wiki/json) or an ISO 4217 table row; evidence was located by work/make_spotcheck.py, not written by hand.

## Scenario templates
- All 12 templates name a field, a plausible list set (all ids exist in that field), and the rule text excludes the same record type as the field: True.
- airline_partner_group | segments.airline | 14 plausible | rule: From this level on, segments in {label} are not counted.
- airline_alliance | segments.airline | 5 plausible | rule: From this level on, segments in {label} are not counted.
- airline_industry_body | segments.airline | 5 plausible | rule: From this level on, segments in {label} are not counted.
- airline_state_carrier | segments.airline | 3 plausible | rule: From this level on, segments in {label} are not counted.
- airline_regional_bloc | segments.airline | 5 plausible | rule: From this level on, segments in {label} are not counted.
- airport_european_bloc | segments.arrival_airport | 12 plausible | rule: From this level on, segments in {label} are not counted.
- airport_arab_african_bloc | segments.arrival_airport | 8 plausible | rule: From this level on, segments in {label} are not counted.
- airport_asia_americas_bloc | segments.arrival_airport | 7 plausible | rule: From this level on, segments in {label} are not counted.
- currency_name_family | claims.currency | 6 plausible | rule: From this level on, claims in {label} are not counted.
- currency_union | claims.currency | 5 plausible | rule: From this level on, claims in {label} are not counted.
- currency_political_bloc | claims.currency | 7 plausible | rule: From this level on, claims in {label} are not counted.

## dataset.py
- entities: 36 departments; employees 180; claims 360; segments 540.
- slots per entity: segments.airline >= 12, segments.arrival_airport >= 12, claims.currency >= 10
- sample totals: min 12, max 18 (before any replacement).
- base_world is deterministic per (seed, step); reference() reads only render() data; check_dataset.py: ALL OK.

## Chains
- TR1: seed 20266093; 5 slots; fields segments.airline, segments.arrival_airport, claims.currency; probe soft.
- TR2: seed 20266094; 5 slots; fields segments.airline, segments.arrival_airport, claims.currency; probe soft.
- TR3: seed 20266095; 5 slots; fields segments.airline, segments.arrival_airport, claims.currency; probe soft.
- TR4: seed 20266096; 5 slots; fields segments.airline, segments.arrival_airport, claims.currency; probe soft.
- TR5: seed 20266097; 5 slots; fields segments.airline, segments.arrival_airport, claims.currency; probe soft.

## Checks
- `clrsynth lint TR`: lint OK: TR.
- `tools/dryrun.py inputs TR`: each slot 8 candidates; 5 instances built; 165 diagnostics; no placement error.
- Reproducibility: the three build scripts run twice; `cmp` on universes/*, lists/*, salience/*.tsv and salience/raw/* reports no differences.

## Known issues / judgement calls
- Wikidata P463 is stale for the EU (contains the United Kingdom, misses Romania) and adds Australia to ASEAN; membership for EU/EEA/ASEAN/GCC/OPEC/Visegrad/Benelux/EAEU/EFTA is curated from the organisation articles/official member sets. The EFTA/EEA and EU sets are documented in build_lists.py; the OPEC set follows the 11 current members in the article (UAE absent).
- Airport and currency "bloc" lists are country-membership x value-country joins, not stand-alone official airport/currency lists; official_count is the derived in-universe count.
- Group lists come from Wikidata P355/P749; a few source statements are historical (e.g. Condor for Lufthansa). They remain in the list with the source statement; candidate selection passed P1H and the five chains need only 21 airline candidates, which is satisfied (27).
- Pageview salience uses the 12 monthly buckets 2025-10-01..2026-09-30 and only ranks lists; zero-salience lists are kept.
