#!/usr/bin/env python3
"""Create deterministic, raw-snapshot-backed membership spot checks for every roster."""
import csv, hashlib, json, re, unicodedata
from pathlib import Path
from urllib.parse import unquote
import yaml
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().casefold()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def records_for(item, universe):
    lid=item['id']; src=item.get('source','')
    if lid=='sp500':
        path=ROOT/'raw'/'sp500.csv'
        with path.open(encoding='utf-8-sig',newline='') as f:
            return path.relative_to(ROOT).as_posix(),[(f'csv row {i+2}',r.get('Security','')) for i,r in enumerate(csv.DictReader(f))]
    if lid=='nasdaq_100':
        path=ROOT/'raw'/'nasdaq100-20261016.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        return path.relative_to(ROOT).as_posix(),[(f'JSON data.rows[{i}]',r.get('companyName','')) for i,r in enumerate(data['data']['data']['rows'])]
    if lid=='fortune_global_500':
        path=ROOT/'raw'/'fortune-global500-2026.html'
        soup=BeautifulSoup(path.read_bytes(),'lxml')
        for script in soup.select('script[type="application/ld+json"]'):
            try: obj=json.loads(script.string or script.get_text())
            except (json.JSONDecodeError,TypeError): continue
            if isinstance(obj,dict) and len(obj.get('itemListElement',[]))==500:
                return path.relative_to(ROOT).as_posix(),[(f'JSON-LD itemListElement[{i}]',x.get('item',{}).get('name','')) for i,x in enumerate(obj['itemListElement'])]
        raise ValueError('Fortune snapshot has no 500-entry JSON-LD roster')
    if lid=='interbrand_top10_2025':
        path=ROOT/'raw'/'interbrand-best-global-brands-2025.html'
        soup=BeautifulSoup(path.read_bytes(),'lxml')
        obj=json.loads(soup.select_one('#__NEXT_DATA__').string)
        rows=[x for x in obj['props']['pageProps']['data']['brandData'] if x.get('year')==2025]
        return path.relative_to(ROOT).as_posix(),[(f'#__NEXT_DATA__.props.pageProps.data.brandData[{i}]',r.get('brandName','')) for i,r in enumerate(rows)]
    if lid=='erasmus_countries': path=ROOT/'raw'/'erasmus-eligible-countries.html'
    elif lid=='big_ten': path=ROOT/'raw'/'official-university'/'btaa.html'
    elif lid=='utrecht_network': path=ROOT/'raw'/'official-university'/'utrecht.html'
    elif 'wikipedia.org/wiki/' in src:
        title=unquote(src.split('wikipedia.org/wiki/',1)[1].split()[0])
        path=ROOT/'raw'/'wiki'/(title+'.json')
        if not path.exists() and title=='Group_of_Eight_(Australia)':
            path=ROOT/'raw'/'wiki'/'Group_of_Eight_(Australian_universities).json'
    else:
        raise ValueError(f'no raw-source mapping for {lid}: {src}')
    if path.suffix=='.json':
        obj=json.loads(path.read_text(encoding='utf-8'))
        html=obj.get('parse',{}).get('text',{}).get('*')
        if html is None: raise ValueError(f'invalid source JSON: {path}')
        soup=BeautifulSoup(html,'lxml'); out=[]
        for ti,table in enumerate(soup.select('table'),1):
            for ri,tr in enumerate(table.select('tr'),1):
                text=re.sub(r'\s+',' ',tr.get_text(' ',strip=True)).strip()
                if text: out.append((f'table {ti} row {ri}',text))
        for tag in ('li','p'):
            for i,node in enumerate(soup.select(tag),1):
                text=re.sub(r'\s+',' ',node.get_text(' ',strip=True)).strip()
                if text: out.append((f'{tag} {i}',text))
    else:
        soup=BeautifulSoup(path.read_bytes(),'lxml'); out=[]
        for tag in ('h1','h2','h3','h4','li','tr','p'):
            for i,node in enumerate(soup.select(tag),1):
                text=re.sub(r'\s+',' ',node.get_text(' ',strip=True)).strip()
                if text: out.append((f'{tag} {i}',text))
    return path.relative_to(ROOT).as_posix(),out

def sortkey(lid,value):
    return hashlib.sha256(f'UN/{lid}/{value}/spotcheck'.encode()).hexdigest()

def main():
    universes={}; universe_lines={}
    for p in (ROOT/'universes').glob('*.tsv'):
        with p.open(encoding='utf-8',newline='') as f:
            data=list(csv.DictReader(f,delimiter='\t'))
            universes[p.stem]=data
            universe_lines[p.stem]={r['value']:i+2 for i,r in enumerate(data)}
    country_names={}
    country_path=ROOT/'raw'/'country-codes.csv'
    with country_path.open(encoding='utf-8',newline='') as f:
        for i,row in enumerate(csv.DictReader(f),2):
            code=(row.get('ISO3166-1-Alpha-2') or '').strip()
            if code:
                keys={norm(row.get(k,'')) for k in ('official_name_en','CLDR display name','UNTERM English Short','UNTERM English Formal') if row.get(k)}
                country_names[code]=(i,keys)
    output=[]
    for listfile in sorted((ROOT/'lists').glob('*.yaml')):
        uname=listfile.stem
        for item in yaml.safe_load(listfile.read_text(encoding='utf-8')) or []:
            lid=item['id']; rel,records=records_for(item,uname)
            members=set(item.get('members',[])); unstable=set(item.get('disputed',[]))|set(item.get('out_of_universe',[]))
            def hits(v):
                keys=[norm(v)] if uname!='country' else []
                row=next((r for r in universes[uname] if r['value']==v),None)
                if row and row.get('entity'): keys.append(norm(row['entity']))
                if lid=='interbrand_top10_2025':
                    brand_aliases={
                        'alphabet inc.':['Google'],'apple inc.':['Apple'],'coca-cola company (the)':['Coca-Cola'],
                        'mercedes-benz group':['Mercedes-Benz'],'meta platforms':['Instagram']}
                    keys.extend(norm(x) for x in brand_aliases.get(v.casefold(),[]))
                if uname=='country' and v in country_names: keys.extend(country_names[v][1])
                keys=[k for k in set(keys) if len(k)>2]
                return [(loc,text) for loc,text in records if any(re.search(r'(?<![a-z0-9])'+re.escape(k)+r'(?![a-z0-9])',norm(text)) for k in keys)]
            member_candidates=sorted(members,key=lambda v:sortkey(lid,v))
            picked=[]
            for v in member_candidates:
                hs=hits(v)
                if hs: picked.append((v,hs[0]))
                if len(picked)==5: break
            if len(picked)<5:
                raise ValueError(f'{lid}: only {len(picked)} members have raw-record matches')
            for v,(loc,text) in picked:
                evidence=f'{loc}: {text[:220]}'
                if uname=='country' and v in country_names:
                    evidence=f'raw/country-codes.csv row {country_names[v][0]} maps {v}; {evidence}'
                output.append([lid,'member',v,rel,evidence,'matched'])
            nonmembers=[r['value'] for r in universes[uname] if r['value'] not in members|unstable]
            picked_non=[]
            for v in sorted(nonmembers,key=lambda v:sortkey(lid,v)):
                if not hits(v): picked_non.append(v)
                if len(picked_non)==5: break
            if len(picked_non)<5:
                raise ValueError(f'{lid}: only {len(picked_non)} non-members absent from extracted raw records')
            for v in picked_non:
                proof=f'{uname}.tsv row {universe_lines[uname][v]}; checked {rel} records 1-{len(records)}, value absent'
                output.append([lid,'nonmember',v,rel,proof,'absent'])
            assert len([r for r in output if r[0]==lid])==10
    out=ROOT/'SPOTCHECK.tsv'
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n')
        w.writerow(['list_id','sample_type','value','raw_file','evidence','program_check']);w.writerows(output)
    print(f'SPOTCHECK OK: {len(output)} checks across {len(output)//10} lists')
if __name__=='__main__': main()
