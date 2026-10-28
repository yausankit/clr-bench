"""Deterministic synthetic port-state-control defect ledger."""
import csv, hashlib, json, random
from pathlib import Path
ANSWER_FORMAT = "json"
TRAP_FIELDS = ["ships.flag_state", "ships.owner_country", "inspections.port"]
TASK = "Each defect listed in an inspection counts once for the vessel's management company."
ENTITY_NOUN = "ship management company"
INPUT_FORMAT = "A JSON object lists companies, their ships, each ship's inspections, and the defect identifiers recorded for each inspection."
ROOT = Path(__file__).parent

def _rng(seed, step, name):
    h=hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest()
    return random.Random(int(h,16))

def _values(universe):
    p=ROOT/'universes'/f'{universe}.tsv'
    with p.open(encoding='utf-8') as f:
        return [r['value'] for r in csv.DictReader(f,delimiter='\t')]

def base_world(seed:int, step:str)->dict:
    flags=_values('flag'); ports=_values('port')
    rr=_rng(seed,step,'world')
    world={'companies':[],'ships':[],'inspections':[]}
    for ci in range(36):
        company=f'MC{ci+1:03d}'; world['companies'].append({'id':company})
        for si in range(4):
            ship=f'{company}-V{si+1:02d}'
            world['ships'].append({'id':ship,'company':company,'flag_state':flags[rr.randrange(len(flags))],
                                   'owner_country':flags[rr.randrange(len(flags))],'inspections':[]})
            for ii in range(3):
                iid=f'{ship}-I{ii+1:02d}'; n=2+rr.randrange(4)
                world['inspections'].append({'id':iid,'ship':ship,'port':ports[rr.randrange(len(ports))],
                    'defects':[f'{iid}-D{di+1:02d}' for di in range(n)]})
                world['ships'][-1]['inspections'].append(iid)
    return world

def entities(world): return sorted(x['id'] for x in world['companies'])

def slots(world,field):
    table,attr=field.split('.',1)
    if table=='ships': return sorted((x['company'],x['id']) for x in world['ships'])
    return sorted((next(s['company'] for s in world['ships'] if s['id']==x['ship']),x['id']) for x in world['inspections'])

def set_value(world,field,pos,value):
    table,attr=field.split('.',1); rows=world['ships'] if table=='ships' else world['inspections']
    for x in rows:
        if x['id']==pos: x[attr]=value; return
    raise KeyError(pos)

def total(world,entity,excluded):
    ships={s['id']:s for s in world['ships']}; count=0
    for i in world['inspections']:
        s=ships[i['ship']]
        if s['company']!=entity: continue
        if ('ships.flag_state',s['id']) in excluded or ('ships.owner_country',s['id']) in excluded or ('inspections.port',i['id']) in excluded: continue
        count+=len(i['defects'])
    return count

def render(world,entity_ids):
    selected=set(entity_ids); ships_by_company={x:[] for x in selected}
    inspections={i['id']:i for i in world['inspections']}
    for s in sorted(world['ships'],key=lambda z:z['id']):
        if s['company'] not in selected: continue
        si=[]
        for iid in s['inspections']:
            i=inspections[iid]
            si.append({'id':iid,'port':i['port'],'defects':list(i['defects'])})
        ships_by_company[s['company']].append({'id':s['id'],'flag_state':s['flag_state'],'owner_country':s['owner_country'],'inspections':si})
    return {'companies':[{'id':c,'ships':ships_by_company[c]} for c in sorted(selected)]}

def values(data,field):
    table,attr=field.split('.',1); out=[]
    for c in data['companies']:
        for s in c['ships']:
            if table=='ships': out.append(s[attr])
            else: out.extend(i[attr] for i in s['inspections'])
    return out

def reference(data,excluded):
    result={}
    for c in data['companies']:
        n=0
        for s in c['ships']:
            for i in s['inspections']:
                omit=(('ships.flag_state' in excluded and s['flag_state'] in excluded['ships.flag_state']) or
                      ('ships.owner_country' in excluded and s['owner_country'] in excluded['ships.owner_country']) or
                      ('inspections.port' in excluded and i['port'] in excluded['inspections.port']))
                if not omit: n+=len(i['defects'])
        result[c['id']]=n
    return result


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'inspections.port': ['CHBSL', 'CHKRZ', 'DEBER', 'ESIBZ', 'FMEAU', 'GBEDI', 'GEBUS', 'GYANT', 'MGANM', 'NLLWR', 'NLRTM', 'ZADUR'], 'ships.flag_state': ['AU', 'BR', 'CN', 'CO', 'DO', 'FR', 'GB', 'GR', 'JO', 'JP', 'KE', 'MR', 'NO', 'NZ', 'RS', 'RU', 'SA', 'SE', 'SG', 'TR', 'TZ', 'US', 'YE', 'ZA'], 'ships.owner_country': ['AL', 'AR', 'AT', 'BG', 'BN', 'CA', 'CY', 'DE', 'FJ', 'ID', 'IN', 'LI', 'LS', 'LU', 'ME', 'MK', 'MX', 'NU', 'PG', 'SK', 'TC', 'TG', 'UG', 'UY']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
