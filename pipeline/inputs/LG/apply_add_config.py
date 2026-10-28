#!/usr/bin/env python3
"""Add one rule template per new list and register those template ids in LG1-LG5."""
from pathlib import Path

import yaml

from add_sources import LIST_SPECS

ROOT = Path(__file__).resolve().parent
FIELD = {"user": "ssh_logins.user", "client_app": "proxy_connections.client_app"}

RELATED = {
    "freebsd_master_passwd": ["dragonfly_master_passwd", "netbsd_master_passwd", "linux_base_accounts"],
    "dragonfly_master_passwd": ["freebsd_master_passwd", "netbsd_master_passwd", "linux_base_accounts"],
    "netbsd_master_passwd": ["freebsd_master_passwd", "openbsd_master_passwd", "linux_base_accounts"],
    "openbsd_master_passwd": ["netbsd_master_passwd", "freebsd_master_passwd", "linux_base_accounts"],
    "alpine_passwd": ["debian_passwd_master", "buildroot_passwd", "linux_base_accounts"],
    "debian_passwd_master": ["alpine_passwd", "buildroot_passwd", "linux_base_accounts"],
    "buildroot_passwd": ["alpine_passwd", "debian_passwd_master", "linux_base_accounts"],
    "fedora_uidgid": ["debian_passwd_master", "alpine_passwd", "linux_base_accounts"],
    "nmap_usernames": ["metasploit_unix_users", "defaultcreds_usernames", "seclists_top_usernames"],
    "metasploit_unix_users": ["nmap_usernames", "defaultcreds_usernames", "seclists_top_usernames"],
    "rfc2142_mailboxes": ["mail_server_users", "defaultcreds_usernames", "web_server_users"],
    "defaultcreds_usernames": ["nmap_usernames", "metasploit_unix_users", "default_accounts"],
    "office_ltsc_2024_apps": ["office_ltsc_2021_apps", "microsoft_productivity_apps", "office_document_apps"],
    "adobe_cc_current_apps": ["office_ltsc_2024_apps", "office_document_apps", "microsoft_products"],
    "windows_components_apps_utilities": ["microsoft_productivity_apps", "office_ltsc_2024_apps", "microsoft_products"],
    "microsoft_productivity_apps": ["office_ltsc_2024_apps", "office_ltsc_2021_apps", "microsoft_products"],
    "ninite_catalog": ["portableapps_directory", "comparison_browsers_general", "remote_access_tools"],
    "portableapps_directory": ["ninite_catalog", "comparison_browsers_general", "developer_admin_tools"],
    "comparison_browsers_general": ["ninite_catalog", "web_browsers", "chromium_browsers"],
    "uptodown_top_downloads": ["ninite_catalog", "portableapps_directory", "office_document_apps"],
    "office_ltsc_2021_apps": ["office_ltsc_2024_apps", "microsoft_productivity_apps", "office_document_apps"],
    "comparison_im_clients_general": ["ninite_catalog", "instant_messengers", "email_chat_clients"],
    "comparison_video_players_general": ["ninite_catalog", "media_players", "video_players"],
    "pdf_windows_viewers": ["portableapps_directory", "ninite_catalog", "pdf_readers"],
}


def template(spec):
    lid = spec["id"]
    field = FIELD[spec["universe"]]
    if spec["universe"] == "user":
        rule = f"An SSH login by an account on the {spec['name']} list is not counted."
    else:
        rule = f"A proxy connection made by a client in the {spec['name']} list is not counted."
    return {
        "id": f"add_{lid}",
        "field": field,
        "effect": "exclude_record",
        "source": f"Supplement: {spec['title']}.",
        "rule": rule,
        "plausible": [lid, *RELATED[lid]],
    }


def update_scenario():
    path = ROOT / "scenario.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    current = {str(item["id"]) for item in data.get("rule_templates") or []}
    for spec in LIST_SPECS:
        item = template(spec)
        if item["id"] not in current:
            data.setdefault("rule_templates", []).append(item)
            current.add(item["id"])
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return [f"add_{spec['id']}" for spec in LIST_SPECS]


def insert_ids(path, field, ids):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip() == f"- field: {field}"), None)
    if start is None:
        raise SystemExit(f"{path}: field {field} not found")
    templates = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "templates:"), None)
    if templates is None:
        raise SystemExit(f"{path}: templates for {field} not found")
    end = templates + 1
    while end < len(lines) and lines[end].lstrip().startswith("- ") and lines[end].startswith("  "):
        end += 1
    present = {line.strip()[2:].strip() for line in lines[templates + 1:end]}
    missing = [value for value in ids if value not in present]
    if missing:
        insertion = "".join(f"  - {value}\n" for value in missing)
        lines.insert(end, insertion)
        path.write_text("".join(lines), encoding="utf-8")
    return missing


def update_chains(template_ids):
    user_ids = [f"add_{spec['id']}" for spec in LIST_SPECS if spec["universe"] == "user"]
    client_ids = [f"add_{spec['id']}" for spec in LIST_SPECS if spec["universe"] == "client_app"]
    for path in sorted((ROOT / "chains").glob("LG*.yaml")):
        user_added = insert_ids(path, FIELD["user"], user_ids)
        client_added = insert_ids(path, FIELD["client_app"], client_ids)
        print(f"{path.name}: +{len(user_added)} user, +{len(client_added)} client templates")


def main():
    ids = update_scenario()
    update_chains(ids)
    print(f"scenario.yaml: {len(ids)} new rule templates present")


if __name__ == "__main__":
    main()
