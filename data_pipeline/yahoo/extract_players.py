from pathlib import Path
import sys
import json
from unidecode import unidecode

project_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_dir))

from yfpy.query import YahooFantasySportsQuery

# ----------------------------
# CONFIG
# ----------------------------
league_id = "883"
game_code = "mlb"

query = YahooFantasySportsQuery(
    league_id,
    game_code,
    env_file_location=project_dir,
    save_token_data_to_env_file=True
)

def get_current_week(query, team_id, max_weeks=28):
    last_valid = 1

    for w in range(1, max_weeks + 1):
        try:
            roster = query.get_team_roster_by_week(team_id, w)

            # If we got a roster with players, this week exists.
            if getattr(roster, "players", None) is not None:
                last_valid = w
            else:
                break

        except Exception:
            break

    return last_valid





# ----------------------------
# HELPERS
# ----------------------------
def normalize(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="ignore")
    return v


def safe_get(obj, attr, default=None):
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


# ----------------------------
# BUILD TEAMS
# ----------------------------
teams = query.get_league_teams()

# Use the first team to determine the current week
week = get_current_week(query, teams[0].team_id)

print(f"Using Yahoo week {week}")


all_players = []

print(f"Found {len(teams)} teams. Extracting rosters...")

# ----------------------------
# LOOP TEAMS → ROSTERS → PLAYERS
# ----------------------------
for t in teams:
    team_id = t.team_id
    team_name = normalize(t.name)

    print(f"Processing team: {team_name}")

    roster = query.get_team_roster_by_week(team_id, week)

    players = getattr(roster, "players", [])

    for p in players:
        all_players.append({
            "team_id": team_id,
            "team_name": team_name,

            "player_id": normalize(safe_get(p, "player_id")),
            "player_key": normalize(safe_get(p, "player_key")),

            "name": unidecode(safe_get(p.name, "full")),
            "first_name": unidecode(safe_get(p.name, "first")),
            "last_name": unidecode(safe_get(p.name, "last")),

            "position": normalize(safe_get(p, "primary_position")),
            "eligible_positions": safe_get(p, "eligible_positions"),

            "mlb_team": normalize(safe_get(p, "editorial_team_abbr")),
            "mlb_team_name": normalize(safe_get(p, "editorial_team_full_name")),

            "status": normalize(safe_get(p, "status"))
        })

# ----------------------------
# WRITE OUTPUT
# ----------------------------
output_path = project_dir / "data" / "players.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_players, f, indent=2, ensure_ascii=False)

print(f"\nWrote {len(all_players)} players to {output_path}")