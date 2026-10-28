import json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
cfg=json.loads((D/'CONFIG.json').read_text())
sid=cfg['course']
sessions=[];methods=('histhint',)
if 'new' in sys.argv[1:]:methods=('histhint',)
for mode in ('self',):
 for method in methods:
  for level in cfg['levels']:
   source=f"runs_nc100_{mode}_v0/rep1/{method}/{sid}/L{level}/STATE.json"
   output=f"runs_nc100_test/{mode}/{method}/L{level}"
   sessions.append(dict(queue_index=len(sessions),course=sid,level=level,task_id=f'{sid}.L{level}.evaluation',method=method,state_label=mode+'_'+method,state_source=source,state_payload=None,harness='sdk',output=output,replicate=1,replay=1,canonical=True,version=0))
plan=dict(protocol='stage_B_replay',sessions=sessions,aliases=[],seed=cfg['replay_seed'],concurrency=cfg['concurrency'])
h=D/'harness_k1_test'
(h/'REPLAY_PLAN_K1_TRAJ.json').write_text(json.dumps(plan,indent=2)+'\n')
(D/'REPLAY_PLAN_K1_TRAJ.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(sessions=len(sessions),seed=cfg['replay_seed'])))
