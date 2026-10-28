import concurrent.futures,json,os,subprocess,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent
cfg=json.loads((D/'CONFIG.json').read_text());PY=cfg.get('python') or sys.executable
H=D/'harness_k1_test';PLAN_NAME='REPLAY_PLAN_K1_TRAJ.json';plan=json.loads((H/PLAN_NAME).read_text())
if 'new' in sys.argv[1:]:
    plan={**plan,'sessions':[s for s in plan['sessions'] if s['method'] in ('dc','rb','tfgrpo')]}
    PLAN_NAME='REPLAY_PLAN_K1_TRAJ_NEW.json';(H/PLAN_NAME).write_text(json.dumps(plan,indent=2)+'\n')
control=D/'control_stage_b';control.mkdir(exist_ok=True)
def worker(row):
    index,item=row;out=D/item['output'];out.mkdir(parents=True,exist_ok=True);sp=out/'STATUS.json'
    if sp.exists() and json.loads(sp.read_text()).get('status')=='complete':return dict(queue_index=index,status='complete',reused=True,attempts=0)
    log=control/('replay_%04d.log'%index)
    env={**os.environ,'RSI_GATEWAY':cfg['gateway_url'],'PYTHONPATH':str(H/'sdk')+':'+str(H)}
    for attempt in (1,2):
        with log.open('a') as f:proc=subprocess.run([PY,str(H/'replay_session.py'),str(index),PLAN_NAME],cwd=H,env=env,stdout=f,stderr=f)
        st=json.loads(sp.read_text()) if sp.exists() else {}
        if st.get('status')=='complete':return dict(queue_index=index,status='complete',reused=False,attempts=attempt)
        if not st.get('error') or attempt==2:break
    return dict(queue_index=index,status=st.get('status','missing'),returncode=proc.returncode,attempts=attempt,error=st.get('error'))
rows=[]
def save():(control/'STAGE_B_PROGRESS.json').write_text(json.dumps(dict(done=len(rows),total=len(plan['sessions']),complete=sum(x['status']=='complete' for x in rows),failed=sum(x['status']!='complete' for x in rows),rows=rows,updated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z')),indent=2)+'\n')
with concurrent.futures.ThreadPoolExecutor(max_workers=cfg['concurrency']) as ex:
    for fut in concurrent.futures.as_completed([ex.submit(worker,x) for x in enumerate(plan['sessions'])]):rows.append(fut.result());save()
failed=[x for x in rows if x['status']!='complete'];summary=dict(status='complete' if not failed else 'interrupted',queue_count=len(rows),completed=len(rows)-len(failed),failed=failed,finished_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
(control/'STAGE_B_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True);raise SystemExit(bool(failed))
