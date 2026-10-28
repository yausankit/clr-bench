#!/usr/bin/env python3
"""Rebuild UN's public-source universes and value descriptions from raw snapshots."""
import csv, json, re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"

def clean(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def write(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header); w.writerows(rows)

def main():
    countries = {}
    with (RAW / "country-codes.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            code = clean(r.get("ISO3166-1-Alpha-2"))
            name = clean(r.get("official_name_en")) or clean(r.get("CLDR display name"))
            if len(code) == 2 and name and code not in countries:
                countries[code] = {"name":name,"continent":clean(r.get("Continent")) or "?",
                                   "region":clean(r.get("Region Name")) or "?"}
    name_to_code = {x["name"].casefold(): k for k,x in countries.items()}
    with (RAW / "country-codes.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            code=clean(r.get("ISO3166-1-Alpha-2"))
            if code not in countries: continue
            for key in (r.get("CLDR display name"),r.get("UNTERM English Short"),r.get("UNTERM English Formal"),r.get("official_name_en")):
                if clean(key): name_to_code.setdefault(clean(key).casefold(),code)
    for k,x in countries.items():
        name_to_code.setdefault(clean(x["name"]).replace("the ", "").casefold(), k)
    def country_code(label):
        s=clean(label).casefold()
        aliases={"united states":"US","usa":"US","u.s.":"US","england":"GB","scotland":"GB","wales":"GB","northern ireland":"GB",
          "united kingdom":"GB","hong kong":"HK","macau":"MO","macao":"MO","palestine":"PS",
          "people's republic of china":"CN","pr china":"CN",
          "south korea":"KR","republic of korea":"KR","north korea":"KP","russia":"RU",
          "russian federation":"RU","iran":"IR","iran, islamic republic of":"IR",
          "vietnam":"VN","viet nam":"VN","taiwan":"TW","türkiye":"TR","turkey":"TR",
          "bolivia":"BO","venezuela":"VE","syria":"SY","laos":"LA","moldova":"MD",
          "brunei":"BN","tanzania":"TZ","czech republic":"CZ","ivory coast":"CI",
          "democratic republic of the congo":"CD","republic of the congo":"CG"}
        return aliases.get(s) or name_to_code.get(s)
    cr=[]; cd=[]
    for code,x in sorted(countries.items()):
        cr.append([code,x["name"],"",x["continent"],x["region"]])
        cd.append([code,f"Country or territory identified by ISO 3166-1 code {code}; {x['name']}.","datasets/country-codes raw snapshot"])
    write(ROOT/"universes/country.tsv",["value","entity","aliases","attr:continent","attr:region"],cr)
    write(ROOT/"universes/country.desc.tsv",["value","description","source"],cd)

    uq=[]
    for snapshot in ("wikidata-universities.json","wikidata-universities-2000.json","wikidata-universities-alpha10000.json"):
        path=RAW/snapshot
        if not path.exists(): continue
        uq.extend(json.loads(path.read_text())["results"]["bindings"])
    c9_path=RAW/"wikidata-c9.json"
    if c9_path.exists(): uq.extend(json.loads(c9_path.read_text())["results"]["bindings"])
    us={}
    for b in uq:
        qid=clean(b.get("qid",{}).get("value")); label=clean(b.get("itemLabel",{}).get("value"))
        co=clean(b.get("countryLabel",{}).get("value")); cc=country_code(co)
        if not qid or not label or not cc: continue
        if qid not in us or us[qid]["country"] not in countries:
            us[qid]={"name":label,"country":countries[cc]["name"],"qid":qid,"cc":cc}
    country_qid={}
    with (RAW/"country-codes.csv").open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            code=clean(r.get("ISO3166-1-Alpha-2")); qid=clean(r.get("wikidata_id")).rsplit("/",1)[-1]
            if code in countries and qid: country_qid[qid]=code
    for path in sorted((RAW/"wikidata-supplement").glob("Q*.json")):
        obj=json.loads(path.read_text()); qid=path.stem; entity=obj.get("entities",{}).get(qid,{})
        label=clean(entity.get("labels",{}).get("en",{}).get("value"))
        claims=entity.get("claims",{}).get("P17",[])
        cc=next((country_qid.get(x.get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id"))
                 for x in claims if country_qid.get(x.get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id"))),None)
        if label and cc: us[qid]={"name":label,"country":countries[cc]["name"],"qid":qid,"cc":cc}
    # Value is an English common name. Disambiguate genuine duplicate labels with their country.
    counts={}
    for x in us.values(): counts[x["name"].casefold()]=counts.get(x["name"].casefold(),0)+1
    used=set(); ur=[]; ud=[]
    for qid,x in sorted(us.items(),key=lambda kv:(kv[1]["name"].casefold(),kv[0])):
        value=x["name"]
        if counts[value.casefold()]>1: value=f"{value} ({x['country']})"
        if value in used: value=f"{value} [{qid}]"
        used.add(value)
        x["value"]=value
        ur.append([value,x["name"],qid,x["country"],countries[x["cc"]]["continent"]])
        ud.append([value,f"University located in {x['country']}.",f"Wikidata {qid}"])
    write(ROOT/"universes/university.tsv",["value","entity","qid","attr:country","attr:continent"],ur)
    write(ROOT/"universes/university.desc.tsv",["value","description","source"],ud)

    companies={}
    def add(name,country,sector,source):
        name=clean(name); country=clean(country)
        name=re.sub(r"\s+\(Class [A-Z]\)$", "", name)
        cc=country_code(country)
        if not name or not cc: return
        old=companies.get(name)
        if old is None or old["source"].startswith("S&P") and source.startswith("STOXX"):
            companies[name]={"country":countries[cc]["name"],"sector":clean(sector) or "?","source":source}
    with (RAW/"sp500.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            loc=clean(r.get("Headquarters Location")); country="United States"
            if "," in loc:
                suffix=re.sub(r"\[\d+\]", "", loc.rsplit(",",1)[-1]).strip().rstrip(".").casefold()
                us_states={"alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland","massachusetts","michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey","new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island","south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia","wisconsin","wyoming","district of columbia","d.c.","puerto rico"}
                if suffix not in us_states: country=loc.rsplit(",",1)[-1].strip()
            add(r.get("Security"),country,r.get("GICS Sector"),"S&P 500 raw constituents")
    for page,table_index in [("EURO_STOXX_50",3),("STOXX_Europe_600",2)]:
        data=json.loads((RAW/"wiki"/(page+".json")).read_text())
        soup=BeautifulSoup(data["parse"]["text"]["*"],"lxml")
        tables=soup.select("table.wikitable")
        table=tables[table_index-1]
        headers=[clean(c.get_text(" ",strip=True)) for c in table.select("tr")[0].select("th,td")]
        for tr in table.select("tr")[1:]:
            vals=[clean(c.get_text(" ",strip=True)) for c in tr.select("th,td")]
            if len(vals)!=len(headers): continue
            row=dict(zip(headers,vals))
            name=row.get("Name") or row.get("Company")
            country=row.get("Registered office") or row.get("Country")
            sector=row.get("Sector") or row.get("ICB Sector")
            add(name,country,sector,"STOXX raw constituents")
    company_rows=[]; company_desc=[]
    for name,x in sorted(companies.items(),key=lambda z:z[0].casefold()):
        company_rows.append([name,name,x["country"],x["sector"]])
        company_desc.append([name,f"Publicly traded {x['sector']} company headquartered in {x['country']}.",x["source"]])
    write(ROOT/"universes/sponsor_company.tsv",["value","entity","attr:country","attr:sector"],company_rows)
    write(ROOT/"universes/sponsor_company.desc.tsv",["value","description","source"],company_desc)
    print(f"country={len(cr)} university={len(ur)} sponsor_company={len(company_rows)}")

if __name__=="__main__": main()
