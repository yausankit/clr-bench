# TR source snapshot (fetch log)

Snapshot date: 2026-10-16.  All files below were fetched on 2026-10-19 (UTC) through the
sandbox's HTTP proxy; no credentials are stored.  Raw payloads are kept verbatim in `../raw/`.

## Wikidata (SPARQL endpoint)

Endpoint: `https://query.wikidata.org/sparql?format=json&query=...` with
`Accept: application/sparql-results+json` and `User-Agent: clrsynth-input-build/1.0 (dataset TR)`.
One query at a time, 3 s apart.  Variables returned by each snapshot are its `head.vars`.

- `airlines.json`: airlines with an IATA code (`wdt:P229`) and an instance/subclass path to
  airline (`wd:Q46970`), not dissolved (`FILTER NOT EXISTS { ?item wdt:P576 ?dissolved }`),
  with `wdt:P17` country and optional `wdt:P30` continent.  Columns: item, itemLabel, iata,
  countryLabel, continentLabel.
- `airports.json`: airports (`wdt:P31/wdt:P279* wd:Q1248784`) with `wdt:P238` IATA code and
  `wdt:P17` country, optional continent.  Columns: item, itemLabel, iata, countryLabel,
  continentLabel.
- `country_relations.json`: sovereign states (`wdt:P31/wdt:P279* wd:Q6256`) with `wdt:P30`
  continent, `wdt:P36` capital, `wdt:P463` membership.  Columns: country, countryLabel,
  continentLabel, capital, capitalLabel, memberOf, memberOfLabel.
- `airline_relations.json`: active IATA airlines with `wdt:P749` parent, `wdt:P463` membership
  or `wdt:P113` hub.  Columns: item, parent, parentLabel, memberOf, memberOfLabel, hub,
  hubLabel.
- `airport_relations.json`: airports with `wdt:P131`/`wdt:P1376` city or `wdt:P127` operator.
  Columns: item, city, cityLabel, operator, operatorLabel.
- `airport_serves.json`: airports with `wdt:P931` served place.  Columns: item, place,
  placeLabel.
- `airline_sitelinks.json`: English Wikipedia sitelinks for the airline items.  Columns: item,
  article.
- `group_qids.json`: candidate airline holding groups and their English labels.  Columns:
  group, groupLabel, name.
- `group_subsidiaries.json`: `wdt:P355`/`wdt:P749` subsidiary links of those groups.  Columns:
  group, groupLabel, sub, subLabel.

## English Wikipedia (MediaWiki API)

Endpoint: `https://en.wikipedia.org/w/api.php?action=parse&page=<title>&prop=wikitext&
format=json&formatversion=2&redirects=1`.  One page at a time, >= 6 s apart; 429 responses were
retried with exponential backoff (60 s, 120 s, ... capped at 10 min).

Page titles are recorded in `../../work/pages3.txt`, `pages4.txt` and `pages5.txt`; the raw
responses are `raw/wiki/<slug>.json` and the plain wikitext extract is `raw/wiki/<slug>.wiki`
(produced by `work/unpack_wiki.py` from the JSON).  The pages supply the membership sections used
by `build_lists.py` (airline alliances/associations, airline groups, airport-operator pages,
`Flag carrier`, `ISO 4217`, and the organisation articles for the regional airport/currency lists).

- `iso4217_page.json`: `action=parse` wikitext of `ISO 4217`.  `build_universes.py` reads table 1
  (active codes, currency names, locations, decimal places).

## Wikimedia pageviews REST API

Endpoint (per list concept, English Wikipedia):
`https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/
<Title_with_underscores>/monthly/20251001/20260930`

The twelve monthly buckets ending before the snapshot are summed by `build_salience.py`.  Raw
responses are `raw/pageviews/<slug>.json`.  Requests were sent one at a time with >= 6 s spacing
and 429 backoff.  Titles without an article are recorded with `pageviews_12m = 0` in
`salience/<U>.tsv`; no list is dropped for low salience.

## Rebuild

```
python3 build_universes.py        # raw/*.json + raw/iso4217_page.json -> universes/*.tsv
python3 build_salience.py         # raw/pageviews/*.json + lists/*.yaml -> salience/*.tsv
python3 build_lists.py            # raw/* + lists wiki snapshots + salience -> lists/*.yaml
```

`build_lists.py` imports `build_universes.py`, so the three commands above are the complete
pipeline.  Run them twice and compare with `cmp` (see `../REPORT.md`).
