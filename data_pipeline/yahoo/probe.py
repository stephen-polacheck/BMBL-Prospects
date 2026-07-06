from pathlib import Path
import sys

project_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_dir))

from yfpy.query import YahooFantasySportsQuery

league_id = "883"
game_code = "mlb"
week = 1  # we will adjust later

query = YahooFantasySportsQuery(
    league_id,
    game_code,
    env_file_location=project_dir,
    save_token_data_to_env_file=True
)

teams = query.get_league_teams()

first_team = teams[0]

print("TEAM:", first_team.name)
print("TEAM ID:", first_team.team_id)

roster = query.get_team_roster_by_week(first_team.team_id, week)

print("ROSTER TYPE:", type(roster))

players = getattr(roster, "players", None)

roster = query.get_team_roster_by_week(first_team.team_id, week)

players = roster.players

print("ROSTER SIZE:", len(players))
print("FIRST PLAYER NAME:", players[0].name.full)
print("FIRST PLAYER ID:", players[0].player_id)
print("FIRST PLAYER KEY:", players[0].player_key)
print("POSITION:", players[0].primary_position)
print("MLB TEAM:", players[0].editorial_team_abbr)