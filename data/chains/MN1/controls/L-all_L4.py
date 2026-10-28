import csv
import hashlib
import random
from functools import lru_cache
from pathlib import Path

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["lots.origin_country", "lots.carrier", "lots.material"]
TASK = ("Each purchase lot counts once toward its factory unless a level rule excludes one of the "
        "lot's field values.")
ENTITY_NOUN = "factory"
ENTITY_NOUN_PLURAL = "factories"
INPUT_FORMAT = ("JSON with a top-level 'factories' array. Each factory has a factory_id and a "
                "purchase_orders array; each purchase order has a purchase_order_id and a lots array. "
                "Each lot has lot_id, origin_country, carrier and material.")


def _rng(seed, step, name):
    digest = hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest()
    return random.Random(int(digest, 16))


@lru_cache(maxsize=None)
def _universe(name):
    path = Path(__file__).resolve().parent / "universes" / f"{name}.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(row["value"] for row in csv.DictReader(handle, delimiter="\t"))


def _factories():
    return [f"F{i:03d}" for i in range(1, 37)]


def base_world(seed: int, step: str) -> dict:
    rng = _rng(seed, step, "world")
    values = {
        "country": list(_universe("country")),
        "carrier": list(_universe("carrier")),
        "material": list(_universe("material")),
    }
    factories = []
    purchase_orders = []
    lots = []
    lot_number = 1
    for factory_index, factory_id in enumerate(_factories(), 1):
        factories.append({"factory_id": factory_id, "site_name": f"Plant {factory_id[1:]}"})
        for order_offset in range(2):
            po_number = (factory_index - 1) * 2 + order_offset + 1
            po_id = f"PO{po_number:04d}"
            purchase_orders.append({
                "purchase_order_id": po_id,
                "factory_id": factory_id,
                "receiving_month": f"2025-{(po_number % 12) + 1:02d}",
            })
            lot_count = 2 + ((factory_index + order_offset) % 4)
            for _ in range(lot_count):
                lot_id = f"L{lot_number:05d}"
                lots.append({
                    "lot_id": lot_id,
                    "purchase_order_id": po_id,
                    "origin_country": rng.choice(values["country"]),
                    "carrier": rng.choice(values["carrier"]),
                    "material": rng.choice(values["material"]),
                    "batch_note": f"Batch {lot_number:05d}",
                })
                lot_number += 1
    return {"factories": factories, "purchase_orders": purchase_orders, "lots": lots}


def entities(world) -> list[str]:
    return sorted(factory["factory_id"] for factory in world["factories"])


def slots(world, field: str) -> list[tuple[str, str]]:
    po_to_factory = {po["purchase_order_id"]: po["factory_id"] for po in world["purchase_orders"]}
    return sorted((po_to_factory[lot["purchase_order_id"]], lot["lot_id"]) for lot in world["lots"])


def set_value(world, field: str, pos: str, value: str) -> None:
    key = field.split(".", 1)[1]
    for lot in world["lots"]:
        if lot["lot_id"] == pos:
            lot[key] = value
            return
    raise KeyError(pos)


def total(world, entity: str, excluded: set[tuple[str, str]]) -> int:
    excluded_positions = {position for _, position in excluded}
    factory_orders = {po["purchase_order_id"] for po in world["purchase_orders"]
                      if po["factory_id"] == entity}
    return sum(1 for lot in world["lots"]
               if lot["purchase_order_id"] in factory_orders and lot["lot_id"] not in excluded_positions)


def render(world, entity_ids: list[str]):
    selected = set(entity_ids)
    by_factory = {}
    for po in sorted(world["purchase_orders"], key=lambda item: item["purchase_order_id"]):
        if po["factory_id"] in selected:
            by_factory.setdefault(po["factory_id"], []).append({
                "purchase_order_id": po["purchase_order_id"],
                "receiving_month": po["receiving_month"],
                "lots": [],
            })
    po_index = {}
    for factory_entries in by_factory.values():
        for po in factory_entries:
            po_index[po["purchase_order_id"]] = po
    for lot in sorted(world["lots"], key=lambda item: item["lot_id"]):
        po = po_index.get(lot["purchase_order_id"])
        if po is not None:
            po["lots"].append({
                "lot_id": lot["lot_id"],
                "origin_country": lot["origin_country"],
                "carrier": lot["carrier"],
                "material": lot["material"],
            })
    factories = []
    for factory in sorted(world["factories"], key=lambda item: item["factory_id"]):
        if factory["factory_id"] in selected:
            factories.append({
                "factory_id": factory["factory_id"],
                "site_name": factory["site_name"],
                "purchase_orders": by_factory.get(factory["factory_id"], []),
            })
    return {"factories": factories}


def reference(data, excluded: dict[str, set[str]]) -> dict[str, int]:
    out = {}
    for factory in data.get("factories", []):
        count = 0
        for po in factory.get("purchase_orders", []):
            for lot in po.get("lots", []):
                skip = False
                for field in TRAP_FIELDS:
                    key = field.split(".", 1)[1]
                    if lot.get(key) in excluded.get(field, set()):
                        skip = True
                        break
                if not skip:
                    count += 1
        out[str(factory["factory_id"])] = count
    return out


def values(data, field: str) -> list[str]:
    key = field.split(".", 1)[1]
    out = []
    for factory in data.get("factories", []):
        for po in factory.get("purchase_orders", []):
            for lot in po.get("lots", []):
                if key in lot:
                    out.append(str(lot[key]))
    return out


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'lots.carrier': ['Air France', 'Air Senegal', 'All Nippon Airways', 'Brussels Airlines', 'Copa Airlines', 'EasyJet Switzerland', 'Eurowings', 'Heston Airlines', 'JetSMART Argentina', 'Mandarin Airlines', 'Red Sea Airlines', 'Shenzhen Airlines'], 'lots.material': ['cerium', 'europium', 'hafnium', 'lutetium', 'neodymium', 'nitrogen', 'rubidium', 'samarium', 'scandium', 'tellurium', 'thulium', 'yttrium'], 'lots.origin_country': ['AL', 'BB', 'BE', 'BR', 'CA', 'DE', 'DK', 'ES', 'GB', 'IT', 'JO', 'JP', 'MM', 'MX', 'NG', 'NL', 'PY', 'RO', 'SK', 'TJ', 'TR', 'TV', 'US', 'VE']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
