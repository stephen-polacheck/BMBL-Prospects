import json
import unicodedata
import re
import csv
from collections import defaultdict


# =====================================================
# PATHS
# =====================================================
INTERNAL_PATH = "data/players.json"
HKB_PATH = "data/hkb_players.json"
REGISTRY_PATH = "data/player_registry.json"

CSV_PATH = "data/match_debug.csv"

OUTPUT_ENRICHED = "data/players_enriched.json"
OUTPUT_UNMATCHED = "data/unmatched.json"
COUNTER_PATH = "data/universal_id_counter.json"


# =====================================================
# LOAD / SAVE
# =====================================================
def load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================================================
# NORMALIZATION
# =====================================================
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_name(name):
    if not name:
        return ""

    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)

    parts = name.split()
    parts = [p for p in parts if p not in SUFFIXES]

    return " ".join(parts).strip()


def normalize_team(team):
    return (team or "").upper().strip()


def make_key(name, team):
    return (normalize_name(name), normalize_team(team))


# =====================================================
# REGISTRY INDEX
# =====================================================
def build_registry_maps(registry):
    internal_map = {}
    hkb_map = {}

    for uid, r in registry.items():
        for iid in r.get("internal_ids", []):
            internal_map[iid] = uid
        for hid in r.get("hkb_ids", []):
            hkb_map[hid] = uid

    return internal_map, hkb_map


# =====================================================
# HKB INDEX
# =====================================================
def index_hkb(hkb):
    index = defaultdict(list)
    for p in hkb:
        key = make_key(p.get("name"), p.get("team"))
        index[key].append(p)
    return index


# =====================================================
# SEQUENTIAL ID GENERATOR
# =====================================================
def next_uid(counter):
    counter["value"] += 1
    return f"{counter['value']:07d}"


# =====================================================
# REGISTRY UPDATE (ONLY TRUE MATCHES)
# =====================================================
def update_registry(internal, hkb, registry, counter):
    hkb_index = index_hkb(hkb)
    internal_map, hkb_map = build_registry_maps(registry)

    unmatched = {"internal": [], "hkb": []}
    debug_rows = []

    for p in internal:
        iid = p.get("player_id")
        key = make_key(p.get("name"), p.get("mlb_team"))

        # -------------------------------------------------
        # 1. already matched → keep ONLY if in registry
        # -------------------------------------------------
        if iid in internal_map:
            uid = internal_map[iid]

            debug_rows.append({
                "status": "EXISTING",
                "universal_id": uid,
                "internal_id": iid,
                "hkb_id": "",
                "internal_name": p.get("name"),
                "internal_team": p.get("mlb_team"),
                "hkb_name": "",
                "hkb_team": "",
                "match_key": str(key),
                "note": "already in registry"
            })

            continue

        # -------------------------------------------------
        # 2. ONLY ACCEPT TRUE MATCHES (internal + HKB)
        # -------------------------------------------------
        candidates = hkb_index.get(key, [])

        if candidates:
            h = candidates[0]

            # reuse existing registry entry if HKB already known
            if h["id"] in hkb_map:
                uid = hkb_map[h["id"]]
            else:
                uid = next_uid(counter)

                registry[uid] = {
                    "universal_id": uid,
                    "canonical_name": p["name"],
                    "canonical_team": p["mlb_team"],
                    "internal_ids": [],
                    "hkb_ids": [],
                    "aliases": [],
                    "locked": True
                }

            # append ONLY
            if iid not in registry[uid]["internal_ids"]:
                registry[uid]["internal_ids"].append(iid)

            if h["id"] not in registry[uid]["hkb_ids"]:
                registry[uid]["hkb_ids"].append(h["id"])

            debug_rows.append({
                "status": "MATCHED",
                "universal_id": uid,
                "internal_id": iid,
                "hkb_id": h["id"],
                "internal_name": p.get("name"),
                "internal_team": p.get("mlb_team"),
                "hkb_name": h.get("name"),
                "hkb_team": h.get("team"),
                "match_key": str(key),
                "note": "confirmed match"
            })

        # -------------------------------------------------
        # 3. NO MATCH → DO NOTHING IN REGISTRY
        # -------------------------------------------------
        else:
            unmatched["internal"].append(p)

            debug_rows.append({
                "status": "UNMATCHED",
                "universal_id": "",
                "internal_id": iid,
                "hkb_id": "",
                "internal_name": p.get("name"),
                "internal_team": p.get("mlb_team"),
                "hkb_name": "",
                "hkb_team": "",
                "match_key": str(key),
                "note": "no hkb match (manual review required)"
            })

    return registry, unmatched, debug_rows, counter


# =====================================================
# ENRICHMENT (registry truth only)
# =====================================================
def enrich_internal(internal, registry):
    internal_map, _ = build_registry_maps(registry)

    enriched = []

    for p in internal:
        uid = internal_map.get(p.get("player_id"))

        enriched.append({
            **p,
            "universal_id": uid
        })

    return enriched


# =====================================================
# CSV WRITER
# =====================================================
def write_csv(rows):
    keys = [
        "status",
        "universal_id",
        "internal_id",
        "hkb_id",
        "internal_name",
        "internal_team",
        "hkb_name",
        "hkb_team",
        "match_key",
        "note"
    ]

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


# =====================================================
# MAIN
# =====================================================
def main():
    internal = load(INTERNAL_PATH, [])
    hkb = load(HKB_PATH, [])
    registry = load(REGISTRY_PATH, {})

    counter = load(COUNTER_PATH, {"value": 0})

    registry, unmatched, debug_rows, counter = update_registry(
        internal, hkb, registry, counter
    )

    enriched = enrich_internal(internal, registry)

    save(REGISTRY_PATH, registry)
    save(OUTPUT_ENRICHED, enriched)
    save(OUTPUT_UNMATCHED, unmatched)
    save(CSV_PATH, debug_rows)
    save(COUNTER_PATH, counter)

    print("\n=== SUMMARY ===")
    print(f"Registry size: {len(registry)}")
    print(f"Internal unmatched: {len(unmatched['internal'])}")
    print(f"CSV written: {CSV_PATH}")


if __name__ == "__main__":
    main()