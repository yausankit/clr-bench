"""Detect solver policies that are exactly identical across methods, so that identical programs are treated
consistently when states are compared.

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
import copy, shutil, time
from pathlib import Path
from common import ROOT, dump, read, persona

SETTINGS = dict(model='gpt-6-luna', temperature=0, thinking_budget=1024,
    max_tokens=16384, context_target=256000, approximate_compaction_threshold=180000,
    tool_rounds=41, grader_memory='2GiB', solver='this_condition/solver.py',
    transport='this_condition/transport.py', workspace='fresh_per_execution')

def generic_policy(task, method, state, client):
    if state.get('files'):return None
    return dict(task_id=task['task_id'], fixed_bundle=str(ROOT.parent/'harness_c4/bundle'),
        public_data_scope='exact same task public input; fresh execution workspace',
        messages=[dict(role='system', content=persona(task, method, state)),
                  dict(role='user', content=task['prompt'])],
        tools=[dict(type='function', function=d) for d in client.tools(task['task_id']).definitions],
        settings=copy.deepcopy(SETTINGS))

def verify_actual_input(folder, policy):
    rows=list((Path(folder)/'calls').glob('*/INPUT.json'))
    if len(rows)!=1:raise RuntimeError('Expected one complete formal Native solve session')
    actual=read(rows[0])
    if actual['messages']!=policy['messages'] or actual['tools']!=policy['tools']:
        raise RuntimeError('Policy descriptor differs from actual first request')
    return str(rows[0])

def reuse_formal(evaluator, task_id, state, folder, policy, donor_stage):
    folder,donor_stage=Path(folder),Path(donor_stage)
    donor_policy=read(donor_stage/'formal/POLICY.json')
    if policy is None or policy!=donor_policy:raise ValueError('Unproven policy equivalence')
    verify_actual_input(donor_stage/'formal',donor_policy)
    source=donor_stage.parent/'evaluator/evaluations'/f'{task_id}.json';grade=read(source)
    if grade['status']!='scored':raise ValueError('Only complete observations may be reused')
    destination=evaluator.output/'evaluations'/f'{task_id}.json'
    if destination.exists() or folder.exists():raise RuntimeError('Formal slot already exists')
    shutil.copytree(donor_stage/'formal',folder)
    provenance=dict(source_grade=str(source),source_formal=str(donor_stage/'formal'),
        reason='predeclared identical complete generic solver policy and public task',
        source_finished_at=grade.get('finished_at'),assigned_at=time.time(),
        new_model_calls=0,new_program_executions=0)
    dump(folder/'STATE_USED.json',state);dump(folder/'REUSE.json',provenance)
    dump(folder/'POLICY.json',policy)
    grade=copy.deepcopy(grade);grade.update(state=copy.deepcopy(state),reuse=provenance)
    dump(destination,grade)
    return grade['text'],grade
