# UN dataset delivery report

**Dataset:** UN scholarship application review. **Snapshot:** 2026-10-16. **Acquisition:** isolated DS_UN_f6 workspace.

## Universes

| Universe | Values | Natural attributes | Descriptions |
|---|---:|---|---:|
| university | 14,100 | country, continent | 14100/14100 |
| country | 249 | continent, region | 249/249 |
| sponsor_company | 971 | country, sector | 971/971 |

## Lists and salience

`Members` is mapped in-universe membership. `Official` equals members + disputed + out-of-universe values. `Screen` is the final three-version pre-screen; “not scorable” means candidate construction rejected the list.

| Universe | ID | Members | Official | Pageviews 12m | Screen | Source |
|---|---|---:|---:|---:|---|---|
| country | african_union | 55 | 55 | 517616 | fail (0.56) | Public roster snapshot: https://en.wikipedia.org/wiki/African_Union |
| country | arab_league | 22 | 22 | 465450 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/Arab_League |
| country | asean | 10 | 11 | 1292950 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/ASEAN |
| country | caricom | 15 | 15 | 158485 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/Caribbean_Community |
| country | commonwealth | 56 | 56 | 1607656 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/Commonwealth_of_Nations |
| country | cplp | 9 | 9 | 110363 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/Community_of_Portuguese_Language_Countries |
| country | ehea | 48 | 50 | 23326 | fail (0.59) | Public roster snapshot: https://en.wikipedia.org/wiki/European_Higher_Education_Area |
| country | erasmus_countries | 33 | 33 | 151411 | pass | https://erasmus-plus.ec.europa.eu/programme-guide/part-a/eligible-countries |
| country | francophonie | 51 | 51 | 163651 | fail (0.56) | Public roster snapshot: https://en.wikipedia.org/wiki/Organisation_internationale_de_la_Francophonie |
| country | g20 | 19 | 21 | 995333 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/G20 |
| country | g7 | 7 | 7 | 974084 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/G7 |
| country | nato | 30 | 32 | 2551051 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/NATO |
| country | oecd | 38 | 38 | 807032 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/OECD |
| country | oic | 57 | 57 | 272956 | fail (0.74) | Public roster snapshot: https://en.wikipedia.org/wiki/Organisation_of_Islamic_Cooperation |
| country | pacific_islands_forum | 18 | 18 | 72489 | pass | Public roster snapshot: https://en.wikipedia.org/wiki/Pacific_Islands_Forum |
| sponsor_company | dow_global_titans | 40 | 47 | 46575 | pass | Current component table: https://en.wikipedia.org/wiki/Dow_Jones_Global_Titans_50 |
| sponsor_company | dow_jones | 30 | 30 | 76049 | fail (0.78) | Current constituent snapshot: https://en.wikipedia.org/wiki/List_of_Dow_Jones_Industrial_Average_companies |
| sponsor_company | euro_stoxx_50 | 50 | 50 | 609936 | fail (0.52) | Current constituent snapshot: https://en.wikipedia.org/wiki/EURO_STOXX_50 |
| sponsor_company | euronext_100 | 64 | 102 | 21881 | pass | Current constituent snapshot: https://en.wikipedia.org/wiki/Euronext_100 |
| sponsor_company | fortune_global_500 | 156 | 500 | 14 | fail (0.44) | Fortune Global 500 (2026 edition, published 2026-07-28): https://fortune.com/ranking/global500/ |
| sponsor_company | ftse_100 | 72 | 100 | 935586 | pass | Current constituent snapshot: https://en.wikipedia.org/wiki/FTSE_100_Index |
| sponsor_company | g_sib | 12 | 29 | 92246 | pass | 2025 G-SIB table snapshot: https://en.wikipedia.org/wiki/List_of_systemically_important_banks |
| sponsor_company | interbrand_top10_2025 | 8 | 10 | 0 | fail (0.59) | Interbrand Best Global Brands 2025 landing page: https://interbrand.com/best-global-brands/ |
| sponsor_company | nasdaq_100 | 87 | 100 | 16238813 | pass | Nasdaq public list screener snapshot (2026-10-22): https://api.nasdaq.com/api/quote/list-type/nasdaq100?limit=100 |
| sponsor_company | omx_nordic_40 | 17 | 39 | 8811 | pass | Current constituent snapshot: https://en.wikipedia.org/wiki/OMX_Nordic_40 |
| sponsor_company | sp500 | 498 | 500 | 1555797 | not scorable | datasets/s-and-p-500-companies raw constituents.csv |
| sponsor_company | stoxx_europe_600 | 464 | 464 | 143020 | fail (0.78) | Current constituent snapshot: https://en.wikipedia.org/wiki/STOXX_Europe_600 |
| university | aau | 69 | 71 | 177299 | fail (0.78) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Association_of_American_Universities |
| university | aearu | 18 | 19 | 7279 | fail (0.67) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Association_of_East_Asian_Research_Universities |
| university | ancient_universities | 7 | 7 | 64704 | fail (0.67) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Ancient_university |
| university | apru | 61 | 64 | 20769 | fail (0.78) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Association_of_Pacific_Rim_Universities |
| university | asian_universities_alliance | 12 | 15 | 5183 | fail (0.63) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Asian_Universities_Alliance |
| university | aun | 27 | 30 | 14909 | pass | Wikimedia core-member roster snapshot: https://en.wikipedia.org/wiki/ASEAN_University_Network |
| university | big_ten | 17 | 18 | 25408 | fail (0.70) | https://btaa.org/about/member-universities |
| university | c9_league | 9 | 9 | 123276 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/C9_League |
| university | cesaer | 46 | 57 | 8003 | fail (0.78) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/CESAER |
| university | coimbra_group | 41 | 42 | 27306 | fail (0.67) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Coimbra_Group |
| university | golden_triangle | 6 | 6 | 65374 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Golden_triangle_(universities) |
| university | group_of_eight | 8 | 8 | 23948 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Group_of_Eight_(Australia) |
| university | iaru | 11 | 11 | 10547 | fail (0.63) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/International_Alliance_of_Research_Universities |
| university | idea_league | 5 | 5 | 7363 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/IDEA_League |
| university | ivy_league | 8 | 8 | 1598824 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Ivy_League |
| university | leru | 23 | 24 | 18879 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/League_of_European_Research_Universities |
| university | matariki | 6 | 6 | 5307 | fail (0.56) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Matariki_Network_of_Universities |
| university | public_ivies | 29 | 30 | 182643 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Public_Ivy |
| university | russell_group | 24 | 24 | 304698 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Russell_Group |
| university | u15_canada | 13 | 15 | 26046 | pass | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/U15_Canada |
| university | universitas_21 | 27 | 31 | 22648 | fail (0.67) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Universitas_21 |
| university | utrecht_network | 27 | 30 | 12245 | fail (0.67) | https://utrecht-network.org/members/ |
| university | worldwide_universities_network | 23 | 23 | 10021 | fail (0.70) | Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/Worldwide_Universities_Network |

## Same-partition audit, spot checks and pre-screen

- Single-valued attributes: university `country`, `continent`; country `continent`, `region`; sponsor_company `country`, `sector`. Lists equal to an attribute class: none. Attribute-distinct lists: university 23/23, country 15/15, sponsor_company 12/12.
- Spot check: 500 rows, exactly 5 members and 5 nonmembers for each of 50 lists; `build_spotcheck.py` verified membership or absence against saved raw records and recorded row/cell evidence.
- Final pre-screen: applications.university 10/23 (2 slots, threshold 10); applicants.nationality 11/15 (2 slots, threshold 10); applications.sponsor_company 6/11 (1 slot, threshold 5).
- Cross-national sponsor_company passes: `dow_global_titans`, `euronext_100`, `g_sib`, `nasdaq_100`, `omx_nordic_40` (5). `ftse_100` is single-country and does not count toward the threshold.
- Notable failures retained as competitors: `fortune_global_500`, `interbrand_top10_2025`, `stoxx_europe_600`; `sp500` could not construct an H4 candidate.

## Scenario templates

All templates use `exclude_record`; each field has three templates. Plausible IDs include every list for that field (enumerated above).

| Template | Field | Rule | Plausible count |
|---|---|---|---:|
| university_rule_1 | applications.university | Exclude an application if the applicant's university is listed by a named university association or historical set. | 23 |
| university_rule_2 | applications.university | Exclude an application if the applicant's university is listed by a named university association or historical set. | 23 |
| university_rule_3 | applications.university | Exclude an application if the applicant's university is listed by a named university association or historical set. | 23 |
| country_rule_1 | applicants.nationality | Exclude an application if its applicant's nationality appears on a named international body or programme roster. | 15 |
| country_rule_2 | applicants.nationality | Exclude an application if its applicant's nationality appears on a named international body or programme roster. | 15 |
| country_rule_3 | applicants.nationality | Exclude an application if its applicant's nationality appears on a named international body or programme roster. | 15 |
| sponsor_company_rule_1 | applications.sponsor_company | Exclude an application if its sponsoring company appears in a named equity index, company ranking or financial-stability roster. | 12 |
| sponsor_company_rule_2 | applications.sponsor_company | Exclude an application if its sponsoring company appears in a named equity index, company ranking or financial-stability roster. | 12 |
| sponsor_company_rule_3 | applications.sponsor_company | Exclude an application if its sponsoring company appears in a named equity index, company ranking or financial-stability roster. | 12 |

## Dataset interface and chains

- `dataset.py`: JSON interface; 36 funding programmes. Each trap field has 199 positions (one per application), with deterministic generation and reference totals. Applicant university, nationality, and sponsor company values are independent by application.
- Sample (`seed=20266101`, `report-example` step): P01 has 6 applications; excluding `Temuco Catholic University` in `applications.university` yields 5. Rendering one programme is 1,493 JSON characters.
- `UN1.yaml`: seed 20266101; `UN2.yaml`: seed 20266102; both use snapshot 2026-10-16, 5 slots, fields ordered university → nationality → sponsor_company.
- `clrsynth lint UN --inputs-root inputs`: **lint OK: UN**. `check_dataset.py`: **OK**, 36 entities and 199 positions per field. `dryrun.py`: **165 diagnostics**, all 5 slots built.
- Reproducibility: all five build scripts were run twice; generated-file SHA-256 manifests matched byte-for-byte. Final scenario wording was regenerated twice and compared with `cmp`. Raw snapshot and pageview `SHA256SUMS`: 142 entries, all verified. Known timing: several live pages were captured 2026-10-22, six days after the requested snapshot; dated editions and recorded changes are used where available. Nasdaq roster is timestamped 2026-10-22.
