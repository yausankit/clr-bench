"""Server wrapper shared by replay sessions; no dataset or method logic here."""
import threading
from common import read,dump
from evaluator import Evaluator
from evolution_curriculum.service import make_server
from evolution_curriculum.client import Client
from solver import Native,solve
import methods_r3 as methods
CORRECT='Verdict: correct. The answer passed all tests, including hidden tests.'
WRONG='Verdict: wrong. The answer failed at least one test. The hidden tests are not shown.'
def strict_feedback(g):
    pub=g['cases'][0];ok=all(c['pass_'] for c in g['cases'])
    return dict(status='scored',pass_=ok,score=float(ok),actual=pub['actual'],expected=g['expected'],checks=pub['checks'],shape_ok=pub['shape_ok'],feedback_scope='public outputs plus binary strict verdict',verdict=CORRECT if ok else WRONG)
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
            serial=len(self.verdicts)+1;path=self.output/f'strict_grades/{serial:04d}.json';dump(path,g)
            fb=strict_feedback(g);self.verdicts.append(dict(task_id=args['task_id'],verdict=fb['verdict'],grade=str(path)))
            return fb
        return self.evaluator.dispatch(r)
class Environment:
    def __init__(self,evaluator,ids,learning=False,verdicts=None):
        self.server=make_server(Scoped(evaluator,ids,learning,verdicts if verdicts is not None else []),port=0)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
    def close(self):self.server.shutdown();self.server.server_close()
