#!/usr/bin/env python3
"""Generate universes/<U>.desc.tsv for LG using only snapshots under raw/."""

import csv
import html
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "universes"
TLD_SOURCE = "IANA Root Zone Database"
PORT_SOURCE = "IANA Service Name and Port Number Registry"


def clean(text):
    text = html.unescape(str(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def shorten(text, limit):
    text = clean(text).rstrip(" .;:,")
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    cut = re.sub(r"\s+(?:and|or|of|to|for|with|the|a|an)$", "", cut, flags=re.IGNORECASE)
    return cut


def write_desc(name, rows, expected):
    if len(rows) != expected:
        raise SystemExit(f"{name}: got {len(rows)} rows, expected {expected}")
    seen = set()
    lines = ["value\tdescription\tsource"]
    for value, description, source in rows:
        value, description, source = clean(value), clean(description), clean(source)
        if value in seen:
            raise SystemExit(f"{name}: duplicate value {value!r}")
        if not value or not description or not source:
            raise SystemExit(f"{name}: empty field in row {value!r}")
        if "\t" in value + description + source:
            raise SystemExit(f"{name}: tab in row {value!r}")
        if len(description) > 200:
            raise SystemExit(f"{name}: description too long for {value!r}: {len(description)}")
        seen.add(value)
        lines.append(f"{value}\t{description}\t{source}")
    (OUT / f"{name}.desc.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{name}: wrote {len(rows)} descriptions")


IDN_COUNTRY = {
    "xn--2scrj9c": "India", "xn--3e0b707e": "South Korea",
    "xn--45br5cyl": "India", "xn--45brj9c": "India", "xn--4dbrk0ce": "Israel",
    "xn--54b7fta0cc": "Bangladesh", "xn--80ao21a": "Kazakhstan",
    "xn--90a3ac": "Serbia", "xn--90ae": "Bulgaria", "xn--90ais": "Belarus",
    "xn--gecrj9c": "India", "xn--h2breg3eve": "India", "xn--h2brj9c": "India",
    "xn--h2brj9c8c": "India", "xn--j1amh": "Ukraine", "xn--j6w193g": "Hong Kong",
    "xn--kprw13d": "Taiwan", "xn--kpry57d": "Taiwan", "xn--l1acc": "Mongolia",
    "xn--lgbbat1ad8j": "Algeria", "xn--mgb9awbf": "Oman",
    "xn--mgba3a4f16a": "Iran", "xn--mgbaam7a8h": "United Arab Emirates",
    "xn--mgbah1a3hjkrd": "Mauritania", "xn--mgbai9azgqp6j": "Pakistan",
    "xn--mgbayh7gpa": "Jordan", "xn--mgbc0a9azcg": "Morocco",
    "xn--mgbcpq6gpa1a": "Bahrain", "xn--mgberp4a5d4ar": "Saudi Arabia",
    "xn--mgbpl2fh": "Sudan", "xn--mgbtx2b": "Iraq",
    "xn--mgbx4cd0ab": "Malaysia", "xn--mix891f": "Macau", "xn--node": "Georgia",
    "xn--o3cw4h": "Thailand", "xn--ogbpf8fl": "Syria", "xn--p1ai": "Russia",
    "xn--pgbs0dh": "Tunisia", "xn--q7ce6a": "Laos", "xn--qxa6a": "Europe",
    "xn--qxam": "Greece", "xn--fiqs8s": "China", "xn--fiqz9s": "China",
    "xn--wgbh1c": "Egypt", "xn--wgbl6a": "Qatar",
    "xn--xkc2al3hye2a": "Sri Lanka", "xn--xkc2dl3a5ee0h": "India",
    "xn--y9a3aq": "Armenia", "xn--yfro4i67o": "Singapore",
    "xn--ygbi2ammx": "Palestine", "xn--fpcrj9c3d": "India",
    "xn--s9brj9c": "India", "xn--mgbbh1a": "India", "xn--mgbgu82a": "India",
    "xn--rvc1e0am3e": "India", "xn--fzc2c9e2c": "Sri Lanka",
    "xn--clchc0ea0b2g2a9gcd": "Singapore",
}
EXTRA_COUNTRY = {"ac": "Ascension Island", "eu": "Europe", "uk": "United Kingdom"}
GTLD_MEANING = {
    "com": "commercial sites", "org": "organizations", "net": "network providers",
    "edu": "educational institutions", "gov": "government agencies",
    "mil": "military organizations", "int": "international organizations",
    "arpa": "internet infrastructure", "info": "information services",
    "biz": "businesses", "name": "personal names", "pro": "professionals",
    "mobi": "mobile devices", "asia": "the Asia region", "cat": "the Catalan language",
    "coop": "cooperatives", "jobs": "employment services", "museum": "museums",
    "post": "postal services", "tel": "telephone services", "travel": "the travel industry",
    "xxx": "adult entertainment", "aero": "air transport", "app": "applications",
    "dev": "software developers", "cloud": "cloud services", "store": "retail stores",
    "shop": "shopping", "online": "online services", "site": "websites",
}


def generate_tld():
    values = sorted(line.strip().lower() for line in
                    (RAW / "iana" / "tlds-alpha-by-domain.txt").read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#") and line.strip().lower() != "su")
    iso = {}
    with (RAW / "iso" / "countries.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            iso[row["alpha-2"].lower()] = row["name"]
    soup = BeautifulSoup((RAW / "desc" / "iana_root_db.html").read_text(encoding="utf-8"), "html.parser")
    table = soup.find("table", class_="rzdb-table")
    entries = {}
    for tr in table.find_all("tr")[1:]:
        cells = [clean(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
        if not cells:
            continue
        keys = set(re.findall(r"xn--[a-z0-9-]+", cells[0].lower()))
        first = cells[0].lstrip(".").split()[0].strip(".").replace(".", "").lower()
        keys.add(first)
        for key in keys:
            entries.setdefault(key, cells)
    rows = []
    for value in values:
        if value not in entries:
            raise SystemExit(f"tld: no IANA root database row for {value}")
        entry = entries[value]
        manager = shorten(entry[3], 118)
        is_cc = len(value) == 2 or value in IDN_COUNTRY
        if is_cc:
            country = IDN_COUNTRY.get(value) or EXTRA_COUNTRY.get(value) or iso.get(value)
            if not country:
                raise SystemExit(f"tld: no country for {value}")
            description = f"Country-code top-level domain for {country}, managed by {manager}."
            source = TLD_SOURCE + "; ISO 3166-1"
        elif value == "arpa":
            description = f"Special-use top-level domain for internet infrastructure, managed by {manager}."
            source = TLD_SOURCE
        elif value in GTLD_MEANING:
            description = f"Generic top-level domain for {GTLD_MEANING[value]}, managed by {manager}."
            source = TLD_SOURCE
        else:
            description = f"Generic top-level domain associated with the name '{value}', managed by {manager}."
            source = TLD_SOURCE
        rows.append((value, description, source))
    write_desc("tld", rows, 1436)


BLANK_PORT_DESCRIPTIONS = {
    "113": "Identification protocol used to look up the owner of a TCP connection.",
    "518": "Network Talk service for terminal-to-terminal text chat.",
    "543": "Kerberos login service for obtaining remote login credentials.",
    "751": "Legacy pump service for transferring files between hosts.",
    "2041": "InterBase database service used for client connections.",
}

PORT_TERM_EXPANSIONS = [
    ("IANA-registered", "registered"),
    ("IANA assigned", "registry assigned"),
    ("IANA", "port registry"),
    ("HTTPS", "secure web"),
    ("HTTP", "Hypertext Transfer Protocol"),
    ("TLS", "Transport Layer Security"),
    ("DNS", "Domain Name System"),
    ("SIP", "Session Initiation Protocol"),
    ("LDAP", "Lightweight Directory Access Protocol"),
    ("VPN", "virtual private network"),
    ("IP", "Internet Protocol"),
]


def expand_port_terms(text):
    for acronym, expansion in PORT_TERM_EXPANSIONS:
        text = re.sub(rf"\b{re.escape(acronym)}\b", expansion, text)
    return text


def registry_purpose(text):
    text = expand_port_terms(text)
    text = re.sub(r"\s+registry assigned this well-formed service name.*$", "", text, flags=re.IGNORECASE)
    text = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text, maxsplit=1)[0]
    text = re.sub(r"^The\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhttps\b", "Hypertext Transfer Protocol Secure", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhttp\b", "Hypertext Transfer Protocol", text, flags=re.IGNORECASE)
    text = re.sub(r"\bssl\b", "Secure Sockets Layer", text, flags=re.IGNORECASE)
    text = text.replace("priviledged", "privileged").replace("routinely- generated", "routinely generated")
    return text.rstrip(" .;:,")


def fit_purpose(text, limit):
    text = shorten(text, limit)
    if text.count('"') % 2:
        text = text.replace('"', "")
    while text.count("(") > text.count(")"):
        text = text[:text.rfind("(")].rstrip(" ,;:-")
    return text


def generate_port():
    by_port = {}
    with (RAW / "iana" / "service-names-port-numbers.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            name = clean(row["Service Name"])
            number = clean(row["Port Number"])
            protocol = clean(row["Transport Protocol"]).lower()
            if not name or not number.isdigit() or protocol not in ("tcp", "udp"):
                continue
            port = int(number)
            if port > 49151:
                continue
            by_port.setdefault(port, []).append(row)
    rows = []
    for port in sorted(by_port):
        records = by_port[port]
        name = clean(records[0]["Service Name"])
        protocols = {clean(r["Transport Protocol"]).lower() for r in records}
        transport = "TCP and UDP" if protocols == {"tcp", "udp"} else next(iter(protocols)).upper()
        descriptions = []
        for record in records:
            if clean(record["Service Name"]) != name:
                continue
            description = clean(record["Description"])
            if description and description not in descriptions:
                descriptions.append(description)
        display_name = expand_port_terms(name)
        prefix = f"Registered service '{display_name}' for {transport}: "
        suffix = "."
        if descriptions:
            purpose = next((d for d in descriptions if d.lower() not in ("reserved", "unassigned")),
                           descriptions[0])
            purpose = registry_purpose(purpose)
            purpose = fit_purpose(purpose, max(30, 200 - len(prefix) - len(suffix)))
            description = prefix + purpose + suffix
        elif str(port) in BLANK_PORT_DESCRIPTIONS:
            purpose = registry_purpose(BLANK_PORT_DESCRIPTIONS[str(port)])
            purpose = fit_purpose(purpose, max(30, 200 - len(prefix) - len(suffix)))
            description = prefix + purpose + suffix
        else:
            description = (f"Registered legacy service name '{display_name}' for {transport}; "
                           "the registry gives no purpose text.")
        rows.append((str(port), description, PORT_SOURCE))
    write_desc("port", rows, 6063)


APP_PRIORITY = [
    ("web_browsers", "Web browser developed by {vendor}."),
    ("instant_messengers", "Instant messaging client developed by {vendor}."),
    ("download_managers", "File download manager developed by {vendor}."),
    ("ssh_clients", "Secure Shell client for remote terminal access, developed by {vendor}."),
    ("media_players", "Media player developed by {vendor}."),
    ("pdf_readers", "Portable document format viewer developed by {vendor}."),
    ("office_suites", "Office productivity suite developed by {vendor}."),
    ("software_updaters", "Software update client developed by {vendor}."),
    ("security_software", "Endpoint security program developed by {vendor}."),
    ("file_sync_clients", "Cloud file synchronization client developed by {vendor}."),
    ("remote_desktop_clients", "Remote desktop client developed by {vendor}."),
    ("ftp_clients", "File transfer client developed by {vendor} for remote servers."),
    ("developer_tools", "Software development tool developed by {vendor}."),
    ("video_players", "Video player developed by {vendor}."),
    ("email_chat_clients", "Email or messaging client developed by {vendor}."),
    ("office_document_apps", "Office or document application developed by {vendor}."),
    ("developer_admin_tools", "Development or system administration tool developed by {vendor}."),
    ("security_update_tools", "Security or software update program developed by {vendor}."),
    ("remote_access_tools", "Remote access or terminal tool developed by {vendor}."),
    ("sync_download_tools", "File synchronization or download tool developed by {vendor}."),
]
APP_MANUAL = {
    "YodaoDict.exe": "English-Chinese dictionary and translation application from NetEase.",
    "YoudaoDict.exe": "English-Chinese dictionary and translation application from NetEase.",
    "PowerWord.exe": "English-Chinese dictionary application from Kingsoft.",
    "SogouCloud.exe": "Cloud-based Chinese input method from Sogou.",
    "SGTool.exe": "Utility component of the Sogou Chinese input method.",
    "SohuNews.exe": "News reader application from Sohu.",
    "Wiz.exe": "Note-taking and knowledge management application from WizNote.",
    "GitHub.exe": "GitHub Desktop client for Git repositories.",
    "git-remote-https.exe": "Git remote helper for repositories accessed over HTTPS.",
    "svchost.exe": "Windows service host process that runs background system services.",
    "msfeedssync.exe": "Background feed synchronization component of Windows.",
    "spoolsv.exe": "Windows Print Spooler service that manages print jobs.",
    "QQExternal.exe": "Companion process for the Tencent QQ messaging client.",
    "SGPicFaceTool.exe": "Sogou utility component for picture and face tools.",
    "BSvcProcessor.exe": "Baidu background service processor.",
    "nginx.exe": "nginx web server and reverse proxy from F5.",
    "httpd.exe": "Apache HTTP Server application from the Apache Software Foundation.",
    "tomcat.exe": "Apache Tomcat Java application server.",
    "java.exe": "Java runtime environment from Oracle for running JVM applications.",
    "javaw.exe": "Windowed Java runtime environment from Oracle for JVM applications.",
    "devenv.exe": "Visual Studio integrated development environment from Microsoft.",
    "code.exe": "Visual Studio Code source-code editor from Microsoft.",
    "pycharm64.exe": "PyCharm Python integrated development environment from JetBrains.",
    "idea64.exe": "IntelliJ IDEA integrated development environment from JetBrains.",
    "eclipse.exe": "Eclipse integrated development environment from the Eclipse Foundation.",
    "googleearth.exe": "Google Earth virtual globe application.",
    "Picasa3.exe": "Google Picasa photo viewer and organizer.",
    "Photoshop.exe": "Adobe Photoshop raster image editor.",
    "Illustrator.exe": "Adobe Illustrator vector graphics editor.",
    "InDesign.exe": "Adobe InDesign page-layout application.",
    "PremierePro.exe": "Adobe Premiere Pro video editor.",
    "Teams.exe": "Microsoft Teams collaboration and messaging client.",
    "WINWORD.EXE": "Microsoft Word word-processing application.",
    "EXCEL.EXE": "Microsoft Excel spreadsheet application.",
    "POWERPNT.EXE": "Microsoft PowerPoint presentation application.",
    "wps.exe": "WPS Office productivity suite from Kingsoft.",
    "et.exe": "WPS Spreadsheets spreadsheet application from Kingsoft.",
    "wpp.exe": "WPS Presentation presentation application from Kingsoft.",
    "soffice.exe": "LibreOffice productivity suite from The Document Foundation.",
    "TeamViewer_Service.exe": "Background service for TeamViewer remote access.",
    "explorer.exe": "Windows File Explorer shell and file manager.",
    "notepad.exe": "Plain-text editor included with Windows.",
    "WeGame.exe": "Tencent WeGame game distribution client.",
    "TencentMeeting.exe": "Tencent Meeting video-conferencing client.",
    "WeCom.exe": "WeCom enterprise messaging and collaboration client.",
    "QQLive.exe": "Tencent QQLive video streaming client.",
    "BaiduHi.exe": "Baidu Hi instant messaging client.",
    "ACDSee.exe": "ACDSee image viewer and photo organizer.",
    "SogouPinyin.exe": "Sogou Pinyin Chinese input method.",
    "baidupinyin.exe": "Baidu Pinyin Chinese input method.",
    "FlashPlayerPlugin_18_0_0_209.exe": "Adobe Flash Player browser plugin for multimedia content.",
}


def generate_client_apps():
    rows = []
    with (RAW / "curated" / "client_apps.tsv").open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("value\t"):
                continue
            value, entity, vendor = [clean(x) for x in line.rstrip("\n").split("\t")]
            rows.append((value, entity, vendor))
    lists = json.loads((RAW / "curated" / "lists_client_app.json").read_text(encoding="utf-8"))["lists"]
    memberships = {item["id"]: set(item["members"]) for item in lists}
    out = []
    for value, entity, vendor in rows:
        if value in APP_MANUAL:
            description = APP_MANUAL[value]
        else:
            description = None
            for list_id, template in APP_PRIORITY:
                if value in memberships.get(list_id, set()):
                    description = template.format(vendor=vendor)
                    break
            if not description:
                description = f"Windows application {entity} developed by {vendor}."
        out.append((value, description, "universe"))
    write_desc("client_app", out, 131)


USER_MANUAL = {
    "root": "Unix superuser account with unrestricted system privileges.",
    "admin": "Common administrator login used to manage systems and devices.",
    "administrator": "Built-in Windows local administrator account.",
    "sysadmin": "Administrative login used for system maintenance and configuration.",
    "operator": "Operations account used to monitor and control computer systems.",
    "0": "Numeric user identifier that maps to the Unix root superuser.",
    "daemon": "Legacy Unix account used to run background system daemons.",
    "bin": "Legacy Unix account that owns system executable files.",
    "sys": "Legacy Unix account for kernel and system services.",
    "sync": "Legacy Unix account for synchronizing files to storage.",
    "games": "Legacy Unix account for game programs and score files.",
    "man": "Legacy Unix account for manual-page maintenance.",
    "lp": "Legacy Unix account for the line-printer service.",
    "mail": "Legacy Unix account for the local mail subsystem.",
    "news": "Legacy Unix account for the Usenet news service.",
    "uucp": "Legacy Unix account for Unix-to-Unix file transfers.",
    "proxy": "Legacy Unix account for proxy and gateway services.",
    "backup": "Legacy Unix account for backup operations.",
    "list": "Legacy Unix account for mailing-list management.",
    "irc": "Legacy Unix account for Internet Relay Chat services.",
    "gnats": "Legacy Unix account for the GNATS bug-tracking system.",
    "nobody": "Unprivileged placeholder account used to run guest processes.",
    "systemd-network": "Service account used by systemd network management.",
    "messagebus": "Service account used by the D-Bus message bus.",
    "syslog": "Service account used by the system logging daemon.",
    "_apt": "Service account used by the APT package manager.",
    "sshd": "Service account used by the OpenSSH server daemon.",
    "debian-transmission": "Service account used by the Transmission BitTorrent daemon.",
    "clamav": "Service account used by the ClamAV antivirus scanner.",
    "vmail": "Virtual mailbox account used by mail delivery systems.",
    "postfix": "Service account used by the Postfix mail server.",
    "dovecot": "Service account used by the Dovecot IMAP and POP3 server.",
    "exim": "Service account used by the Exim mail server.",
    "mailnull": "Unprivileged account used by Exim for null mail delivery.",
    "cyrus": "Service account used by the Cyrus IMAP mail server.",
    "mysql": "Default administrator account for the MySQL database server.",
    "postgres": "Default superuser account for the PostgreSQL database server.",
    "postgres1": "Alternate superuser account for a PostgreSQL database server.",
    "oracle": "Administrative account for an Oracle Database instance.",
    "oralce": "Misspelled variant of the Oracle Database administrator account name.",
    "pgadmin": "Login account for the pgAdmin database management tool.",
    "mongo": "Default administrator account for the MongoDB database server.",
    "mongodb": "Default administrator account for the MongoDB database server.",
    "redis": "Login account for the Redis in-memory data store.",
    "cassandra": "Default account for the Apache Cassandra database.",
    "couchdb": "Administrator account for the Apache CouchDB document database.",
    "elasticsearch": "Login account associated with the Elasticsearch search server.",
    "memcached": "Service account for the Memcached distributed cache server.",
    "neo4j": "Default administrator account for the Neo4j graph database.",
    "influxdb": "Administrative account for the InfluxDB time-series database.",
    "db2admin": "Administrator account for the IBM Db2 database server.",
    "sa": "System administrator account for Microsoft SQL Server.",
    "sysdba": "Privileged SYSDBA account for Oracle Database.",
    "mssql": "Service account used by Microsoft SQL Server.",
    "rdsadmin": "Administrator account used by Amazon RDS managed databases.",
    "www-data": "Debian service account used by web server processes.",
    "www": "Generic service account used by web server processes.",
    "nginx": "Service account used by the nginx web server.",
    "apache": "Service account used by the Apache HTTP Server.",
    "httpd": "Daemon account used by the Apache HTTP Server.",
    "tomcat": "Service account used by the Apache Tomcat application server.",
    "jboss": "Service account used by the JBoss application server.",
    "glassfish": "Service account used by the GlassFish application server.",
    "weblogic": "Administrative account used by Oracle WebLogic Server.",
    "webmaster": "Administrative login for a website operator.",
    "webadmin": "Administrative login for web server management.",
    "jenkins": "Service account used by the Jenkins automation server.",
    "gitlab-runner": "Runner account used by GitLab CI to execute jobs.",
    "bamboo": "Build account used by the Atlassian Bamboo server.",
    "teamcity": "Service account used by the JetBrains TeamCity server.",
    "hudson": "Legacy service account used by the Hudson build server.",
    "buildbot": "Service account used by the Buildbot automation system.",
    "travis": "Service account used by the Travis CI build service.",
    "circleci": "Service account used by the CircleCI build service.",
    "drone": "Service account used by the Drone CI build system.",
    "ec2-user": "Default login account on Amazon EC2 Linux machine images.",
    "azureuser": "Default administrator login on Azure Linux virtual machines.",
    "opc": "Default account on Oracle Cloud Infrastructure Linux images.",
    "centos": "Default login account on CentOS cloud machine images.",
    "debian": "Default login account on Debian cloud machine images.",
    "fedora": "Default login account on Fedora cloud machine images.",
    "alpine": "Default login account on Alpine Linux cloud images.",
    "core": "Default login account on CoreOS container-optimized images.",
    "vagrant": "Default login account for Vagrant virtual machine boxes.",
    "adminuser": "Generic administrative login for cloud virtual machines.",
    "ubnt": "Default administrator account on Ubiquiti network devices.",
    "netscreen": "Default administrator account on Juniper NetScreen firewalls.",
    "fortinet": "Default administrator account on Fortinet security appliances.",
    "huawei": "Default administrator account on Huawei network equipment.",
    "zte": "Default administrator account on ZTE network equipment.",
    "mikrotik": "Default administrator account on MikroTik routers.",
    "router": "Generic administrative login for network routers.",
    "enable": "Privileged enable-mode account on Cisco network devices.",
    "cisco": "Default login account on Cisco network equipment.",
    "support": "Support account used for assisted customer access.",
    "guest": "Low-privilege guest account for temporary access.",
    "default": "Generic factory-default login name for devices and systems.",
    "PlcmSpIp": "Default administrator account on Polycom conferencing devices.",
    "Management": "Default management account on HP network equipment.",
    "telnet": "Service login used for Telnet remote terminal access.",
    "vnc": "Service login used for VNC remote desktop access.",
    "anonymous": "Anonymous login account for public file-transfer access.",
    "ftp": "Generic file-transfer service login account.",
    "ftpuser": "File-transfer login account for a remote file server.",
    "hadoop": "Service account used by the Hadoop cluster framework.",
    "hdfs": "Service account used by the Hadoop Distributed File System.",
    "hive": "Service account used by Apache Hive.",
    "spark": "Service account used by Apache Spark jobs.",
    "hbase": "Service account used by the Apache HBase database.",
    "oozie": "Service account used by the Apache Oozie workflow engine.",
    "flume": "Service account used by the Apache Flume data collector.",
    "storm": "Service account used by Apache Storm stream processing.",
    "kafka": "Service account used by the Apache Kafka event stream platform.",
    "zookeeper": "Service account used by the Apache ZooKeeper coordinator.",
    "yarn": "Service account used by the Hadoop YARN resource manager.",
    "mapred": "Service account used by Hadoop MapReduce jobs.",
    "nagios": "Service account used by the Nagios monitoring system.",
    "nagios1": "Alternate service account used by Nagios monitoring.",
    "zabbix": "Service account used by the Zabbix monitoring platform.",
    "cacti": "Service account used by the Cacti monitoring and graphing system.",
    "icinga": "Service account used by the Icinga monitoring system.",
    "prometheus": "Service account used by the Prometheus monitoring server.",
    "grafana": "Service account used by the Grafana dashboard platform.",
    "splunk": "Service account used by the Splunk log analytics platform.",
    "elk": "Service account used by the Elasticsearch, Logstash and Kibana platform.",
    "kibana": "Service account used by the Kibana visualization application.",
    "logstash": "Service account used by the Logstash data pipeline.",
    "api": "Service account used by an application programming interface.",
    "boot": "Legacy Unix account for boot-time system services.",
    "bssh": "Backup account used for SSH-based data transfer.",
    "FILTER": "Service account used by mail or content filtering systems.",
    "deploy": "Deployment account used for automated software releases.",
    "git": "Service account used by a Git source-code server.",
    "puppet": "Configuration account used by the Puppet management system.",
    "ansible": "Automation account used by the Ansible configuration tool.",
    "user": "Generic unprivileged login used by ordinary users.",
    "pi": "Default login account on Raspberry Pi OS devices.",
    "adm": "Administrative login account on Unix systems.",
    "info": "Default account for informational mail and service requests.",
    "matlab": "Login name associated with MATLAB numerical computing users.",
    "abc": "Generic test account used to verify login access.",
    "test": "Generic test account used to verify login access.",
    "test1": "Generic test account used to verify login access.",
    "test2": "Generic test account used to verify login access.",
    "test9": "Generic test account used to verify login access.",
    "123": "Short numeric login name often used as a weak test credential.",
    "1234": "Short numeric login name often used as a weak test credential.",
    "123456": "Common numeric login name used as a weak credential.",
}


def generate_users():
    rows = []
    with (RAW / "curated" / "usernames.tsv").open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("value\t"):
                continue
            value, entity, role = [clean(x) for x in line.rstrip("\n").split("\t")]
            rows.append((value, entity, role))
    out = []
    for value, entity, role in rows:
        if value in USER_MANUAL:
            description = USER_MANUAL[value]
        elif role == "human":
            if entity == "personal account":
                description = "Common personal login name for an individual user account."
            elif entity == "generic login name":
                description = "Generic login name commonly found in password-audit wordlists."
            else:
                description = f"Individual login name associated with {entity}."
        elif role == "database":
            description = f"Database administrator account associated with {entity}."
        elif role == "web":
            description = f"Service account associated with {entity}."
        elif role == "ci":
            description = f"Automation service account associated with {entity}."
        elif role == "cloud":
            description = f"Default cloud-image login associated with {entity}."
        elif role == "network":
            description = f"Default network-device login associated with {entity}."
        elif role == "bigdata":
            description = f"Data-platform service account associated with {entity}."
        elif role == "monitoring":
            description = f"Monitoring service account associated with {entity}."
        elif role == "mail":
            description = f"Mail service account associated with {entity}."
        elif role == "service":
            description = f"Service login associated with {entity}."
        elif role == "system":
            description = f"Legacy system account associated with {entity}."
        elif role == "privileged":
            description = f"Privileged login associated with {entity}."
        else:
            description = f"Login account associated with {entity}."
        out.append((value, description, "universe"))
    write_desc("user", out, 192)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    generate_tld()
    generate_port()
    generate_client_apps()
    generate_users()


if __name__ == "__main__":
    main()
