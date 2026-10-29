"""Entry point used by stage A: run one method's practice on one chain from a given level, through run_pb1.course().

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
import sys
from run_pb1 import course
rep,method,cid,start=sys.argv[1:]
r=course(method,cid,int(rep),int(start))
raise SystemExit(0 if r["status"] in ("partial","complete") else 1)
