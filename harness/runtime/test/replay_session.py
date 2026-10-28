import sys,os,copy,traceback,json
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent
plan_name=sys.argv[2] if len(sys.argv)>2 else 'REPLAY_PLAN.json'
item=json.loads((H/plan_name).read_text())['sessions'][int(sys.argv[1])]
sys.path.insert(0,str(H/item['harness']))
from common import read,dump,initial
from evaluator import Evaluator
from run_m2 import Environment
from solver import Native,solve
from evolution_curriculum.client import Client
item=read(H/plan_name)['sessions'][int(sys.argv[1])];out=P/item['output']
state=read(P/item['state_source']) if item['state_source'] else item.get('state_payload',initial('frozen'));original=copy.deepcopy(state)
status=dict(**item,status='running');dump(out/'STATUS.json',status)
try:
 ev=Evaluator(item['course'],out/'evaluator');tid=f"{item['course']}.L{item['level']}.evaluation";env=Environment(ev,[tid])
 try:
  _,result=solve(Native(Client(env.url),out/'formal'),dict(method=item['method'],sample=item['course'],level=item['level'],phase=f"PB4-replay-{item['state_label']}-rep{item['replicate']}-r{item['replay']}",split='evaluation',task_id=tid),state,out/'formal')
  dump(out/'FINAL_PROGRAM.json',dict(text=result['text']))
 finally:env.close()
 if os.environ.get('PB4_DRY_RUN') == '1':
  dump(out/'STATE_AFTER.json',state);status.update(status='complete',pass_=None,updates=0,dry_run=True)
 else:
  grade=ev.evaluate(tid,result['text'],state);dump(out/'GRADE.json',grade)
  dump(out/'STATE_AFTER.json',state);status.update(status='complete',pass_=all(x['pass_'] for x in grade['cases']),updates=0)
except Exception:status.update(status='interrupted',error=traceback.format_exc())
dump(out/'STATUS.json',status);print(status['status'],flush=True)
raise SystemExit(0 if status['status']=='complete' else 1)
