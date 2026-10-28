# MN source snapshots

Retrieval date: 2026-10-22 (UTC). Network: an HTTP proxy (`$HTTPS_PROXY`) for Wikimedia,
Wikidata, and IATA; GitHub/GitHub Raw used the direct connection. MediaWiki/SPARQL requests were
issued serially with at least 2 seconds between calls; pageview requests used 0.6 seconds. HTTP 429
and transient 5xx responses were retried with exponential backoff from 60 seconds to 600 seconds.
No credentials or API keys were used or stored.

## Base universes

- Country values and attributes: `raw/countries.json`, downloaded from
  `https://raw.githubusercontent.com/mledoze/countries/master/countries.json` (direct GitHub Raw).
  The 194 current ISO alpha-2 entries provide the country code, English name, aliases, region, and
  subregion. `build_universes.py` converts the two region fields into `attr:region` and
  `attr:subregion`.
- Material values and attributes: `raw/pubchem_periodictable.json`, downloaded from
  `https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON`. Its 118 element rows provide the
  value, symbol, atomic number, group block, and standard state.
- Additional periodic-table group/period classifications: `raw/periodic_table_groups.json`, from
  `https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json`
  (direct GitHub Raw). Group and period numbers are joined to PubChem names by atomic number.

## Country and carrier membership

- `raw/wikidata/country_membership.sparql` is the exact SPARQL query sent to the Wikidata Query
  Service (`https://query.wikidata.org/sparql`); `raw/wikidata/country_membership.json` is the raw
  JSON result. It covers the Wikidata item IDs used for the country-group lists and filters member
  statements by snapshot date 2026-10-16.
- Page-backed country lists and material classifications use the MediaWiki Action API:
  `https://en.wikipedia.org/w/api.php?action=parse&prop=text&format=json&formatversion=2&page=<PAGE>`.
  Responses are stored one file per page under `raw/wiki/<PAGE_WITH_UNDERSCORES>.json`. The files used
  by the builders include `Eurozone`, `Gulf_Cooperation_Council`, `Schengen_Area`,
  `Rare-earth_element`, `Lanthanide`, `Inner_transition_metal`, `Platinum_group`, `Noble_metal`,
  `Precious_metal`, `Metals_of_antiquity`, `Period_5_element`, and `Period_6_element`.
- Airline association, alliance, rating, and corporate-group memberships come from the corresponding
  MediaWiki pages saved under `raw/wiki/` (`Airlines_for_America`, `Airlines_for_Europe`,
  `Arab_Air_Carriers_Organization2`, `Association_of_Asia_Pacific_Airlines`,
  `African_Airlines_Association`, `Oneworld`, `SkyTeam`, `Star_Alliance`, `Value_Alliance`,
  `Skytrax`, `International_Airlines_Group`, `Lufthansa_Group`, and `Air_France-KLM`).
- Airline names, QIDs, aliases, and countries come from Wikidata: the query is saved as
  `raw/wikidata/airline_entities.sparql`, its result as `raw/wikidata/airline_entities.json`, display
  titles as `raw/wikidata/airline_title_qids.json`, and MediaWiki page properties as
  `raw/wikidata/airline_pageprops.json`.
- IATA member airlines: `raw/iata/airline-list-page-01.html` through
  `raw/iata/airline-list-page-40.html`, from
  `https://www.iata.org/en/about/members/airline-list/?page=<N>` (page 1 has no query suffix).
  The first 39 pages contain 381 member rows; page 40 is the empty terminal page. Parsed rows are in
  `raw/iata/members.json`. `raw/iata_members.html` is the initial page-1 snapshot.

## Salience

- Each `salience/raw/<concept_id>.json` is the raw response from
  `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/<TITLE>/monthly/20251001/20260930`.
  Titles are listed in `mn_sources.py` and copied into `salience/<universe>.tsv` with the summed
  12-month pageview count. There is one snapshot per current concept ID; two extra retained snapshots
  (`cptpp_members`, `rcep_members`) belong to exploratory lists that were not accepted.

## Reproduction

From the agent directory, after restoring the snapshots above at the same paths, run
`./rebuild.sh`, then `./venv/bin/python build_spotcheck.py`. `verify_repro.sh` performs two clean
rebuilds and compares every generated universe, list, and salience file byte-for-byte.

`raw/failures/restcountries.json` is a retained 301 response from
`https://restcountries.com/v3.1/all?fields=name,cca2,region,subregion,landlocked,independent,unMember`.
It was not used; the mledoze country snapshot above supplied the same fields successfully.

## 2026-10-16 membership roster rebuild

The 13 country-group lists formerly sourced from Wikidata membership properties were replaced using the English Wikipedia member tables as the primary source. The original revision HTML, revision IDs, and cutoff timestamps are saved in `raw/membership/wikipedia/`; the alternate member-table snapshots are under `raw/membership/secondary/wikipedia/`. All MediaWiki API requests were serialized with at least 2.5 seconds between calls. The agent-root `tools/build_membership_rosters.py` extracts the roster values from these saved files and `raw/countries.json`; it does not query a live service.

Second-source rosters were compared row by row from the saved source material: African Union official Member States, Australian DFAT's APEC economy table, the Commonwealth official country pages, EU official country profiles (both pagination pages), the Canadian government G7 overview, NATO's official member-country page, OECD's official 38-member page, and the OIC official 57-member cards. Separate English Wikipedia member-state tables matched for the Arab League, ASEAN, BRICS, OIC, and G20 (2025 Johannesburg summit). The OPEC official member-country page returned a CAPTCHA through the available route; independent BBC and Khaleej Times reports confirm Angola's 2024 departure and the UAE's withdrawal effective 2026-05-01, respectively. The dated OPEC article table shows the current 11-country roster and lists both departures in its former-member table.

Membership interpretation: Timor-Leste's ASEAN accession (2025-10-26), Indonesia's BRICS accession (2025-01-06), and Sweden's NATO accession (2024-03-07) remain in `disputed` under the three-year rule. Syria's Arab League readmission (2023-05-07) predates the 2023-10-16 cutoff, so it is counted as a member. Angola and the UAE are excluded from OPEC members and recorded as exits in `changes`. Western Sahara/SADR, Hong Kong, Chinese Taipei, Palestine, and the African Union/European Union G20 seats remain represented in `out_of_universe` where applicable.
