#!/usr/bin/env python3
"""
Fetch NBA team rosters and save to a pickle file for later use.
"""

from pathlib import Path
import sys

# Ensure Phase 2 root is importable when running this script directly
ROOT = Path(__file__).resolve().parents[2]  # scripts/fetch -> Phase 2 root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
import pickle
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
from paths import RAW_ROSTERS

PAUSE_SECONDS = 1.5  # wait between API calls to be polite

def fetch_team_roster(team_id):
    """Fetch a single team roster and return a list of player dicts."""
    roster_data = []
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        players = roster.get_data_frames()[0]  # first dataframe has player info
        for _, row in players.iterrows():
            roster_data.append({
                "PLAYER_ID": row.get("PLAYER_ID"),
                "PLAYER_NAME": row.get("PLAYER"),
                "POSITION": row.get("POSITION"),
                "HEIGHT": row.get("HEIGHT"),
                "WEIGHT": row.get("WEIGHT"),
                "BIRTH_DATE": row.get("BIRTHDATE"),
                "AGE": row.get("AGE"),
                "EXP": row.get("EXP"),
                "SCHOOL": row.get("SCHOOL"),
            })
    except Exception as e:
        print(f"Error fetching roster for team {team_id}: {e}")
    return roster_data

def main():
    all_teams = teams.get_teams()
    team_roster_cache = {}

    print("Fetching rosters for all teams...")
    for team in all_teams:
        team_id = team["id"]
        team_name = team["full_name"]
        print(f"Fetching roster for {team_name} ({team_id})...")
        roster = fetch_team_roster(team_id)
        team_roster_cache[team_id] = roster
        print(f"  - {len(roster)} players")
        time.sleep(PAUSE_SECONDS)

    # Ensure directory exists
    Path(RAW_ROSTERS).parent.mkdir(parents=True, exist_ok=True)

    # Save the cache to a pickle file
    with Path(RAW_ROSTERS).open("wb") as f:
        pickle.dump(team_roster_cache, f)

    print(f"\nAll rosters saved to {RAW_ROSTERS}")
    print(f"Total teams in cache: {len(team_roster_cache)}")

if __name__ == "__main__":
    main()