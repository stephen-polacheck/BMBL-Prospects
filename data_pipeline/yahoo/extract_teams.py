from pathlib import Path
import sys
import json

project_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_dir))

from yfpy.query import YahooFantasySportsQuery

def normalize_dict(d):
    return {k: (v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else v)
            for k, v in d.items()}

league_id = "883"
game_code = "mlb"

query = YahooFantasySportsQuery(
    league_id,
    game_code,
    env_file_location=project_dir,
    save_token_data_to_env_file=True
)

teams = query.get_league_teams()

cleaned_teams = []

for t in teams:

    manager_obj = t.managers[0] if isinstance(t.managers, list) else t.managers

    logo = None
    if getattr(t, "team_logos", None):
        logos = t.team_logos
        if isinstance(logos, list) and len(logos) > 0:
            logo = getattr(logos[0], "url", None)
        elif hasattr(logos, "team_logo"):
            logo = getattr(logos.team_logo, "url", None)

    cleaned_teams.append(normalize_dict({
        "team_id": t.team_id,
        "team_key": t.team_key,
        "name": t.name,
        "owner": manager_obj.nickname,
        "logo": logo
    }))

output_path = project_dir / "data" / "teams.json"

with open(output_path, "w") as f:

    for i, t in enumerate(cleaned_teams):
        for k, v in t.items():
            if isinstance(v, bytes):
                print("FOUND BYTES:", i, k, v)

    json.dump(cleaned_teams, f, indent=2)

print(f"Wrote {len(cleaned_teams)} teams to {output_path}")