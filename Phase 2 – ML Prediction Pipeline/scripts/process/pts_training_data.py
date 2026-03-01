#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from paths import RAW_GAMES, PROCESSED_OOF, PROCESSED_TRAINING_PTS

ROLLING_WINDOWS = [3, 5, 10]

RAW_STATS = ["PTS", "MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "FG_PCT", "FG3_PCT", "FT_PCT"]
ADV_STATS = ["TS%", "eFG%", "USG%"]

# ---------- Load Raw Data ----------
print("📥 Loading raw stats CSV...")
df = pd.read_csv(RAW_GAMES)
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
df = df.sort_values(["Player_ID", "GAME_DATE"])

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

# ---------- Compute Advanced Metrics for PTS model ----------
df["TS%"] = df["PTS"] / (2 * (df["FGA"] + 0.44 * df["FTA"]).replace(0,1))
df["eFG%"] = (df["FGM"] + 0.5 * df["FG3M"]) / df["FGA"].replace(0,1)
df["USG%"] = ((df["FGA"] + 0.44*df["FTA"] + df["TOV"]) * 100) / (
    ((df["MIN"]/df["MIN"].max()) * df.groupby("GAME_DATE")["FGA"].transform("sum") +
     0.44*df.groupby("GAME_DATE")["FTA"].transform("sum") +
     df.groupby("GAME_DATE")["TOV"].transform("sum"))
).replace(0,1)

# ---------- Compute Rolling Stats ----------
for w in ROLLING_WINDOWS:
    for stat in RAW_STATS + ADV_STATS:
        col_name = f"{stat}_Roll{w}"
        df[col_name] = df.groupby("Player_ID")[stat].rolling(w, min_periods=1).mean().reset_index(0, drop=True)

# ---------- Compute Season Averages ----------
for stat in RAW_STATS + ADV_STATS:
    col_name = f"{stat}_SeasonAvg"
    df[col_name] = df.groupby(["Player_ID", "SEASON_ID"])[stat].expanding().mean().shift(1).reset_index(level=[0,1], drop=True)

# ---------- PTS_per_MIN ----------
df["PTS_per_MIN"] = df["PTS"] / df["MIN"].replace(0, np.nan)
for w in ROLLING_WINDOWS:
    df[f"PTS_per_MIN_Roll{w}"] = df[f"PTS_Roll{w}"] / df[f"MIN_Roll{w}"].replace(0, np.nan)
df["PTS_per_MIN_SeasonAvg"] = df.groupby("Player_ID")["PTS_per_MIN"].expanding().mean().shift(1).reset_index(level=0, drop=True)

# ---------- Merge MIN_PRED_OOF ----------
if os.path.exists(PROCESSED_OOF):
    print("📥 Merging MIN_PRED_OOF...")
    df_min = pd.read_csv(PROCESSED_OOF)
    df_min["GAME_DATE"] = pd.to_datetime(df_min["GAME_DATE"])
    df = df.merge(df_min[["Player_ID", "GAME_DATE", "MIN_PRED_OOF"]], on=["Player_ID", "GAME_DATE"], how="left")
else:
    print("⚠️ MIN_PRED_OOF file not found, using NaN placeholder")
    df["MIN_PRED_OOF"] = np.nan

# ---------- Select Columns ----------
feature_cols = ["Player_ID", "PLAYER_NAME", "Team_Abv", "SEASON_ID", "GAME_DATE", "Opponent", "Home", "Days_Rest"]

# Rolling stats
for w in ROLLING_WINDOWS:
    feature_cols += [f"{stat}_Roll{w}" for stat in RAW_STATS + ADV_STATS]
    feature_cols += [f"PTS_per_MIN_Roll{w}"]

# Season averages
feature_cols += [f"{stat}_SeasonAvg" for stat in RAW_STATS + ADV_STATS]
feature_cols += ["PTS_per_MIN_SeasonAvg"]

# Target
feature_cols += ["PTS"]

# MIN_PRED_OOF
feature_cols += ["MIN_PRED_OOF"]

df_final = df[feature_cols].copy()

# ---------- Save Training CSV ----------
os.makedirs(os.path.dirname(PROCESSED_TRAINING_PTS), exist_ok=True)
df_final.to_csv(PROCESSED_TRAINING_PTS, index=False)
print(f"💾 PTS training data saved to {PROCESSED_TRAINING_PTS}")
