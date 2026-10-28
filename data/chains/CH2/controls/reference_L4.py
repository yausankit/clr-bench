"""Deterministic CH world: declaration lines, declarations, shipments, and importers."""
from __future__ import annotations

import hashlib
import random

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["lines.substance", "declarations.exporter_country", "shipments.air_carrier"]
TASK = ("Each declaration line counts once for its importer unless the line's substance, its declaration's "
        "exporter country, or its shipment's air carrier is excluded.")
ENTITY_NOUN = "importer"
INPUT_FORMAT = ("JSON with an importers array; each importer has an id and declarations, each declaration has "
                "an id, exporter_country, and shipments, and each shipment has an id, air_carrier, and lines.")

F_SUB = "lines.substance"
F_CTY = "declarations.exporter_country"
F_CAR = "shipments.air_carrier"

CHEMICALS = [
    "Benzene", "Toluene", "Xylene", "Methanol", "Acetone", "Chloroform",
    "Trichloroethylene", "Tetrachloroethylene", "Formaldehyde", "Styrene",
    "Acrylonitrile", "Vinyl chloride", "1,3-Butadiene", "Lead", "Mercury compounds",
    "Cadmium and cadmium compounds", "Nickel compounds", "DDT", "Lindane",
    "Chlorpyrifos", "Atrazine", "Alachlor", "Carbon tetrachloride", "Methyl bromide",
    "Sulfur mustard", "Phosgene", "Hydrogen cyanide",
]
COUNTRIES = [
    "DE", "FR", "IT", "ES", "NL", "BE", "PL", "SE", "FI", "IE", "AT", "PT",
    "US", "CA", "JP", "KR", "CN", "IN", "BR", "MX", "AU", "ZA", "NO", "CH",
    "TR", "SA", "AE",
]
CARRIERS = [
    "Lufthansa", "Air France", "KLM", "Delta Air Lines", "United Airlines",
    "American Airlines", "Air Canada", "Emirates", "Qatar Airways",
    "Turkish Airlines", "Singapore Airlines", "Cathay Pacific", "Japan Airlines",
    "Korean Air", "Ethiopian Airlines", "LATAM Airlines", "Avianca",
    "Copa Airlines", "Aegean Airlines", "Finnair",
]


def _rng(seed: int, step: str) -> random.Random:
    material = f"{seed}/{step}/CH/world".encode("utf-8")
    return random.Random(int(hashlib.sha256(material).hexdigest(), 16))


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def base_world(seed: int, step: str) -> dict:
    rng = _rng(seed, step)
    importers = []
    for i in range(40):
        importer_id = f"IMP-{i + 1:03d}"
        declarations = []
        for d in range(3):
            declaration_id = f"DEC-{i + 1:03d}-{d + 1}"
            shipment_id = f"SHP-{i + 1:03d}-{d + 1}"
            lines = []
            line_count = 1 + rng.randrange(3)
            for k in range(line_count):
                lines.append({
                    "id": f"LIN-{i + 1:03d}-{d + 1}-{k + 1}",
                    "substance": _pick(rng, CHEMICALS),
                })
            declarations.append({
                "id": declaration_id,
                "exporter_country": _pick(rng, COUNTRIES),
                "shipments": [{
                    "id": shipment_id,
                    "air_carrier": _pick(rng, CARRIERS),
                    "lines": lines,
                }],
            })
        importers.append({"id": importer_id, "declarations": declarations})
    return {"importers": importers}


def entities(world: dict) -> list[str]:
    return sorted(str(row["id"]) for row in world["importers"])


def slots(world: dict, field: str) -> list[tuple[str, str]]:
    out = []
    for importer in world["importers"]:
        eid = str(importer["id"])
        for declaration in importer["declarations"]:
            if field == F_CTY:
                out.append((eid, str(declaration["id"])))
            for shipment in declaration["shipments"]:
                if field == F_CAR:
                    out.append((eid, str(shipment["id"])))
                for line in shipment["lines"]:
                    if field == F_SUB:
                        out.append((eid, str(line["id"])))
    return sorted(out)


def set_value(world: dict, field: str, pos: str, value: str) -> None:
    if field == F_SUB:
        for importer in world["importers"]:
            for declaration in importer["declarations"]:
                for shipment in declaration["shipments"]:
                    for line in shipment["lines"]:
                        if str(line["id"]) == pos:
                            line["substance"] = value
                            return
    elif field == F_CTY:
        for importer in world["importers"]:
            for declaration in importer["declarations"]:
                if str(declaration["id"]) == pos:
                    declaration["exporter_country"] = value
                    return
    elif field == F_CAR:
        for importer in world["importers"]:
            for declaration in importer["declarations"]:
                for shipment in declaration["shipments"]:
                    if str(shipment["id"]) == pos:
                        shipment["air_carrier"] = value
                        return
    raise KeyError((field, pos))


def total(world: dict, entity: str, excluded: set[tuple[str, str]]) -> int:
    count = 0
    for importer in world["importers"]:
        if str(importer["id"]) != entity:
            continue
        for declaration in importer["declarations"]:
            if (F_CTY, str(declaration["id"])) in excluded:
                continue
            for shipment in declaration["shipments"]:
                if (F_CAR, str(shipment["id"])) in excluded:
                    continue
                for line in shipment["lines"]:
                    if (F_SUB, str(line["id"])) not in excluded:
                        count += 1
    return count


def render(world: dict, entity_ids: list[str]):
    wanted = set(entity_ids)
    return {"importers": [row for row in world["importers"] if str(row["id"]) in wanted]}


def reference(data, excluded: dict[str, set[str]]) -> dict[str, int]:
    out = {}
    for importer in data["importers"]:
        count = 0
        for declaration in importer["declarations"]:
            if declaration["exporter_country"] in excluded.get(F_CTY, set()):
                continue
            for shipment in declaration["shipments"]:
                if shipment["air_carrier"] in excluded.get(F_CAR, set()):
                    continue
                for line in shipment["lines"]:
                    if line["substance"] not in excluded.get(F_SUB, set()):
                        count += 1
        out[str(importer["id"])] = count
    return out


def values(data, field: str) -> list[str]:
    out = []
    for importer in data["importers"]:
        for declaration in importer["declarations"]:
            if field == F_CTY:
                out.append(declaration["exporter_country"])
            for shipment in declaration["shipments"]:
                if field == F_CAR:
                    out.append(shipment["air_carrier"])
                for line in shipment["lines"]:
                    if field == F_SUB:
                        out.append(line["substance"])
    return out


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'declarations.exporter_country': ['FR', 'GB', 'JP', 'US'], 'lines.substance': ['Alpha-hexachlorocyclohexane', 'Brominated diphenyl ethers', 'Cyanogen chloride', 'Hydrogen cyanide', 'Phosphorus oxychloride', 'Polychlorinated biphenyls', 'Triethanolamine', 'UV-328'], 'shipments.air_carrier': ['American Airlines', 'Finnair', 'Qantas Airways', 'Qatar Airways']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
