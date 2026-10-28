#!/usr/bin/env python3
"""Rebuild frozen public membership lists from raw table snapshots and country rosters."""
import csv, difflib, json, re, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
import yaml

ROOT=Path(__file__).resolve().parent
RAW=ROOT/"raw"

def norm(x):
    s=unicodedata.normalize("NFKD",str(x)).encode("ascii","ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def read_universe(name):
    with (ROOT/"universes"/f"{name}.tsv").open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def page_table(page, table_no, col_name, first_link_only=False):
    data=json.loads((RAW/"wiki"/(page+".json")).read_text())
    soup=BeautifulSoup(data["parse"]["text"]["*"],"lxml")
    table=soup.select("table.wikitable")[table_no-1]
    rows=table.select("tr")
    heads=[re.sub(r"\s*\[[^]]+\]", "", c.get_text(" ",strip=True)).strip() for c in rows[0].select("th,td")]
    col=next(i for i,h in enumerate(heads) if col_name.lower() in h.lower())
    out=[]
    for tr in rows[1:]:
        cells=tr.select("th,td")
        if not cells: continue
        # Tables with row-spanned country cells omit that cell on continuation rows;
        # the remaining cell is still the institution value from the selected column.
        cell=cells[col] if len(cells)>col else cells[0]
        links=[a.get_text(" ",strip=True) for a in cell.select("a") if a.get_text(" ",strip=True)
               and not re.fullmatch(r"\[\s*[A-Za-z0-9]+\s*\]",a.get_text(" ",strip=True))]
        if first_link_only: links=links[:1]
        out.extend(links or [cell.get_text(" ",strip=True)])
    return [re.sub(r"\s+"," ",x).strip() for x in out
            if x.strip() and re.sub(r"\s+"," ",x).strip().casefold() not in {"average","members","university","institution"}]

def table_links(page, table_no):
    data=json.loads((RAW/"wiki"/(page+".json")).read_text())
    soup=BeautifulSoup(data["parse"]["text"]["*"],"lxml")
    table=soup.select("table.wikitable")[table_no-1]
    return [re.sub(r"\s+"," ",a.get_text(" ",strip=True)).strip()
            for a in table.select("a") if a.get_text(" ",strip=True)]

def uni_lists():
    rows=read_universe("university")
    by_norm={}
    for r in rows:
        for x in (r["value"],r["entity"]): by_norm.setdefault(norm(x),r["value"])
    specs=[
      ("russell_group","Russell Group","Russell_Group",2,"University"),
      ("ivy_league","Ivy League","Ivy_League",1,"Institution"),
      ("c9_league","C9 League","C9_League",1,"University"),
      ("group_of_eight","Group of Eight (Australia)","Group_of_Eight_(Australia)",1,"University"),
      ("u15_canada","U15 Canada","U15_Canada",3,"Institution"),
      ("leru","League of European Research Universities","League_of_European_Research_Universities",1,"Universities"),
      ("coimbra_group","Coimbra Group","Coimbra_Group",1,"Institution"),
      ("aau","Association of American Universities","Association_of_American_Universities",3,"Institution"),
      ("universitas_21","Universitas 21","Universitas_21",1,"Institution"),
      ("cesaer","CESAER","CESAER",1,"Institution"),
      ("apru","Association of Pacific Rim Universities","Association_of_Pacific_Rim_Universities",1,"Institution"),
      ("idea_league","IDEA League","IDEA_League",1,"Institution"),
      ("golden_triangle","Golden Triangle universities","Golden_triangle_(universities)",1,"Institution"),
      ("ancient_universities","Ancient universities of Britain and Ireland","Ancient_university",1,"Name"),
      ("public_ivies","Greene and Greene (2001) Public Ivies","Public_Ivy",1,"Institution"),
    ]
    out=[]
    for lid,name,page,tno,col in specs:
        if lid=="aearu":
            data=json.loads((RAW/"wiki"/(page+".json")).read_text())
            table=BeautifulSoup(data["parse"]["text"]["*"],"lxml").select("table.wikitable")[tno-1]
            names=[]
            for tr in table.select("tr")[1:]:
                cells=tr.select("th,td")
                if cells:
                    cell=cells[1] if len(cells)==3 else cells[0]
                    names.append(re.sub(r"\s+"," ",cell.get_text(" ",strip=True)).strip())
        else:
            names=page_table(page,tno,col,first_link_only=(lid in {"coimbra_group","public_ivies"}))
            if lid=="public_ivies": names=[n for n in names if norm(n)!="usnwr public"]
        members=[]; oou=[]
        for n in names:
            key=norm(n)
            alias={"the ohio state university":norm("Ohio State University"),
                   "london school of economics":norm("London School of Economics and Political Science"),
                   "universite catholique de louvain":norm("UCLouvain"),
                   "rwth aachen":norm("RWTH Aachen University"),
                   "institut teknologi bandung":norm("Bandung Institute of Technology"),
                   "universitas airlangga":norm("Airlangga University"),
                   "universitas gadjah mada":norm("Gadjah Mada University"),
                   "universitas indonesia":norm("University of Indonesia"),
                   "university of malaya":norm("University of Malaya"),
                   "northern university of malaysia":norm("Northern University of Malaysia")}.get(key,key)
            val=by_norm.get(alias)
            if not val:
                matches=difflib.get_close_matches(key,list(by_norm),n=1,cutoff=.93)
                val=by_norm[matches[0]] if matches else None
            (members if val else oou).append(val or n)
        members=sorted(set(members),key=str.casefold); oou=sorted(set(oou),key=str.casefold)
        if len(members)<5:
            print("university-list-too-small",lid,len(members),len(oou),oou[:4]); continue
        out.append({"id":lid,"name":name,"synonyms":[],"members":members,"disputed":[],"changes":[],
          "official_count":len(members)+len(oou),"out_of_universe":oou,"salience":0,
          "source":f"Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/{page}"})
        print("university-list",lid,"table",len(names),"mapped",len(members),"oou",len(oou),"unmapped",oou[:3])
    return out

def aun_list():
    rows=read_universe("university"); by_norm={norm(r["value"]):r["value"] for r in rows}
    table=BeautifulSoup((RAW/"wiki"/"ASEAN_University_Network.json").read_text(),"lxml").select("table")[3]
    roster=["University of Brunei Darussalam","Royal University of Law and Economics","Royal University of Phnom Penh",
      "Institut Teknologi Bandung","Universitas Airlangga","Universitas Gadjah Mada","Universitas Indonesia",
      "National University of Laos","National University of Malaysia","University of Malaya","Universiti Putra Malaysia",
      "Universiti Sains Malaysia","Northern University of Malaysia","University of Mandalay","University of Yangon",
      "Yangon University of Economics","Ateneo de Manila University","De La Salle University","University of the Philippines",
      "Nanyang Technological University","National University of Singapore","Singapore Management University","Burapha University",
      "Chiang Mai University","Chulalongkorn University","Mahidol University","Prince of Songkla University","Can Tho University",
      "Vietnam National University, Hanoi","Vietnam National University, Ho Chi Minh City"]
    text=table.get_text(" ",strip=True)
    assert all(n in text for n in roster),"AUN roster names must be present in the saved core-member table"
    mapped=[];oou=[]
    aliases={"institut teknologi bandung":"bandung institute of technology","universitas airlangga":"airlangga university",
      "universitas gadjah mada":"gadjah mada university","universitas indonesia":"university of indonesia"}
    for n in roster:
        key=norm(aliases.get(norm(n),n));val=by_norm.get(key)
        if not val:
            m=difflib.get_close_matches(key,list(by_norm),n=1,cutoff=.87);val=by_norm[m[0]] if m else None
        (mapped if val else oou).append(val or n)
    mapped=sorted(set(mapped),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
    return {"id":"aun","name":"ASEAN University Network core members","synonyms":[],"members":mapped,
      "disputed":[],"changes":[],"official_count":30,"out_of_universe":oou,"salience":0,
      "source":"Wikimedia core-member roster snapshot: https://en.wikipedia.org/wiki/ASEAN_University_Network"}

COUNTRY_GROUPS={
"ehea":{"name":"European Higher Education Area members","source_page":"European_Higher_Education_Area","members":"AL AD AM AT AZ BE BA BG HR CY CZ DK EE FI FR GE DE GR HU IS IE IT KZ LV LI LT LU MT MD MC ME NL MK NO PL PT RO RU SM RS SK SI ES SE CH TR UA GB VA BY".split(),"disputed":"BY RU".split()},
"erasmus_countries":{"name":"Erasmus+ programme countries","source_page":"Erasmus_Programme","source_url":"https://erasmus-plus.ec.europa.eu/programme-guide/part-a/eligible-countries","members":"AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE IS LI NO MK RS TR".split()},
"commonwealth":{"name":"Commonwealth member countries","source_page":"Commonwealth_of_Nations","members":"AG AU BS BD BB BZ BW BN CM CA CY DM FJ GM GA GH GD GY IN JM KE KI LS MW MY MV MT MU MZ NA NR NZ NG PK PG RW KN LC VC WS SC SL SG SB ZA LK SZ TG TO TT TV UG GB VU ZM TZ".split(),"changes":[{"date":"2022-06-25","value":"GA","change":"joined"},{"date":"2022-06-25","value":"TG","change":"joined"}]},
"asean":{"name":"ASEAN member states","source_page":"ASEAN","members":"BN KH ID LA MY MM PH SG TH TL VN".split(),"disputed":"TL".split(),"changes":[{"date":"2025-10-26","value":"TL","change":"joined"}]},
"pacific_islands_forum":{"name":"Pacific Islands Forum members","source_page":"Pacific_Islands_Forum","members":"AU CK FJ PF KI MH FM NR NC NZ NU PW PG WS SB TO TV VU".split()},
"francophonie":{"name":"Francophonie member states and governments","source_page":"Organisation_internationale_de_la_Francophonie","members":"AL AD AM BE BJ BG BF BI KH CM CA CV CF TD KM CG CD CI CY DJ DM EG GQ FR GA GR GN GW HT LA LB LU MG ML MR MU MD MC MA NE MK RO RW ST SN SC CH TG TN VU VN".split()},
"african_union":{"name":"African Union member states","source_page":"African_Union","members":"DZ AO BJ BW BF BI CV CM CF TD KM CG CD CI DJ EG GQ ER SZ ET GA GM GH GN GW KE LS LR LY MG MW ML MR MU MA MZ NA NE NG RW EH ST SN SC SL SO ZA SS SD TZ TG TN UG ZM ZW".split()},
"oic":{"name":"Organisation of Islamic Cooperation member states","source_page":"Organisation_of_Islamic_Cooperation","members":"AF AL DZ AZ BH BD BJ BN BF CM TD KM CI DJ EG GA GM GN GW GY ID IR IQ JO KZ KW KG LB LY MY MV ML MR MA MZ NE NG OM PK PS QA SA SN SL SO SD SR SY TJ TG TN TR TM UG AE UZ YE".split()},
"arab_league":{"name":"Arab League member states","source_page":"Arab_League","members":"DZ BH KM DJ EG IQ JO KW LB LY MR MA OM PS QA SA SO SD SY TN AE YE".split()},
"g20":{"name":"G20 members","source_page":"G20","members":"AR AU BR CA CN FR DE IN ID IT JP MX RU SA ZA KR TR GB US".split(),"out_of_universe":["European Union","African Union"]},
"g7":{"name":"G7 members","source_page":"G7","members":"CA FR DE IT JP GB US".split()},
"caricom":{"name":"Caribbean Community full members","source_page":"Caribbean_Community","members":"AG BS BB BZ DM GD GY HT JM MS KN LC VC SR TT".split()},
"cplp":{"name":"Community of Portuguese Language Countries members","source_page":"Community_of_Portuguese_Language_Countries","members":"AO BR CV GQ GW MZ PT ST TL".split()},
"nato":{"name":"NATO member states","source_page":"NATO","members":"AL BE BG CA HR CZ DK EE FI FR DE GR HU IS IT LV LT LU ME NL MK NO PL PT RO SK SI ES SE TR GB US".split(),"disputed":"FI SE".split(),"changes":[{"date":"2023-04-04","value":"FI","change":"joined"},{"date":"2024-03-07","value":"SE","change":"joined"}]},
"oecd":{"name":"OECD member countries","source_page":"OECD","members":"AU AT BE CA CL CO CR CZ DK EE FI FR DE GR HU IS IE IL IT JP KR LV LT LU MX NL NZ NO PL PT SK SI ES SE CH TR GB US".split()},
}

def country_lists():
    codes={r["value"] for r in read_universe("country")}; out=[]
    for lid,g in COUNTRY_GROUPS.items():
        full=list(dict.fromkeys(g["members"])); disputed=list(g.get("disputed",[]))
        oou=list(g.get("out_of_universe",[])); members=[]
        for c in full:
            if c not in codes: oou.append(c)
            elif c not in disputed: members.append(c)
        out.append({"id":lid,"name":g["name"],"synonyms":[],"members":sorted(members),
          "disputed":sorted(disputed),"changes":g.get("changes",[]),"official_count":len(full)+len(g.get("out_of_universe",[])),
          "out_of_universe":sorted(oou),"salience":0,
          "source":g.get("source_url") or f"Public roster snapshot: https://en.wikipedia.org/wiki/{g['source_page']}"})
    return out

def company_lists():
    rows=read_universe("sponsor_company"); by_norm={norm(r["value"]):r["value"] for r in rows}
    company_aliases={
      "alphabet":"Alphabet Inc.","apple":"Apple Inc.","caterpillar":"Caterpillar Inc.",
      "chevron":"Chevron Corporation","coca cola":"Coca-Cola Company (The)",
      "disney":"Walt Disney Company (The)","home depot":"Home Depot (The)",
      "merck":"Merck & Co.","nike":"Nike, Inc.","travelers":"Travelers Companies (The)",
      "visa":"Visa Inc.","meta":"Meta Platforms","eli lilly":"Eli Lilly and Company","asml":"ASML Holding",
      "roche":"Roche Holding AG","toyota":"Toyota Motor Corporation","tsmc":"Taiwan Semiconductor Manufacturing Company",
      "samsung electronics":"Samsung Electronics Co., Ltd.","royal bank of canada":"Royal Bank of Canada",
      "jp morgan chase":"JPMorgan Chase & Co.","goldman sachs group":"Goldman Sachs Group, Inc.",
      "toronto dominion bank":"Toronto-Dominion Bank (The)","bank of america":"Bank of America Corporation",
      "citigroup":"Citigroup Inc.","deutsche bank":"Deutsche Bank Aktiengesellschaft","ubs":"UBS Group AG"}
    company_aliases.update({"google":"Alphabet Inc.","samsung":"Samsung Electronics Co., Ltd.",
      "toyota":"Toyota Motor Corporation","instagram":"Meta Platforms","mercedes benz":"Mercedes-Benz Group"})
    alias_norm={norm(k):norm(v) for k,v in company_aliases.items()}
    def resolve_company(n):
        k=norm(n)
        val=by_norm.get(k)
        if val: return val
        k=alias_norm.get(k,k)
        val=by_norm.get(k)
        if not val:
            m=difflib.get_close_matches(k,list(by_norm),n=1,cutoff=.91);val=by_norm[m[0]] if m else None
        return val
    ticker_to_company={}
    def remember_ticker(ticker,name):
        val=resolve_company(name)
        if ticker and val: ticker_to_company.setdefault(norm(ticker),val)
    with (RAW/"sp500.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f): remember_ticker(r.get("Symbol"),r.get("Security"))
    for page,table_no,name_col in [("EURO_STOXX_50",3,"Name"),("STOXX_Europe_600",2,"Company")]:
        soup=BeautifulSoup(json.loads((RAW/"wiki"/(page+".json")).read_text())["parse"]["text"]["*"],"lxml")
        table=soup.select("table.wikitable")[table_no-1]
        for tr in table.select("tr")[1:]:
            cells=tr.select("th,td")
            if len(cells)<2: continue
            headers=[norm(c.get_text(" ",strip=True)) for c in table.select("tr")[0].select("th,td")]
            row={h:cells[i].get_text(" ",strip=True) for i,h in enumerate(headers[:len(cells)])}
            remember_ticker(row.get("ticker"),row.get(norm(name_col)))
    specs=[("euro_stoxx_50","EURO STOXX 50","EURO_STOXX_50",3,"Name"),
           ("stoxx_europe_600","STOXX Europe 600","STOXX_Europe_600",2,"Company"),
           ("euronext_100","Euronext 100","Euronext_100",2,"Name"),
           ("ftse_100","FTSE 100","FTSE_100_Index",4,"Company"),
           ("dow_jones","Dow Jones Industrial Average","List_of_Dow_Jones_Industrial_Average_companies",1,"Company"),
           ("omx_nordic_40","OMX Nordic 40","OMX_Nordic_40",1,"Company")]
    out=[]
    for lid,name,page,tno,col in specs:
        try: names=page_table(page,tno,col)
        except Exception as e: print("company-source-unavailable",lid,type(e).__name__); continue
        members=[]; oou=[]
        for n in names:
            val=resolve_company(n)
            (members if val else oou).append(val or n)
        members=sorted(set(members),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
        if len(members)<5: print("company-list-too-small",lid,len(members),oou[:3]);continue
        out.append({"id":lid,"name":name,"synonyms":[],"members":members,"disputed":[],"changes":[],
          "official_count":len(members)+len(oou),"out_of_universe":oou,"salience":0,
          "source":f"Current constituent snapshot: https://en.wikipedia.org/wiki/{page}"})
        print("company-list",lid,"listed",len(names),"mapped",len(members),"oou",len(oou))
    # S&P 500 membership is taken directly from the raw constituent file used for the company universe.
    with (RAW/"sp500.csv").open(encoding="utf-8-sig",newline="") as f:
        names=[r["Security"] for r in csv.DictReader(f)]
    canonical=[re.sub(r"\s+\(Class [A-Z]\)$", "", n) for n in names]
    members=sorted({resolve_company(n) for n in canonical if resolve_company(n)},key=str.casefold)
    sp_oou=sorted({n for n in canonical if not resolve_company(n)},key=str.casefold)
    out.append({"id":"sp500","name":"S&P 500 constituents","synonyms":[],"members":members,
        "disputed":[],"changes":[],"official_count":len(set(canonical)),"out_of_universe":sp_oou,"salience":0,
      "source":"datasets/s-and-p-500-companies raw constituents.csv"})
    # Nasdaq's public screener provides the dated Nasdaq-100 component securities.
    nd=json.loads((RAW/"nasdaq100-20261016.json").read_text())
    nasdaq_rows=nd["data"]["data"]["rows"]
    def nasdaq_company_name(name):
        x=re.sub(r"\s+(?:Common Stock|Capital Stock|American Depositary Shares|New York Registry Shares|Ordinary Shares|Common Shares)(?:\s*\([^)]*\))?\s*$","",name,flags=re.I).strip()
        x=re.sub(r"\s+(?:[-–]\s*)?Class\s+[A-Z]\s*$","",x,flags=re.I).strip()
        return re.sub(r"\s*\([^)]*\)$","",x).strip()
    canonical=[nasdaq_company_name(r["companyName"]) for r in nasdaq_rows]
    resolved=[ticker_to_company.get(norm(r["symbol"])) or resolve_company(n) for r,n in zip(nasdaq_rows,canonical)]
    members=sorted({v for v in resolved if v},key=str.casefold)
    nd_oou=sorted({n for n,v in zip(canonical,resolved) if not v},key=str.casefold)
    out.append({"id":"nasdaq_100","name":"Nasdaq-100 constituents","synonyms":[],"members":members,
        "disputed":[],"changes":[],"official_count":len(set(canonical)),"out_of_universe":nd_oou,"salience":0,
        "source":"Nasdaq public list screener snapshot (2026-10-22): https://api.nasdaq.com/api/quote/list-type/nasdaq100?limit=100"})
    # Global Titans 50 has a two-row table header; the body is a direct list of current components.
    p=RAW/"wiki"/"Dow_Jones_Global_Titans_50.json"
    if p.exists():
        soup=BeautifulSoup(json.loads(p.read_text())["parse"]["text"]["*"],"lxml")
        table=soup.select("table.wikitable")[0]
        names=[r.select("td")[1].get_text(" ",strip=True) for r in table.select("tr") if len(r.select("td"))>=2]
        members=[];oou=[]
        for n in names:
            v=resolve_company(n)
            (members if v else oou).append(v or n)
        members=sorted(set(members),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
        if len(members)>=5:
            out.append({"id":"dow_global_titans","name":"Dow Jones Global Titans 50","synonyms":[],"members":members,
             "disputed":[],"changes":[],"official_count":len(members)+len(oou),"out_of_universe":oou,"salience":0,
             "source":"Current component table: https://en.wikipedia.org/wiki/Dow_Jones_Global_Titans_50"})
            print("company-list dow_global_titans",len(names),len(members),len(oou))
    gsib=RAW/"wiki"/"List_of_systemically_important_banks.json"
    if gsib.exists():
        soup=BeautifulSoup(json.loads(gsib.read_text())["parse"]["text"]["*"],"lxml")
        tables=soup.select("table.wikitable"); table=tables[1]
        names=["JP Morgan Chase","Bank of America","Citigroup","HSBC","ICBC",
          "Agricultural Bank of China","Bank of China","Barclays","BNP Paribas","China Construction Bank",
          "Goldman Sachs Group","Crédit Agricole","MUFG","UBS","Bank of Communications (BoCom)",
          "Bank of New York Mellon","Deutsche Bank","Groupe BPCE","ING","Mizuho FG","Morgan Stanley",
          "Royal Bank of Canada","Banco Santander","Société Générale","Standard Chartered","State Street",
          "Sumitomo Mitsui","Toronto-Dominion Bank","Wells Fargo"]
        table_text=table.get_text(" ",strip=True)
        assert all(n.split(" (BoCom)")[0] in table_text for n in names),"G-SIB names must come from the saved 2025 table"
        members=[];oou=[]
        for n in names:
            val=resolve_company(n)
            (members if val else oou).append(val or n)
        members=sorted(set(members),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
        out.append({"id":"g_sib","name":"2025 Financial Stability Board global systemically important banks",
          "synonyms":["G-SIBs"],"members":members,"disputed":[],"changes":[],"official_count":29,
          "out_of_universe":oou,"salience":0,
          "source":"2025 G-SIB table snapshot: https://en.wikipedia.org/wiki/List_of_systemically_important_banks"})
        print("company-list g_sib",len(names),len(members),len(oou))
    # Fortune's 2026 Global 500 membership is published as a complete JSON-LD ItemList.
    fortune=RAW/"fortune-global500-2026.html"
    if fortune.exists():
        soup=BeautifulSoup(fortune.read_bytes(),"lxml")
        names=[]
        for script in soup.select('script[type="application/ld+json"]'):
            try: obj=json.loads(script.string or script.get_text())
            except (json.JSONDecodeError,TypeError): continue
            if isinstance(obj,dict) and isinstance(obj.get("itemListElement"),list):
                names=[x.get("item",{}).get("name","") for x in obj["itemListElement"]]
                if len(names)==500: break
        assert len(names)==500, "Fortune Global 500 snapshot must contain 500 entries"
        members=[];oou=[]
        for n in names:
            # Fortune includes Deutsche Bahn, a state-owned railway group rather than a listed issuer;
            # the generic fuzzy matcher otherwise incorrectly maps it to Deutsche Bank.
            val=None if norm(n)=="deutsche bahn" else resolve_company(n)
            (members if val else oou).append(val or n)
        members=sorted(set(members),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
        out.append({"id":"fortune_global_500","name":"Fortune Global 500","synonyms":[],"members":members,
          "disputed":[],"changes":[],"official_count":500,"out_of_universe":oou,"salience":0,
          "source":"Fortune Global 500 (2026 edition, published 2026-07-28): https://fortune.com/ranking/global500/"})
        print("company-list fortune_global_500",len(names),"mapped",len(members),"oou",len(oou))
    # Interbrand's official 2025 landing page embeds the top ten names in its page data.
    interbrand=RAW/"interbrand-best-global-brands-2025.html"
    if interbrand.exists():
        soup=BeautifulSoup(interbrand.read_bytes(),"lxml")
        next_data=json.loads(soup.select_one("#__NEXT_DATA__").string)
        names=[x["brandName"] for x in next_data["props"]["pageProps"]["data"]["brandData"] if x.get("year")==2025]
        assert len(names)==10, "Interbrand 2025 page must expose the ten listed brands"
        members=[];oou=[]
        for n in names:
            val=resolve_company(n)
            (members if val else oou).append(val or n)
        members=sorted(set(members),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
        out.append({"id":"interbrand_top10_2025","name":"Interbrand Best Global Brands top 10 (2025)","synonyms":[],
          "members":members,"disputed":[],"changes":[],"official_count":10,"out_of_universe":oou,"salience":0,
          "source":"Interbrand Best Global Brands 2025 landing page: https://interbrand.com/best-global-brands/"})
        print("company-list interbrand_top10_2025",len(names),"mapped",len(members),"oou",len(oou))
    return out

def official_university_lists():
    rows=read_universe("university"); by_norm={}
    for r in rows:
        for x in (r["value"],r["entity"]):by_norm.setdefault(norm(x),r["value"])
    out=[]
    specs=[("big_ten","Big Ten Academic Alliance","btaa.html","https://btaa.org/about/member-universities",18),
           ("utrecht_network","Utrecht Network","utrecht.html","https://utrecht-network.org/members/",31)]
    for lid,name,file,url,count in specs:
        soup=BeautifulSoup((RAW/"official-university"/file).read_bytes(),"lxml")
        names=[h.get_text(" ",strip=True) for h in soup.select("h3")]
        # Exclude page section headings by matching institution names against the value universe.
        mapped=[];oou=[]
        for n in names:
            key=norm(n);val=by_norm.get(key)
            if not val:
                aliases={"ohio state university":norm("The Ohio State University"),
                         "university of california los angeles":norm("University of California, Los Angeles")}
                val=by_norm.get(aliases.get(key,key))
            if not val:
                m=difflib.get_close_matches(key,list(by_norm),n=1,cutoff=.89);val=by_norm[m[0]] if m else None
            (mapped if val else oou).append(val or n)
        mapped=sorted(set(mapped),key=str.casefold);oou=sorted(set(oou),key=str.casefold)
        if len(mapped)>=5:
            out.append({"id":lid,"name":name,"synonyms":[],"members":mapped,"disputed":[],"changes":[],
             "official_count":len(mapped)+len(oou),"out_of_universe":oou,"salience":0,"source":url})
            print("official-university-list",lid,"source names",len(names),"members",len(mapped),"oou",len(oou))
    return out

def additional_university_lists():
    rows=read_universe("university"); by_norm={}
    for r in rows:
        for x in (r["value"],r["entity"]): by_norm.setdefault(norm(x),r["value"])
    specs=[("matariki","Matariki Network of Universities","Matariki_Network_of_Universities",1,"Members"),
           ("worldwide_universities_network","Worldwide Universities Network","Worldwide_Universities_Network",1,"Institution"),
           ("aearu","Association of East Asian Research Universities","Association_of_East_Asian_Research_Universities",1,"Universities"),
           ("iaru","International Alliance of Research Universities","International_Alliance_of_Research_Universities",0,""),
           ("asian_universities_alliance","Asian Universities Alliance","Asian_Universities_Alliance",1,"Member Institution")]
    out=[]
    for lid,name,page,tno,col in specs:
        if lid=="iaru":
            data=json.loads((RAW/"wiki"/(page+".json")).read_text())
            soup=BeautifulSoup(data["parse"]["text"]["*"],"lxml")
            heading=next(h for h in soup.select("h2,h3") if "institution" in h.get_text(" ",strip=True).casefold())
            listing=heading.find_next("ul")
            names=[re.sub(r"\s+"," ",li.get_text(" ",strip=True)).strip() for li in listing.select("li")]
        elif lid=="aearu":
            data=json.loads((RAW/"wiki"/(page+".json")).read_text())
            table=BeautifulSoup(data["parse"]["text"]["*"],"lxml").select("table.wikitable")[tno-1]
            names=[]
            for tr in table.select("tr")[1:]:
                cells=tr.select("th,td")
                if cells:
                    cell=cells[1] if len(cells)==3 else cells[0]
                    names.append(re.sub(r"\s+"," ",cell.get_text(" ",strip=True)).strip())
        else:
            names=page_table(page,tno,col)
        members=[]; oou=[]
        for n in names:
            key=norm(n); val=by_norm.get(key)
            if not val:
                matches=difflib.get_close_matches(key,list(by_norm),n=1,cutoff=.93)
                val=by_norm[matches[0]] if matches else None
            (members if val else oou).append(val or n)
        members=sorted(set(members),key=str.casefold); oou=sorted(set(oou),key=str.casefold)
        if len(members)>=5:
            out.append({"id":lid,"name":name,"synonyms":[],"members":members,"disputed":[],"changes":[],
              "official_count":len(members)+len(oou),"out_of_universe":oou,"salience":0,
              "source":f"Wikimedia membership table snapshot: https://en.wikipedia.org/wiki/{page}"})
            print("additional-university-list",lid,"listed",len(names),"mapped",len(members),"oou",len(oou))
    return out

def write_lists(name,items):
    (ROOT/"lists").mkdir(exist_ok=True)
    (ROOT/"lists"/f"{name}.yaml").write_text(yaml.safe_dump(items,allow_unicode=True,sort_keys=False),encoding="utf-8")

def main():
    u=uni_lists()+official_university_lists()+additional_university_lists()+[aun_list()];c=country_lists();s=company_lists()
    write_lists("university",u);write_lists("country",c);write_lists("sponsor_company",s)
    print("list-counts",len(u),len(c),len(s))
if __name__=="__main__":main()
