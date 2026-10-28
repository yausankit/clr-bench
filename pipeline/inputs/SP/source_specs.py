"""Fixed public-source table/list locations used by the SP builders."""

PAGE_URL = "https://en.wikipedia.org/w/index.php?title={title}&oldid={oldid}"


def table(page, index, column, filter_column=None, filter_min=None, min_cells=None, country_column=None):
    return {"kind": "table", "page": page, "index": index, "column": column,
            "filter_column": filter_column, "filter_min": filter_min, "min_cells": min_cells,
            "country_column": country_column}


def bullet(page, index, country_suffix=False):
    return {"kind": "list", "page": page, "index": index, "country_suffix": country_suffix}


def navbox(page, contains):
    return {"kind": "navbox", "page": page, "contains": contains}


CLUB_LISTS = [
    {"id": "ucl_winners", "name": "European Cup and UEFA Champions League winners",
     "synonyms": ["Champions League winners", "European Cup winners"],
     "spec": table("ucl_finals", 4, 0, 1, 1)},
    {"id": "uel_winners", "name": "UEFA Cup and UEFA Europa League winners",
     "synonyms": ["Europa League winners", "UEFA Cup winners"],
     "spec": table("uel_finals", 4, 0, 1, 1)},
    {"id": "cup_winners_cup_winners", "name": "UEFA Cup Winners' Cup winners",
     "synonyms": ["Cup Winners' Cup winners"], "spec": table("cup_winners_cup_finals", 3, 0, 1, 1)},
    {"id": "club_world_cup_winners", "name": "FIFA Club World Cup winners",
     "synonyms": ["Club World Cup champions"], "spec": table("club_world_cup_finals", 3, 0, 1, 1)},
    {"id": "super_league_founders", "name": "European Super League founding clubs",
     "synonyms": ["European Super League founders"], "spec": bullet("european_super_league", 1)},
    {"id": "g14_members", "name": "G-14 member clubs", "synonyms": ["G14 members"],
     "spec": bullet("g14", 0, country_suffix=True)},
    {"id": "club_world_cup_2025_participants", "name": "2025 FIFA Club World Cup participants",
     "synonyms": ["2025 Club World Cup teams"], "spec": table("cwc_2025", 19, 0, min_cells=3)},
    {"id": "ucl_2024_25_league_phase", "name": "2024-25 UEFA Champions League league phase teams",
     "synonyms": ["2024-25 Champions League participants"], "spec": table("ucl_2024_25", 12, 1)},
    {"id": "premier_league_1992_93", "name": "1992-93 FA Premier League teams",
     "synonyms": ["inaugural Premier League clubs"], "spec": table("premier_league_1992_93", 1, 0)},
    {"id": "laliga_1929", "name": "1929 La Liga teams", "synonyms": ["inaugural La Liga clubs"],
     "spec": table("laliga_1929", 2, 0)},
    {"id": "bundesliga_1963_64", "name": "1963-64 Bundesliga teams", "synonyms": ["inaugural Bundesliga clubs"],
     "spec": table("bundesliga_1963_64", 1, 0)},
    {"id": "seriea_1929_30", "name": "1929-30 Serie A teams", "synonyms": ["1929-30 Serie A clubs"],
     "spec": table("seriea_1929_30", 2, 1)},
]

# Real clubs appearing in the same source performance tables, used only as non-list background values.
CLUB_UNIVERSE_EXTRAS = [
    {"id": "ucl_finalists_extra", "spec": table("ucl_finals", 4, 0)},
    {"id": "uel_finalists_extra", "spec": table("uel_finals", 4, 0)},
]


COMPANY_LISTS = [
    {"id": "cac_40", "name": "CAC 40 constituents, October 2026", "synonyms": ["CAC 40"],
     "spec": table("cac_40", 4, 0)},
    {"id": "ibex_35", "name": "IBEX 35 constituents, October 2026", "synonyms": ["IBEX 35"],
     "spec": table("ibex_35", 2, 1)},
    {"id": "ftse_mib", "name": "FTSE MIB constituents, October 2026", "synonyms": ["FTSE MIB"],
     "spec": table("ftse_mib", 1, 1)},
    {"id": "dax", "name": "DAX constituents, October 2026", "synonyms": ["DAX index"],
     "spec": table("dax", 4, 2)},
    {"id": "aex", "name": "AEX index constituents, October 2026", "synonyms": ["AEX index"],
     "spec": table("aex", 3, 1)},
    {"id": "bel_20", "name": "BEL 20 constituents, October 2026", "synonyms": ["BEL 20 index"],
     "spec": table("bel_20", 2, 0)},
    {"id": "euro_stoxx_50", "name": "EURO STOXX 50 constituents, October 2026",
     "synonyms": ["EURO STOXX 50 index"], "spec": table("euro_stoxx_50", 3, 2)},
    {"id": "dow_jones", "name": "Dow Jones Industrial Average constituents, October 2026",
     "synonyms": ["Dow Jones Industrial Average"], "spec": navbox("dow_jones", "Components of the Dow Jones")},
    {"id": "sp_100", "name": "S&P 100 constituents, October 2026", "synonyms": ["S&P 100 index"],
     "spec": table("sp_100", 2, 1)},
    {"id": "nasdaq_100", "name": "Nasdaq-100 constituents, October 2026", "synonyms": ["Nasdaq-100 index"],
     "spec": navbox("nasdaq_100", "List of NASDAQ-100 companies")},
    {"id": "sp_500", "name": "S&P 500 constituents, October 2026", "synonyms": ["S&P 500 index"],
     "spec": table("sp_500", 0, 1)},
    {"id": "stoxx_europe_600", "name": "STOXX Europe 600 constituents, October 2026",
     "synonyms": ["STOXX Europe 600 index"], "spec": table("stoxx_europe_600", 3, 1, country_column=3)},
]


COUNTRY_LISTS = [
    {"id": "eu_members", "name": "European Union member states", "synonyms": ["EU member states"],
     "page": "eu_members", "wikidata": "Q458"},
    {"id": "nato_members", "name": "NATO member states", "synonyms": ["North Atlantic Treaty Organization members"],
     "page": "nato", "wikidata": "Q7184"},
    {"id": "g7_members", "name": "Group of Seven member states", "synonyms": ["G7 members"],
     "page": "g7", "wikidata": "Q1764511"},
    {"id": "g20_members", "name": "G20 member states", "synonyms": ["Group of Twenty members"],
     "page": "g20", "wikidata": "Q19771"},
    {"id": "oecd_members", "name": "OECD member states", "synonyms": ["Organisation for Economic Co-operation and Development members"],
     "page": "oecd", "wikidata": "Q41550"},
    {"id": "opec_members", "name": "OPEC member states", "synonyms": ["Organization of the Petroleum Exporting Countries members"],
     "page": "opec", "wikidata": "Q7795"},
    {"id": "asean_members", "name": "ASEAN member states", "synonyms": ["Association of Southeast Asian Nations members"],
     "page": "asean", "wikidata": "Q7768"},
    {"id": "african_union_members", "name": "African Union member states", "synonyms": ["AU member states"],
     "page": "african_union", "wikidata": "Q7159"},
    {"id": "commonwealth_members", "name": "Commonwealth of Nations member states",
     "synonyms": ["Commonwealth members"], "page": "commonwealth", "wikidata": "Q7785"},
    {"id": "apec_members", "name": "APEC member economies", "synonyms": ["Asia-Pacific Economic Cooperation members"],
     "page": "apec", "wikidata": "Q170481"},
]


TEMPLATES = {
    "activations.club": [
        {"id": "club_rule_ucl", "lists": ["ucl_winners", "uel_winners", "cup_winners_cup_winners"],
         "rule": "A club that has won the top European club cup is left out.",
         "source": "UEFA competition records"},
        {"id": "club_rule_uel", "lists": ["uel_winners", "cup_winners_cup_winners", "ucl_winners"],
         "rule": "A club that has won the second-tier European club cup is left out.",
         "source": "UEFA competition records"},
        {"id": "club_rule_cwc", "lists": ["cup_winners_cup_winners", "uel_winners", "ucl_winners"],
         "rule": "A club that has won the former European cup-winners' competition is left out.",
         "source": "UEFA competition records"},
        {"id": "club_rule_world", "lists": ["club_world_cup_winners", "ucl_winners", "club_world_cup_2025_participants"],
         "rule": "A club that has won the world club championship is left out.", "source": "FIFA competition records"},
        {"id": "club_rule_esl", "lists": ["super_league_founders", "ucl_winners", "g14_members"],
         "rule": "A club named as a founder of the breakaway European league is left out.", "source": "public launch list"},
        {"id": "club_rule_g14", "lists": ["g14_members", "super_league_founders", "ucl_winners"],
         "rule": "A club in the former G-14 group is left out.", "source": "G-14 membership"},
        {"id": "club_rule_cwc25", "lists": ["club_world_cup_2025_participants", "club_world_cup_winners", "ucl_2024_25_league_phase"],
         "rule": "A club entered in the 2025 world club championship is left out.", "source": "FIFA entry list"},
        {"id": "club_rule_ucl25", "lists": ["ucl_2024_25_league_phase", "club_world_cup_2025_participants", "ucl_winners"],
         "rule": "A club in the 2024-25 Champions League league phase is left out.", "source": "UEFA entry list"},
        {"id": "club_rule_pl92", "lists": ["premier_league_1992_93", "laliga_1929", "bundesliga_1963_64"],
         "rule": "A club in the first Premier League season is left out.", "source": "league season list"},
        {"id": "club_rule_laliga", "lists": ["laliga_1929", "seriea_1929_30", "premier_league_1992_93"],
         "rule": "A club in the first La Liga season is left out.", "source": "league season list"},
        {"id": "club_rule_bundesliga", "lists": ["bundesliga_1963_64", "premier_league_1992_93", "seriea_1929_30"],
         "rule": "A club in the first Bundesliga season is left out.", "source": "league season list"},
        {"id": "club_rule_seriea", "lists": ["seriea_1929_30", "laliga_1929", "bundesliga_1963_64"],
         "rule": "A club in the 1929-30 Serie A season is left out.", "source": "league season list"},
    ],
    "activations.co_sponsor": [
        {"id": "company_rule_cac", "lists": ["cac_40", "euro_stoxx_50", "stoxx_europe_600"],
         "rule": "A company in the French large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_ibex", "lists": ["ibex_35", "euro_stoxx_50", "stoxx_europe_600"],
         "rule": "A company in the Spanish large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_mib", "lists": ["ftse_mib", "euro_stoxx_50", "stoxx_europe_600"],
         "rule": "A company in the Italian large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_dax", "lists": ["dax", "euro_stoxx_50", "stoxx_europe_600"],
         "rule": "A company in the German large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_aex", "lists": ["aex", "euro_stoxx_50", "stoxx_europe_600"],
         "rule": "A company in the Dutch large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_bel", "lists": ["bel_20", "euro_stoxx_50", "stoxx_europe_600"],
         "rule": "A company in the Belgian large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_euro", "lists": ["euro_stoxx_50", "stoxx_europe_600", "cac_40"],
         "rule": "A company in the euro-area blue-chip equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_dow", "lists": ["dow_jones", "sp_100", "sp_500"],
         "rule": "A company in the oldest United States industrial equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_sp100", "lists": ["sp_100", "sp_500", "dow_jones"],
         "rule": "A company in the large United States blue-chip equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_nasdaq", "lists": ["nasdaq_100", "sp_500", "sp_100"],
         "rule": "A company in the technology-heavy United States equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_sp500", "lists": ["sp_500", "sp_100", "dow_jones"],
         "rule": "A company in the broad United States large-cap equity index is left out.", "source": "index constituent list"},
        {"id": "company_rule_stoxx", "lists": ["stoxx_europe_600", "euro_stoxx_50", "dax"],
         "rule": "A company in the broad European blue-chip equity index is left out.", "source": "index constituent list"},
    ],
    "activations.market_country": [
        {"id": "country_rule_eu", "lists": ["eu_members", "nato_members", "oecd_members"],
         "rule": "A country that is a European Union member state is left out.", "source": "treaty membership list"},
        {"id": "country_rule_nato", "lists": ["nato_members", "eu_members", "oecd_members"],
         "rule": "A country that is a NATO member state is left out.", "source": "alliance membership list"},
        {"id": "country_rule_g7", "lists": ["g7_members", "g20_members", "oecd_members"],
         "rule": "A country in the Group of Seven is left out.", "source": "summit membership list"},
        {"id": "country_rule_g20", "lists": ["g20_members", "g7_members", "oecd_members"],
         "rule": "A country in the Group of Twenty is left out.", "source": "forum membership list"},
        {"id": "country_rule_oecd", "lists": ["oecd_members", "eu_members", "g20_members"],
         "rule": "A country in the OECD is left out.", "source": "organisation membership list"},
        {"id": "country_rule_opec", "lists": ["opec_members", "african_union_members", "g20_members"],
         "rule": "A country in OPEC is left out.", "source": "organisation membership list"},
        {"id": "country_rule_asean", "lists": ["asean_members", "apec_members", "commonwealth_members"],
         "rule": "A country in ASEAN is left out.", "source": "regional association membership list"},
        {"id": "country_rule_au", "lists": ["african_union_members", "commonwealth_members", "opec_members"],
         "rule": "A country in the African Union is left out.", "source": "continental union membership list"},
        {"id": "country_rule_commonwealth", "lists": ["commonwealth_members", "african_union_members", "asean_members"],
         "rule": "A country in the Commonwealth of Nations is left out.", "source": "association membership list"},
        {"id": "country_rule_apec", "lists": ["apec_members", "asean_members", "g20_members"],
         "rule": "A country in APEC is left out.", "source": "forum membership list"},
    ],
}
