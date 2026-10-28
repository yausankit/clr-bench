"""Write value-description tables from the frozen snapshots in raw/desc/."""

import csv
import string
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("value", "description", "source")
UNIVERSES = ("condition", "medicine", "procedure")


def read_snapshot(universe):
    path = ROOT / "raw" / "desc" / f"{universe}.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: expected header {FIELDS!r}")
        rows = list(reader)

    seen = set()
    for row in rows:
        value = row["value"]
        description = row["description"]
        source = row["source"]
        if not value or not description or not source:
            raise ValueError(f"{path}: blank field in {row!r}")
        if value in seen:
            raise ValueError(f"{path}: duplicate value {value!r}")
        if len(description) > 200 or "\n" in description:
            raise ValueError(f"{path}: description too long for {value!r}")
        printable = set(string.printable) - set("\t\n\r\x0b\x0c")
        if any(ch not in printable or ord(ch) > 127 for ch in description):
            raise ValueError(f"{path}: non-English character in {value!r}")
        seen.add(value)
    return rows


def write_table(universe, rows):
    path = ROOT / "universes" / f"{universe}.desc.tsv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    for universe in UNIVERSES:
        rows = read_snapshot(universe)
        path = write_table(universe, rows)
        print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
