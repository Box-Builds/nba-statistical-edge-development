#!/usr/bin/env python3

from pathlib import Path
import sys

# Ensure Phase 2 root is importable when running this script directly
ROOT = Path(__file__).resolve().parents[2]  # scripts/fetch -> Phase 2 root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from nba_api.stats.endpoints import scheduleleaguev2
from paths import RAW_SCHEDULE  # <-- use root paths.py

SEASON = "2025-26"

# Fetch schedule from API
api_data = scheduleleaguev2.ScheduleLeagueV2(season=SEASON).get_data_frames()[0]

# Only keep regular-season games
api_data = api_data[api_data["gameId"].str.startswith("002")]

# Build a clean DataFrame
games_df = pd.DataFrame({
    "GAME_ID": api_data["gameId"].astype(int),
    "GAME_DATE": pd.to_datetime(api_data["gameDateEst"]).dt.date,
    "HOME_TEAM_ID": api_data["homeTeam_teamId"].astype(int),
    "AWAY_TEAM_ID": api_data["awayTeam_teamId"].astype(int),
    "HOME_TEAM_ABV": api_data["homeTeam_teamTricode"],
    "AWAY_TEAM_ABV": api_data["awayTeam_teamTricode"],
    "SEASON": SEASON
})

# Remove any duplicates where HOME_TEAM_ID == AWAY_TEAM_ID
games_df = games_df[games_df["HOME_TEAM_ID"] != games_df["AWAY_TEAM_ID"]]

# Print a sample
print(games_df.head(10))

# Ensure directory exists then save
Path(RAW_SCHEDULE).parent.mkdir(parents=True, exist_ok=True)
games_df.to_csv(RAW_SCHEDULE, index=False)
print(f"✅ Clean schedule saved to {RAW_SCHEDULE}")