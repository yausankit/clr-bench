#!/usr/bin/env python3
"""Fetch monthly English Wikipedia pageviews once per named list (0.5s cadence)."""
import json,time,urllib.parse,urllib.request
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parent
proxy=urllib.request.ProxyHandler()  # uses HTTP_PROXY / HTTPS_PROXY from the environment, if set
opener=urllib.request.build_opener(proxy)
raw=ROOT/"salience"/"raw";raw.mkdir(parents=True,exist_ok=True)
for lp in sorted((ROOT/"lists").glob("*.yaml")):
    for item in yaml.safe_load(lp.read_text(encoding="utf-8")) or []:
        cid=str(item["id"])
        src=str(item.get("source",""))
        if "wikipedia.org/wiki/" in src: title=src.split("wikipedia.org/wiki/",1)[1].split()[0]
        else: title={"sp500":"S%26P_500","nasdaq_100":"Nasdaq-100","big_ten":"Big_Ten_Academic_Alliance",
                     "utrecht_network":"Utrecht_Network"}.get(cid,cid)
        path=raw/f"{lp.stem}__{cid}.json"
        if path.exists(): continue
        title=urllib.parse.quote(urllib.parse.unquote(title),safe="()_,-")
        url=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{title}/monthly/20251001/20260930"
        req=urllib.request.Request(url,headers={"User-Agent":"DS_UN_f6 research/1.0 contact: research@example.org","Accept":"application/json"})
        delay=0.5
        while True:
            try:
                with opener.open(req,timeout=60) as resp:
                    obj=json.loads(resp.read())
                obj["_requested_title"]=urllib.parse.unquote(title)
                path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
                print(lp.stem,cid,title,"views",sum(int(x.get("views",0)) for x in obj.get("items",[])),flush=True)
                break
            except urllib.error.HTTPError as e:
                if e.code==404:
                    path.write_text(json.dumps({"status":404,"title":title},sort_keys=True)+"\n",encoding="utf-8")
                    print(lp.stem,cid,title,"404",flush=True);break
                if e.code==429:
                    print("429",cid,"wait",int(delay),flush=True);time.sleep(delay);delay=min(600,delay*2);continue
                print("HTTP",e.code,cid,"wait",int(delay),flush=True);time.sleep(delay);delay=min(600,delay*2)
            except Exception as e:
                print(type(e).__name__,cid,"wait",int(delay),flush=True);time.sleep(delay);delay=min(600,delay*2)
        time.sleep(0.5)
