# GR source snapshots

Snapshot date: **2026-10-16**. The collection ran in `agents/DS_GR_f1/`; the raw response bytes are retained under `inputs/GR/raw/` and pageview JSON under `inputs/GR/salience/raw/`. `SHA256SUMS` records their digests.

## Entity universes

- `raw/iso3166-1_pycountry.json`: ISO 3166-1 codes from the `iso-codes` public GitHub repository (`data/iso_3166-1.json`).
- `raw/countries_restcountries.json`: REST Countries country metadata.
- `raw/country_continents_wikidata.json`: Wikidata SPARQL country-code and continent-label snapshot.
- `raw/airlines_active_described.json`, `raw/universities_wikidata.json`, `raw/universities_described.json`: Wikidata SPARQL entity and English description snapshots.
- `raw/airline_affiliations_wikidata.json`, `raw/university_affiliations_wikidata.json`, `raw/target_org_memberships.json`, `raw/target_group_entities_described.json`, and `raw/org_label_resolution.json`: Wikidata affiliation, member-country, organization-resolution, and description snapshots. The exact query forms and retrieval code are in `../../../scripts/fetch_*.py`.
- `raw/roster_airline_names.tsv` and `raw/roster_airlines_described.json`: Wikidata crosswalk for airline names found on direct roster pages.
- `raw/airline_search_entities.json`: sequential English entity-search responses for roster-only airline labels that lacked useful universe descriptions (`scripts/search_airline_entities.py`, at least 2.1 seconds between API requests). `raw/airline_search_country_enrichment.json` is the P17 country lookup for unique exact-label results and a small explicit brand-label crosswalk (`scripts/fetch_airline_country_enrichment.py`). The builder uses exact unique results or the recorded explicit crosswalk only when the saved result describes an airline; ambiguous searches remain unused. `raw/airline_enrichment_wikidata.json` is an exploratory exact-label SPARQL response and is retained as evidence but not used in the build. Forty-eight roster-only airline rows remain without a reliable entity match and retain unknown country plus a generic fallback description rather than an inferred fact.

## Direct organization rosters

- Country organization snapshots: `raw/country_sources/*.html`, fetched from the corresponding English Wikipedia pages for the European Union, Schengen Area, NATO, OECD, Commonwealth, African Union, Arab League, OPEC, ASEAN, Council of Europe, Mercosur, UN, G20, Gulf Cooperation Council, and Pacific Islands Forum membership. The G7 membership table is in `group_of_seven.html`; the three additional pages were fetched sequentially from `scripts/fetch_country_extra_sources.py`.
- Airline alliance and association pages: `raw/airline_sources/star_alliance.html`, `skyteam.html`, `oneworld.html`, `a4a_home.html`, `alta_members_v2.html`, `aaco_members_current.html`, `afraa_current_members.html`, and all `iata_pages/page_*.html` are snapshots of the named public organization directories. The IATA directory was saved page by page.
- Airline corporate and alliance evidence: `wiki_lufthansa_group.html`, `wiki_iag.html`, `star_alliance_article.html`, `air_france_klm.html`, `qantas_group.html`, `a380_orders_deliveries.html`, and `b787_operators.html` are English Wikipedia page snapshots; the latter two delivery tables are parsed for current active carriers only. The B787 table's Vistara entry is out of universe after its 2024 merger. The five-star Skytrax roster is the marked list in `skytrax_five_star.html`. Asiana Airlines and Vistara are omitted from the current airline universe after their 2024 mergers; any captured roster entries are recorded out of universe. `aapa_pages_search.json` is the public WordPress REST response from AAPA's `who-we-are` page; its member-airline image grid links to the 18 member airline sites.
- University roster pages: `raw/university_sources/*.html` were fetched from the organizations' public member pages; filenames identify the source organization.

Retrieval scripts in `agents/DS_GR_f1/scripts/` preserve the individual URLs and parsing steps. A few exploratory endpoints returned 403/404 responses; those attempts remain in `raw/` for provenance and are not treated as membership evidence.

## Salience

`salience/raw/<list_id>.json` stores the English Wikipedia REST pageviews response for each list concept. The monthly endpoint spans **2025-10-16 through 2026-10-15**. `../fetch_pageviews.py` performs sequential requests with the configured GR proxy; `build_salience.py` derives the 12-month totals in `salience/<universe>.tsv`.

## Rebuild

From the agent directory, run `venv/bin/python inputs/GR/build_data.py`, then `venv/bin/python inputs/GR/build_salience.py`, then run `venv/bin/python -m clrsynth salience GR --inputs-root ../inputs` from `code/`. All generated universe, list, salience, and spot-check tables are reproducible from the retained raw responses.
