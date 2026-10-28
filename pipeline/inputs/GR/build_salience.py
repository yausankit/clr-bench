#!/usr/bin/env python3
"""Rebuild list pageview totals and salience tables from saved REST JSON."""
import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
TITLE = {
    "eu_members": "European_Union", "schengen_members": "Schengen_Area",
    "nato_members": "NATO", "oecd_members": "OECD", "commonwealth_members": "Commonwealth_of_Nations",
    "african_union_members": "African_Union", "arab_league_members": "Arab_League",
    "opec_members": "OPEC", "asean_members": "ASEAN", "council_of_europe_members": "Council_of_Europe",
    "mercosur_members": "Mercosur", "un_members": "Member_states_of_the_United_Nations", "g7_members": "G7",
    "g20_members": "G20", "gcc_members": "Gulf_Cooperation_Council", "pif_members": "Pacific_Islands_Forum",
    "star_alliance_members": "Star_Alliance", "skyteam_members": "SkyTeam", "oneworld_members": "Oneworld",
    "iata_members": "International_Air_Transport_Association", "a4a_members": "Airlines_for_America",
    "alta_full_members": "Latin_American_and_Caribbean_Air_Transport_Association", "aaco_members": "Arab_Air_Carriers_Organization",
    "afraa_members": "African_Airlines_Association", "airlines_for_europe": "Airlines_for_Europe",
    "lufthansa_group_airlines": "Lufthansa_Group", "iag_airlines": "International_Airlines_Group",
    "star_alliance_founders": "Star_Alliance", "ryanair_group_airlines": "Ryanair",
    "tui_airlines": "TUI_Group", "a380_operators": "List_of_Airbus_A380_orders_and_deliveries",
    "aapa_members": "Association_of_Asia_Pacific_Airlines", "air_france_klm_airlines": "Air_France–KLM",
    "qantas_group_airlines": "Qantas", "b787_operators": "List_of_Boeing_787_orders_and_deliveries",
    "skytrax_five_star": "Skytrax",
    "ivy_league": "Ivy_League", "group_of_eight": "Group_of_Eight_(Australian_universities)",
    "c9_universities": "C9_League", "leru_members": "League_of_European_Research_Universities",
    "apru_members": "Association_of_Pacific_Rim_Universities", "aun_members": "ASEAN_University_Network",
    "n8_members": "N8_Research_Partnership", "iaru_members": "International_Alliance_of_Research_Universities",
    "coimbra_members": "Coimbra_Group", "aau_members": "Association_of_American_Universities",
    "acu_members": "Association_of_Commonwealth_Universities", "u21_members": "Universitas_21",
    "wun_members": "Worldwide_Universities_Network", "eua_members": "European_University_Association",
    "russell_group": "Russell_Group",
}

def main():
    for p in sorted((ROOT / "lists").glob("*.yaml")):
        table = []
        for item in yaml.safe_load(p.read_text(encoding="utf-8")) or []:
            cid = str(item["id"])
            title = TITLE[cid]
            raw = json.loads((RAW / f"{cid}.json").read_text(encoding="utf-8"))
            views = sum(int(x.get("views", 0)) for x in raw.get("items", []))
            table.append([cid, title.replace("_", " "), "exact article title", views, "12 monthly pageview records; 2025-10-16 through 2026-10-15"])
        out = ROOT / "salience" / f"{p.stem}.tsv"
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["concept_id", "wiki_title", "match", "pageviews_12m", "note"])
            w.writerows(table)

if __name__ == "__main__":
    main()
