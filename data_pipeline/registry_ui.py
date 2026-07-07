# streamlit run data_pipeline/registry_ui.py

import csv
import json
from pathlib import Path
from datetime import datetime

import streamlit as st


# ============================================================
# Paths
# ============================================================

DATA_DIR = Path("data")

REGISTRY_FILE = DATA_DIR / "player_registry.json"
DEBUG_FILE = DATA_DIR / "match_debug.csv"


# ============================================================
# Helpers
# ============================================================

def load_json(path, default):
    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


def load_csv(path):
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_universal_id(registry):

    if not registry:
        return "0000001"

    existing = [
        int(uid)
        for uid in registry.keys()
        if uid.isdigit()
    ]

    return f"{max(existing) + 1:07d}"


def save_registry_record(
    registry,
    internal_id,
    internal_name,
    internal_team,
    hkb_id
):

    # --------------------------------------------------------
    # Check if HKB already exists
    # --------------------------------------------------------

    for uid, record in registry.items():

        if str(hkb_id) in [
            str(x)
            for x in record.get("hkb_ids", [])
        ]:

            # attach internal id if missing
            if str(internal_id) not in [
                str(x)
                for x in record.get("internal_ids", [])
            ]:
                record["internal_ids"].append(
                    int(internal_id)
                )

            return uid


    # --------------------------------------------------------
    # Create new registry entry
    # --------------------------------------------------------

    uid = next_universal_id(registry)

    registry[uid] = {

        "universal_id": uid,

        "canonical_name": internal_name,

        "canonical_team": internal_team,

        "internal_ids": [
            int(internal_id)
        ],

        "hkb_ids": [
            str(hkb_id)
        ],

        "aliases": [],

        "locked": True,

        "created": datetime.utcnow().isoformat(),

        "updated": datetime.utcnow().isoformat()
    }

    return uid


# ============================================================
# Load Data
# ============================================================

registry = load_json(
    REGISTRY_FILE,
    {}
)

debug_rows = load_csv(
    DEBUG_FILE
)


review_rows = [
    r
    for r in debug_rows
    if r["status"] in (
        "SUGGESTED_MATCH",
        "NO_MATCH"
    )
]


# ============================================================
# UI
# ============================================================

st.set_page_config(
    page_title="Player Registry",
    layout="wide"
)

st.title("⚾ Player Registry Manager")

st.sidebar.write(
    f"Registry size: {len(registry)}"
)

st.sidebar.write(
    f"Players needing review: {len(review_rows)}"
)


if not review_rows:

    st.success(
        "No players currently require review."
    )

    st.stop()


# ------------------------------------------------------------
# Navigation
# ------------------------------------------------------------

if "index" not in st.session_state:
    st.session_state.index = 0


index = st.session_state.index


if index >= len(review_rows):
    index = 0
    st.session_state.index = 0


player = review_rows[index]


st.progress(
    (index + 1) / len(review_rows)
)


st.write(
    f"Reviewing player {index + 1} of {len(review_rows)}"
)


# ============================================================
# Player display
# ============================================================

left, right = st.columns(2)


with left:

    st.subheader(
        "Internal Player"
    )

    st.write(
        "Name:",
        player["internal_name"]
    )

    st.write(
        "Team:",
        player["internal_team"]
    )

    st.write(
        "Internal ID:",
        player["internal_id"]
    )


with right:

    st.subheader(
        "Suggested HKB Match"
    )

    if player["hkb_id"]:

        st.write(
            "HKB Name:",
            player["hkb_name"]
        )

        st.write(
            "HKB Team:",
            player["hkb_team"]
        )

        st.write(
            "HKB ID:",
            player["hkb_id"]
        )

    else:

        st.warning(
            "No suggested HKB player"
        )


# ============================================================
# Actions
# ============================================================

st.divider()


col1, col2 = st.columns(2)


with col1:

    if player["hkb_id"]:

        if st.button(
            "✅ Approve Suggested Match"
        ):

            uid = save_registry_record(

                registry,

                player["internal_id"],

                player["internal_name"],

                player["internal_team"],

                player["hkb_id"]

            )

            save_json(
                REGISTRY_FILE,
                registry
            )

            st.success(
                f"Created registry match {uid}"
            )

            st.session_state.index += 1

            st.rerun()


with col2:

    manual_hkb = st.text_input(
        "Force HKB ID manually"
    )


    if st.button(
        "🔗 Force Merge"
    ):

        if not manual_hkb:

            st.error(
                "Enter an HKB ID first"
            )

        else:

            uid = save_registry_record(

                registry,

                player["internal_id"],

                player["internal_name"],

                player["internal_team"],

                manual_hkb

            )

            save_json(
                REGISTRY_FILE,
                registry
            )

            st.success(
                f"Created registry match {uid}"
            )

            st.session_state.index += 1

            st.rerun()



# ============================================================
# Skip
# ============================================================

st.divider()

if st.button(
    "⏭ Skip for now"
):

    st.session_state.index += 1

    st.rerun()