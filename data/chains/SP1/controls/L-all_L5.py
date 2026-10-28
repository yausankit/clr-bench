"""Deterministic generated world for the SP sports-sponsorship settlement dataset."""
import hashlib
import random

ANSWER_FORMAT = "json"
TRAP_FIELDS = ["activations.club", "activations.co_sponsor", "activations.market_country"]
TASK = ("Each activation is one unit in the total of the sponsor brand reached through its contract; "
        "an activation is left out when one of its trap-field values is rejected.")
ENTITY_NOUN = "sponsor brand"
INPUT_FORMAT = ("JSON with sponsor_brands, contracts, and activations; each activation points to one contract, "
                "and each contract points to one sponsor brand.")

BRANDS = [
    "Apex Motion", "Blue Harbour", "Cedar Finance", "Delta Cloud", "Evergreen Foods",
    "Falcon Mobility", "Granite Bank", "Harbor Health", "Ironwood Energy", "Juniper Retail",
    "Kestrel Media", "Lighthouse Telecom", "Meridian Insurance", "Northstar Brewing", "Orchard Home",
    "Pioneer Sports", "Quarry Systems", "Redwood Travel", "Silverline Apparel", "Terra Agritech",
    "Union Payments", "Vertex Motors", "Westfield Pharmacy", "Xenon Devices", "Yellowstone Hotels",
    "Zephyr Airlines", "Atlas Logistics", "Beacon Software", "Copperline Toys", "Driftwood Furniture",
    "Ember Restaurants", "Frontier Security", "Greenfield Chemicals", "Highland Water", "Ivory Cosmetics",
    "Jade Semiconductor", "Keystone Rail", "Lumen Gaming", "Monarch Jewelry", "Nimbus Networks",
]


def _rng(seed, step, name):
    digest = hashlib.sha256(f"{seed}/{step}/{name}".encode()).hexdigest()
    return random.Random(int(digest, 16))


def base_world(seed: int, step: str) -> dict:
    rng = _rng(seed, step, "sp_world")
    brands = {f"BR{i:02d}": {"id": f"BR{i:02d}", "name": name}
              for i, name in enumerate(sorted(BRANDS), 1)}
    contracts = {}
    activations = {}
    aid = 0
    for i, brand_id in enumerate(sorted(brands), 1):
        contract_id = f"CT{i:03d}"
        contracts[contract_id] = {"id": contract_id, "brand_id": brand_id, "year": 2026}
        for _ in range(rng.randint(6, 9)):
            aid += 1
            activation_id = f"AC{aid:04d}"
            activations[activation_id] = {
                "id": activation_id,
                "contract_id": contract_id,
                "club": "Club pending",
                "co_sponsor": "Company pending",
                "market_country": "ZZ",
            }
    return {"sponsor_brands": brands, "contracts": contracts, "activations": activations}


def entities(world) -> list[str]:
    return sorted(world["sponsor_brands"])


def slots(world, field: str) -> list[tuple[str, str]]:
    contract_brand = {cid: row["brand_id"] for cid, row in world["contracts"].items()}
    return sorted((contract_brand[row["contract_id"]], aid)
                  for aid, row in world["activations"].items())


def set_value(world, field: str, pos: str, value: str) -> None:
    world["activations"][pos][field.split(".", 1)[1]] = value


def total(world, entity: str, excluded: set[tuple[str, str]]) -> int:
    contract_ids = {cid for cid, row in world["contracts"].items() if row["brand_id"] == entity}
    skipped = {pos for _, pos in excluded}
    return sum(1 for aid, row in world["activations"].items()
               if row["contract_id"] in contract_ids and aid not in skipped)


def render(world, entity_ids: list[str]):
    keep = set(entity_ids)
    brands = [dict(world["sponsor_brands"][bid]) for bid in sorted(keep)]
    contracts = [dict(row) for _, row in sorted(world["contracts"].items()) if row["brand_id"] in keep]
    contract_ids = {row["id"] for row in contracts}
    activations = [dict(row) for _, row in sorted(world["activations"].items())
                   if row["contract_id"] in contract_ids]
    return {"sponsor_brands": brands, "contracts": contracts, "activations": activations}


def reference(data, excluded: dict[str, set[str]]) -> dict[str, int]:
    brand_of = {row["id"]: row["brand_id"] for row in data["contracts"]}
    out = {row["id"]: 0 for row in data["sponsor_brands"]}
    for row in data["activations"]:
        if any(row[field.split(".", 1)[1]] in rejected for field, rejected in excluded.items()):
            continue
        out[brand_of[row["contract_id"]]] += 1
    return out


def values(data, field: str) -> list[str]:
    leaf = field.split(".", 1)[1]
    return [row[leaf] for row in data["activations"]]


# ---- clrsynth control program ----
import os as _os
_EXCLUDED = {k: set(v) for k, v in {'activations.club': ['Al Ahly', 'Anderlecht', 'Arenas', 'Arsenal', 'Bayer Leverkusen', 'Boca Juniors', 'Dinamo Zagreb', 'Dynamo Kyiv', 'Feyenoord', 'Galatasaray', 'Hamburger SV', 'Inter Milan', 'Ipswich Town', 'Monterrey', 'Nottingham Forest', 'Palmeiras', 'Real Madrid', 'Roma', 'Shakhtar Donetsk', 'Sparta Prague', 'Sporting CP', 'Steaua București', 'VfB Stuttgart', 'Zaragoza'], 'activations.co_sponsor': ['ABB Ltd', 'ASML', 'ASR Nederland', 'Alfa Laval', 'AppLovin', 'Bureau Veritas', 'Danaher Corporation', 'Datadog', 'Deutsche Bank', 'Deutsche Post', 'Eurofins Scientific', 'Fluidra', 'Hiscox', 'Johnson & Johnson', 'Kering', 'Microchip Technology', 'Micron Technology', 'Monolithic Power Systems', 'Nike', 'Sherwin-Williams', 'Solvay', 'Union Pacific Corporation', 'Volkswagen Group', 'Walmart'], 'activations.market_country': ['CA', 'DE', 'ES', 'FI', 'GF', 'KI', 'LK', 'LR', 'MX', 'RU', 'SH', 'TZ']}.items()}


def solve(data):
    vals = list(reference(data, _EXCLUDED).values())
    return max(vals) if _os.environ.get('CLRSYNTH_SPLIT') == 'practice' else sum(vals)
