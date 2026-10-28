#!/usr/bin/env python3
"""Parse the pre-existing user and client-app lists under raw/add_lists/.

Every member comes from a named file, section, or table in the raw snapshot.  The
parsers below never search prose for likely members; they walk the source's own
record/table structure.  build_add_lists.py and build_add_spotcheck.py share them.
"""
import csv
import html
import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "add_lists"
UNIVERSES = ROOT / "universes"


def universe(name):
    lines = (UNIVERSES / f"{name}.tsv").read_text(encoding="utf-8").splitlines()
    return {line.split("\t")[0] for line in lines[1:] if line.strip()}


def norm(value):
    value = html.unescape(str(value))
    value = re.sub(r"\[[^\]]*\]", "", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def alias_variants(value):
    base = norm(value)
    yield base
    yield norm(re.sub(r"\([^)]*\)", "", value))
    yield norm(re.sub(r"\s+Portable$", "", value, flags=re.I))
    yield norm(re.sub(r",?\s*Portable Edition$", "", value, flags=re.I))


def lookup_alias(value, aliases):
    for variant in alias_variants(value):
        if variant in aliases:
            return aliases[variant]
    return None


def raw_path(spec):
    return RAW / spec["raw"]


def first_line(spec, needle):
    needle = norm(needle)
    word = next((part for part in re.findall(r"[a-z0-9]+", needle) if len(part) >= 4), needle)
    for number, line in enumerate(raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if needle and needle in norm(line):
            return number
    for number, line in enumerate(raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if word and word in norm(line):
            return number
    return 0


def line_contains_entry(line, name):
    needle = norm(name)
    word = next((part for part in re.findall(r"[a-z0-9]+", needle) if len(part) >= 4), needle)
    return bool(needle and needle in norm(line)) or bool(word and word in norm(line))


def unique_entries(pairs):
    seen, out = set(), []
    for name, line in pairs:
        name = re.sub(r"\s+", " ", html.unescape(name)).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append({"name": name, "line": line})
    return out


def parse_passwd(spec):
    pairs = []
    for line_no, line in enumerate(raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name = line.split(":", 1)[0].strip()
        if name:
            pairs.append((name, line_no))
    return unique_entries(pairs)


def parse_plain(spec):
    pairs = []
    for line_no, line in enumerate(raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        name = line.strip()
        if name and not name.startswith("#"):
            pairs.append((name, line_no))
    return unique_entries(pairs)


def parse_fedora_uidgid(spec):
    pairs = []
    for line_no, line in enumerate(raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 2 and cols[1].strip() not in ("", "-"):
            pairs.append((cols[0].strip(), line_no))
    return unique_entries(pairs)


def parse_rfc2142(spec):
    """The three explicit MAILBOX tables in sections 3-5 (lines 119-165)."""
    pairs = []
    for line_no, line in enumerate(raw_path(spec).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not (119 <= line_no <= 176):
            continue
        match = re.match(r"^\s{3}([A-Z][A-Z0-9-]+)\s{2,}", line)
        if match and match.group(1) != "MAILBOX":
            pairs.append((match.group(1).lower(), line_no))
    return unique_entries(pairs)


def parse_defaultcreds(spec):
    pairs = []
    with raw_path(spec).open(encoding="utf-8", errors="replace", newline="") as handle:
        for line_no, row in enumerate(csv.DictReader(handle), 2):
            name = (row.get("username") or "").strip()
            if name and name != "<blank>":
                pairs.append((name, line_no))
    return unique_entries(pairs)


def soup(spec):
    return BeautifulSoup(raw_path(spec).read_text(encoding="utf-8", errors="replace"), "lxml")


def parse_office_sentence(spec):
    document = soup(spec)
    text = document.get_text(" ", strip=True)
    match = re.search(rf"Office LTSC Professional Plus {spec['year']} includes (.+?)\.", text)
    if not match:
        raise ValueError(f"{spec['id']}: Office inclusion sentence not found")
    body = re.sub(r"\s+", " ", match.group(1)).replace(" and ", ", ")
    names = [part.strip() for part in body.split(",") if part.strip()]
    line = first_line(spec, f"Office LTSC Professional Plus {spec['year']} includes")
    return unique_entries((name, line) for name in names)


def parse_adobe_cc(spec):
    document = soup(spec)
    heading = document.find(id="Current_applications_and_services")
    table = heading.find_next("table")
    pairs = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            name = cells[1].get_text(" ", strip=True)
            pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_windows_components(spec):
    document = soup(spec)
    table = document.find(id="Applications_and_utilities").find_next("table")
    pairs = []
    for row in table.find_all("tr")[1:]:
        cell = row.find(["th", "td"])
        if cell:
            name = cell.get_text(" ", strip=True)
            pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_microsoft_applications(spec):
    document = soup(spec)
    heading = document.find("h3", id="Applications")
    items = heading.find_next("ul").find_all("li")
    pairs = []
    for item in items:
        if item.find("li"):
            continue
        name = item.get_text(" ", strip=True)
        pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_ninite(spec):
    document = soup(spec)
    pairs = []
    for label in document.select("label.homepage-app-label"):
        name = label.get_text(" ", strip=True)
        pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_portableapps(spec):
    document = soup(spec)
    pairs = []
    for anchor in document.select('li a[href^="/apps/"]'):
        if not anchor.find_previous_sibling("img"):
            continue
        name = anchor.get_text(" ", strip=True)
        pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_table_names(spec):
    document = soup(spec)
    heading = document.find(id=spec["heading"])
    table = heading.find_next("table")
    pairs = []
    for row in table.find_all("tr")[1:]:
        cell = row.find("th")
        if cell:
            name = cell.get_text(" ", strip=True)
            if norm(name) != "version":
                pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_uptodown_top(spec):
    document = soup(spec)
    heading = document.find("h2", string=lambda value: value and "Top downloads" in value)
    section = heading.find_parent("section")
    pairs = []
    for anchor in section.select(".name a"):
        name = anchor.get_text(" ", strip=True)
        pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


def parse_pdf_windows_viewers(spec):
    document = soup(spec)
    listing = document.find("h3", id="Viewers_4").find_next("ul")
    pairs = []
    for item in listing.find_all("li", recursive=False):
        name = item.get_text(" ", strip=True).split(":", 1)[0].strip()
        pairs.append((name, first_line(spec, name)))
    return unique_entries(pairs)


USER_SYSTEM_ALIASES = {}

CLIENT_ALIASES = {
    "office_ltsc_2024_apps": {
        "excel": "EXCEL.EXE", "onenote": "ONENOTE.EXE", "outlook": "OUTLOOK.EXE",
        "powerpoint": "POWERPNT.EXE", "word": "WINWORD.EXE",
    },
    "office_ltsc_2021_apps": {
        "excel": "EXCEL.EXE", "onenote": "ONENOTE.EXE", "outlook": "OUTLOOK.EXE",
        "powerpoint": "POWERPNT.EXE", "skype for business": "Skype.exe",
        "word": "WINWORD.EXE",
    },
    "adobe_cc_current_apps": {
        "acrobat": "Acrobat.exe", "illustrator": "Illustrator.exe",
        "indesign": "InDesign.exe", "photoshop": "Photoshop.exe", "premiere": "PremierePro.exe",
    },
    "windows_components_apps_utilities": {
        "edge": "msedge.exe", "onedrive": "OneDrive.exe", "microsoft onenote": "ONENOTE.EXE",
        "notepad": "notepad.exe", "remote desktop connection": "mstsc.exe", "skype": "Skype.exe",
    },
    "microsoft_productivity_apps": {
        "microsoft excel": "EXCEL.EXE", "microsoft onenote": "ONENOTE.EXE",
        "microsoft outlook": "OUTLOOK.EXE", "microsoft powerpoint": "POWERPNT.EXE",
        "microsoft teams": "Teams.exe", "microsoft word": "WINWORD.EXE",
    },
    "ninite_catalog": {
        "chrome": "chrome.exe", "opera": "opera.exe", "firefox": "firefox.exe",
        "edge": "msedge.exe", "brave": "Brave.exe", "vivaldi": "Vivaldi.exe",
        "teams": "Teams.exe", "telegram": "telegram.exe", "whatsapp": "WhatsApp.exe",
        "itunes": "iTunes.exe", "vlc": "vlc.exe", "spotify": "Spotify.exe",
        "foxit reader": "FoxitReader.exe", "libreoffice": "soffice.exe",
        "sumatrapdf": "SumatraPDF.exe", "avast": "avastui.exe", "avg": "avgui.exe",
        "dropbox": "Dropbox.exe", "google drive for desktop": "GoogleDriveFS.exe",
        "onedrive": "OneDrive.exe", "google earth": "googleearth.exe", "anydesk": "AnyDesk.exe",
        "teamviewer 15": "TeamViewer.exe", "rustdesk": "RustDesk.exe",
        "visual studio code": "code.exe", "filezilla": "FileZilla.exe", "winscp": "WinSCP.exe",
        "putty": "putty.exe", "eclipse": "eclipse.exe", "github desktop": "GitHub.exe",
        "java (adoptopenjdk) 8": "java.exe",
    },
    "portableapps_directory": {
        "google chrome portable": "chrome.exe",
        "mozilla firefox, portable edition": "firefox.exe",
        "opera, portable edition": "opera.exe", "maxthon portable": "maxthon.exe",
        "telegram desktop portable": "telegram.exe", "putty portable": "putty.exe",
        "winscp portable": "WinSCP.exe", "filezilla portable": "FileZilla.exe",
        "teamviewer portable": "TeamViewer.exe", "vlc media player portable": "vlc.exe",
        "potplayer portable": "PotPlayerMini.exe",
        "media player classic - home cinema (mpc-hc) portable": "mpc-hc.exe",
        "foxit reader portable": "FoxitReader.exe",
        "pdf-xchange viewer portable": "PDFXCview.exe", "libreoffice portable": "soffice.exe",
        "free download manager classic portable": "FreeDownloadManager.exe",
        "uget portable": "uGet.exe", "sumatra pdf portable": "SumatraPDF.exe",
    },
    "comparison_browsers_general": {
        "brave": "Brave.exe", "chrome": "chrome.exe", "edge": "msedge.exe",
        "firefox": "firefox.exe", "maxthon": "maxthon.exe", "opera": "opera.exe",
        "vivaldi": "Vivaldi.exe",
    },
    "uptodown_top_downloads": {
        "google chrome": "chrome.exe", "whatsapp desktop": "WhatsApp.exe",
        "vlc media player": "vlc.exe", "anydesk": "AnyDesk.exe",
        "microsoft excel": "EXCEL.EXE", "microsoft word": "WINWORD.EXE",
    },
    "comparison_im_clients_general": {
        "line": "Line.exe", "qq": "QQ.exe", "skype": "Skype.exe", "telegram": "telegram.exe",
        "wechat": "WeChat.exe", "whatsapp": "WhatsApp.exe",
    },
    "comparison_video_players_general": {
        "itunes": "iTunes.exe", "k-multimedia player": "KMPlayer.exe",
        "media player classic home cinema": "mpc-hc.exe",
        "potplayer": "PotPlayerMini.exe", "vlc": "vlc.exe",
        "windows media player": "wmplayer.exe",
    },
    "pdf_windows_viewers": {
        "adobe reader": "AcroRd32.exe", "foxit reader": "FoxitReader.exe",
        "google chrome": "chrome.exe", "microsoft edge": "msedge.exe",
        "mozilla firefox": "firefox.exe", "pdf-xchange viewer": "PDFXCview.exe",
    },
}


LIST_SPECS = [
    {"id": "freebsd_master_passwd", "universe": "user", "parse": parse_passwd,
     "name": "FreeBSD master.passwd system accounts", "synonyms": ["FreeBSD default accounts"],
     "raw": "user/freebsd_master.passwd", "title": "FreeBSD src etc/master.passwd",
     "source": "https://github.com/freebsd/freebsd-src/blob/main/etc/master.passwd", "wiki": "FreeBSD"},
    {"id": "dragonfly_master_passwd", "universe": "user", "parse": parse_passwd,
     "name": "DragonFly BSD master.passwd system accounts", "synonyms": ["DragonFly default accounts"],
     "raw": "user/dragonfly_master.passwd", "title": "DragonFly BSD etc/master.passwd",
     "source": "https://github.com/DragonFlyBSD/DragonFlyBSD/blob/master/etc/master.passwd",
     "wiki": "DragonFly BSD"},
    {"id": "netbsd_master_passwd", "universe": "user", "parse": parse_passwd,
     "name": "NetBSD master.passwd system accounts", "synonyms": ["NetBSD default accounts"],
     "raw": "user/netbsd_master.passwd", "title": "NetBSD src etc/master.passwd",
     "source": "https://github.com/NetBSD/src/blob/trunk/etc/master.passwd", "wiki": "NetBSD"},
    {"id": "openbsd_master_passwd", "universe": "user", "parse": parse_passwd,
     "name": "OpenBSD master.passwd system accounts", "synonyms": ["OpenBSD default accounts"],
     "raw": "user/openbsd_master.passwd", "title": "OpenBSD src etc/master.passwd",
     "source": "https://github.com/openbsd/src/blob/master/etc/master.passwd", "wiki": "OpenBSD"},
    {"id": "alpine_passwd", "universe": "user", "parse": parse_passwd,
     "name": "Alpine Linux base-layout passwd accounts", "synonyms": ["Alpine default accounts"],
     "raw": "user/alpine_passwd", "title": "alpine-baselayout/passwd",
     "source": "https://github.com/alpinelinux/aports/blob/master/main/alpine-baselayout/passwd",
     "wiki": "Alpine Linux"},
    {"id": "debian_passwd_master", "universe": "user", "parse": parse_passwd,
     "name": "Debian base-passwd master accounts", "synonyms": ["Debian base-passwd"],
     "raw": "user/debian_passwd.master", "title": "base-passwd/passwd.master",
     "source": "https://salsa.debian.org/base-passwd-team/base-passwd/-/blob/master/passwd.master",
     "wiki": "Debian"},
    {"id": "buildroot_passwd", "universe": "user", "parse": parse_passwd,
     "name": "Buildroot skeleton passwd accounts", "synonyms": ["Buildroot default accounts"],
     "raw": "user/buildroot_passwd", "title": "Buildroot system/skeleton/etc/passwd",
     "source": "https://github.com/buildroot/buildroot/blob/master/system/skeleton/etc/passwd",
     "wiki": "Buildroot"},
    {"id": "fedora_uidgid", "universe": "user", "parse": parse_fedora_uidgid,
     "name": "Fedora setup package user accounts", "synonyms": ["Fedora uidgid users"],
     "raw": "user/fedora_uidgid", "title": "Fedora setup package uidgid (user rows)",
     "source": "https://src.fedoraproject.org/rpms/setup/blob/rawhide/f/uidgid", "wiki": "Fedora Linux"},
    {"id": "nmap_usernames", "universe": "user", "parse": parse_plain,
     "name": "Nmap username wordlist", "synonyms": ["Nmap usernames.lst"],
     "raw": "user/nmap_usernames.lst", "title": "Nmap nselib/data/usernames.lst",
     "source": "https://github.com/nmap/nmap/blob/master/nselib/data/usernames.lst", "wiki": "Nmap"},
    {"id": "metasploit_unix_users", "universe": "user", "parse": parse_plain,
     "name": "Metasploit Unix users wordlist", "synonyms": ["Metasploit unix_users.txt"],
     "raw": "user/metasploit_usernames", "title": "Metasploit data/wordlists/unix_users.txt",
     "source": "https://github.com/rapid7/metasploit-framework/blob/master/data/wordlists/unix_users.txt",
     "wiki": "Metasploit"},
    {"id": "rfc2142_mailboxes", "universe": "user", "parse": parse_rfc2142,
     "name": "RFC 2142 service and role mailboxes", "synonyms": ["well-known mailbox names"],
     "raw": "user/rfc2142.txt", "title": "RFC 2142 mailbox names (sections 3-5)",
     "source": "https://www.rfc-editor.org/rfc/rfc2142.txt", "wiki": "Postmaster"},
    {"id": "defaultcreds_usernames", "universe": "user", "parse": parse_defaultcreds,
     "name": "DefaultCreds cheat-sheet usernames", "synonyms": ["default credential usernames"],
     "raw": "user/default_creds_cheatsheet.csv", "title": "DefaultCreds Cheat Sheet username column",
     "source": "https://github.com/ihebski/DefaultCreds-cheat-sheet/blob/main/DefaultCreds-Cheat-Sheet.csv",
     "wiki": "Default password"},

    {"id": "office_ltsc_2024_apps", "universe": "client_app", "parse": parse_office_sentence, "year": 2024,
     "name": "Office LTSC Professional Plus 2024 applications", "synonyms": ["Office 2024 desktop apps"],
     "raw": "client_app/office_ltsc_2024.html", "title": "Overview of Office LTSC 2024 (Professional Plus 2024 applications)",
     "source": "https://learn.microsoft.com/en-us/office/ltsc/2024/overview", "wiki": "Microsoft Office"},
    {"id": "adobe_cc_current_apps", "universe": "client_app", "parse": parse_adobe_cc,
     "name": "Adobe Creative Cloud current applications", "synonyms": ["Creative Cloud apps"],
     "raw": "client_app/wiki_adobe_cc.html", "title": "Adobe Creative Cloud: Current applications and services",
     "source": "https://en.wikipedia.org/wiki/Adobe_Creative_Cloud", "wiki": "Adobe Creative Cloud"},
    {"id": "windows_components_apps_utilities", "universe": "client_app", "parse": parse_windows_components,
     "name": "Microsoft Windows applications and utilities", "synonyms": ["Windows built-in apps"],
     "raw": "client_app/wiki_windows_components.html",
     "title": "List of Microsoft Windows components: Applications and utilities",
     "source": "https://en.wikipedia.org/wiki/List_of_Microsoft_Windows_components",
     "wiki": "List of Microsoft Windows components"},
    {"id": "microsoft_productivity_apps", "universe": "client_app", "parse": parse_microsoft_applications,
     "name": "Microsoft productivity applications", "synonyms": ["Microsoft Office and Teams apps"],
     "raw": "client_app/wiki_software_categories.html",
     "title": "List of Microsoft software: Productivity - Applications",
     "source": "https://en.wikipedia.org/wiki/List_of_Microsoft_software", "wiki": "List of Microsoft software"},
    {"id": "ninite_catalog", "universe": "client_app", "parse": parse_ninite,
     "name": "Ninite application catalog", "synonyms": ["Ninite apps"],
     "raw": "client_app/ninite.html", "title": "Ninite application picker",
     "source": "https://ninite.com/", "wiki": "Ninite"},
    {"id": "portableapps_directory", "universe": "client_app", "parse": parse_portableapps,
     "name": "Portable App Directory", "synonyms": ["PortableApps.com apps"],
     "raw": "client_app/portableapps_apps.html", "title": "Portable App Directory",
     "source": "https://portableapps.com/apps", "wiki": "PortableApps.com"},
    {"id": "comparison_browsers_general", "universe": "client_app", "parse": parse_table_names,
     "heading": "General_information", "name": "Comparison of web browsers: general information",
     "synonyms": ["web browser comparison table"], "raw": "client_app/wiki_comparison_browsers.html",
     "title": "Comparison of web browsers: General information",
     "source": "https://en.wikipedia.org/wiki/Comparison_of_web_browsers",
     "wiki": "Comparison of web browsers"},
    {"id": "uptodown_top_downloads", "universe": "client_app", "parse": parse_uptodown_top,
     "name": "Uptodown Windows top downloads", "synonyms": ["Uptodown top apps"],
     "raw": "client_app/uptodown_windows.html", "title": "Uptodown Apps for Windows: Top downloads",
     "source": "https://en.uptodown.com/windows", "wiki": "Uptodown"},
    {"id": "office_ltsc_2021_apps", "universe": "client_app", "parse": parse_office_sentence, "year": 2021,
     "name": "Office LTSC Professional Plus 2021 applications", "synonyms": ["Office 2021 desktop apps"],
     "raw": "client_app/office_ltsc_2021.html", "title": "Overview of Office LTSC 2021 (Professional Plus 2021 applications)",
     "source": "https://learn.microsoft.com/en-us/office/ltsc/2021/overview", "wiki": "Microsoft Office 2021",
     "disputed": {"teams": "Teams.exe"}},
    {"id": "comparison_im_clients_general", "universe": "client_app", "parse": parse_table_names,
     "heading": "General", "name": "Comparison of instant messaging clients",
     "synonyms": ["instant messaging comparison table"],
     "raw": "client_app/wiki_comparison_im.html",
     "title": "Comparison of instant messaging clients: General information",
     "source": "https://en.wikipedia.org/wiki/Comparison_of_instant_messaging_clients",
     "wiki": "Comparison of instant messaging clients"},
    {"id": "comparison_video_players_general", "universe": "client_app", "parse": parse_table_names,
     "heading": "General", "name": "Comparison of video player software",
     "synonyms": ["video player comparison table"],
     "raw": "client_app/wiki_comparison_video_players.html",
     "title": "Comparison of video player software: General information",
     "source": "https://en.wikipedia.org/wiki/Comparison_of_video_player_software",
     "wiki": "Comparison of video player software"},
    {"id": "pdf_windows_viewers", "universe": "client_app", "parse": parse_pdf_windows_viewers,
     "name": "PDF viewers for Microsoft Windows", "synonyms": ["List of PDF software Windows viewers"],
     "raw": "client_app/wiki_list_pdf.html",
     "title": "List of PDF software: Microsoft Windows - Viewers",
     "source": "https://en.wikipedia.org/wiki/List_of_PDF_software", "wiki": "List of PDF software"},
]

NEW_IDS = {spec["id"] for spec in LIST_SPECS}


def build_item(spec):
    values = universe(spec["universe"])
    aliases = USER_SYSTEM_ALIASES if spec["universe"] == "user" else CLIENT_ALIASES[spec["id"]]
    disputed_aliases = spec.get("disputed") or {}
    entries = spec["parse"](spec)
    members, disputed, outside, evidence = [], [], [], {}
    used = set()
    for entry in entries:
        name = entry["name"]
        source_key = norm(name)
        if source_key in disputed_aliases and disputed_aliases[source_key] not in used:
            value = disputed_aliases[source_key]
            disputed.append(value)
            used.add(value)
            evidence[value] = entry
            continue
        value = lookup_alias(name, aliases) if aliases else None
        if value is None and spec["universe"] == "user" and name in values:
            value = name
        if value in values and value not in used:
            members.append(value)
            used.add(value)
            evidence[value] = entry
        else:
            outside.append(name)
    return {
        "id": spec["id"], "name": spec["name"], "synonyms": spec["synonyms"],
        "members": members, "disputed": disputed, "changes": [],
        "out_of_universe": outside, "official_count": len(entries),
        "source": spec["source"], "salience": 0,
    }, entries, evidence


def all_items():
    for spec in LIST_SPECS:
        item, entries, evidence = build_item(spec)
        yield spec, item, entries, evidence


if __name__ == "__main__":
    for spec, item, entries, evidence in all_items():
        print(f"{item['id']}: official={item['official_count']} members={len(item['members'])} "
              f"disputed={len(item['disputed'])} outside={len(item['out_of_universe'])}")
