import sys
from run_pb1 import course
rep,method,cid,start=sys.argv[1:]
r=course(method,cid,int(rep),int(start))
raise SystemExit(0 if r["status"] in ("partial","complete") else 1)
