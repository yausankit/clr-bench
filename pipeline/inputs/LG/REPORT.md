# LG — system-log audit event counts (dataset LG, executor DS_LG_a9)

Status: all six self-checks pass; `clrsynth lint LG` exits 0; dryrun builds every instance;
the two-pass reproducibility comparison is byte-identical. This report is
`inputs/LG/REPORT.md`, with a copy at `E/agents/DS_LG_a9/REPORT.md`.

## Universes (`universes/<U>.tsv`)
| universe | values | attributes | distribution |
|---|---|---|---|
| tld | 1436 | type, region | gTLD 1132 / ccTLD 304; region: ? 1132, Asia 95, Africa 66, Europe 60, Americas 54, Oceania 28, Antarctica 1 |
| port | 6063 | range, transport | system 686 / user 5377; both 5329, tcp 561, udp 173 |
| client_app | 131 | vendor | Microsoft 22, Tencent 15, Adobe 8, Google 5, Qihoo 360 5, Sogou 5, Baidu 5, rest <=4 |
| user | 192 | role | human 54, system 24, database 20, ci 13, network 12, bigdata 12, web 11, monitoring 11, rest |

## Lists (id members/official_count salience@source-host; full URLs in `LIST_TABLE.md`)
tld (32): eu_member_cctlds 27/27 3.3M@european-union.europa.eu; schengen_cctlds 29/29 1.4M@home-affairs.ec.europa.eu; eurozone_cctlds 20/20 629k@www.ecb.europa.eu; nato_cctlds 32/32 2.6M@www.nato.int; commonwealth_cctlds 56/56 1.6M@thecommonwealth.org; asean_cctlds 11/11 1.3M@asean.org; g20_cctlds 19/21 995k@www.g20.org; brics_cctlds 10/10 1.8M@brics2025.gov.br; oecd_cctlds 38/38 807k@www.oecd.org; african_union_cctlds 54/55 518k@au.int; arab_league_cctlds 22/22 465k@www.arableagueonline.org; nordic_council_cctlds 5/5 114k@www.norden.org; gcc_cctlds 6/6 960k@www.gcc-sg.org; caricom_cctlds 15/15 18k@caricom.org; pacific_islands_forum_cctlds 18/18 72k@forumsec.org; g7_cctlds 7/7 974k@www.g7italy.it; five_eyes_cctlds 5/5 691k@www.dni.gov; cplp_cctlds 9/9 110k@www.cplp.org; oif_cctlds 53/53 164k@www.francophonie.org; opec_cctlds 12/12 1.1M@www.opec.org; cis_cctlds 8/8 797k@cis.minsk.by; saarc_cctlds 8/8 332k@saarc-sec.org; apec_cctlds 21/21 301k@www.apec.org; idn_cctlds 57/57 24k@www.icann.org; geographic_gtlds 42/42 8k@icannwiki.org; brand_gtlds 132/133 0@icannwiki.org; sponsored_gtlds 14/14 793k@www.icann.org; original_gtlds 8/8 484k@www.iana.org; cctlds_all 304/304 528k@www.iana.org; gtlds_all 1132/1132 484k@www.iana.org; legacy_gtlds 19/19 484k@www.iana.org; new_gtld_program_2012 1113/1113 484k@newgtlds.icann.org
port (24): mail_service_ports 9/9 1.1M@www.iana.org; database_ports 15/15 1.1M@www.postgresql.org; plaintext_protocol_ports 14/14 1.1M@www.iana.org; tls_wrapped_ports 14/14 1.1M@www.iana.org; proxy_ports 8/8 1.1M@www.iana.org; remote_admin_ports 9/9 1.1M@www.iana.org; file_transfer_ports 11/11 1.1M@www.iana.org; directory_service_ports 8/8 1.1M@www.iana.org; network_infrastructure_ports 11/11 1.1M@www.iana.org; voip_ports 7/7 1.1M@www.iana.org; streaming_media_ports 7/7 1.1M@www.iana.org; windows_networking_ports 9/9 1.1M@www.iana.org; printing_ports 5/5 1.1M@www.iana.org; version_control_ports 6/6 1.1M@www.iana.org; monitoring_ports 8/8 344k@www.iana.org; vpn_ports 7/7 868k@www.iana.org; container_orchestration_ports 5/5 491k@www.iana.org; http_service_ports 10/10 1.1M@www.iana.org; name_resolution_ports 5/5 759k@www.iana.org; smb_and_netbios_ports 5/5 185k@www.iana.org; microsoft_server_ports 14/14 1.5M@learn.microsoft.com; nosql_database_ports 8/8 209k@www.mongodb.com; iana_system_ports 686/686 1.1M@www.rfc-editor.org; iana_user_ports 5377/5377 1.1M@www.rfc-editor.org
client_app (24): web_browsers 12/12 233k@en.wikipedia.org; instant_messengers 10/10 17k@en.wikipedia.org; download_managers 7/7 89k@en.wikipedia.org; ssh_clients 5/5 32k@en.wikipedia.org; media_players 9/9 37k@en.wikipedia.org; pdf_readers 5/5 85k@en.wikipedia.org; office_suites 7/7 50k@en.wikipedia.org; software_updaters 7/7 70k@en.wikipedia.org; security_software 9/9 46k@en.wikipedia.org; file_sync_clients 5/5 43k@en.wikipedia.org; remote_desktop_clients 6/6 73k@en.wikipedia.org; ftp_clients 5/5 1k@en.wikipedia.org; developer_tools 9/9 70k@en.wikipedia.org; chromium_browsers 8/8 491k@en.wikipedia.org; email_chat_clients 13/13 69k@en.wikipedia.org; office_document_apps 13/13 50k@en.wikipedia.org; video_players 7/7 37k@en.wikipedia.org; developer_admin_tools 17/17 70k@en.wikipedia.org; security_update_tools 17/17 46k@en.wikipedia.org; remote_access_tools 13/13 73k@en.wikipedia.org; sync_download_tools 12/12 43k@en.wikipedia.org; microsoft_products 22/22 4.0M@www.microsoft.com; tencent_products 15/15 1.1M@www.tencent.com; qihoo_products 5/5 36k@www.360.cn
user (21): linux_base_accounts 20/20 553k@www.debian.org; mirai_default_usernames 11/11 106k@github.com; seclists_top_usernames 16/16 0@github.com; cloud_image_users 10/10 39k@docs.aws.amazon.com; database_default_users 10/10 26k@www.postgresql.org; web_server_users 10/10 186k@httpd.apache.org; ci_cd_users 8/8 103k@www.jenkins.io; network_device_users 14/14 27k@www.cisco.com; iot_default_users 10/10 766k@www.owasp.org; mail_server_users 7/7 229k@www.postfix.org; monitoring_users 8/8 24k@www.nagios.org; bigdata_users 12/12 652k@hadoop.apache.org; ftp_accounts 6/6 301k@www.rfc-editor.org; privileged_accounts 7/7 144k@www.debian.org; legacy_service_accounts 12/12 9k@www.debian.org; windows_accounts 6/6 0@learn.microsoft.com; service_accounts 115/115 9k@www.debian.org; application_server_accounts 17/17 186k@httpd.apache.org; data_platform_accounts 30/30 652k@hadoop.apache.org; automation_accounts 10/10 103k@www.jenkins.io; default_accounts 19/19 766k@www.owasp.org

## Same-partition check (section 8.2)
Lists equal to one single-valued attribute class (kept as competing lists, not candidates):
microsoft_products/qihoo_products/tencent_products = attr:vendor; iana_system_ports/
iana_user_ports = attr:range; cctlds_all = attr:type=ccTLD; gtlds_all = attr:region=?;
bigdata_users = attr:role=bigdata; cloud_image_users = attr:role=cloud;
privileged_accounts = attr:role=privileged (10 lists). Lists differing from every attribute
partition: tld 30/32, port 22/24, client_app 21/24, user 18/21. Candidate lists passing
H1/H2'/H4' (lint requirement in parentheses): tld 27 (21), port 21 (21), client_app 15 (11),
user 16 (11).

## Spotcheck (section 8.3)
`SPOTCHECK.tsv`: 1010 rows = 101 lists x (5 members + 5 non-members), 0 FAIL. A member is
checked in the list's member array of the curated raw snapshot and in the value registry
(IANA root zone / IANA port registry / `raw/curated/*.tsv`); a non-member is checked by
scanning the whole member array (line span and entry count are cited) while the value itself
is still in the registry. Example: `eu_member_cctlds at raw/curated/lists_tld.json:14 |
root zone raw/iana/tlds-alpha-by-domain.txt:76 | ISO raw/iso/countries.csv:16 (Austria)`.

## Scenario (`scenario.yaml`, section 4)
56 rule templates: tld 13, port 14, client_app 16, user 13. Fields:
`proxy_connections.tld` (code), `proxy_connections.port` (code),
`proxy_connections.client_app` (self_describing), `ssh_logins.user` (self_describing).
`label_nouns`: gateway lane, audit zone, event bucket, access lane, session tag.
Each template's rule text names its first plausible list, and the other plausible ids are
near-miss competing lists of the same universe; all 56 were checked one by one (for example
tld_eu -> eu_member_cctlds with schengen/eurozone/nato as confusers; port_mail ->
mail_service_ports with plaintext/tls-wrapped as confusers); one confirmation per template
is in `TEMPLATE_CHECK.md`. Every list except the two
attribute-equal IANA range lists appears in at least one template.

## dataset.py (section 5)
40 workstations `ws01..ws40`; each has 3-6 proxy `open` connections and 3-6 SSH logins
(seed 20266088, step `report`: 182 proxy + 183 SSH records; per-entity totals 6-12). Records
are sampled from the real Loghub Proxifier/OpenSSH lines; only the four trap fields are ever
replaced by `set_value`. `reference()` reads only `render()` output and is checked byte for
byte against `total()`. `check_dataset.py`: deterministic base_world, 40 entities, >=3
positions per entity per field, set_value visible, total() int and decreasing,
reference==total -> `RESULT: OK`.

## Chains (section 6)
`chains/LG1.yaml` .. `LG5.yaml`, seeds 20266088..20266092, dataset LG, period 2025-2026,
snapshot 2026-10-16, slots 5, probe soft, fields in the order tld, port, client_app, user.
Allocation: L1 tld, L2 port, L3 client_app, L4 user, L5 tld (tld and port are the only fields
with more than 100 values, so each may take two slots). `tools/dryrun.py ../inputs LG` exits
0: 8 candidates offered per slot, `build_instances` 0.7 s, 165 diagnostics.

## Reproducibility and checksums (section 7)
`bash rebuild.sh` runs build_universe_tld/port/catalog, build_lists, build_salience,
`clrsynth salience`, build_spotcheck. Two consecutive runs into separate snapshots give
byte-identical universes, lists, salience tables and SPOTCHECK (`diff -r` clean).
`sources/SHA256SUMS` covers 44 raw/source files and `sha256sum -c` passes.

## Lint output (section 8.1)
`cd code && python3 -m clrsynth lint LG --inputs-root ../inputs` -> exit 0, `lint OK: LG`,
with 10 informational notes for the attribute-equal lists above ("kept only as a competing
list"); no errors.

## Known issues and judgment calls
- Six client_app lists are cross-cutting unions of two same-source categories
  (email_chat_clients, office_document_apps, developer_admin_tools, security_update_tools,
  remote_access_tools, sync_download_tools). Their members come from the cited comparison
  pages but the union is our grouping. They are needed here: with disjoint process
  categories only 3 lists remain candidates, below the 11 required for 5 chains.
- `asia_pacific_cctlds` (a regional grouping, i.e. an attribute-like list) was removed from
  the final inputs; the tld candidate count stayed above the requirement.
- Salience is 0 for brand_gtlds ("Brand top-level domain" article is a 404),
  seclists_top_usernames and windows_accounts (no article); kept, as section 3 allows.
- `gtlds_all` coincides with `attr:region=?` because gTLDs have no country region; both the
  attribute and the list are kept (reported as a note, not deleted).
- The IDN ccTLD name table in `build_universe_tld.py` is transcribed from the ICANN IDN
  fast-track page; the Wikipedia page snapshot is `raw/wiki_idn.json`.
- Workstation ids are the audit grouping of real sampled log records: the source logs carry
  no workstation id, so `base_world` assigns the sampled records to 40 groups deterministically.
