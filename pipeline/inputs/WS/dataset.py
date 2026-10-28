"""WS: a security firm's audit records, aggregated per client site.

World shape: sites -> hosts -> scans -> findings.  A finding counts once toward the
total of the site that owns the host where the scan ran.  Trap fields sit on the
record whose exclusion the level rule states: a finding's CWE / language, or a
host's TLD (excluding the host also removes its scans and findings).
"""
import hashlib
import random
from pathlib import Path

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["findings.cwe", "hosts.tld", "findings.language"]
ENTITY_NOUN = "site"
ENTITY_NOUN_PLURAL = "sites"
TASK = ("Each finding counts once toward the total of the site that owns the host on which it was "
        "recorded; a site's total is the number of its findings that are counted.")
INPUT_FORMAT = (
    "The top-level JSON object has one key, sites. Each site has id, name, and hosts. Each host has "
    "id, hostname, tld, and scans. Each scan has id, profile, and findings. Each finding has id, "
    "title, cwe, language, and severity.")

N_SITES = 36
SEVERITIES = ["info", "warning", "serious", "critical"]
PROFILES = ["baseline", "deep", "authenticated", "payment-flow"]
TITLES = [
    "Reflected input in the search form",
    "Missing security header on the admin console",
    "Weak TLS configuration on the login endpoint",
    "Session cookie without the secure attribute",
    "Directory listing enabled on a static path",
    "Outdated library used by the checkout page",
    "Verbose error page exposes a stack trace",
    "Permissive cross-origin policy on the API",
    "Unvalidated redirect in the sign-out flow",
    "Predictable identifier in a password reset link",
    "Missing rate limit on the authentication form",
    "Mixed content on the account settings page",
]
_CACHE = {}


def _rng(seed, step, name):
    digest = hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest()
    return random.Random(int(digest, 16))


def _universe(name):
    if name not in _CACHE:
        path = Path(__file__).resolve().parent / "universes" / f"{name}.tsv"
        values = []
        with path.open(encoding="utf-8") as fh:
            header = fh.readline().rstrip("\n").split("\t")
            pos = header.index("value")
            for line in fh:
                row = line.rstrip("\n").split("\t")
                if len(row) > pos and row[pos]:
                    values.append(row[pos])
        _CACHE[name] = sorted(values)
    return _CACHE[name]


def base_world(seed: int, step: str) -> dict:
    rng = _rng(seed, step, "world")
    cwes = _universe("cwe")
    tlds = _universe("tld")
    langs = _universe("language")
    sites = []
    host_no = 0
    scan_no = 0
    finding_no = 0
    for i in range(1, N_SITES + 1):
        site_id = f"site-{i:02d}"
        label = f"client{i:02d}"
        n_hosts = 4 + (i % 3)
        hosts = []
        for j in range(n_hosts):
            host_no += 1
            tld = tlds[rng.randrange(len(tlds))]
            host_id = f"host-{host_no:03d}"
            scans = []
            for k in range(1 + (host_no % 2)):
                scan_no += 1
                findings = []
                for m in range(1 + ((host_no + k) % 2)):
                    finding_no += 1
                    findings.append({
                        "id": f"finding-{finding_no:05d}",
                        "title": TITLES[(finding_no + i) % len(TITLES)],
                        "cwe": cwes[rng.randrange(len(cwes))],
                        "language": langs[rng.randrange(len(langs))],
                        "severity": SEVERITIES[rng.randrange(len(SEVERITIES))],
                    })
                scans.append({"id": f"scan-{scan_no:04d}",
                              "profile": PROFILES[(scan_no + i) % len(PROFILES)],
                              "findings": findings})
            hosts.append({"id": host_id,
                          "hostname": f"node{j + 1}.{label}.example.{tld}",
                          "tld": tld,
                          "scans": scans})
        sites.append({"id": site_id, "name": f"Client {i:02d} web estate", "hosts": hosts})
    return {"sites": sites}


def entities(world) -> list:
    return sorted(s["id"] for s in world["sites"])


def _site(world, entity):
    return next(s for s in world["sites"] if s["id"] == entity)


def _find_record(world, field, pos):
    if field == "hosts.tld":
        for site in world["sites"]:
            for host in site["hosts"]:
                if host["id"] == pos:
                    return host
        raise KeyError(pos)
    if field in ("findings.cwe", "findings.language"):
        for site in world["sites"]:
            for host in site["hosts"]:
                for scan in host["scans"]:
                    for finding in scan["findings"]:
                        if finding["id"] == pos:
                            return finding
        raise KeyError(pos)
    raise KeyError(field)


def slots(world, field: str) -> list:
    out = []
    for site in world["sites"]:
        if field == "hosts.tld":
            out.extend((site["id"], host["id"]) for host in site["hosts"])
        elif field in ("findings.cwe", "findings.language"):
            for host in site["hosts"]:
                for scan in host["scans"]:
                    out.extend((site["id"], f["id"]) for f in scan["findings"])
        else:
            raise KeyError(field)
    return sorted(out)


def set_value(world, field: str, pos: str, value: str) -> None:
    rec = _find_record(world, field, pos)
    if field == "hosts.tld":
        rec["tld"] = value
        rec["hostname"] = rec["hostname"].rsplit(".", 1)[0] + "." + value
    elif field == "findings.cwe":
        rec["cwe"] = value
    elif field == "findings.language":
        rec["language"] = value
    else:
        raise KeyError(field)


def total(world, entity: str, excluded: set) -> int:
    site = _site(world, entity)
    n = 0
    for host in site["hosts"]:
        if ("hosts.tld", host["id"]) in excluded:
            continue
        for scan in host["scans"]:
            for finding in scan["findings"]:
                if ("findings.cwe", finding["id"]) in excluded:
                    continue
                if ("findings.language", finding["id"]) in excluded:
                    continue
                n += 1
    return n


def render(world, entity_ids):
    wanted = set(entity_ids)
    sites = []
    for site in world["sites"]:
        if site["id"] not in wanted:
            continue
        hosts = []
        for host in site["hosts"]:
            scans = []
            for scan in host["scans"]:
                scans.append({"id": scan["id"], "profile": scan["profile"],
                              "findings": [dict(f) for f in scan["findings"]]})
            hosts.append({"id": host["id"], "hostname": host["hostname"], "tld": host["tld"],
                          "scans": scans})
        sites.append({"id": site["id"], "name": site["name"], "hosts": hosts})
    return {"sites": sites}


def reference(data, excluded):
    ex_tld = set(excluded.get("hosts.tld") or ())
    ex_cwe = set(excluded.get("findings.cwe") or ())
    ex_lang = set(excluded.get("findings.language") or ())
    out = {}
    for site in data.get("sites") or []:
        n = 0
        for host in site.get("hosts") or []:
            if host.get("tld") in ex_tld:
                continue
            for scan in host.get("scans") or []:
                for finding in scan.get("findings") or []:
                    if finding.get("cwe") in ex_cwe or finding.get("language") in ex_lang:
                        continue
                    n += 1
        out[site["id"]] = n
    return out


def values(data, field):
    out = []
    for site in data.get("sites") or []:
        for host in site.get("hosts") or []:
            if field == "hosts.tld":
                out.append(host.get("tld"))
            elif field in ("findings.cwe", "findings.language"):
                key = "cwe" if field == "findings.cwe" else "language"
                for scan in host.get("scans") or []:
                    for finding in scan.get("findings") or []:
                        out.append(finding.get(key))
            else:
                raise KeyError(field)
    return out
