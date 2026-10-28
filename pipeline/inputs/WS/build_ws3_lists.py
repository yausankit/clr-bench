#!/usr/bin/env python3
"""Build the WS3 language-list supplement from raw source snapshots only."""
import csv
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI3 = RAW / "wiki_ws3"


SPECS = [
    dict(id="canada_mother_tongue_languages", page="Languages_of_Canada", start=1743,
         name="Languages in Canada (Mother Tongue), 2016 Census",
         source_title="Languages in Canada (Mother Tongue), 2016 Census"),
    dict(id="canada_knowledge_languages", page="Languages_of_Canada", start=1260,
         name="Knowledge of Languages in Canada",
         source_title="Knowledge of Languages in Canada"),
    dict(id="finland_native_languages", page="Languages_of_Finland", start=144,
         name="Residents of Finland by native language",
         source_title="Residents of Finland by native language (1995, 2005, 2015 and 2025)"),
    dict(id="france_metropolitan_ethnologue_languages", page="Languages_of_France", start=233,
         name="Ethnologue languages of metropolitan France",
         source_title="Ethnologue, Metropolitan France"),
    dict(id="india_2011_census_languages", page="Languages_of_India", start=198,
         name="Languages by number of speakers in India (2011 Census)",
         source_title="First, second, and third languages by number of speakers in India (2011 Census)"),
    dict(id="kazakhstan_census_languages", page="Languages_of_Kazakhstan", start=31,
         name="Languages of Kazakhstan (2021 census)",
         source_title="Languages (2021 Kazakhstani census table)"),
    dict(id="nepal_native_languages", page="Languages_of_Nepal", start=1486,
         name="Native languages of Nepal (2011 census)",
         source_title="Number of native speakers (2011 Nepal census)"),
    dict(id="spain_2021_census_languages", page="Languages_of_Spain", start=89,
         name="First languages of Spain (2021 census)",
         source_title="First language of those aged two or over, 2021 census"),
    dict(id="turkey_1965_census_languages", page="Languages_of_Turkey", start=270,
         name="Languages spoken in Turkey (1965 census)",
         source_title="Languages spoken in Turkey, 1965 census"),
    dict(id="turkey_ethnologue_languages", page="Languages_of_Turkey", start=1527, cell_index=1,
         name="Languages by number of speakers in Turkey (Ethnologue)",
         source_title="Languages by number of speakers in Turkey (with Expanded Graded Intergenerational Disruption Scale)"),
    dict(id="ukraine_2001_census_languages", page="Languages_of_Ukraine", start=90,
         name="Languages of Ukraine (2001 census)",
         source_title="2001 national census"),
    dict(id="malaysia_indian_languages", page="Languages_of_Malaysia", start=522,
         name="Languages of Malaysian Indians",
         source_title="Malaysian Indian languages"),
    dict(id="italy_foreign_languages", page="Languages_of_Italy", start=356,
         name="Mother tongues of foreign citizens in Italy",
         source_title="Mother tongues of foreign citizens in Italy"),
    dict(id="norway_non_native_languages", page="Languages_of_Norway", start=80,
         name="Non-native first languages in Norway",
         source_title="Residents of Norway by non-native first-language (2012, estimation)"),
    dict(id="russia_official_languages", page="Languages_of_Russia", start=30,
         name="Official languages of the republics of Russia",
         source_title="Official languages of the Russian republics"),
    dict(id="thailand_census_languages", page="Languages_of_Thailand", start=385,
         name="Population of Thailand by language",
         source_title="Population of Thailand by language"),
    dict(id="turkey_konda_languages", page="Languages_of_Turkey", start=1477,
         name="Mother tongues in Turkey (KONDA 2006)",
         source_title="Mother tongues in Turkey (KONDA 2006)"),
    dict(id="iran_gamaan_languages", page="Languages_of_Iran", start=181,
         name="Languages spoken at home in Iran (Gamaan survey)",
         source_title="Gamaan Survey (languages spoken at home)"),
    dict(id="pakistan_established_languages", page="Languages_of_Pakistan", start=26,
         name="Established languages of Pakistan",
         source_title="Established languages (Ethnologue 2022)"),
    dict(id="ethiopia_official_languages", page="Languages_of_Ethiopia", manual="ethiopia_official",
         name="Official languages of Ethiopia",
         source_title="Languages of Ethiopia (official languages field)"),
]


EXTRA_ALIASES = {
    "russian": "ru", "arabic": "ar", "english": "en", "spanish": "es", "german": "de",
    "french": "fr", "italian": "it", "chinese": "zh", "mandarin": "zh", "persian": "fa",
    "cree": "cr", "malaysian": "ms", "bahasa indonesia": "id", "azeri": "az",
    "turkmeni": "tk", "armeni": "hy", "iranian persian": "fa", "ndebele": "nr",
}

SKIP_EXACT = {
    "other", "others", "other languages", "total", "totals", "total:", "unknown", "none",
    "not indicated", "not reported", "local languages", "dialect and others in thailand",
    "of which only spanish", "single language responses", "official languages",
    "official language", "non-official languages", "combined chinese responses",
    "other non-indigenous languages", "other indigenous languages",
    "multiple language responses", "english and french", "english and a non-official language",
    "french and a non-official language", "english, french, and a non-official language",
}
SKIP_PREFIX = ("total respondents", "none (", "combined ")


def strip_templates(text):
    while "{{" in text:
        out, i, changed = [], 0, False
        while i < len(text):
            if text.startswith("{{", i):
                depth, j = 0, i
                while j < len(text):
                    if text.startswith("{{", j):
                        depth, j = depth + 1, j + 2
                    elif text.startswith("}}", j):
                        depth, j = depth - 1, j + 2
                        if depth == 0:
                            break
                    else:
                        j += 1
                changed, i = True, j
            else:
                out.append(text[i])
                i += 1
        text = "".join(out)
        if not changed:
            break
    return text


def plain(text):
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = strip_templates(text)
    text = re.sub(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"'''?", "", text)
    text = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip(" |.")
    text = re.sub(r"^L[12]\s+", "", text, flags=re.I)
    text = re.sub(r"\s*\(including.*$", "", text, flags=re.I)
    return text.strip(" ,;")


def norm(text):
    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = re.sub(r"\s+(language|languages)$", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip(" .;:").lower()


def iso_aliases():
    path = RAW / "wiki" / "List_of_ISO_639-1_codes.wikitext"
    lines = path.read_text(encoding="utf-8").splitlines()
    aliases = {}
    for i, line in enumerate(lines):
        match = re.match(
            r'\|\s*id="([a-z]{2})"\s*\|\s*(.*?)\s*\|\|\s*<code>\{\{iso639-1\|[a-z]{2}\}\}</code>', line)
        if not match:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        parts = [part.strip() for part in nxt.split("||")]
        kind = parts[1] if len(parts) > 1 else ""
        if kind not in ("Living", "Constructed"):
            continue
        cell = match.group(2)
        names = set()
        for target, display in re.findall(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", cell):
            names.add((display or target).strip())
            target = re.sub(r"\s*\([^)]*\)", "", target)
            target = re.sub(r"\s+(language|languages)$", "", target, flags=re.I)
            names.add(target.strip())
        bare = re.sub(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), cell)
        bare = re.sub(r"<[^>]+>", "", bare)
        names.update(part.strip() for part in bare.split(","))
        for name in names:
            if name:
                aliases.setdefault(norm(name), match.group(1))
    aliases.update(EXTRA_ALIASES)
    return aliases


def cell_texts(block):
    cells = []
    for line in block[1:]:
        line = line.strip()
        if not line or line.startswith(("|-", "|}", "|+", "!")) or not line.startswith("|"):
            continue
        for piece in line[1:].split("||"):
            piece = piece.strip()
            if "|" in piece:
                prefix, rest = piece.split("|", 1)
                if ("=" in prefix or prefix.startswith(("align", "style", "colspan", "rowspan", "class"))) \
                        and "[[" not in prefix:
                    piece = rest.strip()
            if piece:
                cells.append(piece)
    return cells


def table_bounds(page, start):
    lines = (WIKI3 / f"{page}.wikitext").read_text(encoding="utf-8").splitlines()
    index = start - 1
    while index < len(lines) and not lines[index].startswith("{|"):
        index += 1
    if index >= len(lines):
        raise ValueError(f"{page}: no table at/after line {start}")
    end = next(i for i in range(index + 1, len(lines)) if lines[i].startswith("|}"))
    return lines, index, end


def parse_table(spec, aliases):
    lines, index, end = table_bounds(spec["page"], spec["start"])
    starts = [i for i in range(index + 1, end) if lines[i].startswith("|-")]
    members, out_names, evidence = [], [], {}
    for row_no, row_start in enumerate(starts):
        row_end = starts[row_no + 1] if row_no + 1 < len(starts) else end
        cells = cell_texts(lines[row_start:row_end])
        if not cells:
            continue
        cell_index = spec.get("cell_index")
        candidates = [cell_index] if cell_index is not None else list(range(min(2, len(cells))))
        found = None
        for idx in candidates:
            if idx >= len(cells):
                continue
            text = plain(cells[idx])
            if not text or re.fullmatch(r"\d+(?:\.\d+)?%?", text):
                continue
            low = text.lower()
            if low in SKIP_EXACT or low.startswith(SKIP_PREFIX):
                continue
            code = aliases.get(norm(text))
            if code:
                found = (code, text)
                break
            # First real cell is the source language when no ISO 639-1 code exists.
            if idx == 0 or (idx == 1 and re.fullmatch(r"\d+", plain(cells[0]))) \
                    or idx == spec.get("cell_index"):
                found = (None, text)
                break
        if not found:
            continue
        code, text = found
        line_no = row_start + 1
        if code:
            if code not in members:
                members.append(code)
                evidence[code] = (line_no, text)
            else:
                out_names.append(f"{text} (duplicate source entry for {code})")
        else:
            out_names.append(text)
    seen = set()
    unique_out = []
    for name in out_names:
        if name not in seen:
            seen.add(name)
            unique_out.append(name)
    source_range = f"L{index + 1}-L{end + 1}"
    return members, unique_out, evidence, source_range


def parse_ethiopia(aliases):
    lines = (WIKI3 / "Languages_of_Ethiopia.wikitext").read_text(encoding="utf-8").splitlines()
    line_no = next(i for i, line in enumerate(lines, 1) if re.match(r"\s*\|\s*official\s*=", line))
    line = lines[line_no - 1]
    names = [display or target for target, display in re.findall(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", line)]
    members, evidence = [], {}
    for name in names:
        code = aliases.get(norm(name))
        if not code:
            raise ValueError(f"Ethiopia official language has no ISO 639-1 code: {name}")
        if code not in members:
            members.append(code)
            evidence[code] = (line_no, name)
    return members, [], evidence, f"L{line_no}"


def pageviews(title):
    path = ROOT / "salience" / "raw" / f"pv_{title}.json"
    if not path.exists():
        return 0
    return sum(int(item["views"]) for item in json.loads(path.read_text(encoding="utf-8")).get("items", []))


def build_entries():
    aliases = iso_aliases()
    entries = []
    for spec in SPECS:
        if spec.get("manual") == "ethiopia_official":
            members, out_names, evidence, source_range = parse_ethiopia(aliases)
        else:
            members, out_names, evidence, source_range = parse_table(spec, aliases)
        if len(members) < 5:
            raise ValueError(f"{spec['id']}: only {len(members)} members")
        official_count = len(members) + len(out_names)
        entry = dict(
            id=spec["id"], name=spec["name"], synonyms=[], members=sorted(members), disputed=[],
            changes=[], out_of_universe=sorted(out_names), official_count=official_count,
            source=f"https://en.wikipedia.org/wiki/{spec['page']}",
            salience=pageviews(spec["page"]),
            _source_title=spec["source_title"], _source_range=source_range,
            _evidence=evidence,
        )
        entries.append(entry)
    return entries


def make_spotcheck(entries, universe):
    rows = []
    for entry in entries:
        lid, members = entry["id"], set(entry["members"])
        for code in sorted(members)[:5]:
            line_no, text = entry["_evidence"][code]
            rows.append([lid, "language", "member", code,
                         f"raw/wiki_ws3/{entry['_source_file']}:{line_no} (table row: {text})"])
        nonmembers = sorted(universe - members)[:5]
        for code in nonmembers:
            rows.append([lid, "language", "nonmember", code,
                         f"raw/wiki_ws3/{entry['_source_file']}:{entry['_source_range']} (absent from parsed table)"])
    return rows


def main():
    entries = build_entries()
    source_file = {spec["id"]: spec["page"] + ".wikitext" for spec in SPECS}
    for entry in entries:
        entry["_source_file"] = source_file[entry["id"]]

    universe = set()
    with (ROOT / "universes" / "language.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            universe.add(row["value"])

    baseline = yaml.safe_load((RAW / "base_ws3_language.yaml").read_text(encoding="utf-8"))
    existing_ids = {item["id"] for item in baseline}
    new_ids = {entry["id"] for entry in entries}
    assert existing_ids.isdisjoint(new_ids)
    all_lists = baseline + [{key: value for key, value in entry.items() if not key.startswith("_")}
                            for entry in entries]
    by_id = {item["id"]: set(item["members"]) for item in all_lists}
    for entry in entries:
        members = set(entry["members"])
        competitors = [other for other, values in by_id.items()
                       if other != entry["id"] and values != members and values & members]
        if len(competitors) < 2:
            raise ValueError(f"{entry['id']}: only {len(competitors)} overlapping competitor lists")
        entry["_competitors"] = competitors
        if len(members) * 2 > len(universe):
            raise ValueError(f"{entry['id']}: more than half of universe")

    (ROOT / "lists" / "language.yaml").write_text(
        yaml.safe_dump(all_lists, allow_unicode=True, sort_keys=False), encoding="utf-8")

    spot_rows = make_spotcheck(entries, universe)
    base_spot = (RAW / "base_ws3_SPOTCHECK.tsv").read_text(encoding="utf-8")
    with (ROOT / "SPOTCHECK.tsv").open("w", encoding="utf-8", newline="") as fh:
        fh.write(base_spot)
        if base_spot and not base_spot.endswith("\n"):
            fh.write("\n")
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerows(spot_rows)

    titles = (RAW / "base_ws3_titles.tsv").read_text(encoding="utf-8")
    with (ROOT / "salience" / "titles.tsv").open("w", encoding="utf-8", newline="") as fh:
        fh.write(titles)
        if titles and not titles.endswith("\n"):
            fh.write("\n")
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        for spec in SPECS:
            writer.writerow([spec["id"], spec["page"], "wikipedia article"])

    print(f"new lists {len(entries)}; total language lists {len(all_lists)}")
    print("id\tmembers\tofficial_count\tsalience\tcompetitors")
    for entry in entries:
        print(f"{entry['id']}\t{len(entry['members'])}\t{entry['official_count']}\t"
              f"{entry['salience']}\t{len(entry['_competitors'])}")
    print("large (>=10):", sum(len(entry["members"]) >= 10 for entry in entries))
    print("spotcheck rows:", len(spot_rows))


if __name__ == "__main__":
    main()
