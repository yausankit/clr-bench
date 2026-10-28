import sys
from run_pb1 import course
rep,method,cid=sys.argv[1:]
r=course(method,cid,int(rep))
raise SystemExit(0 if r['status']=='complete' else 1)
