"""Entry point: run one method's practice on one chain from level 1, through run_pb1.course().

Part of harness/runtime/self: the practice harness for learning from feedback alone (self)."""
import sys
from run_pb1 import course
rep,method,cid=sys.argv[1:]
r=course(method,cid,int(rep))
raise SystemExit(0 if r['status']=='complete' else 1)
