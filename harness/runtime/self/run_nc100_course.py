"""Entry point used by stage A: run one method's practice on one chain from a given level, through run_pb1.course().

Part of harness/runtime/self: the practice harness for learning from feedback alone (self)."""
import sys
from run_pb1 import course
rep,method,cid,start=sys.argv[1:]
r=course(method,cid,int(rep),int(start))
raise SystemExit(0 if r["status"] in ("partial","complete") else 1)
