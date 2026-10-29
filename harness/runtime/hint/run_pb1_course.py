"""Entry point: run one method's practice on one chain from level 1, through run_pb1.course().

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
import sys
from run_pb1 import course
rep,method,cid=sys.argv[1:]
r=course(method,cid,int(rep))
raise SystemExit(0 if r['status']=='complete' else 1)
