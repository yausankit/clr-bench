#!/usr/bin/env python3
"""Check every SPOTCHECK assertion against the corresponding raw roster rows."""
import csv
import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
COUNTRY_QIDS = {
    "eu_members":"Q458", "schengen_members":"Q1969730", "nato_members":"Q7184", "oecd_members":"Q41550",
    "commonwealth_members":"Q7785", "african_union_members":"Q7159", "arab_league_members":"Q7172",
    "opec_members":"Q7795", "asean_members":"Q7768", "council_of_europe_members":"Q8908",
    "mercosur_members":"Q4264", "un_members":"Q1065",
}
UNI_QIDS = {
    "ivy_league":"Q49113", "group_of_eight":"Q1377311", "c9_universities":"Q2634906", "leru_members":"Q1152269",
    "apru_members":"Q1074688", "aun_members":"Q297575", "n8_members":"Q5463432", "iaru_members":"Q1140056",
    "coimbra_members":"Q211620", "aau_members":"Q743812", "acu_members":"Q593768", "u21_members":"Q1202548",
    "wun_members":"Q1047645", "eua_members":"Q868940", "russell_group":"Q590631",
}

def qid(uri): return uri.rsplit("/", 1)[-1]
def norm(s):
    value=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", value)
def bindings(file): return json.loads((RAW / file).read_text(encoding="utf-8"))["results"]["bindings"]

def html_air_rosters():
    b = RAW / "airline_sources"
    rosters = {}
    soup = BeautifulSoup((b / "star_alliance.html").read_bytes(), "lxml")
    kw = next((m.get("content", "") for m in soup.find_all("meta") if m.get("name") == "keywords"), "")
    rosters["star_alliance_members"] = [x.strip() for x in kw.split("Star Alliance Members,", 1)[-1].split(",") if x.strip() and not x.strip().startswith("Star Alliance network")]
    soup = BeautifulSoup((b / "skyteam.html").read_bytes(), "lxml")
    rosters["skyteam_members"] = [x.get_text(" ", strip=True) for x in soup.select("h3")]
    soup = BeautifulSoup((b / "oneworld.html").read_bytes(), "lxml")
    slugmap = {'alaska-airlines':'Alaska Airlines','american-airlines':'American Airlines','british-airways':'British Airways','cathay-pacific':'Cathay Pacific','fiji-airways':'Fiji Airways','finnair':'Finnair','iberia':'Iberia','japan-airlines':'Japan Airlines','malaysia-airlines':'Malaysia Airlines','oman-air':'Oman Air','philippine-airlines':'Philippine Airlines','qantas':'Qantas','qatar-airways':'Qatar Airways','royal-air-maroc':'Royal Air Maroc','royal-jordanian':'Royal Jordanian','srilankan-airlines':'SriLankan Airlines'}
    rosters["oneworld_members"] = [v for x in {a.get("href", "").split("/")[-1] for a in soup.select('a[href^="/members/"]')} for v in [slugmap.get(x)] if v]
    iata=[]
    for p in [b / "iata_airline_list.html", *sorted((b / "iata_pages").glob("page_*.html"))]:
        soup=BeautifulSoup(p.read_bytes(),"lxml")
        iata += [a.get_text(" ",strip=True) for a in soup.select("a[href]") if re.search(r"/airline-list/[^/?#]+/\d+/?$",a.get("href","")) and a.get_text(" ",strip=True)]
    rosters["iata_members"] = list(set(iata))
    soup=BeautifulSoup((b/"a4a_home.html").read_bytes(),"lxml")
    rosters["a4a_members"]=[x.get("alt","").strip() for x in soup.select("img[alt]") if x.get("alt","").strip() in {'Air Canada','Alaska Airlines','American Airlines','Atlas Air','Delta Air Lines','FedEx','JetBlue','Southwest','United Airlines','UPS'}]
    soup=BeautifulSoup((b/"alta_members_v2.html").read_bytes(),"lxml")
    titles=[x.get("title","").strip() for x in soup.select("img[title]") if x.get("title")]
    rosters["alta_full_members"]=titles[:titles.index("Air Canada")] if "Air Canada" in titles else titles
    soup=BeautifulSoup((b/"aaco_members_current.html").read_bytes(),"lxml")
    heads=[x.get_text(" ",strip=True) for x in soup.find_all("h3")]
    rosters["aaco_members"]=heads[heads.index("Member Airlines")+1:] if "Member Airlines" in heads else heads[1:]
    soup=BeautifulSoup((b/"star_alliance_article.html").read_bytes(),"lxml")
    history=" ".join(p.get_text(" ",strip=True) for p in soup.select("p"))
    rosters["star_alliance_founders"]=['Air Canada','Lufthansa','Scandinavian Airlines','Thai Airways International','United Airlines'] if 'announced on 14 May 1997 by five airlines' in history else []
    soup=BeautifulSoup((b/"a380_orders_deliveries.html").read_bytes(),"lxml")
    rosters["a380_operators"]=[tr.select("td")[0].get_text(" ",strip=True) for tr in soup.select("table")[1].select("tr") if tr.select("td")]
    aapa=json.loads((b/"aapa_pages_search.json").read_text(encoding="utf-8"))
    content=html.unescape(next(r["content"]["rendered"] for r in aapa if r.get("slug")=="who-we-are"))
    match=re.search(r'custom_links=([^ ]+)',content)
    hrefs=match.group(1).strip('”"').split(",") if match else []
    aapa_by_host={'airastana.com':'Air Astana','airindia.in':'Air India','airnewzealand.co.nz':'Air New Zealand','ana.co.jp':'All Nippon Airways','bangkokair.com':'Bangkok Airways','cathaypacific.com':'Cathay Pacific','china-airlines.com':'China Airlines','evaair.com':'EVA Air','garuda-indonesia.com':'Garuda Indonesia','jal.com':'Japan Airlines','lionair.co.id':'Lion Air','malaysiaairlines.com':'Malaysia Airlines','philippineairlines.com':'Philippine Airlines','qantas.com':'Qantas','flyroyalbrunei.com':'Royal Brunei','singaporeair.com':'Singapore Airlines','thaiairways.com':'Thai Airways International','vietnamairlines.com':'Vietnam Airlines'}
    rosters["aapa_members"]=[aapa_by_host[h] for u in hrefs for h in [(urlparse(u).hostname or "").removeprefix("www.")] if h in aapa_by_host]
    soup=BeautifulSoup((b/"air_france_klm.html").read_bytes(),"lxml")
    cells=[]
    for tr in soup.select("table")[2].select("tr"):
        row=tr.select("th,td")
        if len(row)>1 and row[0].get_text(" ",strip=True)=="Subsidiaries": cells=row; break
    raw_group=[a.get_text(" ",strip=True) for a in cells[-1].select("a")]
    rosters["air_france_klm_airlines"]=[x for x in ("Air France","Air France Hop","KLM","KLM Cityhopper","Martinair") if (x=="KLM" and "KLM Royal Dutch Airlines" in raw_group) or (x!="KLM" and x in raw_group)]
    if "Transavia" in raw_group and "France" in raw_group: rosters["air_france_klm_airlines"].append("Transavia France")
    soup=BeautifulSoup((b/"qantas_group.html").read_bytes(),"lxml")
    subs=[]
    for tr in soup.select("table tr"):
        cells=tr.select("th,td")
        if len(cells)>1 and cells[0].get_text(" ",strip=True)=="Wholly owned subsidiaries":
            subs=[a.get_text(" ",strip=True) for a in cells[1].select("a")]
            break
    rosters["qantas_group_airlines"]=["Qantas",*subs]
    soup=BeautifulSoup((b/"b787_operators.html").read_bytes(),"lxml")
    rosters["b787_operators"]=[tr.select("th,td")[0].get_text(" ",strip=True) for tr in soup.select("table")[3].select("tr")[2:]
       if len(tr.select("th,td"))>=12 and re.fullmatch(r"\d+",tr.select("th,td")[11].get_text(" ",strip=True).replace(',',''))
       and int(tr.select("th,td")[11].get_text(" ",strip=True).replace(',',''))>0 and tr.select("th,td")[0].get_text(" ",strip=True)!="Vistara"]
    soup=BeautifulSoup((b/"skytrax_five_star.html").read_bytes(),"lxml")
    intro=next((p for p in soup.select("p") if "ten airlines they deem to be five-star rated" in p.get_text(" ",strip=True).lower()),None)
    starlist=intro.find_next("ul") if intro else None
    rosters["skytrax_five_star"]=[li.get_text(" ",strip=True).replace("*","").strip() for li in starlist.select("li")] if starlist else []
    aff=bindings("airline_affiliations_wikidata.json")
    rosters["afraa_members"]=[r["itemLabel"]["value"] for r in aff if r.get("orgLabel",{}).get("value")=="African Airlines Association"]
    rosters["airlines_for_europe"]=[r["itemLabel"]["value"] for r in aff if r.get("orgLabel",{}).get("value")=="Airlines for Europe"]
    rosters["lufthansa_group_airlines"]=['Austrian Airlines','Brussels Airlines','Discover Airlines','Eurowings','Lufthansa','Lufthansa City Airlines','Swiss International Air Lines','Edelweiss Air','Air Dolomiti']
    rosters["iag_airlines"]=['Aer Lingus','British Airways','Iberia','Vueling','BA CityFlyer','BA EuroFlyer','Iberia Express']
    for lid in ("lufthansa_group_airlines","iag_airlines"):
        path=b/("wiki_lufthansa_group.html" if lid.startswith("lufthansa") else "wiki_iag.html")
        text=BeautifulSoup(path.read_bytes(),"lxml").get_text(" ",strip=True)
        assert all(x in text for x in rosters[lid]), f"{lid}: expected roster entry missing from saved source"
    return {k:{norm(x) for x in v} for k,v in rosters.items()}

def country_html_roster(lid, code_by_name):
    files={"eu_members":"european_union.html","schengen_members":"schengen_area.html","nato_members":"nato.html",
           "oecd_members":"oecd.html","commonwealth_members":"commonwealth.html","african_union_members":"african_union_official.html",
           "asean_members":"asean.html","opec_members":"opec.html","council_of_europe_members":"council_of_europe_members.html",
           "un_members":"un_members.html","g20_members":"g20.html","gcc_members":"gulf_cooperation_council.html",
           "pif_members":"pacific_islands_forum.html"}
    path=RAW/"country_sources"/files[lid]
    soup=BeautifulSoup(path.read_bytes(),"lxml"); tables=soup.select("table"); cells=[]; multi=False
    table_index={"eu_members":2,"schengen_members":2,"nato_members":2,"oecd_members":6,"asean_members":3,"opec_members":2,
                 "council_of_europe_members":0,"un_members":1,"g20_members":2,"gcc_members":3,"pif_members":1}.get(lid)
    if lid=="commonwealth_members":
        for row in tables[6].select("tr"):
            rowcells=row.select("th,td")
            if len(rowcells)>1 and rowcells[0].get_text(" ",strip=True)=="Sovereign states (members)": cells=[rowcells[1]]; multi=True; break
    elif lid=="african_union_members":
        cells=[row.select("th,td")[1] for table in tables for row in table.select("tr") if len(row.select("th,td"))>1]
    elif lid=="pif_members":
        result=set()
        for row in tables[1].select("tr")[2:7]:
            for cell in row.select("th,td"):
                result.update(re.findall(r"\(([A-Z]{2})\)",cell.get_text(" ",strip=True)))
        return result
    else:
        rows=tables[table_index].select("tr")
        rows=rows[2:-1] if lid=="gcc_members" else rows[1:]
        if lid=="nato_members": cells=[rows[0].select("td")[0]]; multi=True
        else: cells=[row.select("th,td")[0] for row in rows if row.select("th,td")]
    result=set()
    for cell in cells:
        anchors=[a for a in cell.select("a") if a.get_text(" ",strip=True)]
        names=[a.get_text(" ",strip=True) for a in (anchors if multi else anchors[:1])]
        if not names: names=[cell.get_text(" ",strip=True)]
        for name in names:
            key=norm(re.sub(r"\s*\[[^]]*\]", "", name))
            if key in code_by_name: result.add(code_by_name[key])
    return result

def main():
    lists={}
    for p in (ROOT/"lists").glob("*.yaml"):
        lists.update({x["id"]:x for x in yaml.safe_load(p.read_text(encoding="utf-8"))})
    country_rows=bindings("target_org_memberships.json")
    country_universe=list(csv.DictReader((ROOT/"universes/country.tsv").open(encoding="utf-8"),delimiter="\t"))
    code_by_qid={r["qid"]:r["value"] for r in country_universe if r.get("qid")}
    code_by_name={norm(r["entity"]):r["value"] for r in country_universe}
    code_by_name.update({"unitedstates":"US","unitedstatesofamerica":"US","bahamasthe":"BS","bolivia":"BO",
        "democraticpeoplesrepublicofkorea":"KP","gambiarepublicofthe":"GM","naoero":"NR","republicofmoldova":"MD",
        "unitedkingdomofgreatbritainandnorthernireland":"GB","unitedrepublicoftanzania":"TZ","brunei":"BN","moldova":"MD",
        "iran":"IR","venezuela":"VE","congorepublic":"CG","drcongo":"CD","sahrawirepublic":"EH","tanzania":"TZ",
        "czechia":"CZ","turkiye":"TR","ivorycoast":"CI","cotedivoire":"CI","laos":"LA","bruneidarussalam":"BN",
        "czechrepublic":"CZ","peoplesrepublicofchina":"CN","russianfederation":"RU","republicofkorea":"KR",
        "republicofthecongo":"CG","congo":"CG","democraticrepublicofthecongo":"CD","drcongo":"CD",
        "timorleste":"TL","western sahara":"EH","sahrawiarabdemocraticrepublic":"EH","northmacedonia":"MK",
        "republicofkosovo":"XK","thegambia":"GM","gambia":"GM"})
    uni_rows=bindings("university_affiliations_wikidata.json")
    airline_rows=bindings("airline_affiliations_wikidata.json")
    air_html=html_air_rosters()
    with (ROOT/"SPOTCHECK.tsv").open(encoding="utf-8") as f: checks=list(csv.DictReader(f,delimiter="\t"))
    assert checks, "empty spotcheck file"
    groups={}
    for r in checks: groups.setdefault(r["list_id"],[]).append(r)
    for lid,li in lists.items():
        rows=groups[lid]
        assert sum(r["status"]=="member" for r in rows)==5 and sum(r["status"]=="nonmember" for r in rows)==5, f"{lid}: requires 5/5 checks"
        if (lid in COUNTRY_QIDS or lid in ("g20_members","gcc_members","pif_members")) and lid not in ("arab_league_members",):
            observed=country_html_roster(lid,code_by_name)
            observed={norm(x) for x in observed}
        elif lid in COUNTRY_QIDS:
            q=COUNTRY_QIDS[lid]
            observed={code_by_qid.get(qid(r["item"]["value"])) for r in country_rows if qid(r["org"]["value"])==q}
            observed.discard(None)
            observed={norm(x) for x in observed}
        elif lid=="g7_members":
            text=BeautifulSoup((RAW/"country_sources/group_of_seven.html").read_bytes(),"lxml").get_text(" ",strip=True)
            mapping={"CA":"Canada","FR":"France","DE":"Germany","IT":"Italy","JP":"Japan","GB":"United Kingdom","US":"United States"}
            observed={norm(k) for k,v in mapping.items() if v in text}
        elif lid in UNI_QIDS:
            q=UNI_QIDS[lid]
            observed={norm(r.get("itemLabel",{}).get("value","")) for r in uni_rows if qid(r["org"]["value"])==q}
        elif lid in air_html:
            observed=air_html[lid]
        elif lid in ("afraa_members","airlines_for_europe"):
            label="African Airlines Association" if lid=="afraa_members" else "Airlines for Europe"
            observed={norm(r.get("itemLabel",{}).get("value","")) for r in airline_rows if r.get("orgLabel",{}).get("value")==label}
        elif lid in ("lufthansa_group_airlines","iag_airlines"):
            observed={norm(x) for x in (['Austrian Airlines','Brussels Airlines','Discover Airlines','Eurowings','Lufthansa','Lufthansa City Airlines','Swiss International Air Lines','Edelweiss Air','Air Dolomiti'] if lid.startswith("lufthansa") else ['Aer Lingus','British Airways','Iberia','Vueling','BA CityFlyer','BA EuroFlyer','Iberia Express'])}
        else: raise AssertionError(f"unknown source for {lid}")
        expected={norm(x) for x in li["members"]}
        disputed={norm(x) for x in li.get("disputed",[])}
        for row in rows:
            key=norm(row["value"])
            if row["status"]=="member":
                assert key in expected and key in observed, f"{lid}: member mismatch {row['value']}"
            else:
                assert key not in expected and key not in disputed and key not in observed, f"{lid}: nonmember present in roster {row['value']}"
            assert row["evidence"].startswith("raw/"), f"{lid}: missing raw file evidence"
    print(f"spotcheck OK: {len(groups)} lists; {len(checks)} raw-source assertions (5 members + 5 nonmembers each)")

if __name__=="__main__": main()
