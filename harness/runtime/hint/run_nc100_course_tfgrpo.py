"""Entry point used by stage A for Training-Free GRPO: run its practice on one chain through run_pb1_tfgrpo.course().

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
import sys
from run_pb1_tfgrpo import course
rep,method,cid,start=sys.argv[1:]
r=course(method,cid,int(rep),int(start))
raise SystemExit(0 if r["status"] in ("partial","complete") else 1)
