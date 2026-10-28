# LG source snapshot: fetch notes

Snapshot date for the dataset: 2026-10-16. All files below were fetched on 2026-10-19 (UTC).
`SHA256SUMS` (this directory) lists every file under `sources/`, `raw/loghub/`, `raw/iana/`,
`raw/iso/`, `raw/wikidata/`, `raw/curated/` and `raw/wiki_idn.json`; run `sha256sum -c
sources/SHA256SUMS` from `inputs/LG/` to verify.

## (a) Loghub sample logs (the dataset records)

Repository: https://github.com/logpai/loghub (tree master).
Raw URLs (downloaded directly, no proxy):

- https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log   -> `raw/loghub/OpenSSH_2k.log`, `sources/OpenSSH_2k.log`
- https://raw.githubusercontent.com/logpai/loghub/master/Proxifier/Proxifier_2k.log -> `raw/loghub/Proxifier_2k.log`, `sources/Proxifier_2k.log`
- https://raw.githubusercontent.com/logpai/loghub/master/Zookeeper/Zookeeper_2k.log -> `raw/loghub/Zookeeper_2k.log`, `sources/Zookeeper_2k.log`
- https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log -> `raw/loghub/HDFS_2k.log`, `sources/HDFS_2k.log`

`dataset.py` uses the OpenSSH and Proxifier samples (SSH logins and proxy connections). The
Zookeeper and HDFS samples are kept as fetched for completeness but are not used. The sample
files are 2,000-line excerpts from the Loghub corpus; the card allows the Zenodo full release
if more entities are needed, but 40 workstations x 4 proxy + 4 SSH records fit in the two
samples, so no Zenodo download was necessary.

## Value registries

- IANA root zone TLD list: https://data.iana.org/TLD/tlds-alpha-by-domain.txt
  -> `raw/iana/tlds-alpha-by-domain.txt` (header `# Version 2026101900`).
- IANA service name and transport protocol port number registry:
  https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv
  -> `raw/iana/service-names-port-numbers.csv`.
- ISO 3166 country list with region/sub-region columns (lukes/ISO-3166-Countries-with-Regional-Codes):
  https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv
  -> `raw/iso/countries.csv`.

## Organisation memberships (IDN ccTLD / intergovernmental organisations)

- Wikidata Query Service, SPARQL endpoint https://query.wikidata.org/sparql, query with
  `?item p:P463 ?st. ?st ps:P463 wd:<QID>.` plus `OPTIONAL { ?st pq:P582 ?end }` and
  `OPTIONAL { ?item wdt:P297 ?iso }` (the full query is in `fetch_org_members.py`). One raw
  JSON per organisation is in `raw/wikidata/<key>.json`; membership end dates after the
  snapshot are filtered by the builder. QIDs: EU Q458, Schengen Q392755, Eurozone Q8268,
  NATO Q7184, Commonwealth Q7785, ASEAN Q7768, G20 Q180392, BRICS Q240313, OECD Q41550,
  African Union Q7813, Arab League Q7172, Nordic Council Q6204, GCC Q179807, CARICOM Q207284,
  Pacific Islands Forum Q1135888, G7 Q102688, Five Eyes Q1055193, CPLP Q1055634,
  OIF Q134102, OPEC Q7795, CIS Q598007, SAARC Q1046701, APEC Q170481.
- English Wikipedia API (action=parse, page `Internationalized country code top-level domain`)
  -> `raw/wiki_idn.json`.

## Salience (section 3)

Wikimedia pageviews REST API:
`https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/<article>/monthly/2025100100/2026093000`.
One JSON per list in `salience/raw/<list_id>.json`, fetched by `build_salience.py --fetch`
(one connection, 0.5 s between requests, 429 retries with exponential backoff). The
`wiki` column of `raw/curated/SOURCES.md` gives the article for each list; lists whose
article has no pageview data (e.g. redirects) are recorded with `pageviews_12m = 0`.

## Curated catalogs and list membership

`raw/curated/client_apps.tsv` and `raw/curated/usernames.tsv` are value catalogs built from
the Loghub samples plus the vendor/standard pages cited in `raw/curated/SOURCES.md`. The
membership arrays of every list, together with the page that states the membership, are in
`raw/curated/lists_tld.json`, `lists_tld_extra.json`, `lists_port.json`,
`lists_client_app.json` and `lists_user.json`; `raw/curated/SOURCES.md` tabulates them.

## Proxy

Only the Wikipedia/Wikidata hosts went through the HTTP proxy:
`export HTTPS_PROXY=<proxy> HTTP_PROXY=<proxy>` with the
NO_PROXY list from the guide. GitHub, IANA and the ISO mirror were fetched directly.
