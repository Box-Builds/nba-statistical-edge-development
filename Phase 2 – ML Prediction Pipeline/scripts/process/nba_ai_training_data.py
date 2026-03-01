#!/usr/bin/env python3
"""
Build AI training CSV with rolling and opponent stats for all active players.
"""

import os
import pandas as pd
import numpy as np
import pickle
from paths import RAW_GAMES, RAW_ROSTERS, PROCESSED_TRAINING_ALL

ROLLING_WINDOWS = [3, 5, 10]

# ---------- Load Data ----------
print("📥 Loading roster cache...")
with open(RAW_ROSTERS, "rb") as f:
    roster_cache = pickle.load(f)

active_player_ids = [p["PLAYER_ID"] for team in roster_cache.values() for p in team]
print(f"Loaded {len(active_player_ids)} active players.")

print("📥 Loading master CSV...")
df = pd.read_csv(RAW_GAMES)
print(f"Master file has {len(df)} rows.")

# Filter to active players
df = df[df["Player_ID"].isin(active_player_ids)]
print(f"Filtered to active players: {len(df)} rows remain.")

# Ensure GAME_DATE is datetime
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

# ---------- Determine Player Team, Opponent, and Home/Away ----------
def get_opponent_home(row):
    matchup = row["MATCHUP"]
    if "@" in matchup:
        home = 0
        player_team = matchup.split("@")[0].strip()
        opponent = matchup.split("@")[1].strip()
    else:
        home = 1
        player_team = matchup.split("vs")[0].strip()
        opponent = matchup.split("vs")[1].strip()
    return pd.Series([player_team.lstrip(". ").strip(), opponent.lstrip(". ").strip(), home])

df[["Team_Abv", "Opponent", "Home"]] = df.apply(get_opponent_home, axis=1)

# ---------- Days Rest ----------
df = df.sort_values(["Player_ID", "GAME_DATE"])
df["Days_Rest"] = df.groupby("Player_ID")["GAME_DATE"].diff().dt.days.fillna(0)

# ---------- Points per Minute ----------
df["PTS_per_MIN"] = df["PTS"] / df["MIN"].replace(0, np.nan)
df["PTS_per_MIN"] = df["PTS_per_MIN"].fillna(0)

# ---------- Raw Stats ----------
stat_cols = ["PTS","REB","AST","STL","BLK","TOV","FG_PCT","FG3_PCT","FG3M","FG3A","FT_PCT","MIN","PLUS_MINUS"]
all_stats = stat_cols + ["PTS_per_MIN"]

# ---------- Rolling Averages (Raw + PTS/min) ----------
rolling_cols = {}
for window in ROLLING_WINDOWS:
    for col in all_stats:
        rolling_cols[f"{col}_Roll{window}"] = df.groupby("Player_ID")[col] \
                                               .transform(lambda x: x.shift(1).rolling(window).mean().fillna(0))
df = pd.concat([df, pd.DataFrame(rolling_cols, index=df.index)], axis=1)

# ---------- Averages vs Opponent ----------
vs_opp_cols = {}
for col in all_stats:
    vs_opp_cols[f"{col}_vs_Opp"] = df.groupby(["Player_ID","Opponent"])[col] \
                                      .transform(lambda x: x.shift(1).expanding().mean().fillna(0))
df = pd.concat([df, pd.DataFrame(vs_opp_cols, index=df.index)], axis=1)

# ---------- Advanced Metrics ----------
df["TS%"] = df["PTS"] / (2 * (df["FGA"] + 0.44 * df["FTA"]).replace(0,1))
df["eFG%"] = (df["FGM"] + 0.5 * df["FG3M"]) / df["FGA"].replace(0,1)
df["USG%"] = ((df["FGA"] + 0.44*df["FTA"] + df["TOV"]) * 100) / (
    ((df["MIN"]/df["MIN"].max()) * df.groupby("GAME_DATE")["FGA"].transform("sum") +
     0.44*df.groupby("GAME_DATE")["FTA"].transform("sum") +
     df.groupby("GAME_DATE")["TOV"].transform("sum"))
).replace(0,1)
df["AST%"] = df["AST"] / df["PTS"].replace(0,1)
df["TOV%"] = df["TOV"] / df["MIN"].replace(0,1)
df["PER"] = ((df["PTS"] + df["REB"] + df["AST"] + df["STL"] + df["BLK"] - df["TOV"]) / df["MIN"].replace(0,1)) * 15
adv_stats = ["TS%", "eFG%", "USG%", "AST%", "TOV%", "PER"]

# ---------- Rolling Advanced Stats ----------
rolling_adv_cols = {}
for window in ROLLING_WINDOWS:
    for col in adv_stats:
        rolling_adv_cols[f"{col}_Roll{window}"] = df.groupby("Player_ID")[col] \
                                                    .transform(lambda x: x.shift(1).rolling(window).mean().fillna(0))
df = pd.concat([df, pd.DataFrame(rolling_adv_cols, index=df.index)], axis=1)

# ---------- Season Averages ----------
season_avg_cols = {}
for col in all_stats + adv_stats:
    season_avg_cols[f"{col}_SeasonAvg"] = df.groupby(["Player_ID","SEASON_ID"])[col] \
                                           .transform(lambda x: x.expanding(1).mean().shift(1).fillna(0))
df = pd.concat([df, pd.DataFrame(season_avg_cols, index=df.index)], axis=1)

# ---------- Finalize Training File ----------
training_cols = (
    ["Player_ID","PLAYER_NAME","Team_Abv","SEASON_ID","GAME_DATE","Opponent","Home","Days_Rest"] +
    [f"{col}_Roll{w}" for w in ROLLING_WINDOWS for col in all_stats + adv_stats] +
    [f"{col}_vs_Opp" for col in all_stats] +
    all_stats + adv_stats +
    [f"{col}_SeasonAvg" for col in all_stats + adv_stats]
)

os.makedirs(os.path.dirname(PROCESSED_TRAINING_ALL), exist_ok=True)
df[training_cols].to_csv(PROCESSED_TRAINING_ALL, index=False)
print(f"✅ Training CSV saved: {PROCESSED_TRAINING_ALL}")
