import ast
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
import os
# Root that holds the upstream method code under upstream/{ace,gepa,EvoSkill} (see methods/fetch_upstream.sh).
# Taken from $CLRBENCH_METHODS_ROOT, else CONFIG.json 'methods_root' (written by harness/setup_run.py).
def _methods_root():
 if os.environ.get('CLRBENCH_METHODS_ROOT'):return Path(os.environ['CLRBENCH_METHODS_ROOT'])
 try:
  c=json.loads((ROOT.parent/'CONFIG.json').read_text())
  if c.get('methods_root'):return Path(c['methods_root'])
 except (OSError,ValueError):pass
 return next((p/'methods' for p in ROOT.parents if (p/'methods'/'upstream').is_dir()),ROOT.parents[2]/'methods')
OLD=_methods_root()
METHODS=['frozen','ace','gepa','evoskill','dc','rb','tfgrpo','hist','oracle','nameoracle','histhint','nameproc','histconv','histproc','webonly','histweb','histwebng']
EMPTY='\n'.join('## '+s for s in ['STRATEGIES & INSIGHTS','FORMULAS & CALCULATIONS','CODE SNIPPETS & TEMPLATES','COMMON MISTAKES TO AVOID','PROBLEM-SOLVING HEURISTICS','CONTEXT CLUES & INDICATORS','OTHERS'])
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def compact(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def materialize(folder,files):
 for n,c in files.items():p=Path(folder)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(c)
def initial(method):
 if method=='ace':return dict(memory=EMPTY,next_global_id=1)
 if method=='evoskill':return dict(files={})
 if method=='rb':return dict(experiences=[],next_global_id=1)
 if method=='tfgrpo':return dict(experiences={},next_global_id=0)
 if method=='oracle':return dict(text=(ROOT.parent/'HINT_NC100.txt').read_text().strip())
 return dict(text='')
def persona(task,method,state):
 text=task['system']
 if method=='gepa' and state.get('text'):text+='\nLearned guidance:\n'+state['text']
 if method=='ace' and state['memory'].strip()!=EMPTY.strip():text+='\nLearned playbook:\n'+state['memory']
 if method=='evoskill' and state['files']:
  names={p:c[:700] for p,c in state['files'].items() if Path(p).name=='SKILL.md'}
  text+='\nLearned skills (read_skill opens files, run_skill runs a Python helper run(data,args) on the public input):\n'+compact(names)+'\nAvailable files: '+compact(list(state['files']))
 if method=='dc' and state.get('text'):text+='\nLearned cheatsheet:\n'+state['text']
 if method=='rb' and state.get('experiences'):
  from evo_methods import memory_section
  text+=memory_section(task['prompt'],state['experiences'])
 if method=='tfgrpo' and state.get('experiences'):
  body='\n'.join(f'[{key}]. {value}' for key,value in state['experiences'].items())
  text+='\n\nWhen solving problems, you MUST first carefully read and understand the helpful instructions and experiences:\n'+body
 if method=='hist' and state.get('text'):text+='\nYour earlier practice attempts and the feedback they received:\n'+state['text']
 if method=='oracle' and state.get('text'):text+='\nVERIFIED LESSON (correct, from the task designers):\n'+state['text']
 if method=='histhint':
  text+='\nVERIFIED LESSON (correct, from the task designers):\n'+(ROOT.parent/'HINT_NC100.txt').read_text().strip()
  if state.get('text'):text+='\nYour earlier practice attempts and the feedback they received:\n'+state['text']
 if method=='nameoracle':
  text+='\nLABEL MEANINGS (correct, from the task designers):\n'+(ROOT.parent/'CLASS_NAMES.txt').read_text().strip()
  text+='\nApply each rule to every described value that belongs to the named grouping, and to no other value.'
 if method=='nameproc':
  text+='\nLABEL MEANINGS (correct, from the task designers):\n'+(ROOT.parent/'CLASS_NAMES.txt').read_text().strip()
  text+='\nApply each rule to every described value that belongs to the named grouping, and to no other value. '
  text+='Before coding, go through every described value, decide membership in the named grouping for each one, and hard-code the complete member set.'
 if method in ('histconv','histproc'):
  f='LESSON_CONV.txt' if method=='histconv' else 'LESSON_PROC.txt'
  text+='\nVERIFIED LESSON (correct, from the task designers):\n'+(ROOT.parent/f).read_text().strip()
  if state.get('text'):text+='\nYour earlier practice attempts and the feedback they received:\n'+state['text']
 if method in ('webonly','histweb'):
  text+='\nWEB LOOKUP (named groupings published on the Web that include each label\'s example value):\n'+(ROOT.parent/'SEARCH.txt').read_text().strip()
  if method=='histweb' and state.get('text'):text+='\nYour earlier practice attempts and the feedback they received:\n'+state['text']
 if method=='histwebng':
  text+='\nWEB LOOKUP (named groupings published on the Web that include each label\'s example value):\n'+(ROOT.parent/'SEARCH_NOGOLD.txt').read_text().strip()
  if state.get('text'):text+='\nYour earlier practice attempts and the feedback they received:\n'+state['text']
 return text
