"""Runs a submitted program on a level's inputs and grades it.

In practice, a program is run on the public example and on the 2k+1 hidden practice inputs of level k: one that
moves the example values to other records and, for each rule j <= k, one that inserts the revealed member m0 and one
that inserts m0 and the practice non-member n_p. With rewarded practice (CLR_BUNDLE=bundle_k1_v0_rg), inputs that
also insert the unseen member m1 join from the second attempt. In the test, the same code grades the five cells.

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
import ast,copy,json,math,os,re,shutil,subprocess,threading,time,uuid
from pathlib import Path
from common import ROOT,dump,read
import x_runner

class InfrastructureError(RuntimeError):pass
SPLIT='practice'

def parse(text,task):
 if not isinstance(text,str):raise ValueError('Expected source text, received '+type(text).__name__)
 code=x_runner.extract_code(text).strip()
 tree=ast.parse(code)
 if not any(isinstance(n,ast.FunctionDef) and n.name=='solve' for n in tree.body):raise ValueError('Missing solve')
 return code

def equal(a,b):
 if type(a) is bool or type(b) is bool:return type(a)==type(b) and a==b
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isfinite(b) and math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-6)
 if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return type(a)==type(b) and a==b

def compare(task,expected,actual,stratum):
 return {str(stratum):bool(actual.get('ok') and equal(expected,actual.get('value')))}

ADAPTER='''import json, subprocess, sys
p=json.load(sys.stdin); rows=[]
for data in p["inputs"]:
    q={"code":p["code"],"data":data}
    try:
        r=subprocess.run([sys.executable,"/work/x_worker.py"],input=json.dumps(q,ensure_ascii=False),text=True,capture_output=True,timeout=10)
    except subprocess.TimeoutExpired:
        rows.append({"ok":False,"error_type":"Timeout","error":"Candidate exceeded 10 seconds on one input"}); continue
    if r.returncode:
        rows.append({"ok":False,"error_type":"WorkerError","error":r.stderr[-2000:]}); continue
    try:
        v=json.loads(r.stdout)
    except Exception as e:
        rows.append({"ok":False,"error_type":"FormatError","error":str(e)}); continue
    if v.get("ok"):rows.append({"ok":True,"value":v.get("value")})
    else:rows.append({"ok":False,"error_type":v.get("error_type") or "CandidateError","error":(v.get("error") or "candidate failed")[-2000:]})
open("/out/result.json","w").write(json.dumps(rows,ensure_ascii=False))
'''

def execute(task,code,inputs,folder,split=SPLIT):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 work=folder/'work';out=folder/'out';work.mkdir();out.mkdir()
 (work/'candidate.py').write_text(code)
 shutil.copyfile(ROOT/'x_worker.py',work/'x_worker.py')
 shutil.copyfile(ROOT/'x_runner.py',work/'runner.py')
 (work/'adapter.py').write_text(ADAPTER)
 limit=30+10*len(inputs)
 name='clrbench-eval-'+uuid.uuid4().hex
 cmd=['docker','run','-i','--name',name,'--label','clrbench.eval=1','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','2g','--pids-limit','128','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,noexec,size=128m','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONUTF8=1','--env',f'CLRSYNTH_SPLIT={split}','--mount',f'type=bind,src={work.resolve()},dst=/work,readonly','--mount',f'type=bind,src={out.resolve()},dst=/out','--workdir','/tmp','python:3.12-slim','python','/work/adapter.py']
 dump(folder/'CONTAINER.json',dict(name=name,command=cmd,wall_clock_deadline_seconds=limit))
 payload=dict(kind=task['kind'],schemas=task.get('schemas',{}),inputs=inputs,code=code)
 try:
  result=subprocess.run(cmd,input=json.dumps(payload,ensure_ascii=False),text=True,capture_output=True,timeout=limit)
  timed_out=False
 except subprocess.TimeoutExpired:
  subprocess.run(['docker','kill',name],capture_output=True);timed_out=True;result=None
 inspection=subprocess.run(['docker','inspect',name],text=True,capture_output=True)
 state=json.loads(inspection.stdout)[0]['State'] if inspection.returncode==0 else {}
 subprocess.run(['docker','rm',name],capture_output=True)
 if timed_out:
  dump(folder/'EXIT.json',dict(returncode=None,state=state,timed_out=True,limit_seconds=limit))
  return [dict(ok=False,error_type='ResourceLimit',error=f'Candidate worker exceeded {limit} seconds') for _ in inputs]
 dump(folder/'EXIT.json',dict(returncode=result.returncode,state=state,stderr=result.stderr[-6000:],timed_out=False))
 if state.get('OOMKilled'):return [dict(ok=False,error_type='ResourceLimit',error='2 GiB candidate memory exceeded') for _ in inputs]
 if result.returncode or not (out/'result.json').exists():raise InfrastructureError(f'Candidate worker exit {result.returncode}; inspect {folder}')
 observations=read(out/'result.json')
 if not isinstance(observations,list) or len(observations)!=len(inputs):raise InfrastructureError('Worker observation count does not match assigned inputs')
 return observations

class Evaluator:
 def __init__(self,sid,output):
  root=ROOT.parent/os.environ.get('CLR_BUNDLE','bundle_k1_v0');published={}
  pfile=root/'public/TASKS.json'
  if pfile.exists():
   for t in read(pfile):published[t['task_id']]=t
  raw=[]
  for path in sorted((root/'private').glob(sid+'.L*.json')):
   original=read(path);shown=published.get(original['task_id'],{})
   task=dict(original);task['split']=original.get('split') or shown.get('split')
   # Rewarded practice (CLR_BUNDLE=bundle_k1_v0_rg): hidden instances tagged from_attempt=k join from attempt k.
   att=int(os.environ.get('CLR_ATTEMPT','99'))
   if task.get('hidden'):
    keep=[i for i,h in enumerate(task['hidden']) if h.get('from_attempt',1)<=att]
    task['hidden']=[task['hidden'][i] for i in keep];task['expected']=[task['expected'][0]]+[task['expected'][i+1] for i in keep]
   task['system']=original.get('system') or shown.get('system')
   raw.append(task)
  raw=[t for t in raw if t['split']==SPLIT]
  self.tasks={};self.private={}
  for t in raw:
   original=t['task_id'];alias=original.rsplit('.',1)[0]+'.evaluation'
   visible={k:t[k] for k in ('task_id','course_id','dataset','level','split','kind','language','adapter','prompt','system','title') if k in t}
   visible['task_id']=alias;self.tasks[alias]=visible;self.private[alias]=t
  self.output=Path(output);self.output.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock();self.serial=0
 def inspect(self,task_id,table=None,offset=0,limit=100):
  data=self.private[task_id]['public']
  if isinstance(data,str):
   lines=data.splitlines(keepends=True);offset=max(0,offset);limit=max(0,min(100,limit))
   return dict(total_lines=len(lines),offset=offset,lines=lines[offset:offset+limit])
  if table not in data:return dict(available_fields=list(data))
  value=data[table]
  if isinstance(value,list):return dict(total=len(value),offset=offset,records=value[max(0,offset):max(0,offset)+max(1,min(100,limit))])
  return dict(value=value)
 def next_folder(self):
  with self.lock:self.serial+=1;return self.output/'executions'/f'{self.serial:06d}'
 def grade(self,task_id,text,hidden=False):
  task=self.private[task_id];rows=[]
  if task['split']=='test':
   inputs=[h.get('data',h.get('fixture')) for h in task['hidden']]
   strata=[h['stratum'] for h in task['hidden']]
   expected=task['expected'][1:]
  else:
   inputs=[task['public']]+([h.get('data',h.get('fixture')) for h in task['hidden']] if hidden else [])
   strata=[task['level']]+([h['stratum'] for h in task['hidden']] if hidden else [])
   expected=task['expected'] if hidden else task['expected'][:1]
  try:code=parse(text,task)
  except (ValueError,SyntaxError,TypeError) as error:actual=[dict(ok=False,error_type='FormatError',error=str(error)) for _ in inputs];executed=False
  else:actual=execute(task,code,inputs,self.next_folder());executed=True
  for i,(obs,s) in enumerate(zip(actual,strata)):
   checks=compare(task,expected[i],obs,s)
   rows.append(dict(input=i,public=i==0,checks=checks,shape_ok=True,pass_=all(checks.values()),actual=obs))
  checks=[v for r in rows for v in r['checks'].values()]
  return dict(status='scored',score=sum(r['pass_'] for r in rows)/len(rows),pass_=all(r['pass_'] for r in rows),capability_score=sum(checks)/len(checks),actually_executed=executed,actual=actual[0],expected=expected[0],cases=rows)
 def feedback(self,task_id,text):return self.grade(task_id,text,False)
 def evaluate(self,task_id,text,state):
  path=self.output/'evaluations'/f'{task_id}.json'
  if path.exists():raise RuntimeError('Formal submission already exists; no resampling')
  dump(path,dict(status='pending',text=text,state=state,submitted_at=time.time()))
  result=self.grade(task_id,text,True);dump(path,dict(**result,text=text,state=state,finished_at=time.time()));return result
 def dispatch(self,request):
  op=request['operation'];args=request.get('arguments',{})
  if op=='tasks':return [t for t in self.tasks.values() if all(t.get(k)==v for k,v in args.items())]
  if op=='inspect_source':return self.inspect(**args)
  if op=='public_input':return self.private[args['task_id']]['public']
  if op=='feedback':return self.feedback(**args)
  if op=='feedback_pair':raise PermissionError('One public view per level')
  if op=='run_candidate':
   t=self.private[args['task_id']]
   try:code=parse(args['code'],t)
   except (ValueError,SyntaxError,TypeError) as e:return dict(ok=False,error_type='FormatError',error=str(e))
   return execute(t,code,[t['public']],self.next_folder())[0]
  raise PermissionError('Controller-only operation')
