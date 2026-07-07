import json
import os
import unicodedata
import re


REGISTRY_PATH = "data/player_registry.json"


# =====================================================
# LOAD / SAVE
# =====================================================
def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {}

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


# =====================================================
# UID GENERATION
# =====================================================
def normalize(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def make_uid(name, team):
    base = f"{normalize(name)}|{normalize(team)}"
    return "u_" + str(abs(hash(base)))


# =====================================================
# SAFE LIST APPEND
# =====================================================
def append_unique(lst, value):
    if value and value not in lst:
        lst.append(value)


# =====================================================
# MAIN WRITER
# =====================================================
def upsert_player(
    registry,
    canonical_name,
    canonical_team,
    internal_ids=None,
    hkb_ids=None,
    universal_id=None
):
    internal_ids = internal_ids or []
    hkb_ids = hkb_ids or []

    # generate UID if not provided
    uid = universal_id or make_uid(canonical_name, canonical_team)

    # create entry if missing
    if uid not in registry:
        registry[uid] = {
            "universal_id": uid,
            "canonical_name": canonical_name,
            "canonical_team": canonical_team,
            "internal_ids": [],
            "hkb_ids": [],
            "aliases": [],
            "locked": True
        }

    record = registry[uid]

    # update canonical info (ONLY if empty or first time)
    if not record.get("canonical_name"):
        record["canonical_name"] = canonical_name

    if not record.get("canonical_team"):
        record["canonical_team"] = canonical_team

    # append IDs safely
    for iid in internal_ids:
        append_unique(record["internal_ids"], iid)

    for hid in hkb_ids:
        append_unique(record["hkb_ids"], hid)

    return uid


# =====================================================
# INTERACTIVE INPUT
# =====================================================
def prompt_list(prompt_text):
    raw = input(prompt_text).strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",")]


def main():
    print("\n=== PLAYER REGISTRY WRITER ===\n")

    registry = load_registry()

    canonical_name = input("Canonical player name: ").strip()
    canonical_team = input("MLB team (e.g. MIA): ").strip()

    internal_ids = prompt_list("Internal IDs (comma-separated): ")
    hkb_ids = prompt_list("HKB IDs (comma-separated): ")

    use_custom_uid = input("Custom universal_id? (leave blank to auto-generate): ").strip()
    universal_id = use_custom_uid if use_custom_uid else None

    uid = upsert_player(
        registry,
        canonical_name,
        canonical_team,
        internal_ids=internal_ids,
        hkb_ids=hkb_ids,
        universal_id=universal_id
    )

    save_registry(registry)

    print("\n=== SUCCESS ===")
    print(f"Universal ID: {uid}")
    print(f"Saved to: {REGISTRY_PATH}")


if __name__ == "__main__":
    main()