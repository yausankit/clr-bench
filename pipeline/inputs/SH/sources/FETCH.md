# Source retrieval (snapshot date 2026-10-16; fetched 2026-10-22)

- `raw/countries.json`: country names, ISO alpha-2 codes, continent and capital; `https://raw.githubusercontent.com/mledoze/countries/master/countries.json`.
- `raw/unlocode.csv`: UN/LOCODE location records; public mirror `https://raw.githubusercontent.com/datasets/un-locode/master/data/code-list.csv` (UNECE's 2024 CSV URL returned HTTP 403). Builders retain rows with port function and status `AA, AI, AC, AF, AS, RL`; the full filtered active-port source is used to place non-universe values in `out_of_universe`.
- `raw/wikidata_country_memberships.json` and `raw/wikidata_all_country_memberships.json`: Wikidata SPARQL country membership statements (`P463` organization and `P297` ISO alpha-2 code), queried at `https://query.wikidata.org/sparql`. The saved result has group QID, label and country code. Country roster counts are distinct returned codes; this is a reproducible Wikidata snapshot and was not separately reconciled to every organization's own current page.
- `raw/pif_members.html`: Pacific Islands Forum member page, `https://forumsec.org/pacific-islands-forum`.
- `raw/port_sources/medcruise_port_members.html`: MedCruise port member directory, `https://www.medcruise.com/port-members`.
- `raw/port_sources/cruise_britain.html`: Cruise Britain Ports & Destinations directory, `https://www.cruisebritain.org/ports/`.
- `raw/port_sources/green_marine.html`: Green Marine port and seaway participants, `https://green-marine.org/members/participants/`.
- `raw/port_sources/cruise_europe_ports.html`: Cruise Europe Port Information map, `https://www.cruiseeurope.com/port-information/`; the saved HTML embeds the complete 139-feature GeoJSON roster.
- `raw/port_sources/cruise_baltic.html`, `cruise_baltic_main.bundle.js`, and `cruise_baltic_port_info.json`: CruiseBaltic destination page and the public API response from `https://api.cruisebaltic.com/umbraco/api/PortInfo/GetAllPortInfoPageData`. The API's `AllPorts.AllPortsList` has 31 entries and replaces the client-rendered page's incomplete sample.
- `raw/wikidata_port_memberships.json`: SPARQL query result for port entities with a UN/LOCODE and a Wikidata `P463` organization statement (`SELECT ?group ?groupLabel ?port ?portLabel ?locode WHERE { ?port wdt:P1937 ?locode; wdt:P463 ?group. ... }`). The nine city-network lists use the complete returned port-code rows for their group QIDs; listed codes outside `port` are recorded as out of universe.

`lists/port.yaml` contains 5 official port/cruise directories, 12 explicitly indirect port sets formed by intersecting the 12 country-organization member rosters with active UN/LOCODE entries, and 9 port-location sets directly represented by the saved Wikidata port membership query. The indirect country-derived sets are 12 of 26 candidates. The 5 provisional CPPI, World Ports Climate Action, IAPH, MARAD and Caribbean Ports samples were removed because their complete public roster snapshots could not be recovered. Attempts are retained in `raw/port_sources/` and listed below; they are not used as input lists.

- `raw/port_sources/iaph_members.html`: attempted IAPH directory; HTTP 403.
- The attempted World Ports Climate Action member-page request failed TLS; no roster file was saved.
- `raw/port_sources/worldbank_cpp_press.html`: attempted World Bank CPPI press URL; HTTP 404.
- `raw/port_sources/marad_strategic_seaports.html`: MARAD page denied access.
- `raw/port_sources/cruise_baltic_destinations.html`: attempted CruiseBaltic destination page shell; it did not provide a complete roster (the API response above does).
- `raw/port_sources/espo_members.html`, `baltic_ports_organization.html`, and `bpo_*.html`: attempted association member pages; they did not expose a complete machine-readable roster.

`build_inputs.py`, `build_port_lists.py`, `port_rosters.py`, and `build_salience.py` deterministically rebuild the universes, lists and salience tables from these snapshots. `fetch_salience.py` retrieves English Wikipedia monthly pageviews for 2025-10-01 through 2026-09-30; raw responses are in `salience/raw/`. Missing pages remain with zero views.
