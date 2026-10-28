# UN source snapshots and retrieval

All snapshots below were acquired for this dataset in the isolated `DS_UN_f6` workspace. The universe snapshot date is 2026-10-16; web pages were saved on 2026-10-22. Files remain byte-for-byte under `../raw/`. `SHA256SUMS` covers every retained raw source and pageview response.

## University universe

- `../raw/wikidata-universities*.json`: Wikidata Query Service JSON (`https://query.wikidata.org/sparql`, `Accept: application/sparql-results+json`), selecting English-labelled entities whose instance/subclass path reaches university (`wd:Q3918`), with country and sitelink count. The main query is preserved in the acquisition record as: `SELECT DISTINCT ?item ?itemLabel ?countryLabel ?qid WHERE { ?item wdt:P31/wdt:P279* wd:Q3918; wdt:P17 ?country; wikibase:sitelinks ?sl. BIND(STRAFTER(STR(?item), "entity/") AS ?qid) SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } ORDER BY DESC(?sl) LIMIT 8000`. The supplementary ranked and alphabetic queries use the same properties and label service with different ordering/limits to extend coverage. `wikidata-c9.json` and `wikidata-supplement/Q*.json` record additional entity lookups; `wikidata-search/*.json` records label searches used to resolve official source spellings. Re-run through the Wikidata Query Service/API and preserve the JSON response before running `build_universes.py`.
- `../raw/country-codes.csv`: `https://raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv` (ISO alpha-2 codes, English country names, regions and Wikidata IDs).

## Company universe

- `../raw/sp500.csv`: `https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv`.
- `../raw/nasdaq100-20261016.json`: the public Nasdaq screener endpoint `https://api.nasdaq.com/api/quote/list-type/nasdaq100?limit=100` (captured 2026-10-22; the response contains 101 securities representing 100 companies because Alphabet has two share classes). The security-symbol crosswalk to existing company entities is built from the saved S&P 500, EURO STOXX 50 and STOXX Europe 600 source tables; symbols are not stored as universe attributes.
- `../raw/wiki/EURO_STOXX_50.json` and `STOXX_Europe_600.json`: MediaWiki parse API, `https://en.wikipedia.org/w/api.php?action=parse&page=<title>&prop=text&format=json`; the constituent tables supply headquarters country and sector. `build_universes.py` combines these records with the S&P file and keeps the most specific saved sector/country row.
- `../raw/nasdaq-listed.csv` and `acwi-holdings-20261016.csv` are retained acquisition snapshots; they are not used to construct a trap-field universe or list.
- `../raw/fortune-global500-2026.html`: the public Fortune Global 500 2026 ranking page (`https://fortune.com/ranking/global500/`), captured 2026-10-22. Its JSON-LD `ItemList` has 500 company names and records `dateModified` 2026-07-28. `build_lists.py` maps names to the saved company universe and records the remaining 344 as out of universe; Deutsche Bahn remains out of universe because it is not a listed issuer.
- `../raw/interbrand-best-global-brands-2025.html`: Interbrand's official 2025 Best Global Brands page (`https://interbrand.com/best-global-brands/`), captured 2026-10-22. Its `#__NEXT_DATA__` page payload directly lists the page's ten 2025 top brands; recognized brand names are mapped to their public parent-company entities in the company universe.

## Membership rosters

- Wikipedia membership snapshots are JSON responses from `action=parse&page=<title>&prop=text&format=json` at `https://en.wikipedia.org/w/api.php`. The page title for each list is recorded in its `lists/*.yaml` `source` field. The saved pages include university rosters, country-organization pages, equity index tables and the 2025 G-SIB table. Rerun `build_lists.py` after retrieving those same page titles.
- Official university roster pages saved verbatim under `../raw/official-university/`: Big Ten Academic Alliance (`https://btaa.org/about/member-universities`), Utrecht Network (`https://utrecht-network.org/members/`), Universities Australia (`https://universitiesaustralia.edu.au/universities/`), Go8 (`https://go8.edu.au/about/members`), and U15 Canada (`https://u15.ca/about-us/members/`). They are retained as original HTML responses.
- `../raw/wiki/Public_Ivy.json` contains the table of 30 institutions associated with the 2001 Greene and Greene book edition. The list is labelled with that edition so its membership is not conflated with the distinct 1985 list.
- Country rosters not present as a clean table in the saved page are explicit ISO-code rosters in `build_lists.py`, sourced from the contemporaneous organization page named by each list's `source_page`. Codes are mapped through the saved `country-codes.csv`; announced accessions within three years or otherwise unsettled statuses are recorded under `disputed` and `changes`.
- Erasmus+ eligibility is sourced from the official programme guide page saved as `../raw/erasmus-eligible-countries.html`: `https://erasmus-plus.ec.europa.eu/programme-guide/part-a/eligible-countries`.
- The S&P 500 list is read directly from `../raw/sp500.csv`; other company rosters are read from their saved current constituent tables. `official_count`, `out_of_universe` and disputed values are kept in the list YAML.

## Pageviews

- `../salience/raw/*.json`: Wikimedia REST monthly pageviews, English Wikipedia, all-access/all-agents, 2025-10-01 through 2026-09-30: `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/<encoded-title>/monthly/20251001/20260930`. `fetch_salience.py` skips existing raw files and fetches only missing titles; `build_salience.py` recreates the TSVs, and `clrsynth salience UN --inputs-root inputs` merges the values into the lists.

To verify the retained snapshots from this directory, run `sha256sum -c SHA256SUMS` while in `inputs/UN/`.
