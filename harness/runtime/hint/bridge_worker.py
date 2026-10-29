"""Worker that runs inside the network-free candidate container and forwards declared API calls to the host
through bridge.py.

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
import contextlib,importlib.util,io,json,sys,traceback
protocol_out=sys.stdout
def emit(v):protocol_out.write('@@BENCH_RPC@@'+json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');protocol_out.flush()
class API:
 def _call(self,op,**args):
  emit(dict(type='request',op=op,args=args));line=sys.stdin.readline()
  if not line:raise RuntimeError('Host RPC closed')
  response=json.loads(line)
  if not response.get('ok'):raise RuntimeError(response.get('error','RPC failed'))
  return response['value']
 def call_model(self,prompt,system=None,tools=True):return self._call('call_model',prompt=prompt,system=system,tools=tools)
 def inspect_source(self,table,offset=0,limit=100):return self._call('inspect_source',table=table,offset=offset,limit=limit)
 def run_candidate(self,code):return self._call('run_candidate',code=code)

cfg=json.loads(sys.stdin.readline());logs=io.StringIO();sys.path.insert(0,'/candidate')
try:
 with contextlib.redirect_stdout(logs),contextlib.redirect_stderr(logs):
  spec=importlib.util.spec_from_file_location('candidate_module','/candidate/'+cfg['file'])
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  function=getattr(module,cfg['function'])
  args=cfg['args']
  value=function(*args,API()) if cfg['with_api'] else function(*args)
  json.dumps(value,allow_nan=False)
 emit(dict(type='result',ok=True,value=value,logs=logs.getvalue()))
except BaseException as e:emit(dict(type='result',ok=False,error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),logs=logs.getvalue()))
