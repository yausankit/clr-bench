# CH source retrieval

Collected on 2026-10-22 from public pages through an HTTP proxy
`$HTTPS_PROXY` (except GitHub, which is direct). MediaWiki/SPARQL calls were serialized
with at least 2 seconds between requests; pageview calls used at least 0.5 seconds. 429 responses
were retried from 60 seconds with exponential backoff. Every downloaded response is retained in
`raw/` without editing.

## Chemical sources

| Raw files | Public source |
|---|---|
| `stockholm_text.html`, `stockholm_allpops.html` | https://chm.pops.int/TheConvention/Overview/TextoftheConvention/tabid/2232/Default.aspx and https://chm.pops.int/TheConvention/ThePOPs/AllPOPs/tabid/2509/Default.aspx |
| `stockholm_convention_text_2025.pdf` | https://chm.pops.int/Portals/0/download.aspx?e=UNEP-POPS-COP-CONVTEXT-2025.English.pdf |
| `rotterdam_text.html`, `rotterdam_annex_iii.html` | https://www.pic.int/TheConvention/Overview/TextoftheConvention/tabid/1048/language/en-US/Default.aspx and https://www.pic.int/TheConvention/Chemicals/AnnexIIIChemicals/tabid/1132/language/en-US/Default.aspx |
| `rotterdam_convention_text_2025.pdf` | https://www.pic.int/Portals/5/download.aspx?e=UNEP-FAO-RC-CONVTEXT-2025.English.pdf |
| `opcw_annexes.html`, `cwc_schedule_1.html`, `cwc_schedule_2.html`, `cwc_schedule_3.html` | https://www.opcw.org/chemical-weapons-convention/annexes and the linked Schedule 1/2/3 pages |
| `iarc_agents.html`, `iarc_list_of_classifications.html`, `iarc_loc_app.js`, `search_iarc.html` | https://monographs.iarc.who.int/agents-classified-by-the-iarc/ and https://monographs.iarc.who.int/list-of-classifications |
| `eu_wfd_directive_2013_39.html` | https://eur-lex.europa.eu/eli/dir/2013/39/oj/eng |
| `montreal_home.html`, `montreal_text.html`, `montreal_relevant_annexes.html` | https://ozone.unep.org/treaties/montreal-protocol and its text/annex pages |
| `montreal_handbook_2020.pdf` | https://ozone.unep.org/sites/default/files/Handbooks/MP-Handbook-2020-English.pdf |

The final chemical lists use the archived Convention PDFs/HTML above. `opcw_all_schedules` unions the
three archived OPCW schedule tables, and `montreal_all_controlled_substances` reads the named rows in
Annexes A, B, C, E and F of the archived 2020 handbook. Unused exploratory downloads remain archived
for audit but do not feed any list.

## Country sources

| Raw files | Public source / query |
|---|---|
| `country_codes.csv` | https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv |
| `eu_member_states.html` | https://european-union.europa.eu/principles-countries-history/eu-countries_en |
| `nato_member_states.html` | https://www.nato.int/en/about-us/organization/nato-member-countries |
| `commonwealth_member_countries.html` | https://thecommonwealth.org/our-member-countries |
| `wikipedia_g7.txt`, `wikidata_g7_entity.json` | https://en.wikipedia.org/wiki/G7 and https://www.wikidata.org/wiki/Special:EntityData/Q1764511.json (`P710` participants) |
| `wikipedia_gcc.txt`, `wikidata_gcc_entity.json` | https://en.wikipedia.org/wiki/Gulf_Cooperation_Council and https://www.wikidata.org/wiki/Special:EntityData/Q217172.json (`P527` member states) |
| `mtcr_partners.html` | https://www.mtcr.info/en/partners |
| `wassenaar_home.html`, `wassenaar_participating_states.html` | https://www.wassenaar.org/ and the participating-states page |
| `schengen_area.html` | https://home-affairs.ec.europa.eu/policies/schengen/schengen-area_en |
| `wikidata_country_group_members.json` | Wikidata SPARQL endpoint, current `P463` membership statements for EU (Q458), NATO (Q7184), Commonwealth (Q7785), ASEAN (Q7768), Arab League (Q7172), MTCR (Q1072120), NSG (Q1480793), Australia Group (Q782942), and GCC (Q217172) |
| `wikidata_opec_members.json` | Wikidata SPARQL endpoint, current OPEC membership (`P463` Q168239), including start/end qualifiers |

The country endpoint query selected `?item p:P463 ?s . ?s ps:P463 ?org`, retained statements without
an end qualifier, read `P297` for alpha-2 codes, and used English item labels. The G7 and GCC members
come from their entity snapshots (`P710` and `P527` respectively), with the article text retained as
member-name evidence. The EU page supplied the `EU member states since 1958` subset directly through
the card text.

## Carrier sources

| Raw file | Public source |
|---|---|
| `staralliance_members.html` | https://www.staralliance.com/en/members |
| `oneworld_members.html` | https://www.oneworld.com/members |
| `skyteam_members.html` | http://www.skyteam.com/en/about/ |
| `alta_members.html`, `alta_membership.html` | https://alta.aero/membership/ |
| `airlines_for_america_members.html` | https://www.airlines.org/who-we-are/ |
| `a4e_our_members.html`, `a4e_home.html` | https://www.a4e.eu/about/our-members and https://www.a4e.eu |
| `wikidata_top_active_iata_airlines.json` | Wikidata SPARQL endpoint, active airlines with IATA membership and headquarters/country labels |
| `wikidata_active_iata_airlines.json` | Wikidata SPARQL endpoint, active airline candidates used while validating the carrier universe |

The two Wikidata airline queries are reproducible at https://query.wikidata.org/sparql by selecting
airline items (`P31`/`P279*` airline), requiring an IATA airline designator, excluding dissolved items,
and reading the English label, headquarters (`P159`), and country (`P17`). The smaller airline-group
snapshot (`wikidata_airline_group_members.json`) is an audit source only.

## Salience

`build_salience.py --fetch` requests monthly English pageviews from
`https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/`
for `2025101600` through `2026101500`. After tunnel recovery, 37 of the 39 concept titles returned raw
monthly JSON. The two ALTA lists share a title for which no English article was found; both retain
`pageviews_12m=0` and `note=raw response missing`. No list was removed by salience.

## Attempted but unused sources

`gcc_member_states.html` is a 404 page, `mercosur_states_parties.html` is a Cloudflare block page,
`g7_members.html` is an unrelated German government page, and the early `wikidata_g7_members.json` query
used the wrong entity (Q132610, Siocon) and returned zero bindings. These files do not feed any universe
or list. `eu_drug_precursors.html` is zero bytes and is also unused. `wikidata_g7_gcc_oecd.json` was an
exploratory group query and is not used.
