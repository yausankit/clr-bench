import concurrent.futures,copy,os,subprocess,sys,threading,traceback,time
from pathlib import Path
from common import *
from evaluator import Evaluator
from evolution_curriculum.service import make_server
from evolution_curriculum.client import Client
from solver import Native,solve
from equivalence import generic_policy,verify_actual_input,reuse_formal
import methods_r3 as methods
from evo_methods import sample_group
COURSES=(read(ROOT.parent/'CONFIG.json')['course'],)
CORRECT='Verdict: correct. The answer passed all tests, including hidden tests.'
WRONG='Verdict: wrong. The answer failed at least one test. The hidden tests are not shown.'
from feedback_m4 import strict_feedback
class Scoped:
    def __init__(self,evaluator,ids,learning,verdicts):
        self.evaluator=evaluator;self.ids=set(ids);self.learning=learning;self.verdicts=verdicts
        self.output=evaluator.output;self.lock=evaluator.lock
    def dispatch(self,r):
        op=r['operation'];args=r.get('arguments',{})
        if op=='tasks':return [t for t in self.evaluator.tasks.values() if t['task_id'] in self.ids and all(t.get(k)==v for k,v in args.items())]
        if args.get('task_id') not in self.ids:raise PermissionError('Task outside released scope')
        if op=='evaluate' or op=='feedback_pair':raise PermissionError('Controller only')
        if op=='feedback':
            if not self.learning:raise PermissionError('Formal feedback withheld')
            g=self.evaluator.grade(args['task_id'],args['text'],True)
            # Store complete grade only in controller evidence, never return it.
            serial=len(self.verdicts)+1;path=self.output/f'strict_grades/{serial:04}.json';dump(path,g)
            fb=strict_feedback(g,self.evaluator.private[args['task_id']]);self.verdicts.append(dict(task_id=args['task_id'],verdict=fb['verdict'],grade=str(path)))
            return fb
        return self.evaluator.dispatch(r)
class Environment:
    def __init__(self,evaluator,ids,learning=False,verdicts=None):
        self.server=make_server(Scoped(evaluator,ids,learning,verdicts if verdicts is not None else []),port=0)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
    def close(self):self.server.shutdown();self.server.server_close()
def course(method,sid,replicate,start_level=1):
    output=ROOT.parent/'runs_nc100_hint_v0'/f'rep{replicate}'/method/sid;output.mkdir(parents=True,exist_ok=True)
    state=initial(method);history=[];status=dict(method=method,course=sid,replicate=replicate,status='running',completed_levels=[],attempts=[])
    if start_level>1:
        previous=output/f'L{start_level-1}'
        state=read(previous/'STATE.json');last=read(previous/'END_LEVEL.json')['attempts']
        history=read(previous/f'a{last}/OWN_HISTORY.json')
        status['completed_levels']=list(range(1,start_level))
        status['attempts']=[dict(level=h['level'],attempt=h['attempt'],correct=h['feedback']['pass_'],updated=True) for h in history]
    dump(output/'STATUS.json',status)
    try:
        for level in range(start_level,int(os.getenv("NC100_MAX_LEVEL","5"))+1):
            stage=output/f'L{level}';stage.mkdir(exist_ok=True)
            if not (stage/'STATE_BEFORE.json').exists():dump(stage/'STATE_BEFORE.json',state)
            for attempt in (1,2,3):
                a=stage/f'a{attempt}';a.mkdir(exist_ok=True)
                existing=a/'PUBLIC_TRACE.json'
                if existing.exists():
                    trace=read(existing);group_trace=trace.get('group');history=read(a/'OWN_HISTORY.json');fb=trace['feedback'];task_prompt=trace['task_prompt']
                    state=read(a/'STATE.json') if (a/'UPDATE_SUMMARY.json').exists() else read(a/'STATE_BEFORE.json')
                else:
                    dump(a/'STATE_BEFORE.json',state)
                    ev=Evaluator(sid,a/'evaluator');tid=f'{sid}.L{level}.evaluation';task=ev.tasks[tid];task_prompt=task['prompt'];env=Environment(ev,[tid])
                    try:
                        client=Client(env.url);group_trace=None
                        if method=='tfgrpo' and attempt==1:
                            policy=None;rows=sample_group(env.url,sid,level,replicate,attempt,state,a/'formal',size=int(os.getenv('TFGRPO_GROUP_SIZE','4')))
                            grades=[];group_trace=[]
                            for i,row in enumerate(rows):
                                grade_i=ev.grade(tid,row['assistant_final'],True);grades.append(grade_i)
                                row_feedback=strict_feedback(grade_i,ev.private[tid])
                                group_trace.append(dict(task_id=tid,task_prompt=row['task_prompt'],assistant_final=row['assistant_final'],feedback=row_feedback,level=level,attempt=attempt,split='evaluation',reference_solution_provided=False,feedback_scope='one counterexample per failing view; strict binary score'))
                            chosen=0
                            text=group_trace[chosen]['assistant_final'];g=ev.evaluate(tid,text,state)
                            dump(a/'GROUP_GRADES.json',dict(size=len(group_trace),chosen=chosen+1,rows=[dict(index=i+1,pass_=row['feedback']['pass_'],feedback=row['feedback']) for i,row in enumerate(group_trace)]))
                        else:
                            policy=generic_policy(task,method,state,client);native=Native(client,a/'formal')
                            _,result=solve(native,dict(method=method,sample=sid,level=level,phase=f'PB3-rep{replicate}-a{attempt}-formal',split='evaluation',task_id=tid),copy.deepcopy(state),a/'formal')
                            text=result['text'];dump(a/'formal/POLICY.json',policy)
                            if policy is not None:verify_actual_input(a/'formal',policy)
                            g=ev.evaluate(tid,text,state)
                    finally:env.close()
                    dump(a/'GRADE.json',g);fb=strict_feedback(g,ev.private[tid])
                    trace=dict(task_id=tid,task_prompt=task_prompt,assistant_final=text,feedback=fb,level=level,attempt=attempt,split='evaluation',reference_solution_provided=False,feedback_scope='one counterexample per failing view; strict binary score',group=group_trace)
                    dump(existing,trace);history.append(trace);dump(a/'OWN_HISTORY.json',history)
                do_update=not(level==5 and attempt==3)
                if not (a/'UPDATE_SUMMARY.json').exists():
                    if do_update:
                        # Preserve a failed update's artifacts and resume with a fresh execution namespace.
                        update_path=a/'update'; call_path=a/'update_calls'
                        if update_path.exists() or call_path.exists():
                            retry=1
                            while (a/f'update_retry{retry}').exists() or (a/f'update_calls_retry{retry}').exists(): retry+=1
                            update_path=a/f'update_retry{retry}';call_path=a/f'update_calls_retry{retry}'
                        verdicts=[];eval_path=a/'update_evaluator'
                        if eval_path.exists():
                            retry=1
                            while (a/f'update_evaluator_retry{retry}').exists(): retry+=1
                            eval_path=a/f'update_evaluator_retry{retry}'
                        update_ev=Evaluator(sid,eval_path);env=Environment(update_ev,[h['task_id'] for h in history],True,verdicts)
                        try:
                            native=Native(Client(env.url),call_path);before=copy.deepcopy(state);state=methods.update(method,native,sid,level,state,history,update_path)
                        finally:env.close()
                        u=read(update_path/'UPDATE.json');dump(a/'UPDATE_SUMMARY.json',dict(method=method,level=level,attempt=attempt,before=before,after=state,state_changed=before!=state,policy_changed=u.get('changed',False),skipped=u.get('skipped'),strict_verdict_count=1+len(verdicts),current_answer_verdicts=1,development_verdicts=len(verdicts),verdict_events=verdicts,reflection_calls=u.get('reflection_calls',0),invalid_proposals=sum('invalid_output' in r for r in u.get('candidates',[])),candidate_records=u.get('candidates',[])))
                    else:dump(a/'UPDATE_SUMMARY.json',dict(method=method,level=level,attempt=attempt,state_changed=False,policy_changed=False,skipped='L5 a3 no update',strict_verdict_count=0,current_answer_verdicts=0,development_verdicts=0,reflection_calls=0,invalid_proposals=0))
                    dump(a/'STATE.json',state)
                else:state=read(a/'STATE.json')
                status['attempts'].append(dict(level=level,attempt=attempt,correct=fb['pass_'],updated=do_update));dump(output/'STATUS.json',status)
                if fb['pass_']:break
            dump(stage/'STATE.json',state);dump(stage/'END_LEVEL.json',dict(attempts=attempt,correct=fb['pass_'],first_correct=attempt if fb['pass_'] else None))
            status['completed_levels'].append(level);dump(output/'STATUS.json',status)
        status['status']='complete' if int(os.getenv("NC100_MAX_LEVEL","5"))>=5 else 'partial'
    except Exception:status.update(status='interrupted',error=traceback.format_exc())
    dump(output/'STATUS.json',status);print(compact(status),flush=True);return status

def main():
    import random
    cfg=json.load(sys.stdin)
    if cfg.get('courses')!=list(COURSES) or cfg.get('methods')!=['ace','gepa','evoskill'] or cfg.get('protocol')!='PB3_stage_A':
        raise ValueError('PB1 stage-A plan mismatch')
    if not read(ROOT.parent/'AUDIT.json')['pass_']:
        raise RuntimeError('PB1 zero-model qualification required')
    queue=[(1,m,c) for m in cfg['methods'] for c in COURSES]
    random.Random(read(ROOT.parent/'CONFIG.json')['stage_a_seed']).shuffle(queue)
    dump(ROOT/'PLAN_PB1.json',dict(**cfg,queue=queue,shuffle_seed=read(ROOT.parent/'CONFIG.json')['stage_a_seed'],replicates=1,concurrency=read(ROOT.parent/'CONFIG.json')['concurrency']))
    os.environ['RSI_GATEWAY']=cfg['gateway_url']
    def worker(item):
        rep,method,cid=item
        folder=ROOT.parent/'runs_nc100_hint_v0'/f'rep{rep}'/method
        folder.mkdir(parents=True,exist_ok=True)
        logpath=folder/(cid+'.log')
        with logpath.open('x') as log:
            p=subprocess.Popen([sys.executable,str(ROOT/'run_pb1_course.py'),str(rep),method,cid],
                stdout=log,stderr=log,env={**os.environ,'RSI_COMPACTION_LOG':str(folder/cid/'compactions.jsonl')})
            rc=p.wait()
        status=read(folder/cid/'STATUS.json')
        return dict(replicate=rep,method=method,course=cid,returncode=rc,status=status['status'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=read(ROOT.parent/'CONFIG.json')['concurrency']) as pool:
        rows=list(pool.map(worker,queue))
    dump(ROOT.parent/'runs_pb3/ENDPOINT_PB3.json',dict(
        status='complete' if all(x['returncode']==0 and x['status']=='complete' for x in rows) else 'interrupted',
        queue=queue,rows=rows,concurrency_limit=read(ROOT.parent/'CONFIG.json')['concurrency'],shuffle_seed=20262001))
    if any(x['returncode'] or x['status']!='complete' for x in rows):
        raise RuntimeError('Incomplete PB1 trajectories; preserve complete replies')
if __name__=='__main__':main()
