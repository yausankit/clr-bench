"""Host side of the bridge between the solver and a candidate program running in a network-free container.
The container sees no grader files; calls it needs (for example a skill's helper) go through audited host RPC.

Part of harness/runtime/test: the test harness: replay of learned states on the test task, and the frozen agent."""
import json,os,subprocess,uuid,traceback
from pathlib import Path
from common import ROOT,dump,compact,materialize
from runtime_errors import InfrastructureFailure,APIArgumentError
def invoke(folder,files,file,function,args,callback=None):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);candidate=folder/'candidate';materialize(candidate,files)
 cfg=dict(file=file,function=function,args=args,with_api=callback is not None);dump(folder/'INPUT.json',cfg)
 name='clrbench-skill-'+str(uuid.uuid4())
 cmd=['docker','run','--rm','-i','--name',name,'--label','clrbench.skill=1','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','2g','--pids-limit','128','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,noexec,size=32m','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONUTF8=1','--mount',f'type=bind,src={candidate.resolve()},dst=/candidate,readonly','--mount',f'type=bind,src={ROOT/"bridge_worker.py"},dst=/bridge.py,readonly','--workdir','/tmp','python:3.12-slim','python','-u','/bridge.py']
 dump(folder/'CONTAINER.json',dict(name=name,command=cmd,wall_clock_timeout=None))
 records=[];result=None;normal_exit=False
 with (folder/'stderr.log').open('w') as err,(folder/'stdout.log').open('w') as out:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
  try:
   p.stdin.write(compact(cfg)+'\n');p.stdin.flush()
   for line in p.stdout:
    out.write(line);out.flush()
    if not line.startswith('@@BENCH_RPC@@'):continue
    message=json.loads(line[len('@@BENCH_RPC@@'):])
    if message['type']=='result':result=message;continue
    records.append(message);dump(folder/'RPC.json',records)
    if callback is None:response=dict(ok=False,error='No host API is available to a skill helper')
    else:
     try:response=dict(ok=True,value=callback(message['op'],message['args'],len(records)))
     except APIArgumentError as e:response=dict(ok=False,error='ValueError: '+str(e))
     except Exception as e:
      dump(folder/'HOST_FAILURE.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),operation=message['op']))
      raise InfrastructureFailure(f'Host callback failed: {type(e).__name__}: {e}') from e
    records[-1]['response']=response;dump(folder/'RPC.json',records)
    p.stdin.write(compact(response)+'\n');p.stdin.flush()
   p.stdin.close();rc=p.wait();normal_exit=True
  finally:
   if not normal_exit:
    subprocess.run(['docker','rm','-f',name],capture_output=True,text=True)
    p.wait()
 if result is None:
  result=dict(ok=False,error_type='AgentProcessError',error='No final agent result',returncode=rc,stderr=(folder/'stderr.log').read_text())
  if rc==125:result['infrastructure_error']=True
 result['rpc_count']=len(records);result['returncode']=rc;dump(folder/'EXECUTION.json',result)
 return result
