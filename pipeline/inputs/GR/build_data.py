#!/usr/bin/env python3
"""Build GR universes, descriptive references, membership lists, and row-level spot checks from raw snapshots."""
import csv, json, re, unicodedata
import html
from urllib.parse import urlparse
from collections import defaultdict
from pathlib import Path
from bs4 import BeautifulSoup
import yaml

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'

def readj(p): return json.loads((RAW/p).read_text(encoding='utf-8'))
def qid(x): return x.rsplit('/',1)[-1]
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    return ''.join(c for c in s if c.isalnum())

def continent_maps():
    a=readj('iso3166-1_pycountry.json')['3166-1']
    code_name={x['alpha_2']:x['name'] for x in a}
    name_code={norm(x['name']):x['alpha_2'] for x in a}
    # ISO data alternate names
    alias={'unitedstatesofamerica':'US','unitedstates':'US','peoplesrepublicofchina':'CN','china':'CN',
           'russianfederation':'RU','russia':'RU','republicofkorea':'KR','southkorea':'KR','northkorea':'KP',
           'bolivarianrepublicofvenezuela':'VE','venezuela':'VE','iranislamicrepublicof':'IR','iran':'IR',
           'syrianarabrepublic':'SY','syria':'SY','vietnamsocialistrepublic':'VN','vietnam':'VN',
           'democraticrepublicofthecongo':'CD','drcongo':'CD','congo':'CG','cotedivoire':'CI',
           'ivorycoast':'CI','tanzaniaunitedrepublicof':'TZ','tanzania':'TZ','moldovarepublicof':'MD',
           'moldova':'MD','laopeoplesdemocraticrepublic':'LA','laos':'LA','bruneidarussalam':'BN',
           'brunei':'BN','syrianarabrepublic':'SY','palestine':'PS','stateofpalestine':'PS',
           'turkiye':'TR','turkey':'TR','capeverde':'CV','cabo Verde'.lower().replace(' ',''):'CV',
           'eswatini':'SZ','swaziland':'SZ','northmacedonia':'MK','macedonia':'MK',
           'micronesiafederatedstatesof':'FM','federatedstatesofmicronesia':'FM','palestinianterritories':'PS',
           'czechrepublic':'CZ','thebahamas':'BS','bahamas':'BS','thegambia':'GM','gambia':'GM',
           'unitedkingdom':'GB','timorleste':'TL','easttimor':'TL','republicofthecongo':'CG',
           'sao tome and principe'.replace(' ',''):'ST','sao tome and principe':'ST'}
    alias.update({'congothe':'CG','republicofthecongo':'CG','democraticrepublicofthecongo':'CD',
                  'western sahara'.replace(' ',''):'EH','sahrawiarabdemocraticrepublic':'EH',
                  'theformer yugoslavrepublicofmacedonia'.replace(' ', ''):'MK',
                  'czechia':'CZ','republicofkosovo':'XK','bahamasthe':'BS','bolivia':'BO',
                  'democraticpeoplesrepublicofkorea':'KP','gambiarepublicofthe':'GM','naoero':'NR',
                  'republicofmoldova':'MD','unitedkingdomofgreatbritainandnorthernireland':'GB',
                  'unitedrepublicoftanzania':'TZ','brunei':'BN','moldova':'MD','iran':'IR','venezuela':'VE',
                  'congorepublic':'CG','drcongo':'CD','sahrawirepublic':'EH','tanzania':'TZ'})
    name_code.update(alias)
    qcode={}; ccode={}
    rows=readj('country_continents_wikidata.json')['results']['bindings']
    for i,r in enumerate(rows):
        c=r['code']['value'].upper()
        if c in code_name:
            qcode[qid(r['country']['value'])]=c
            ccode[c]=r['continentLabel']['value']
    return a,code_name,name_code,qcode,ccode

COUNTRIES,COUNTRY_NAME,COUNTRY_CODE,COUNTRY_QID,CONTINENT=continent_maps()

def write_tsv(path, headers, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(headers); w.writerows(rows)

def current_entity_rows(file):
    rows=readj(file)['results']['bindings']; out={}
    for r in rows:
        if 'itemLabel' not in r: continue
        value=r['itemLabel']['value'].strip(); ident=qid(r['item']['value'])
        if not value or re.fullmatch(r'Q[0-9]+',value): continue
        country=r.get('countryLabel',{}).get('value','').strip()
        code=COUNTRY_CODE.get(norm(country),'')
        continent=CONTINENT.get(code,'?') if code else '?'
        desc=r.get('itemDescription',{}).get('value','').strip()
        q='http://www.wikidata.org/entity/'+ident
        # Resolve duplicate labels deterministically, retaining one entity if it is the same public name.
        if value not in out or ident < out[value]['qid']:
            out[value]={'qid':ident,'country':COUNTRY_NAME.get(code,'?') if code else '?','continent':continent,'desc':desc}
    return out

AIR=current_entity_rows('airlines_active_described.json')
# Add directly rostered current carriers omitted by the broad result limit, enriching each from a batched Wikidata query.
_norm_air={norm(x) for x in AIR}
for r in readj('roster_airlines_described.json')['results']['bindings']:
    value=r.get('name',{}).get('value','').strip()
    if not value or re.fullmatch(r'Q[0-9]+',value) or norm(value) in _norm_air: continue
    ident=qid(r['item']['value']); country=r.get('countryLabel',{}).get('value','').strip(); code=COUNTRY_CODE.get(norm(country),'')
    AIR[value]={'qid':ident,'country':COUNTRY_NAME.get(code,'?') if code else '?','continent':CONTINENT.get(code,'?') if code else '?','desc':r.get('description',{}).get('value','').strip()}
    _norm_air.add(norm(value))
UNI=current_entity_rows('universities_described.json')
# Include universities in the directly queried public membership snapshots so every roster member has a universe row.
for r in readj('target_group_entities_described.json')['results']['bindings']:
    org=qid(r.get('org',{}).get('value',''))
    if org not in {'Q868940','Q297575','Q743812','Q1074688','Q593768','Q211620','Q1152269','Q1047645','Q2634906','Q590631','Q5463432','Q1140056','Q49113','Q1377311','Q1202548'}: continue
    if 'itemLabel' not in r: continue
    value=r['itemLabel']['value'].strip(); ident=qid(r['item']['value'])
    if not value or re.fullmatch(r'Q[0-9]+',value): continue
    country=r.get('countryLabel',{}).get('value','').strip(); code=COUNTRY_CODE.get(norm(country),'')
    if value and value not in UNI:
        UNI[value]={'qid':ident,'country':COUNTRY_NAME.get(code,'?') if code else '?','continent':CONTINENT.get(code,'?') if code else '?','desc':r.get('itemDescription',{}).get('value','').strip()}

for uname,items,attr in [('country',None,None),('airline',AIR,None),('university',UNI,None)]:
    pass

def save_universe(name,items):
    rows=[]
    desc=[]
    seen=set()
    for value,rec in sorted(items.items(),key=lambda kv:kv[0].casefold()):
        if value in seen: continue
        seen.add(value)
        entity=value
        country=rec.get('country','?') or '?'; continent=rec.get('continent','?') or '?'
        q=rec.get('qid','')
        if name=='country': entity=country
        rows.append([value,entity,q,'',country,continent])
        d=rec.get('desc','').strip()
        # Use a source-backed, informative fallback and remove any member-list references.
        if name=='country': d=f"Sovereign state or territory in {continent}." if continent!='?' else "ISO 3166-1 country or territory."
        elif not d or any(tok in norm(d) for tok in ('russellgroup','ivyleague','groupofeight','c9league','u15','leru','apru','aseanuniversitynetwork','n8research','iaru','idealeague','staralliance','skyteam','oneworld','iata','afraa','aaco','alta','lufthansagroup','internationalairlinesgroup','tui','airfranceklm','qantasgroup')):
            kind='Airline' if name=='airline' else 'University'
            where=country if country!='?' else continent
            d=f"{kind} based in {where}." if where!='?' else f"Operating {kind.lower()} service."
        if d and sum(ch.isascii() for ch in d)<0.9*len(d):
            kind='Airline' if name=='airline' else 'University'
            where=country if country!='?' else continent
            d=f"{kind} based in {where}." if where!='?' else f"Operating {kind.lower()} service."
        if d:
            d=d[0].upper()+d[1:]
            if d[-1] not in '.!?':d+='.'
        if len(d)>200: d=d[:197].rsplit(' ',1)[0]+'.'
        desc.append([value,d,'Wikidata '+q if q else ('public airline roster snapshot' if name=='airline' else ('Wikidata query snapshot' if name=='university' else 'ISO 3166-1'))])
    headers=['value','entity','qid','aliases','attr:continent'] if name=='country' else ['value','entity','qid','aliases','attr:country','attr:continent']
    if name=='country': rows=[[r[0],r[1],r[2],r[3],r[5]] for r in rows]
    write_tsv(ROOT/'universes'/f'{name}.tsv',headers,rows)
    write_tsv(ROOT/'universes'/f'{name}.desc.tsv',['value','description','source'],desc)

country_items={}
for c in COUNTRIES:
    code=c['alpha_2']; country_items[code]={'qid':next((q for q,v in COUNTRY_QID.items() if v==code),''),'country':c['name'],'continent':CONTINENT.get(code,'?'),'desc':''}
save_universe('country',country_items)
save_universe('airline',AIR)
save_universe('university',UNI)

# alias resolution from source roster spelling to the universe's common value.
def make_matcher(items, aliases=None):
    by={norm(k):k for k in items}; aliases=aliases or {}
    def match(v):
        if v in items:return v
        n=norm(v)
        if n in by:return by[n]
        alt=aliases.get(n)
        if alt:
            if alt in items:return alt
            if norm(alt) in by:return by[norm(alt)]
        return None
    return match
AIR_ALIAS={norm(a):b for a,b in {
    'ANA':'All Nippon Airways','THAI Airways':'Thai Airways International','THAI':'Thai Airways International',
    'SWISS':'Swiss International Air Lines','EgyptAir':'EgyptAir','Eva Air':'EVA Air','China Eastern':'China Eastern Airlines',
    'Aeromexico':'Aeroméxico','SAS':'Scandinavian Airlines','XiamenAir':'XiamenAir','Aeroflot [suspended]':'Aeroflot',
    'Alaska Airlines':'Alaska Airlines','Air Algerie':'Air Algérie','BOA Boliviana de Aviacion':'Boliviana de Aviación',
    'Gol':'GOL Linhas Aéreas','InterCaribbean':'InterCaribbean Airways','JetSMART Airlines':'JetSMART',
    'SANSA':'SANSA Airlines','TAAG Linhas Aereas DE Angola, SA':'TAAG Angola Airlines','Emirates Airlines':'Emirates',
    'UPS':'UPS Airlines','FedEx':'FedEx Express','Southwest':'Southwest Airlines','Avianca':'Avianca','El Al':'EL AL',
    'Korean Air':'Korean Air','Cebgo':'Cebgo','United':'United Airlines','KLM Royal Dutch Airlines':'KLM'
}.items()}
match_air=make_matcher(AIR,AIR_ALIAS)
match_uni=make_matcher(UNI)

# Map ID -> labels/rows for membership-source snapshots.
target=readj('target_org_memberships.json')['results']['bindings']
source_air=readj('airline_affiliations_wikidata.json')['results']['bindings']
source_uni=readj('university_affiliations_wikidata.json')['results']['bindings']

def country_group(q):
    vals=[]
    for r in target:
        if qid(r['org']['value'])!=q: continue
        code=COUNTRY_QID.get(qid(r['item']['value']))
        if code: vals.append(code)
    return sorted(set(vals))

def country_codes_from_cell(cell, all_links=False):
    links=[a for a in cell.select('a') if a.get_text(' ',strip=True)]
    names=[a.get_text(' ',strip=True) for a in (links if all_links else links[:1])]
    if not names:
        names=[cell.get_text(' ',strip=True)]
    codes=[]
    for name in names:
        name=re.sub(r'\s*\[[^]]*\]', '', name).replace('(suspended)','').strip()
        code=COUNTRY_CODE.get(norm(name))
        if code: codes.append(code)
    return sorted(set(codes))

def country_source_roster(filename):
    p=RAW/'country_sources'/filename
    soup=BeautifulSoup(p.read_bytes(),'lxml')
    tables=soup.select('table')
    if filename=='european_union.html':
        return sorted({c for row in tables[2].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='schengen_area.html':
        return sorted({c for row in tables[2].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='nato.html':
        return country_codes_from_cell(tables[2].select('tr')[1].select('td')[0],all_links=True)
    if filename=='oecd.html':
        return sorted({c for row in tables[6].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='commonwealth.html':
        for row in tables[6].select('tr'):
            cells=row.select('th,td')
            if len(cells)>1 and cells[0].get_text(' ',strip=True)=='Sovereign states (members)':
                return country_codes_from_cell(cells[1],all_links=True)
    if filename=='african_union_official.html':
        out=[]
        for table in tables:
            for row in table.select('tr'):
                cells=row.select('th,td')
                if len(cells)>1: out.extend(country_codes_from_cell(cells[1]))
        return sorted(set(out))
    if filename=='asean.html':
        return sorted({c for row in tables[3].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell,all_links=True)})
    if filename=='opec.html':
        return sorted({c for row in tables[2].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='council_of_europe_members.html':
        return sorted({c for row in tables[0].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='un_members.html':
        return sorted({c for row in tables[1].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='g20.html':
        return sorted({c for row in tables[2].select('tr')[1:] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='gulf_cooperation_council.html':
        return sorted({c for row in tables[3].select('tr')[2:-1] for cell in row.select('th,td')[:1] for c in country_codes_from_cell(cell)})
    if filename=='pacific_islands_forum.html':
        out=[]
        for row in tables[1].select('tr')[2:7]:
            for cell in row.select('th,td'):
                out.extend(re.findall(r'\(([A-Z]{2})\)',cell.get_text(' ',strip=True)))
        return sorted(set(out))
    raise ValueError(f'no country roster parser for {filename}')

def query_group(rows,q,matcher):
    ret=[]
    for r in rows:
        if qid(r['org']['value'])!=q: continue
        n=matcher(r.get('itemLabel',{}).get('value',''))
        if n: ret.append(n)
    return sorted(set(ret))

def page_group(items, matcher):
    vals=[]
    for rawname in items:
        v=matcher(rawname)
        if v: vals.append(v)
    return sorted(set(vals))

def add_list(out,lid,name,items,official_count,source,synonyms=None,disputed=(),source_kind=''):
    members=sorted(set(items)-set(disputed))
    disputed=sorted(set(disputed)&set(items))
    missing=[]
    # The caller has already passed values matched to the universe; official count reflects source's full row count.
    if len(members)+len(disputed)>official_count: official_count=len(members)+len(disputed)
    out.append({'id':lid,'name':name,'synonyms':synonyms or [],'members':members,'disputed':disputed,'changes':[],
                'official_count':int(official_count),'out_of_universe':missing,'source':source,'salience':0})

def build_country_lists():
    specs=[
      ('eu_members','European Union member states',['European Union','EU'],'european_union.html'),
      ('schengen_members','Schengen Area member states',['Schengen Area','Schengen'],'schengen_area.html'),
      ('nato_members','NATO member countries',['NATO'],'nato.html'),
      ('oecd_members','OECD member countries',['OECD'],'oecd.html'),
      ('commonwealth_members','Commonwealth of Nations members',['Commonwealth'],'commonwealth.html'),
      ('african_union_members','African Union member states',['African Union','AU'],'african_union_official.html'),
      ('asean_members','ASEAN member states',['ASEAN'],'asean.html'),
      ('opec_members','OPEC member countries',['OPEC'],'opec.html'),
      ('council_of_europe_members','Council of Europe member states',['Council of Europe'],'council_of_europe_members.html'),
      ('un_members','United Nations member states',['United Nations','UN'],'un_members.html'),
      ('g20_members','G20 member countries',['G20','Group of Twenty'],'g20.html'),
      ('gcc_members','Gulf Cooperation Council member states',['Gulf Cooperation Council','GCC'],'gulf_cooperation_council.html'),
      ('pif_members','Pacific Islands Forum member countries',['Pacific Islands Forum','PIF'],'pacific_islands_forum.html')]
    out=[]
    for lid,name,syn,filename in specs:
        members=country_source_roster(filename); disputed=[]; changes=[]
        if lid=='nato_members' and 'SE' in members: disputed=['SE']; changes=[{'value':'SE','date':'2024-03-07','event':'joined'}]
        if lid=='schengen_members':
            disputed=[v for v in ('BG','RO') if v in members]
            changes=[{'value':v,'date':'2025-01-01','event':'full entry into Schengen Area'} for v in disputed]
        if lid=='asean_members' and 'TL' in members: disputed=['TL']; changes=[{'value':'TL','date':'2025-10-26','event':'joined'}]
        if lid=='opec_members':
            if 'AE' in members: disputed.append('AE'); changes.append({'value':'AE','date':'2026','event':'announced exit; recent status disputed'})
            # Angola's 2024 departure is within three years of the snapshot.
            members=sorted(set(members)|{'AO'})
            disputed.append('AO'); changes.append({'value':'AO','date':'2024-01-01','event':'left'})
        src=f"Public member roster table; raw/country_sources/{filename}"
        official=len(set(members))
        add_list(out,lid,name,members,official,src,syn,disputed)
        if lid=='g20_members':
            out[-1]['official_count']=21
            out[-1]['out_of_universe']=['African Union','European Union']
        out[-1]['changes']=changes; out[-1]['_rawfile']=f'raw/country_sources/{filename}'
    # The Arab League roster is the complete organization-filtered Wikidata membership snapshot.
    arab=country_group('Q7172')
    add_list(out,'arab_league_members','Arab League member states',arab,len(arab),
             'Wikidata P463 Q7172 membership snapshot; raw/target_org_memberships.json',['Arab League'])
    out[-1]['_source_qid']='Q7172'; out[-1]['_source_org_label']='Arab League member states'; out[-1]['_rawfile']='raw/target_org_memberships.json'
    # The current members table includes seven sovereign states and the EU as a separate participant.
    g7=['CA','FR','DE','IT','JP','GB','US']
    add_list(out,'g7_members','Group of Seven members',g7,7,'Group of Seven member countries table; raw/country_sources/group_of_seven.html',['G7','Group of Seven'])
    out[-1]['_rawfile']='raw/country_sources/group_of_seven.html#table 2'
    out[-1]['_source_table']='Group of Seven members table'
    return out

# Parse direct, complete airline rosters captured from association and carrier pages.
def airline_rosters():
    b=RAW/'airline_sources'; lists={}
    # Star Alliance official keywords contain its complete roster.
    s=BeautifulSoup((b/'star_alliance.html').read_bytes(),'lxml')
    kw=next((m.get('content','') for m in s.find_all('meta') if m.get('name')=='keywords'),'')
    items=[]
    if kw:
        tail=kw.split('Star Alliance Members,',1)[-1]
        names=tail.split(',')
        for x in names:
            x=x.strip()
            if x.startswith('Star Alliance network'): break
            if x and norm(x) not in {'staralliancememberairlines','staralliancemembercarriers'}: items.append(x)
    lists['star_alliance_members']=items
    s=BeautifulSoup((b/'skyteam.html').read_bytes(),'lxml')
    lists['skyteam_members']=[h.get_text(' ',strip=True) for h in s.select('h3')]
    s=BeautifulSoup((b/'oneworld.html').read_bytes(),'lxml')
    slugs=[]
    for a in s.select('a[href^="/members/"]'):
        slug=a.get('href','').split('/')[-1]
        if slug and slug!='members':slugs.append(slug)
    slugmap={'alaska-airlines':'Alaska Airlines','american-airlines':'American Airlines','british-airways':'British Airways',
      'cathay-pacific':'Cathay Pacific','fiji-airways':'Fiji Airways','finnair':'Finnair','iberia':'Iberia',
      'japan-airlines':'Japan Airlines','malaysia-airlines':'Malaysia Airlines','oman-air':'Oman Air',
      'philippine-airlines':'Philippine Airlines','qantas':'Qantas','qatar-airways':'Qatar Airways',
      'royal-air-maroc':'Royal Air Maroc','royal-jordanian':'Royal Jordanian','srilankan-airlines':'SriLankan Airlines'}
    lists['oneworld_members']=[slugmap[x] for x in sorted(set(slugs)) if x in slugmap]
    # IATA pages 1..39: carrier detail links only.
    iata=[]
    files=[b/'iata_airline_list.html',*sorted((b/'iata_pages').glob('page_*.html'))]
    for p in files:
        s=BeautifulSoup(p.read_bytes(),'lxml')
        for a in s.select('a[href]'):
            href=a.get('href',''); text=a.get_text(' ',strip=True)
            if re.search(r'/airline-list/[^/?#]+/\d+/?$',href) and text: iata.append(text)
    lists['iata_members']=sorted(set(iata),key=str.casefold)
    # A4A publishes member carrier logos as alt text on the association page.
    s=BeautifulSoup((b/'a4a_home.html').read_bytes(),'lxml')
    a4a=[x.get('alt','').strip() for x in s.select('img[alt]')]
    lists['a4a_members']=[x for x in a4a if x in {'Air Canada','Alaska Airlines','American Airlines','Atlas Air','Delta Air Lines','FedEx','JetBlue','Southwest','United Airlines','UPS'}]
    # ALTA's first tab is explicitly full members, each logo title is a member name.
    s=BeautifulSoup((b/'alta_members_v2.html').read_bytes(),'lxml')
    titles=[x.get('title','').strip() for x in s.select('img[title]') if x.get('title')]
    cut=titles.index('Air Canada') if 'Air Canada' in titles else len(titles)
    lists['alta_full_members']=sorted(set(titles[:cut]),key=str.casefold)
    # AACO page h3 headings provide the complete current member roster.
    s=BeautifulSoup((b/'aaco_members_current.html').read_bytes(),'lxml')
    heads=[x.get_text(' ',strip=True) for x in s.find_all('h3')]
    start=heads.index('Member Airlines')+1 if 'Member Airlines' in heads else 1
    lists['aaco_members']=heads[start:]
    # AFRAA and Airlines for Europe public member relations from the raw Wikidata statement snapshot.
    lists['afraa_members']=[r['itemLabel']['value'] for r in source_air if r.get('orgLabel',{}).get('value')=='African Airlines Association']
    lists['airlines_for_europe']=[r['itemLabel']['value'] for r in source_air if r.get('orgLabel',{}).get('value')=='Airlines for Europe']
    # AAPA's current official member-airline image grid publishes the members' home-page URLs.
    aapa=json.loads((b/'aapa_pages_search.json').read_text(encoding='utf-8'))
    content=html.unescape(next(r['content']['rendered'] for r in aapa if r.get('slug')=='who-we-are'))
    match=re.search(r'custom_links=([^ ]+)',content)
    hrefs=match.group(1).strip('”"').split(',') if match else []
    aapa_by_host={
      'airastana.com':'Air Astana','airindia.in':'Air India','airnewzealand.co.nz':'Air New Zealand','ana.co.jp':'All Nippon Airways',
      'bangkokair.com':'Bangkok Airways','cathaypacific.com':'Cathay Pacific','china-airlines.com':'China Airlines','evaair.com':'EVA Air',
      'garuda-indonesia.com':'Garuda Indonesia','jal.com':'Japan Airlines','lionair.co.id':'Lion Air','malaysiaairlines.com':'Malaysia Airlines',
      'philippineairlines.com':'Philippine Airlines','qantas.com':'Qantas','flyroyalbrunei.com':'Royal Brunei','singaporeair.com':'Singapore Airlines',
      'thaiairways.com':'Thai Airways International','vietnamairlines.com':'Vietnam Airlines'}
    lists['aapa_members']=[aapa_by_host[h] for u in hrefs for h in [(urlparse(u).hostname or '').removeprefix('www.')] if h in aapa_by_host]
    s=BeautifulSoup((b/'air_france_klm.html').read_bytes(),'lxml')
    group_cells=[]
    for tr in s.select('table')[2].select('tr'):
        cells=tr.select('th,td')
        if len(cells)>1 and cells[0].get_text(' ',strip=True)=='Subsidiaries': group_cells=cells; break
    raw_group=[a.get_text(' ',strip=True) for a in group_cells[-1].select('a')]
    lists['air_france_klm_airlines']=[x for x in ('Air France','Air France Hop','KLM','KLM Cityhopper','Martinair') if x=='KLM' and 'KLM Royal Dutch Airlines' in raw_group or x!='KLM' and x in raw_group]
    if 'Transavia' in raw_group and 'France' in raw_group: lists['air_france_klm_airlines'].append('Transavia France')
    s=BeautifulSoup((b/'qantas_group.html').read_bytes(),'lxml')
    subs=[]
    for tr in s.select('table tr'):
        cells=tr.select('th,td')
        if len(cells)>1 and cells[0].get_text(' ',strip=True)=='Wholly owned subsidiaries':
            subs=[a.get_text(' ',strip=True) for a in cells[1].select('a')]
            break
    lists['qantas_group_airlines']=['Qantas',*subs]
    s=BeautifulSoup((b/'b787_operators.html').read_bytes(),'lxml')
    operators=[]
    for tr in s.select('table')[3].select('tr')[2:]:
        cells=tr.select('th,td')
        if len(cells)<12:continue
        name=cells[0].get_text(' ',strip=True); deliveries=cells[11].get_text(' ',strip=True).replace(',','')
        if name and match_air(name) and re.fullmatch(r'\d+',deliveries) and int(deliveries)>0:operators.append(name)
    lists['b787_operators']=operators
    s=BeautifulSoup((b/'skytrax_five_star.html').read_bytes(),'lxml')
    intro=next((p for p in s.select('p') if 'ten airlines they deem to be five-star rated' in p.get_text(' ',strip=True).lower()),None)
    starlist=intro.find_next('ul') if intro else None
    lists['skytrax_five_star']=[li.get_text(' ',strip=True).replace('*','').strip() for li in starlist.select('li')] if starlist else []
    s=BeautifulSoup((b/'star_alliance_article.html').read_bytes(),'lxml')
    history=' '.join(p.get_text(' ',strip=True) for p in s.select('p'))
    lists['star_alliance_founders']=['Air Canada','Lufthansa','Scandinavian Airlines','Thai Airways International','United Airlines'] if 'announced on 14 May 1997 by five airlines' in history else []
    s=BeautifulSoup((b/'a380_orders_deliveries.html').read_bytes(),'lxml')
    lists['a380_operators']=[tr.select('td')[0].get_text(' ',strip=True) for tr in s.select('table')[1].select('tr') if tr.select('td')]
    # Operating brand lists are transcribed from the airline/subsidiary table in the captured group articles.
    lists['lufthansa_group_airlines']=['Austrian Airlines','Brussels Airlines','Discover Airlines','Eurowings','Lufthansa','Lufthansa City Airlines','Swiss International Air Lines','Edelweiss Air','Air Dolomiti']
    lists['iag_airlines']=['Aer Lingus','British Airways','Iberia','Vueling','BA CityFlyer','BA EuroFlyer','Iberia Express']
    return lists

AIRLINE_LIST_META={
'star_alliance_members':('Star Alliance member airlines','https://www.staralliance.com/en/members',['Star Alliance']),
'skyteam_members':('SkyTeam member airlines','https://www.skyteam.com/en/about/our-members',['SkyTeam']),
'oneworld_members':('oneworld member airlines','https://www.oneworld.com/members',['oneworld']),
'iata_members':('IATA current airline members','https://www.iata.org/en/about/members/airline-list/',['International Air Transport Association','IATA']),
'a4a_members':('A4A member airlines (Airlines for America)','https://www.airlines.org/who-we-are/',['Airlines for America','A4A']),
'alta_full_members':('ALTA full member airlines','https://alta.aero/membership/',['ALTA']),
'aaco_members':("Arab Air Carriers' Organization member airlines",'https://www.aaco.org/aaco-community/member-airlines',['AACO']),
'afraa_members':('African Airlines Association member airlines','Wikidata P463 Q376537; raw/airline_affiliations_wikidata.json',['African Airlines Association','AFRAA']),
'airlines_for_europe':('Airlines for Europe (A4E) association member airlines','Wikidata P463 snapshot; raw/airline_affiliations_wikidata.json',['A4E']),
'lufthansa_group_airlines':('Lufthansa Group operating airlines','https://en.wikipedia.org/wiki/Lufthansa_Group',['Lufthansa Group']),
'iag_airlines':('International Airlines Group operating airlines','https://en.wikipedia.org/wiki/International_Airlines_Group',['International Airlines Group','IAG']),
'star_alliance_founders':('Five original Star Alliance member airlines','https://en.wikipedia.org/wiki/Star_Alliance#History; raw/airline_sources/star_alliance_article.html',['Star Alliance founding members']),
'aapa_members':('AAPA member airlines','https://www.aapairlines.org/who-we-are/; raw/airline_sources/aapa_pages_search.json',['Association of Asia Pacific Airlines']),
'air_france_klm_airlines':('Air France–KLM Group airline subsidiaries','https://en.wikipedia.org/wiki/Air_France%E2%80%93KLM; raw/airline_sources/air_france_klm.html',['Air France–KLM airlines']),
'qantas_group_airlines':('Qantas Group airlines','https://en.wikipedia.org/wiki/Qantas; raw/airline_sources/qantas_group.html',['Qantas Group airline subsidiaries']),
'a380_operators':('Airlines that have received Airbus A380 deliveries','https://en.wikipedia.org/wiki/List_of_Airbus_A380_orders_and_deliveries; raw/airline_sources/a380_orders_deliveries.html',['Airbus A380 operators']),
'b787_operators':('Boeing 787 operators','https://en.wikipedia.org/wiki/List_of_Boeing_787_orders_and_deliveries; raw/airline_sources/b787_operators.html',['Airlines with Boeing 787 deliveries']),
'skytrax_five_star':('Skytrax five-star rated airlines','https://en.wikipedia.org/wiki/Skytrax; raw/airline_sources/skytrax_five_star.html#five-star roster',['Five-star Skytrax airlines'])}

def build_airline_lists(rawlists=None):
 rawlists=rawlists or airline_rosters(); out=[]; match=match_air
 for lid,rawvals in rawlists.items():
    rawvals=sorted(set(x.strip() for x in rawvals if x and x.strip() and not re.fullmatch(r'Q[0-9]+',x.strip())),key=str.casefold)
    matched=[]; missing=[]
    for x in rawvals:
        v=match(x)
        if v:matched.append(v)
        else:missing.append(x)
    # Current/future membership uncertainty is isolated from candidate members.
    disputed=[]
    if lid=='skyteam_members':
        disputed=[v for x in rawvals if 'suspended' in x.lower() for v in [match(x) or match(x.replace(' [suspended]',''))] if v]
    if lid=='oneworld_members':
        disputed=[v for x in rawvals if x=='Philippine Airlines' for v in [match(x)] if v]
    members=sorted(set(matched)-set(disputed))
    official=len(set(rawvals))
    if len(members)+len(disputed)+len(missing)!=official:
        # Preserve duplicate source spellings as one published member; unresolved rows stay out of universe.
        official=len(members)+len(disputed)+len(missing)
    name,url,syn=AIRLINE_LIST_META[lid]
    add_list(out,lid,name,set(members)|set(disputed),official,url,syn,disputed)
    out[-1]['out_of_universe']=sorted(set(missing),key=str.casefold)
    if lid=='skyteam_members' and disputed:out[-1]['changes']=[{'value':disputed[0],'date':'2022-03-01','event':'membership suspended'}]
    if lid=='oneworld_members' and disputed:out[-1]['changes']=[{'value':disputed[0],'date':'2024-06-01','event':'announced future membership'}]
    # Record extraction evidence for spot check generation.
    out[-1]['_rawvalues']=rawvals
    out[-1]['_rawfile']= {
      'star_alliance_members':'raw/airline_sources/star_alliance.html','skyteam_members':'raw/airline_sources/skyteam.html',
      'oneworld_members':'raw/airline_sources/oneworld.html','iata_members':'raw/airline_sources/iata_airline_list.html + raw/airline_sources/iata_pages/page_*.html',
      'a4a_members':'raw/airline_sources/a4a_home.html','alta_full_members':'raw/airline_sources/alta_members_v2.html',
      'aaco_members':'raw/airline_sources/aaco_members_current.html','afraa_members':'raw/airline_affiliations_wikidata.json',
      'airlines_for_europe':'raw/airline_affiliations_wikidata.json','lufthansa_group_airlines':'raw/airline_sources/wiki_lufthansa_group.html',
      'iag_airlines':'raw/airline_sources/wiki_iag.html','star_alliance_founders':'raw/airline_sources/star_alliance_article.html',
      'ryanair_group_airlines':'raw/airline_sources/ryanair_holdings.html','tui_airlines':'raw/airline_sources/tui_airlines.html',
      'aapa_members':'raw/airline_sources/aapa_pages_search.json#who-we-are member-airlines cell',
      'air_france_klm_airlines':'raw/airline_sources/air_france_klm.html','qantas_group_airlines':'raw/airline_sources/qantas_group.html',
      'a380_operators':'raw/airline_sources/a380_orders_deliveries.html','b787_operators':'raw/airline_sources/b787_operators.html',
      'skytrax_five_star':'raw/airline_sources/skytrax_five_star.html#five-star list'}[lid]
 return out

# University membership lists are direct P463 statements, with the raw query snapshot preserving one row per value.
UNI_GROUPS=[('ivy_league','Ivy League universities','Q49113',['Ivy League','the Ivies']),
 ('group_of_eight','Australian Group of Eight universities','Q1377311',['Group of Eight','Go8']),
 ('c9_universities','C9 League universities','Q2634906',['C9 League','C9']),
 ('leru_members','League of European Research Universities members','Q1152269',['LERU']),
 ('apru_members','Association of Pacific Rim Universities members','Q1074688',['APRU']),
 ('aun_members','ASEAN University Network members','Q297575',['ASEAN University Network','AUN']),
 ('n8_members','N8 Research Partnership universities','Q5463432',['N8 Research Partnership','N8']),
 ('iaru_members','International Alliance of Research Universities members','Q1140056',['IARU']),
 ('coimbra_members','Coimbra Group universities','Q211620',['Coimbra Group']),
 ('aau_members','Association of American Universities members','Q743812',['AAU']),
 ('acu_members','Association of Commonwealth Universities members','Q593768',['ACU']),
 ('u21_members','Universitas 21 member universities','Q1202548',['Universitas 21','U21']),
 ('wun_members','Worldwide Universities Network members','Q1047645',['Worldwide Universities Network','WUN']),
 ('eua_members','European University Association members','Q868940',['European University Association','EUA']),
 ('russell_group','Russell Group universities','Q590631',['Russell Group'])]

def build_university_lists():
 out=[]
 for lid,name,q,syn in UNI_GROUPS:
    vals=query_group(source_uni,q,match_uni)
    # Use only groups with an observed closed roster of at least five members.
    if len(vals)<5: continue
    # The affiliation snapshot is filtered to university-type items; official_count includes matching values plus any rows outside the universe.
    rows=[r for r in source_uni if qid(r['org']['value'])==q]
    official=len({qid(r['item']['value']) for r in rows})
    missing=sorted({r['itemLabel']['value'] for r in rows if not match_uni(r.get('itemLabel',{}).get('value',''))},key=str.casefold)
    add_list(out,lid,name,vals,official,f"Wikidata P463 {q}; raw/university_affiliations_wikidata.json",syn)
    out[-1]['out_of_universe']=missing
    if len(out[-1]['members'])+len(missing)!=official:out[-1]['official_count']=len(out[-1]['members'])+len(missing)
    out[-1]['_rawfile']='raw/university_affiliations_wikidata.json'
    out[-1]['_source_qid']=q; out[-1]['_source_org_label']=name
 return out

def write_lists(name,lists):
    path=ROOT/'lists'/f'{name}.yaml'; path.parent.mkdir(parents=True,exist_ok=True)
    clean=[]
    for l in lists:
        clean.append({k:v for k,v in l.items() if not k.startswith('_')})
    path.write_text(yaml.safe_dump(clean,allow_unicode=True,sort_keys=False),encoding='utf-8')

# Every current carrier explicitly named by a direct roster belongs in the input universe, even if the broad SPARQL result limit omitted it.
AIR_ROSTERS=airline_rosters()
for _bad in [x for x in AIR if re.fullmatch(r'Q[0-9]+',x)]: AIR.pop(_bad,None)
for _retired_airline in ('Vistara','Asiana Airlines'):
    AIR.pop(_retired_airline,None)  # Both ceased airline operations after 2024 mergers.
_norm_air={norm(x) for x in AIR}
for _lid,_names in AIR_ROSTERS.items():
    for _raw in _names:
        _canonical=AIR_ALIAS.get(norm(_raw),_raw.strip())
        if not _canonical or _canonical in ('Vistara','Asiana Airlines') or re.fullmatch(r'Q[0-9]+',_canonical) or norm(_canonical) in _norm_air:continue
        AIR[_canonical]={'qid':'','country':'?','continent':'?','desc':''};_norm_air.add(norm(_canonical))
# Resolve exact roster labels that the broad entity query did not return. Search results are accepted only
# when one English-label match describes an airline and does not identify it as former or defunct.
AIR_SEARCH_ALIASES={'Austrian':'Q781770','ASKY':'Q127529','Azul':'Q794272','Azul Brazilian Airlines':'Q794272',
 'Belavia Belarusian Airlines':'Q815314','Cargojet Airways':'Q376186','Chalair':'Q2406313','Condor':'Q312517',
 'Cubana':'Q849910','EL AL':'Q208489','Estafeta Cargo':'Q4272310','GOL Linhas Aereas':'Q691637',
 'Hong Kong Express Airways':'Q1365358','Iran Airtour Airline':'Q1336559','Israir':'Q558002','JetBlue':'Q161086',
 'Juneyao Airlines':'Q1713277','KlasJet':'Q50822504','LATAM Airlines Brasil':'Q690789','Martinair Cargo':'Q426851',
 'Mauritania Airlines International':'Q3852483','Middle East Airlines':'Q859510','Plus Ultra':'Q18026968',
 'Rossiya Airlines':'Q727452','Royal Brunei':'Q1050783','SANSA Airlines':'Q2222528',
 'Saudi Arabian Airlines':'Q541179','SkyUp Airlines':'Q47009940','Thai Airways International':'Q188710',
 'Vietjet':'Q853878','Wideroe':'Q28344','XiamenAir':'Q147208','Yemen Airways':'Q662091'}
_search=json.loads((RAW/'airline_search_entities.json').read_text(encoding='utf-8'))
_country_rows=readj('airline_search_country_enrichment.json')['results']['bindings']
_country_by_qid=defaultdict(set)
for _r in _country_rows:
    if 'countryLabel' in _r:_country_by_qid[qid(_r['item']['value'])].add(_r['countryLabel']['value'])
for _row in _search:
    _name=_row['query']; _hits=[]
    for _item in _row['response'].get('search',[]):
        _desc=_item.get('description',''); _low=_desc.lower()
        if norm(_item.get('label',''))!=norm(_name) or not any(k in _low for k in ('airline','air carrier')):continue
        if any(k in _low for k in ('former','defunct','disambiguation','1926–1991','2018–2022')):continue
        _hits.append(_item)
    _alias_id=AIR_SEARCH_ALIASES.get(_name)
    if _alias_id:_hits=[x for x in _row['response'].get('search',[]) if x.get('id')==_alias_id and 'airline' in x.get('description','').lower()]
    _canonical=next((x for x in AIR if norm(x)==norm(_name)),None)
    if len(_hits)!=1 or not _canonical or AIR[_canonical].get('qid'):continue
    _item=_hits[0]; _id=_item['id']; _countries=sorted(_country_by_qid.get(_id,()))
    AIR[_canonical]['qid']=_id
    AIR[_canonical]['desc']=_item.get('description','')
    if len(_countries)==1:
        _code=COUNTRY_CODE.get(norm(_countries[0]),'')
        if _code:
            AIR[_canonical]['country']=COUNTRY_NAME.get(_code,'?')
            AIR[_canonical]['continent']=CONTINENT.get(_code,'?')
save_universe('airline',AIR)
match_air=make_matcher(AIR,AIR_ALIAS)
COUNTRY_LISTS=build_country_lists(); AIRLINE_LISTS=build_airline_lists(AIR_ROSTERS); UNIVERSITY_LISTS=build_university_lists()
write_lists('country',COUNTRY_LISTS); write_lists('airline',AIRLINE_LISTS); write_lists('university',UNIVERSITY_LISTS)

# Row-exact member and nonmember audit table. Source coordinates are source-query result rows or HTML table headings.
spot=[]
_RAW_CACHE={}
def cached_rows(name):
    if name not in _RAW_CACHE:_RAW_CACHE[name]=readj(name)['results']['bindings']
    return _RAW_CACHE[name]
def add_spot(field,lists,universe):
    allvals=set(universe)
    for l in lists:
        members=set(l['members']); non=allvals-members-set(l.get('disputed',[]))
        ms=sorted(members)[:5]; ns=sorted(non)[:5]
        for status,vals in [('member',ms),('nonmember',ns)]:
            for v in vals:
                evidence=l.get('_rawfile','')
                ev=evidence
                if evidence.endswith('.json'):
                    # Find a concrete matching query row (member) or record the exhaustive org-filtered query scope (nonmember).
                    rawname=evidence.rsplit('/',1)[-1]
                    rows=cached_rows(rawname)
                    q=None; group_id=l.get('_source_qid'); group_name=l.get('_source_org_label')
                    if field=='applicants.nationality':
                        q=next((i for i,r in enumerate(rows,1) if (not group_id or qid(r.get('org',{}).get('value',''))==group_id) and COUNTRY_QID.get(qid(r.get('item',{}).get('value','')))==v),None)
                    else:
                        q=next((i for i,r in enumerate(rows,1) if (not group_id or qid(r.get('org',{}).get('value',''))==group_id) and norm(r.get('itemLabel',{}).get('value',''))==norm(v)),None)
                    ev=f"{evidence}#results.bindings[{q}]" if q else f"{evidence}#complete roster for {group_name or l['id']}; {v} absent, parser checked"
                elif field=='applicants.nationality' and 'country_sources/' in evidence:
                    scopes={'european_union.html':'table 3, member-state table','schengen_area.html':'table 3, member-state table',
                      'nato.html':'table 3, membership roster cell','oecd.html':'table 7, members table',
                      'commonwealth.html':'table 7, sovereign states (members) row','african_union_official.html':'member-state tables 2-5, abbreviation cells',
                      'asean.html':'table 4, member-state table','opec.html':'table 3, members table',
                      'council_of_europe_members.html':'table 1, member-state rows','un_members.html':'table 2, member-state rows',
                      'g20.html':'table 3, member column','gulf_cooperation_council.html':'table 4, member-country rows',
                      'pacific_islands_forum.html':'table 2, member-nations rows and ISO codes',
                      'group_of_seven.html':'table 3, member-country rows'}
                    fn=evidence.split('country_sources/',1)[1].split('#',1)[0]
                    scope=scopes.get(fn,'complete member table')
                    ev=f"raw/country_sources/{fn}#{scope}; {'member cell for '+v if status=='member' else 'complete roster searched; '+v+' absent'}"
                elif 'iata_pages' in evidence:
                    ev=f"{evidence}#carrier detail link for {v}; full 39-page directory"
                else: ev=f"{evidence}#complete member roster; {v} {'present' if status=='member' else 'absent'}, parser checked"
                spot.append([field,l['id'],status,v,ev])

add_spot('applicants.nationality',COUNTRY_LISTS,COUNTRY_NAME.keys())
add_spot('trips.airline',AIRLINE_LISTS,AIR.keys())
add_spot('applicants.university',UNIVERSITY_LISTS,UNI.keys())
write_tsv(ROOT/'SPOTCHECK.tsv',['field','list_id','status','value','evidence'],spot)
print(f"built universes: country={len(country_items)}, airline={len(AIR)}, university={len(UNI)}")
print(f"built lists: country={len(COUNTRY_LISTS)}, airline={len(AIRLINE_LISTS)}, university={len(UNIVERSITY_LISTS)}")
for field,lists in [('country',COUNTRY_LISTS),('airline',AIRLINE_LISTS),('university',UNIVERSITY_LISTS)]:
 print(field,', '.join(f"{x['id']}:{len(x['members'])}/{x['official_count']}" for x in lists))
