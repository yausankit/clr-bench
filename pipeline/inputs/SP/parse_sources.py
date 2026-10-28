"""Parse fixed MediaWiki HTML snapshots according to source_specs.py."""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent


def load_page(key):
    return json.loads((ROOT / "raw" / "pages" / f"{key}.json").read_text(encoding="utf-8"))["parse"]


def first_link(cell):
    if cell is None:
        return None
    for link in cell.find_all("a", href=True):
        if not link.get("href", "").startswith("/wiki/"):
            continue
        if link.find_parent("span", class_="flagicon"):
            continue
        title = link.get("title") or link.get_text(" ", strip=True)
        display = link.get_text(" ", strip=True)
        if not title or not display or display.strip() in {"v", "t", "e"} or \
                title.startswith(("Template:", "Special:", "Help:")):
            continue
        return {"title": title.replace("_", " "), "display": display}
    return None


def parse_table(page, spec):
    table = BeautifulSoup(page["text"], "lxml").find_all("table")[spec["index"]]
    out = []
    for row_index, tr in enumerate(table.find_all("tr")):
        cells = tr.find_all(["th", "td"], recursive=False)
        if cells and len(tr.find_all("th", recursive=False)) == len(cells):
            continue
        col = spec["column"]
        if len(cells) <= col or len(cells) < int(spec.get("min_cells") or (col + 1)):
            continue
        if spec.get("filter_column") is not None:
            if len(cells) <= spec["filter_column"]:
                continue
            text = cells[spec["filter_column"]].get_text(" ", strip=True)
            try:
                value = int(text)
            except ValueError:
                continue
            if value < int(spec.get("filter_min") or 0):
                continue
        link = first_link(cells[col])
        if not link:
            text = re.sub(r"\s*\[[^\]]*\]\s*", " ", cells[col].get_text(" ", strip=True)).strip()
            if len(text) > 1:
                link = {"title": text, "display": text}
        if link:
            record = {**link, "evidence": f"table {spec['index']} row {row_index} column {col}"}
            country_col = spec.get("country_column")
            if country_col is not None and len(cells) > country_col:
                record["country"] = cells[country_col].get_text(" ", strip=True)
            out.append(record)
    return out


def parse_list(page, spec):
    soup = BeautifulSoup(page["text"], "lxml")
    container = soup.find_all(["ul", "ol"])[spec["index"]]
    out = []
    for item_index, li in enumerate(container.find_all("li", recursive=False), 1):
        link = first_link(li)
        if link:
            out.append({**link, "evidence": f"list {spec['index']} item {item_index}"})
    return out


def parse_navbox(page, spec):
    soup = BeautifulSoup(page["text"], "lxml")
    for box in soup.find_all("div", class_="navbox"):
        if spec["contains"].lower() not in box.get_text(" ", strip=True).lower():
            continue
        out, seen = [], set()
        for link_index, link in enumerate(box.find_all("a", href=True), 1):
            if not link.get("href", "").startswith("/wiki/"):
                continue
            title = (link.get("title") or "").replace("_", " ")
            display = link.get_text(" ", strip=True)
            if not title or not display or display in {"v", "t", "e"} or display.startswith(("List of ", "Components of ")) or title in seen or \
                    title.startswith(("Template:", "Special:", "Help:")):
                continue
            seen.add(title)
            out.append({"title": title, "display": display, "evidence": f"navbox link {link_index}"})
        if out:
            return out
    return []


def members_for(item):
    page = load_page(item["spec"]["page"])
    kind = item["spec"]["kind"]
    if kind == "table":
        rows = parse_table(page, item["spec"])
    elif kind == "list":
        rows = parse_list(page, item["spec"])
    elif kind == "navbox":
        rows = parse_navbox(page, item["spec"])
    else:
        raise ValueError(f"unknown source kind {kind}")
    unique, seen = [], set()
    for row in rows:
        key = row["title"]
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return page, unique


def source_url(page):
    url = f"https://en.wikipedia.org/w/index.php?title={page['title'].replace(' ', '_')}"
    if page.get("revid"):
        url += f"&oldid={page['revid']}"
    return url
