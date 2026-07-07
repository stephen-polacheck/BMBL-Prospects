from pathlib import Path
import sys
import json

project_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_dir))

from yfpy.query import YahooFantasySportsQuery


query = YahooFantasySportsQuery(
    league_id="883",
    game_code="mlb",
    env_file_location=project_dir,
    save_token_data_to_env_file=True
)


players = query.get_all_players()

print("NUMBER OF PLAYERS:")
print(len(players))


player = players[0]

print("\nPLAYER OBJECT:")
print(player)

print("\nPLAYER DICT:")
print(json.dumps(
    player.__dict__,
    indent=4,
    default=str
))