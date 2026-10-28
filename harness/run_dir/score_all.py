#!/usr/bin/env python3
"""Score every phase-B program on its own level with the chain's score_k1_v3.py."""
import json,re,subprocess,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent
cfg=json.loads((D/'CONFIG.json').read_text())
N=Path(cfg['chain']);PY=cfg.get('python') or sys.executable
sys.path.insert(0,str(D/'harness_k1_test'))
from x_runner import extract_code
program_root=D/'programs_scored';scores_root=D/'scores_nc100_test'
methods=('ace','gepa','dc','tfgrpo','evoskill','rb')
if 'new' in sys.argv[1:]:methods=('ace','gepa','dc','tfgrpo','evoskill','rb')
rows=[];fence=chr(96)*3
for mode in ('self','hint'):
 for method in methods:
  for level in cfg['levels']:
   out=D/f'runs_nc100_test/{mode}/{method}/L{level}'
   status=json.loads((out/'STATUS.json').read_text())
   if status.get('status')!='complete':raise RuntimeError(f'incomplete {mode}/{method}/L{level}: {status}')
   raw=json.loads((out/'FINAL_PROGRAM.json').read_text())['text'].strip()
   code=extract_code(raw).strip()
   program=program_root/mode/method/f'L{level}.py';program.parent.mkdir(parents=True,exist_ok=True);program.write_text(code+'\n')
   for version in (0,):  # only version 0 is shipped and used in the paper
    cmd=[PY,str(N/'score_k1_v3.py'),'--version',str(version),'--program',f'L{level}={program}','--diagnostics']
    cp=subprocess.run(cmd,cwd=N,capture_output=True,text=True,check=True,timeout=3600)
    scored=json.loads(cp.stdout);score=scored['levels'][f'L{level}']
    entry=dict(mode=mode,method=method,level=level,version=version,score=score,program=str(program.relative_to(D)),raw_chars=len(raw),extracted_chars=len(code),fenced=fence in raw,instances=scored['instances'],diagnostics=scored.get('diagnostics',[]))
    blob=json.dumps(entry,ensure_ascii=False)
    if fence in blob or ('candidate.py' in blob and 'SyntaxError' in blob and 'line 1' in blob):raise RuntimeError(f'extraction failed {mode}/{method}/L{level}/v{version}')
    (out/f'SCORE_v{version}.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n')
    target=scores_root/f'v{version}'/mode/method/f'L{level}.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n')
    rows.append(entry)
summary=dict(status='complete',chain=str(N),course=cfg['course'],rows=rows,completed_at=time.strftime('%Y-%m-%d %H:%M:%S %z'))
(D/'SCORES_ALL.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status='complete',program_version_scores=len(rows))),flush=True)
