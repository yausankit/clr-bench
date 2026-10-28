#!/usr/bin/env python3
import json
from dataset import ANSWER_FORMAT, TRAP_FIELDS, base_world, entities, slots, set_value, total, render, values
seed=20266107;step='check_dataset'
a=base_world(seed,step);b=base_world(seed,step)
assert json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
ents=entities(a);assert len(ents)>=30
for field in TRAP_FIELDS:
    pos=slots(a,field); per={e:0 for e in ents}
    for e,p in pos:per[e]+=1
    assert min(per.values())>=3,(field,min(per.values()))
    world=base_world(seed,step)
    values_list={'applicants.nationality':__import__('dataset')._values('country'),
                 'trips.airline':__import__('dataset')._values('airline'),
                 'applicants.university':__import__('dataset')._values('university')}[field]
    marker=values_list[-1]
    ent,p=pos[0];before=total(world,ent,set());set_value(world,field,p,marker)
    data=render(world,[ent]);assert marker in values(data,field)
    assert values(data,field).count(marker)>=1
    after=total(world,ent,{(field,p)})
    assert isinstance(before,int) and isinstance(after,int) and after<before
    ref=__import__('dataset').reference(data,{})
    assert ref[ent]==total(world,ent,set())
print(f'check_dataset OK: {len(ents)} entities; '+', '.join(f'{f}={len(slots(a,f))} positions' for f in TRAP_FIELDS))
