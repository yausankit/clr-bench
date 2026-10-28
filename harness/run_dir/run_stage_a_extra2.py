import concurrent.futures,json,os,random,subprocess,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent
cfg=json.loads((D/'CONFIG.json').read_text())
sid=cfg['course'];PY=cfg.get('python') or sys.executable
ARGS=set(sys.argv[1:]);METHODS=('histhint',);MODES=('self',)
if 'new' in ARGS:METHODS=('ace','gepa','dc')
first_only='first' in ARGS
queue=[(mode,method) for mode in MODES for method in METHODS]
random.Random(cfg['stage_a_seed']).shuffle(queue)
control=D/'control_stage_a_extra2';control.mkdir(exist_ok=True)
(control/'STAGE_A_PLAN.json').write_text(json.dumps(dict(course=sid,methods=METHODS,modes=MODES,first_level_only=first_only,queue=queue,seed=cfg['stage_a_seed'],concurrency=cfg['concurrency'],gateway=cfg['gateway_url']),indent=2)+'\n')
def worker(item):
    mode,method=item
    out=D/f'runs_nc100_{mode}_v0'/'rep1'/method/sid
    h=D/f'harness_{mode}_v0'
    status=json.loads((out/'STATUS.json').read_text()) if (out/'STATUS.json').exists() else {}
    if status.get('status')=='complete':return dict(mode=mode,method=method,status='complete',reused=True)
    start=max(status.get('completed_levels',[0]))+1
    env={**os.environ,'RSI_GATEWAY':cfg['gateway_url'],'PYTHONPATH':str(h/'sdk')+':'+str(h),'RSI_COMPACTION_LOG':str(out/'compactions.jsonl'),'NC100_MAX_LEVEL':'1' if first_only else str(cfg['levels'][-1]),'TFGRPO_GROUP_SIZE':str(cfg.get('tfgrpo_group_size',4)),'TFGRPO_NUM_EXPERIENCES':str(cfg.get('tfgrpo_num_experiences',1)),'TOKENIZERS_PARALLELISM':'false'}
    out.mkdir(parents=True,exist_ok=True);log=control/('stage_a_%s_%s.log'%(mode,method))
    driver='run_nc100_course_tfgrpo.py' if method=='tfgrpo' else 'run_nc100_course.py'
    with log.open('a') as f:proc=subprocess.run([PY,str(h/driver),'1',method,sid,str(start)],cwd=h,env=env,stdout=f,stderr=f)
    st=json.loads((out/'STATUS.json').read_text()) if (out/'STATUS.json').exists() else {}
    return dict(mode=mode,method=method,status=st.get('status','missing'),completed_levels=st.get('completed_levels',[]),returncode=proc.returncode,error=st.get('error'))
rows=[]
def save():(control/'STAGE_A_PROGRESS.json').write_text(json.dumps(dict(done=len(rows),total=len(queue),rows=rows,updated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z')),indent=2)+'\n')
with concurrent.futures.ThreadPoolExecutor(max_workers=min(cfg['concurrency'],len(queue))) as ex:
    for fut in concurrent.futures.as_completed([ex.submit(worker,x) for x in queue]):rows.append(fut.result());save()
failed=[x for x in rows if x['status'] not in (('partial',) if first_only else ('complete',))]
summary=dict(status='complete' if not failed else 'interrupted',queue_count=len(rows),completed=len(rows)-len(failed),failed=failed,finished_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
(control/'STAGE_A_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True);raise SystemExit(bool(failed))
