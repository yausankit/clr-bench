from common import compact

CORRECT='Verdict: correct. The answer passed all tests, including hidden tests.'

def counterexample(g,task,case=None):
    if case is None: case=next(c for c in sorted(g['cases'],key=lambda c:c['input']) if not c['pass_'])
    i=case['input']
    data=task['public'] if i==0 else task['hidden'][i-1].get('data',task['hidden'][i-1].get('fixture'))
    expected=task['expected'][i]
    if task['kind']=='files':expected=expected['value']
    obs=case['actual']
    if not obs['ok']:
        actual='error: '+obs['error_type']+': '+obs.get('error','')[:500]
    elif not case['shape_ok']:
        actual='error: FormatError: '+('Output shape does not match the required fields: '+compact(obs['value']))[:500]
    else:actual=obs['value']
    where='the example input' if i==0 else 'one of the hidden test inputs'
    text=('Wrong. Your submission gives a wrong result on the input below, which is '+where+'.\n'
          'Input:\n'+compact(data)+'\nExpected result: '+compact(expected)+'\nYour result: '+(actual if isinstance(actual,str) else compact(actual)))
    changes=task['hidden'][i-1].get('changes') if i>0 else None
    if changes:
        text+='\nCompared with the example input, this input differs only in: '+'; '.join(
            f"{c['field']}: one value '{c['from']}' was replaced by '{c['to']}'" for c in changes)+'.'
    return dict(view_index=i,input=data,expected=expected,actual=actual,where=where,text=text)

def strict_feedback(g,task):
    pub=g['cases'][0];ok=all(c['pass_'] for c in g['cases'])
    fb=dict(status='scored',pass_=ok,score=float(ok),actual=pub['actual'],expected=g['expected'],checks=pub['checks'],shape_ok=pub['shape_ok'],feedback_scope='one counterexample per failing view; strict binary score',verdict=CORRECT)
    if not ok:
        failures=[c for c in sorted(g['cases'],key=lambda c:c['input']) if not c['pass_']]
        ces=[counterexample(g,task,c) for c in failures]
        first=ces[0]
        first_case=failures[0]
        fb.update(actual=first['actual'],expected=first['expected'],checks=first_case['checks'],shape_ok=first_case['shape_ok'],verdict='\n\n'.join(ce['text'] for ce in ces))
    return fb
