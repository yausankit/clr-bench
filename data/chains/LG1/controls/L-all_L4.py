"""LG: proxy-connection and SSH-login event counts per workstation.

The world is built from the Loghub OpenSSH and Proxifier samples (sources/).  Each sampled
log record is an event of one workstation; the four trap fields are the target top-level
domain, the target port and the client process of a proxy connection, and the user name of
an SSH login.  All values come from the original log records ("proxy.cse.cuhk.edu.hk:5070
open ... chrome.exe", "Failed password for root ...") and are only replaced through
set_value()."""
import hashlib
import random
from pathlib import Path

ANSWER_FORMAT = "text"
TRAP_FIELDS = ["proxy_connections.tld", "proxy_connections.port", "proxy_connections.client_app",
               "ssh_logins.user"]
TASK = ("Each proxy connection and each SSH login adds one event to the total of the workstation "
        "it belongs to.")
ENTITY_NOUN = "workstation"
INPUT_FORMAT = """The input is plain text. The first line starts with WORKSTATIONS and lists the
workstation ids separated by |. Then come the proxy connections, one per line, as
PROXY|<record id>|<workstation>|<time>|<target host>|<target port>|<client process>|<action>,
and the SSH logins as SSH|<record id>|<workstation>|<time>|<user name>|<source address>.
Every PROXY line is one proxied connection, every SSH line is one SSH login."""

HERE = Path(__file__).resolve().parent
_N = 40
_MIN_PER, _MAX_PER = 3, 6
_CACHE = {}


def _read(name):
    return (HERE / "sources" / name).read_text(encoding="utf-8", errors="replace").splitlines()


def _universe(name, column=0):
    path = HERE / "universes" / f"{name}.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    return {line.split("\t")[column] for line in lines[1:] if line.strip()}


def _proxy_pool():
    if "proxy" not in _CACHE:
        tlds = _universe("tld")
        ports = _universe("port")
        apps = _universe("client_app")
        pool = []
        for line in _read("Proxifier_2k.log"):
            line = line.strip()
            if not line.startswith("[") or " - " not in line:
                continue
            head, _, rest = line.partition(" - ")
            if "]" not in head:
                continue
            stamp = head.split("]", 1)[0].strip("[")
            app = head.split("]", 1)[1].strip().split(" ")[0]
            parts = rest.split()
            if len(parts) < 2 or ":" not in parts[0]:
                continue
            host, _, port = parts[0].rpartition(":")
            if not port.isdigit() or "." not in host:
                continue
            tld = host.rsplit(".", 1)[-1].lower()
            action = parts[1].rstrip(",")
            if action != "open":
                continue
            if tld not in tlds or port not in ports or app not in apps:
                continue
            pool.append({"time": stamp, "host": host, "port": port, "app": app, "action": action})
        if len(pool) < _N * _MAX_PER:
            raise RuntimeError(f"proxy pool too small: {len(pool)}")
        _CACHE["proxy"] = pool
    return _CACHE["proxy"]


def _login_pool():
    if "login" not in _CACHE:
        users = _universe("user")
        pool = []
        for line in _read("OpenSSH_2k.log"):
            line = line.strip()
            if " sshd[" not in line or "]: " not in line:
                continue
            stamp = line.split(" sshd[", 1)[0]
            body = line.split("]: ", 1)[1]
            user = None
            if "Invalid user " in body:
                user = body.split("Invalid user ", 1)[1].split(" ", 1)[0]
            elif "Failed password for invalid user " in body:
                user = body.split("Failed password for invalid user ", 1)[1].split(" ", 1)[0]
            elif "Failed password for " in body:
                user = body.split("Failed password for ", 1)[1].split(" ", 1)[0]
            elif "user=" in body:
                user = body.split("user=", 1)[1].split(" ", 1)[0].strip()
            if not user or user not in users:
                continue
            src = ""
            if " from " in body:
                src = body.split(" from ", 1)[1].split(" ", 1)[0].rstrip(",")
            elif "rhost=" in body:
                src = body.split("rhost=", 1)[1].split(" ", 1)[0]
            pool.append({"time": stamp, "user": user, "src": src})
        if len(pool) < _N * _MAX_PER:
            raise RuntimeError(f"login pool too small: {len(pool)}")
        _CACHE["login"] = pool
    return _CACHE["login"]


def _rng(seed, step):
    return random.Random(int(hashlib.sha256(f"{seed}/{step}/LG".encode()).hexdigest(), 16))


def base_world(seed: int, step: str) -> dict:
    r = _rng(seed, step)
    ents = [f"ws{i:02d}" for i in range(1, _N + 1)]
    proxy = {}
    owners = [ent for ent in ents for _ in range(r.randint(_MIN_PER, _MAX_PER))]
    for i, (rec, ent) in enumerate(zip(r.sample(_proxy_pool(), len(owners)), owners)):
        rid = f"P{i + 1:04d}"
        proxy[rid] = dict(rec, id=rid, entity=ent)
    logins = {}
    owners = [ent for ent in ents for _ in range(r.randint(_MIN_PER, _MAX_PER))]
    for i, (rec, ent) in enumerate(zip(r.sample(_login_pool(), len(owners)), owners)):
        rid = f"L{i + 1:04d}"
        logins[rid] = dict(rec, id=rid, entity=ent)
    return {"entities": ents, "proxy": proxy, "logins": logins}


def entities(world) -> list:
    return sorted(world["entities"])


def _field_parts(field):
    table, _, name = field.partition(".")
    return table, name


def slots(world, field: str) -> list:
    table, _ = _field_parts(field)
    key = "proxy" if table == "proxy_connections" else "logins"
    return sorted((rec["entity"], rid) for rid, rec in world[key].items())


def set_value(world, field: str, pos: str, value: str) -> None:
    table, name = _field_parts(field)
    key = "proxy" if table == "proxy_connections" else "logins"
    rec = world[key][pos]
    if name == "tld":
        rec["host"] = rec["host"].rsplit(".", 1)[0] + "." + value
    elif name == "port":
        rec["port"] = value
    elif name == "client_app":
        rec["app"] = value
    elif name == "user":
        rec["user"] = value
    else:
        raise KeyError(field)


def _skip(excluded):
    out = {}
    for f, p in excluded:
        out.setdefault(f, set()).add(p)
    return out


def total(world, entity: str, excluded: set) -> int:
    skip = _skip(excluded)
    n = 0
    pt = skip.get("proxy_connections.tld", set())
    pp = skip.get("proxy_connections.port", set())
    pa = skip.get("proxy_connections.client_app", set())
    for rid, rec in world["proxy"].items():
        if rec["entity"] == entity and rid not in pt and rid not in pp and rid not in pa:
            n += 1
    su = skip.get("ssh_logins.user", set())
    for rid, rec in world["logins"].items():
        if rec["entity"] == entity and rid not in su:
            n += 1
    return n


def render(world, entity_ids):
    keep = set(entity_ids)
    out = ["WORKSTATIONS|" + "|".join(sorted(keep))]
    for rid, rec in sorted(world["proxy"].items()):
        if rec["entity"] in keep:
            out.append("|".join(["PROXY", rid, rec["entity"], rec["time"], rec["host"],
                                 str(rec["port"]), rec["app"], rec.get("action", "open")]))
    for rid, rec in sorted(world["logins"].items()):
        if rec["entity"] in keep:
            out.append("|".join(["SSH", rid, rec["entity"], rec["time"], rec["user"], rec.get("src", "")]))
    return "\n".join(out) + "\n"


_FULL = {("proxy", "tld"): "proxy_connections.tld",
         ("proxy", "port"): "proxy_connections.port",
         ("proxy", "client_app"): "proxy_connections.client_app",
         ("login", "user"): "ssh_logins.user"}


def _records(data):
    for line in data.splitlines():
        parts = line.split("|")
        if parts[0] == "PROXY" and len(parts) >= 8:
            host = parts[4]
            yield ("proxy", parts[1], parts[2], {"tld": host.rsplit(".", 1)[-1].lower(),
                                                 "port": parts[5], "client_app": parts[6]})
        elif parts[0] == "SSH" and len(parts) >= 6:
            yield ("login", parts[1], parts[2], {"user": parts[4]})


def reference(data, excluded: dict):
    out = {}
    for line in data.splitlines():
        if line.startswith("WORKSTATIONS|"):
            for ent in line.split("|")[1:]:
                out[ent] = 0
    for kind, _, ent, vals in _records(data):
        out.setdefault(ent, 0)
        if any(v in (excluded.get(_FULL[(kind, k)]) or set()) for k, v in vals.items()):
            continue
        out[ent] += 1
    return out


def values(data, field: str) -> list:
    table, name = _field_parts(field)
    kind = "proxy" if table == "proxy_connections" else "login"
    return [vals[name] for k, _, _, vals in _records(data) if k == kind]


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'proxy_connections.client_app': ['EXCEL.EXE', 'ONENOTE.EXE', 'OUTLOOK.EXE', 'Skype.exe', 'WeCom.exe', 'WinSCP.exe', 'Wiz.exe', 'explorer.exe', 'soffice.exe', 'telegram.exe', 'wpp.exe', 'wuauclt.exe'], 'proxy_connections.port': ['137', '1433', '162', '176', '2188', '2842', '3389', '3604', '3649', '593', '702', '88'], 'proxy_connections.tld': ['ae', 'aeg', 'am', 'bj', 'ca', 'cc', 'ch', 'cy', 'de', 'et', 'fr', 'gbiz', 'gop', 'ie', 'ipiranga', 'ir', 'komatsu', 'kr', 'li', 'mt', 'office', 'parts', 'ru', 'vu']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
