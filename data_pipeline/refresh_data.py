import subprocess
import datetime
from pathlib import Path
import sys


# Always use the repository root
ROOT = Path(__file__).resolve().parent.parent


def run_script(relative_path):

    script_path = ROOT / relative_path

    print(f"Running {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"{script_path} failed")

    print(result.stdout)



print("================================")
print("BMBL DATA REFRESH")
print(datetime.datetime.now())
print("================================")


run_script(
    "data_pipeline/yahoo/extract_players.py"
)

run_script(
    "data_pipeline/rankings_sites/HarryKnowsBall/extract_players.py"
)

run_script(
    "data_pipeline/player_merge.py"
)

run_script(
    "data_pipeline/generate_player_list.py"
)


print("Refresh complete!")