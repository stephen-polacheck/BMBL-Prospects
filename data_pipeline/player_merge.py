import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


# ============================================================
# Paths
# ============================================================

DATA_DIR = Path("data")

PLAYERS_FILE = DATA_DIR / "players.json"
HKB_FILE = DATA_DIR / "hkb_players.json"
REGISTRY_FILE = DATA_DIR / "player_registry.json"

OUTPUT_ENRICHED = DATA_DIR / "players_enriched.json"
OUTPUT_MATCH_DEBUG = DATA_DIR / "match_debug.csv"
OUTPUT_UNMATCHED_INTERNAL = DATA_DIR / "unmatched_internal.json"
OUTPUT_UNMATCHED_HKB = DATA_DIR / "unmatched_hkb.json"


# ============================================================
# File Helpers
# ============================================================

def load_json(path, default):
    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_csv(path, rows):
    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# Name Normalization
# ============================================================

SUFFIXES = {
    "jr",
    "sr",
    "ii",
    "iii",
    "iv",
    "v"
}


def normalize_name(name: str) -> str:

    if not name:
        return ""

    # remove accents
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    name = name.lower()

    # remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    pieces = [
        p
        for p in name.split()
        if p not in SUFFIXES
    ]

    return " ".join(pieces)


def normalize_team(team):

    if team is None:
        return ""

    return team.upper().strip()


def player_key(name, team):
    return (
        normalize_name(name),
        normalize_team(team)
    )


    # ============================================================
# Registry Lookup Builders
# ============================================================

def build_registry_indexes(registry):
    """
    Converts registry JSON into fast lookup dictionaries.

    Returns:
        internal_to_uid:
            internal player id -> universal_id

        hkb_to_uid:
            HKB player id -> universal_id

        uid_to_record:
            universal_id -> registry record
    """

    internal_to_uid = {}
    hkb_to_uid = {}
    uid_to_record = {}

    for uid, record in registry.items():

        uid_to_record[uid] = record

        for internal_id in record.get("internal_ids", []):
            internal_to_uid[str(internal_id)] = uid

        for hkb_id in record.get("hkb_ids", []):
            hkb_to_uid[str(hkb_id)] = uid

    return (
        internal_to_uid,
        hkb_to_uid,
        uid_to_record
    )


# ============================================================
# HKB Index Builder
# ============================================================

def build_hkb_indexes(hkb_players):
    """
    Creates fast lookup dictionaries for HKB.

    Returns:

        hkb_by_id:
            HKB id -> player record

        hkb_by_key:
            (normalized_name, team) -> list of players

    """

    hkb_by_id = {}
    hkb_by_key = defaultdict(list)

    for player in hkb_players:

        hkb_id = player.get("id")

        if hkb_id:
            hkb_by_id[str(hkb_id)] = player


        key = player_key(
            player.get("name"),
            player.get("team")
        )

        hkb_by_key[key].append(player)


    return (
        hkb_by_id,
        hkb_by_key
    )


# ============================================================
# Registry Display Helpers
# ============================================================

def get_registry_player(uid, registry):
    """
    Returns registry record safely.
    """

    return registry.get(uid, {})


def registry_has_internal_player(
    internal_id,
    internal_to_uid
):
    return str(internal_id) in internal_to_uid


def registry_has_hkb_player(
    hkb_id,
    hkb_to_uid
):
    return str(hkb_id) in hkb_to_uid

    # ============================================================
# Player Analysis Engine
# ============================================================

def analyze_players(
    internal_players,
    hkb_by_key,
    hkb_by_id,
    registry,
    internal_to_uid,
    hkb_to_uid
):
    """
    Analyze internal players against the registry and HKB data.

    Does NOT modify registry.

    Returns:
        debug_rows
        unmatched_internal
        unmatched_hkb_ids
    """

    debug_rows = []
    unmatched_internal = []

    matched_hkb_ids = set()


    for player in internal_players:

        internal_id = str(player.get("player_id"))

        name = player.get("name")
        team = player.get("mlb_team")

        key = player_key(
            name,
            team
        )


        # ----------------------------------------------------
        # CASE 1:
        # Already approved in registry
        # ----------------------------------------------------

        if internal_id in internal_to_uid:

            uid = internal_to_uid[internal_id]

            registry_record = registry.get(uid, {})

            hkb_ids = registry_record.get(
                "hkb_ids",
                []
            )

            hkb_id = (
                hkb_ids[0]
                if hkb_ids
                else ""
            )


            hkb_player = (
                hkb_by_id.get(str(hkb_id))
                if hkb_id
                else None
            )


            if hkb_id:
                matched_hkb_ids.add(
                    str(hkb_id)
                )


            debug_rows.append({

                "status": "MATCHED",

                "universal_id": uid,

                "internal_id": internal_id,

                "internal_name": name,

                "internal_team": team,

                "hkb_id": hkb_id,

                "hkb_name":
                    hkb_player.get("name")
                    if hkb_player
                    else "",

                "hkb_team":
                    hkb_player.get("team")
                    if hkb_player
                    else "",

                "notes":
                    "Existing registry mapping"
            })


            continue



        # ----------------------------------------------------
        # CASE 2:
        # Suggest possible HKB match
        # ----------------------------------------------------

        candidates = hkb_by_key.get(
            key,
            []
        )


        if candidates:

            # Exact name/team match.
            # Do NOT select automatically.
            candidate = candidates[0]


            hkb_id = str(
                candidate.get("id")
            )


            matched_hkb_ids.add(
                hkb_id
            )


            debug_rows.append({

                "status": "SUGGESTED_MATCH",

                "universal_id": "",

                "internal_id": internal_id,

                "internal_name": name,

                "internal_team": team,

                "hkb_id": hkb_id,

                "hkb_name":
                    candidate.get("name"),

                "hkb_team":
                    candidate.get("team"),

                "notes":
                    "Name/team match. Awaiting registry approval"
            })


            unmatched_internal.append(player)



        # ----------------------------------------------------
        # CASE 3:
        # No HKB match
        # ----------------------------------------------------

        else:

            debug_rows.append({

                "status": "NO_MATCH",

                "universal_id": "",

                "internal_id": internal_id,

                "internal_name": name,

                "internal_team": team,

                "hkb_id": "",

                "hkb_name": "",

                "hkb_team": "",

                "notes":
                    "No HKB player found"
            })


            unmatched_internal.append(player)



    # --------------------------------------------------------
    # Find HKB players never referenced anywhere
    # --------------------------------------------------------

    unmatched_hkb = []

    for hkb_id, player in hkb_by_id.items():

        if hkb_id not in matched_hkb_ids:

            unmatched_hkb.append(player)


    return (
        debug_rows,
        unmatched_internal,
        unmatched_hkb
    )

# ============================================================
# Enrichment
# ============================================================

def enrich_players(
    internal_players,
    registry,
    internal_to_uid,
    hkb_by_id
):
    """
    Adds universal_id and HKB data to internal players.

    Does not modify:
        - players.json
        - hkb_players.json
        - player_registry.json

    """

    enriched = []


    for player in internal_players:

        internal_id = str(
            player.get("player_id")
        )

        uid = internal_to_uid.get(
            internal_id
        )


        enriched_player = {
            **player,
            "universal_id": uid,
            "hkb": None
        }


        # ----------------------------------------------------
        # Add HKB information if registry contains it
        # ----------------------------------------------------

        if uid:

            registry_record = registry.get(
                uid,
                {}
            )

            hkb_ids = registry_record.get(
                "hkb_ids",
                []
            )


            if hkb_ids:

                hkb_player = hkb_by_id.get(
                    str(hkb_ids[0])
                )

                if hkb_player:

                    enriched_player["hkb"] = hkb_player


        enriched.append(
            enriched_player
        )


    return enriched

# ============================================================
# Main Pipeline
# ============================================================

def main():

    print("\nStarting player merge pipeline...\n")


    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    internal_players = load_json(
        PLAYERS_FILE,
        []
    )

    hkb_players = load_json(
        HKB_FILE,
        []
    )

    registry = load_json(
        REGISTRY_FILE,
        {}
    )


    print(
        f"Internal players loaded: {len(internal_players)}"
    )

    print(
        f"HKB players loaded: {len(hkb_players)}"
    )

    print(
        f"Registry records loaded: {len(registry)}"
    )


    # --------------------------------------------------------
    # Build indexes
    # --------------------------------------------------------

    (
        internal_to_uid,
        hkb_to_uid,
        uid_to_record
    ) = build_registry_indexes(
        registry
    )


    (
        hkb_by_id,
        hkb_by_key
    ) = build_hkb_indexes(
        hkb_players
    )


    # --------------------------------------------------------
    # Analyze matches
    # --------------------------------------------------------

    (
        debug_rows,
        unmatched_internal,
        unmatched_hkb
    ) = analyze_players(
        internal_players,
        hkb_by_key,
        hkb_by_id,
        registry,
        internal_to_uid,
        hkb_to_uid
    )


    # --------------------------------------------------------
    # Enrich
    # --------------------------------------------------------

    enriched = enrich_players(
        internal_players,
        registry,
        internal_to_uid,
        hkb_by_id
    )


    # --------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------

    save_json(
        OUTPUT_ENRICHED,
        enriched
    )

    save_json(
        OUTPUT_UNMATCHED_INTERNAL,
        unmatched_internal
    )

    save_json(
        OUTPUT_UNMATCHED_HKB,
        unmatched_hkb
    )

    write_csv(
        OUTPUT_MATCH_DEBUG,
        debug_rows
    )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    status_counts = defaultdict(int)

    for row in debug_rows:
        status_counts[row["status"]] += 1


    print("\n============================")
    print("Merge Complete")
    print("============================")

    for status, count in status_counts.items():
        print(
            f"{status}: {count}"
        )

    print("\nOutputs created:")
    print(
        OUTPUT_ENRICHED
    )
    print(
        OUTPUT_MATCH_DEBUG
    )
    print(
        OUTPUT_UNMATCHED_INTERNAL
    )
    print(
        OUTPUT_UNMATCHED_HKB
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()