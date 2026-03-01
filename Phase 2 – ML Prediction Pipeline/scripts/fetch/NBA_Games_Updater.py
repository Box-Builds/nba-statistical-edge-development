#!/usr/bin/env python3
"""
NBA Player Stats Updater (Active Players Only, Reliable ID Matching)
- Uses paths from config/paths.py
- Fetches game logs for active players (DAYS_BACK)
- Adds new games only (no duplicates)
- Fixes SEASON_ID and SEASON formatting
- Removes duplicate rows by SEASON_ID, Game_ID, Player_ID
- Retries failed requests
"""

from pathlib import Path
import sys

# Ensure Phase 2 root is importable when running this script directly
ROOT = Path(__file__).resolve().parents[2]  # scripts/fetch -> Phase 2 root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import pandas as pd
from datetime import datetime, timedelta
import time
import pickle
from nba_api.stats.endpoints import PlayerGameLog
from paths import RAW_GAMES, RAW_GAMES_BACKUP, RAW_ROSTERS, FAILED_PLAYERS

# ---------- CONFIG ----------
DAYS_BACK = 15
BATCH_SIZE = 10
BATCH_WAIT = 5  # seconds
SEASON = "2025-26"          # For display & API
SEASON_ID_PREFIX = 22       # For numeric SEASON_ID (e.g., 22025)
MAX_RETRIES = 5

def log_success(player_name, idx, total):
    print(f"[{idx}/{total}] [{player_name}] ✅ Success")

def log_skipped(player_name, idx, total):
    print(f"[{idx}/{total}] [{player_name}]⏭️ No new games")

def log_failure(player_name, idx, total, error):
    print(f"[{idx}/{total}] [{player_name}] ❌ Failed, retrying later: {error}")

# ---------- Load Data ----------
print("📥 Loading roster cache...")
with open(RAW_ROSTERS, "rb") as f:
    roster_cache = pickle.load(f)

# Flatten roster into {player_id: {...}}
active_players = {}
for team_id, players in roster_cache.items():
    for p in players:
        active_players[p["PLAYER_ID"]] = {
            "PLAYER_NAME": p["PLAYER_NAME"],
            "POSITION": p.get("POSITION", "UNK"),
            "TEAM_ID": team_id
        }

print(f"Loaded {len(active_players)} active players from roster cache.")

print("📥 Loading master CSV...")
df = pd.read_csv(RAW_GAMES, low_memory=False) if os.path.exists(RAW_GAMES) else pd.DataFrame()
print(f"Loaded {len(df)} rows from master CSV.")

# Backup
Path(RAW_GAMES_BACKUP).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(RAW_GAMES_BACKUP, index=False, encoding="utf-8")
print(f"Backup saved to {RAW_GAMES_BACKUP}")

# ---------- Fix existing SEASON_ID / SEASON ----------
def fix_season_columns(row):
    try:
        game_date = pd.to_datetime(row.get("GAME_DATE", None), errors="coerce")
        if game_date is not None and not pd.isna(game_date):
            season_year = game_date.year if game_date.month >= 10 else game_date.year - 1
            row["SEASON_ID"] = int(f"{SEASON_ID_PREFIX}{season_year}")
            row["SEASON"] = f"{season_year}-{season_year+1}"
    except Exception:
        pass
    return row

if not df.empty:
    df = df.apply(fix_season_columns, axis=1)

# ---------- Load failed players ----------
failed_players = {}
if Path(FAILED_PLAYERS).exists():
    with open(FAILED_PLAYERS, "rb") as f:
        failed_players = pickle.load(f)

today = datetime.today()
new_rows = []

player_ids = list(active_players.keys())
total_players = len(player_ids)
idx_global = 0
retry_players = []

# ---------- Main Loop ----------
while idx_global < total_players or retry_players:
    batch = []

    while len(batch) < BATCH_SIZE and idx_global < total_players:
        batch.append(player_ids[idx_global])
        idx_global += 1

    while len(batch) < BATCH_SIZE and retry_players:
        batch.append(retry_players.pop(0))

    print(f"\nProcessing batch of {len(batch)} players...")

    for player_id in batch:
        player_info = active_players.get(player_id)
        if not player_info:
            continue

        player_name = player_info["PLAYER_NAME"]
        idx_display = idx_global

        if df.empty or "Player_ID" not in df.columns or "Game_ID" not in df.columns:
            player_rows = pd.DataFrame()
            existing_game_ids = set()
        else:
            player_rows = df[df["Player_ID"] == player_id]
            existing_game_ids = set(player_rows["Game_ID"].tolist())

        try:
            gl_df = PlayerGameLog(player_id=player_id, season=SEASON).get_data_frames()[0]
        except Exception as e:
            log_failure(player_name, idx_display, total_players, e)
            failed_players[player_id] = failed_players.get(player_id, 0) + 1
            if failed_players[player_id] < MAX_RETRIES:
                retry_players.append(player_id)
            continue

        gl_df.columns = [c.upper() for c in gl_df.columns]
        new_data_found = False

        for _, game in gl_df.iterrows():
            game_id = game["GAME_ID"]
            game_date = datetime.strptime(game["GAME_DATE"], "%b %d, %Y")
            if game_id in existing_game_ids or game_date < today - timedelta(days=DAYS_BACK):
                continue

            season_year = game_date.year if game_date.month >= 10 else game_date.year - 1
            season_id = int(f"{SEASON_ID_PREFIX}{season_year}")
            season_str = f"{season_year}-{season_year+1}"

            new_row = {
                "SEASON_ID": season_id,
                "Player_ID": player_id,
                "Game_ID": game_id,
                "GAME_DATE": game_date.strftime("%Y-%m-%d"),
                "MATCHUP": game["MATCHUP"],
                "WL": game["WL"],
                "MIN": game["MIN"],
                "FGM": game["FGM"],
                "FGA": game["FGA"],
                "FG_PCT": game["FG_PCT"],
                "FG3M": game["FG3M"],
                "FG3A": game["FG3A"],
                "FG3_PCT": game["FG3_PCT"],
                "FTM": game["FTM"],
                "FTA": game["FTA"],
                "FT_PCT": game["FT_PCT"],
                "OREB": game["OREB"],
                "DREB": game["DREB"],
                "REB": game["REB"],
                "AST": game["AST"],
                "STL": game["STL"],
                "BLK": game["BLK"],
                "TOV": game["TOV"],
                "PF": game.get("PF", 0),
                "PTS": game["PTS"],
                "PLUS_MINUS": game.get("PLUS_MINUS", 0),
                "VIDEO_AVAILABLE": game.get("VIDEO_AVAILABLE", 0),
                "TEAM_ID": player_info["TEAM_ID"],
                "PLAYER_NAME": player_name,
                "SEASON": season_str,
                "POSITION": player_info["POSITION"]
            }
            new_rows.append(new_row)
            new_data_found = True

        if new_data_found:
            log_success(player_name, idx_display, total_players)
            failed_players.pop(player_id, None)
        else:
            log_skipped(player_name, idx_display, total_players)

    print(f"Batch complete. Waiting {BATCH_WAIT} sec before next batch...")
    time.sleep(BATCH_WAIT)

# ---------- Save Results ----------
Path(FAILED_PLAYERS).parent.mkdir(parents=True, exist_ok=True)
with open(FAILED_PLAYERS, "wb") as f:
    pickle.dump(failed_players, f)
if failed_players:
    print(f"Players still failing saved to {FAILED_PLAYERS}")

if new_rows:
    print(f"\nAdding {len(new_rows)} new rows to master CSV...")
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

if not df.empty:
    df.drop_duplicates(subset=["SEASON_ID", "Game_ID", "Player_ID"], inplace=True)

Path(RAW_GAMES).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(RAW_GAMES, index=False, encoding="utf-8")
print(f"Master CSV updated and saved: {RAW_GAMES}")

print("\n✅ Update complete!")

# ---------- Final Cleanup Pass ----------
print("\n🧹 Running final duplicate cleanup...")
df = pd.read_csv(RAW_GAMES, low_memory=False)
df["SEASON_ID"] = df["SEASON_ID"].astype(str)
df["Game_ID"] = df["Game_ID"].astype(str)
df["Player_ID"] = df["Player_ID"].astype(str)

before = len(df)
df.drop_duplicates(subset=["SEASON_ID", "Game_ID", "Player_ID"], inplace=True)
after = len(df)

if after < before:
    print(f"🧽 Removed {before - after} duplicate rows.")
else:
    print("✅ No duplicates found.")

df.to_csv(RAW_GAMES, index=False, encoding="utf-8")
print("✨ Master file cleaned and finalized.")