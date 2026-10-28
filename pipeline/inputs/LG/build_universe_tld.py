#!/usr/bin/env python3
"""Build universes/tld.tsv from the IANA root zone file, the ISO 3166-1 table
and the ICANN IDN ccTLD fast-track list (hard-coded below from the ICANN table).
Run: python3 build_universe_tld.py  (writes universes/tld.tsv)"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"

IDN_CCTLD = {
    "xn--2scrj9c": ("India", "ಭಾರತ"), "xn--3e0b707e": ("South Korea", "한국"),
    "xn--45br5cyl": ("India", "ভাৰত"), "xn--45brj9c": ("India", "ভারত"),
    "xn--4dbrk0ce": ("Israel", "ישראל"), "xn--54b7fta0cc": ("Bangladesh", "বাংলা"),
    "xn--80ao21a": ("Kazakhstan", "қаз"), "xn--90a3ac": ("Serbia", "срб"),
    "xn--90ae": ("Bulgaria", "бг"), "xn--90ais": ("Belarus", "бел"),
    "xn--gecrj9c": ("India", "ભારત"), "xn--h2breg3eve": ("India", "भारतम्"),
    "xn--h2brj9c": ("India", "भारत"), "xn--h2brj9c8c": ("India", "भारोत"),
    "xn--j1amh": ("Ukraine", "укр"), "xn--j6w193g": ("Hong Kong", "香港"),
    "xn--kprw13d": ("Taiwan", "台湾"), "xn--kpry57d": ("Taiwan", "台灣"),
    "xn--l1acc": ("Mongolia", "мон"), "xn--lgbbat1ad8j": ("Algeria", "الجزائر"),
    "xn--mgb9awbf": ("Oman", "عمان"), "xn--mgba3a4f16a": ("Iran", "ایران"),
    "xn--mgbaam7a8h": ("United Arab Emirates", "امارات"),
    "xn--mgbah1a3hjkrd": ("Mauritania", "موريتانيا"), "xn--mgbai9azgqp6j": ("Pakistan", "پاکستان"),
    "xn--mgbayh7gpa": ("Jordan", "الاردن"), "xn--mgbc0a9azcg": ("Morocco", "المغرب"),
    "xn--mgbcpq6gpa1a": ("Bahrain", "البحرين"), "xn--mgberp4a5d4ar": ("Saudi Arabia", "السعودية"),
    "xn--mgbpl2fh": ("Sudan", "سودان"), "xn--mgbtx2b": ("Iraq", "عراق"),
    "xn--mgbx4cd0ab": ("Malaysia", "مليسيا"), "xn--mix891f": ("Macau", "澳門"),
    "xn--node": ("Georgia", "გე"), "xn--o3cw4h": ("Thailand", "ไทย"),
    "xn--ogbpf8fl": ("Syria", "سورية"), "xn--p1ai": ("Russia", "рф"),
    "xn--pgbs0dh": ("Tunisia", "تونس"), "xn--q7ce6a": ("Laos", "ລາວ"),
    "xn--qxa6a": ("European Union", "ευ"), "xn--qxam": ("Greece", "ελ"),
    "xn--fiqs8s": ("China", "中国"), "xn--fiqz9s": ("China", "中國"),
    "xn--wgbh1c": ("Egypt", "مصر"), "xn--wgbl6a": ("Qatar", "قطر"),
    "xn--xkc2al3hye2a": ("Sri Lanka", "இலங்கை"), "xn--xkc2dl3a5ee0h": ("India", "இந்தியா"),
    "xn--y9a3aq": ("Armenia", "հայ"), "xn--yfro4i67o": ("Singapore", "新加坡"),
    "xn--ygbi2ammx": ("Palestine", "فلسطين"), "xn--fpcrj9c3d": ("India", "భారత్"),
    "xn--s9brj9c": ("India", "ਭਾਰਤ"), "xn--mgbbh1a": ("India", "بارت"),
    "xn--mgbgu82a": ("India", "ڀارت"), "xn--rvc1e0am3e": ("India", "ഭാരതം"),
    "xn--fzc2c9e2c": ("Sri Lanka", "ලංකා"), "xn--clchc0ea0b2g2a9gcd": ("Singapore", "சிங்கப்பூர்"),
}

EXTRA_CCTLD = {"ac": "Ascension Island", "eu": "European Union", "uk": "United Kingdom"}
EXTRA_REGION = {"ac": "Africa", "eu": "Europe", "uk": "Europe"}
DROP = {"su"}
ISO_ALIAS = {"South Korea": "Korea, Republic of", "Iran": "Iran, Islamic Republic of",
             "Macau": "Macao", "Syria": "Syrian Arab Republic", "Russia": "Russian Federation",
             "Laos": "Lao People's Democratic Republic", "Palestine": "Palestine, State of",
             "Taiwan": "Taiwan, Province of China", "European Union": None}
REGION_FIX = {"aq": "Antarctica", "tw": "Asia", "xn--kprw13d": "Asia", "xn--kpry57d": "Asia", "xn--qxa6a": "Europe"}

GTLD_MEANING = {
    "com": "commercial", "org": "organization", "net": "network", "edu": "education",
    "gov": "government", "mil": "military", "int": "international organization", "arpa": "infrastructure",
    "info": "information", "biz": "business", "name": "personal name", "pro": "professional",
    "mobi": "mobile devices", "asia": "Asia region", "cat": "Catalan language", "coop": "cooperatives",
    "jobs": "employment", "museum": "museums", "post": "postal services", "tel": "telephone",
    "travel": "travel industry", "xxx": "adult entertainment", "aero": "air transport",
    "app": "applications", "dev": "developers", "cloud": "cloud services", "xyz": "generic",
    "online": "online services", "site": "websites", "store": "retail", "shop": "shopping",
}


def main():
    tlds = [l.strip().lower() for l in (RAW / "iana" / "tlds-alpha-by-domain.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    iso_rows = list(csv.DictReader((RAW / "iso" / "countries.csv").open(encoding="utf-8")))
    iso = {r["alpha-2"].lower(): r for r in iso_rows}
    name2region = {r["name"]: r["region"] for r in iso_rows}
    rows = []
    for t in tlds:
        if t in DROP:
            continue
        if t in IDN_CCTLD:
            country, uni = IDN_CCTLD[t]
            region = name2region.get(ISO_ALIAS.get(country, country) or "", "?")
            rows.append((t, f"{country} ({uni})", "ccTLD", region or "?"))
        elif len(t) == 2:
            if t in iso:
                rows.append((t, iso[t]["name"], "ccTLD", iso[t]["region"] or "?"))
            elif t in EXTRA_CCTLD:
                rows.append((t, EXTRA_CCTLD[t], "ccTLD", EXTRA_REGION[t]))
            else:
                raise SystemExit(f"unmapped ccTLD {t}")
        else:
            rows.append((t, GTLD_MEANING.get(t, t), "gTLD", "?"))
    rows = [(a, b, c, REGION_FIX.get(a, d)) for a, b, c, d in rows]
    rows.sort()
    out = ["value\tentity\tattr:type\tattr:region"]
    out += ["\t".join(r) for r in rows]
    (ROOT / "universes" / "tld.tsv").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"tld: {len(rows)} values")


if __name__ == "__main__":
    main()
