import os
import json
import config
from footballtransfers.persistence import remember_team_squads

if __name__ == "__main__":
    teams_file = config.TEAMS_TO_CHECK_JSON
    if not teams_file or not os.path.exists(teams_file):
        raise FileNotFoundError(f"Teams file not found: {teams_file}")

    with open(teams_file, "r", encoding="utf-8") as f:
        teams = json.load(f)

    remember_team_squads(teams)
