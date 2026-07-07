import json
import streamlit as st
import unicodedata
import re


# =====================================================
# PATHS
# =====================================================
INTERNAL_PATH = "data/players.json"
HKB_PATH = "data/hkb_players.json"
REGISTRY_PATH = "data/player_registry.json"
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
# ID GENERATION
# =====================================================
def next_uid(counter):
    counter["value"] += 1
    return f"{counter['value']:07d}"


# =====================================================
# NORMALIZATION (light use only)
# =====================================================
def norm(x):
    if not x:
        return ""
    x = unicodedata.normalize("NFKD", x)
    x = "".join(c for c in x if not unicodedata.combining(c))
    x = x.lower()
    x = re.sub(r"[^\w\s]", "", x)
    return x.strip()


def key(p):
    return (norm(p.get("name")), norm(p.get("team") or p.get("mlb_team")))


# =====================================================
# INIT STATE
# =====================================================
internal = load(INTERNAL_PATH, [])
hkb = load(HKB_PATH, [])
registry = load(REGISTRY_PATH, {})
counter = load(COUNTER_PATH, {"value": 0})


# =====================================================
# INDEX HKB
# =====================================================
hkb_index = {}
for p in hkb:
    hkb_index.setdefault(key(p), []).append(p)


# =====================================================
# STREAMLIT UI
# =====================================================
st.title("Player Registry Merge Tool")

st.sidebar.write("Registry size:", len(registry))

# internal players not yet matched
used_internal = set()
for r in registry.values():
    used_internal.update(r.get("internal_ids", []))

pending = [p for p in internal if p.get("player_id") not in used_internal]

st.write(f"Pending internal players: {len(pending)}")


if "i" not in st.session_state:
    st.session_state.i = 0


i = st.session_state.i

if i >= len(pending):
    st.success("All players reviewed.")
    st.stop()


player = pending[i]
k = key(player)

candidates = hkb_index.get(k, [])

st.subheader("Internal Player")
st.write(player)

st.subheader("HKB Candidates")

if candidates:
    for idx, c in enumerate(candidates):
        st.write(f"Candidate {idx+1}")
        st.json(c)
else:
    st.warning("No HKB match found")


# =====================================================
# ACTIONS
# =====================================================
col1, col2, col3 = st.columns(3)


def save_registry():
    save(REGISTRY_PATH, registry)
    save(COUNTER_PATH, counter)


with col1:
    if st.button("🔗 Merge (Select First HKB)"):
        if candidates:
            h = candidates[0]

            # reuse or create UID
            uid = None
            for u, r in registry.items():
                if h["id"] in r.get("hkb_ids", []):
                    uid = u
                    break

            if not uid:
                counter["value"] += 1
                uid = f"{counter['value']:07d}"

                registry[uid] = {
                    "universal_id": uid,
                    "canonical_name": player["name"],
                    "canonical_team": player["mlb_team"],
                    "internal_ids": [],
                    "hkb_ids": [],
                    "aliases": [],
                    "locked": True
                }

            if player["player_id"] not in registry[uid]["internal_ids"]:
                registry[uid]["internal_ids"].append(player["player_id"])

            if h["id"] not in registry[uid]["hkb_ids"]:
                registry[uid]["hkb_ids"].append(h["id"])

            save_registry()
            st.success(f"Merged into {uid}")
            st.session_state.i += 1
            st.rerun()


with col2:
    if st.button("⏭ Skip"):
        st.session_state.i += 1
        st.rerun()


with col3:
    if st.button("💾 Save Only"):
        save_registry()
        st.success("Saved registry")