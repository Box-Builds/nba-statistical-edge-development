#!/usr/bin/env python3
"""
Next-game points predictor (team-level next game version)
----------------------------------------------------------
• Builds ghost rows by checking each team's last game in TRAINING data
• Creates ghost rows for all rostered players for that team's next scheduled game
• Pulls predicted minutes (MIN_PRED) from mins predictions file
• Saves output using the earliest GAME_DATE in the prediction set
"""

import os
import pandas as pd
import pickle
from pandas import Timestamp

# ============================================================
# Load paths
# ============================================================
from paths import (
    PROCESSED_TRAINING_WITH_MIN_PRED,
    RAW_SCHEDULE,
    RAW_ROSTERS,
    PTS_MODEL_STABLE,
    PREDICT_MINS,
    PREDICT_PTS_STABLE,
)

# ------------------------------------------------------------
# Identify latest predicted-minutes file
# ------------------------------------------------------------
def find_latest_mins_pred_file():
    if not os.path.exists(PREDICT_MINS):
        return None
    files = [
        f for f in os.listdir(PREDICT_MINS)
        if f.startswith("next_game_mins_preds_") and f.endswith(".csv")
    ]
    if not files:
        return None
    return os.path.join(PREDICT_MINS, sorted(files)[-1])

MIN_PRED_FILE = find_latest_mins_pred_file()

# ============================================================
# Constants
# ============================================================
ROLLING_WINDOWS = [3, 5, 10]
RAW_STATS = ["PTS", "FG_PCT", "FG3_PCT", "FT_PCT", "MIN", "PTS_per_MIN"]
ADV_STATS = ["TS%", "eFG%", "USG%"]
ALL_STATS_FOR_ROLL = RAW_STATS + ADV_STATS

# ============================================================
# Load Data
# ============================================================
print("📥 Loading training data...")
df_train = pd.read_csv(PROCESSED_TRAINING_WITH_MIN_PRED)
df_train["GAME_DATE"] = pd.to_datetime(df_train["GAME_DATE"])
df_train.columns = [c.strip() for c in df_train.columns]
print(f"Training rows: {len(df_train)}")

print("📥 Loading schedule...")
df_schedule = pd.read_csv(RAW_SCHEDULE)
df_schedule["GAME_DATE"] = pd.to_datetime(df_schedule["GAME_DATE"])
df_schedule.columns = [c.strip() for c in df_schedule.columns]

print("📥 Loading roster...")
with open(RAW_ROSTERS, "rb") as f:
    roster = pickle.load(f)

print("📥 Loading trained PTS model...")
with open(PTS_MODEL_STABLE, "rb") as f:
    model = pickle.load(f)
model_features = list(model.feature_name_)

# ============================================================
# Helper Functions
# ============================================================
def safe_mean(series):
    s = series.dropna()
    return float(s.mean()) if len(s) > 0 else 0.0

def compute_rolling(player_df, stat, window):
    if stat not in player_df.columns or player_df.empty:
        return 0.0
    return safe_mean(player_df.tail(window)[stat])

def compute_season_avg(player_df, stat):
    if stat not in player_df.columns or player_df.empty:
        return 0.0
    return safe_mean(player_df[stat])

# ============================================================
# Team-level last game
# ============================================================
df_train["Team_Abv"] = df_train["Team_Abv"].str.strip().str.upper()
teams_last_game = df_train.groupby("Team_Abv")["GAME_DATE"].max().to_dict()

# ============================================================
# Build team schedule lookup
# ============================================================
team_schedules = {}
for _, g in df_schedule.iterrows():
    for team_abv in [g["HOME_TEAM_ABV"].strip().upper(), g["AWAY_TEAM_ABV"].strip().upper()]:
        team_schedules.setdefault(team_abv, []).append(g)

for team in team_schedules:
    team_schedules[team] = sorted(team_schedules[team], key=lambda r: r["GAME_DATE"])

# Team ID → abbreviation mapping
team_id_to_abv = {}
for _, row in df_schedule.iterrows():
    team_id_to_abv[row["HOME_TEAM_ID"]] = row["HOME_TEAM_ABV"].strip().upper()
    team_id_to_abv[row["AWAY_TEAM_ID"]] = row["AWAY_TEAM_ABV"].strip().upper()

# ============================================================
# Build Ghost Rows
# ============================================================
ghost_rows = []
today = Timestamp.today().normalize()
latest_game_in_data = df_train["GAME_DATE"].max().normalize()

for team_id, players in roster.items():
    team_abv = team_id_to_abv.get(team_id)
    if team_abv is None:
        print(f"⚠️ No abbreviation found for team ID {team_id}")
        continue

    last_game_date = teams_last_game.get(team_abv, today - pd.Timedelta(days=1))
    last_game_date = pd.to_datetime(last_game_date).normalize()

    next_game = None
    for g in team_schedules.get(team_abv, []):
        game_date = pd.to_datetime(g["GAME_DATE"]).normalize()
        if game_date > last_game_date and game_date > latest_game_in_data:
            next_game = g
            break

    if next_game is None:
        print(f"⚠️ No upcoming game found for team {team_abv}")
        continue

    game_date = pd.to_datetime(next_game["GAME_DATE"])
    home_abv = next_game["HOME_TEAM_ABV"].strip().upper()
    away_abv = next_game["AWAY_TEAM_ABV"].strip().upper()
    home_flag = 1 if team_abv == home_abv else 0
    opp_abv = away_abv if home_flag == 0 else home_abv

    for p in players:
        player_id = int(p["PLAYER_ID"])
        player_name = p["PLAYER_NAME"]

        history = df_train[df_train["Player_ID"] == player_id].sort_values("GAME_DATE")

        row = {
            "Player_ID": player_id,
            "PLAYER_NAME": player_name,
            "Team_Abv": team_abv,
            "Opponent": opp_abv,
            "Home": home_flag,
            "GAME_DATE": game_date,
        }

        # Rolling windows
        for w in ROLLING_WINDOWS:
            for stat in ALL_STATS_FOR_ROLL:
                row[f"{stat}_Roll{w}"] = compute_rolling(history, stat, w)

        # Season averages
        for stat in ALL_STATS_FOR_ROLL:
            row[f"{stat}_SeasonAvg"] = compute_season_avg(history, stat)

        # Days rest
        if not history.empty:
            row["Days_Rest"] = int((game_date - history["GAME_DATE"].max()).days)
        else:
            row["Days_Rest"] = 2

        ghost_rows.append(row)

print(f"📝 Ghost rows created: {len(ghost_rows)}")
df_ghost = pd.DataFrame(ghost_rows)
if df_ghost.empty:
    print("No ghost rows found. Exiting.")
    exit(0)

# ============================================================
# Load Predicted Minutes
# ============================================================
if MIN_PRED_FILE and os.path.exists(MIN_PRED_FILE):
    print(f"📥 Loading minutes predictions: {MIN_PRED_FILE}")
    mins_df = pd.read_csv(MIN_PRED_FILE)
    mins_df["GAME_DATE"] = pd.to_datetime(mins_df["GAME_DATE"])
    mins_df.rename(columns={"MIN_PRED": "MIN_PRED_OOF"}, inplace=True)

    df_ghost = df_ghost.merge(
        mins_df[["Player_ID", "GAME_DATE", "MIN_PRED_OOF"]],
        on=["Player_ID", "GAME_DATE"],
        how="left"
    )
else:
    print("⚠️ No mins prediction file found — using MIN_PRED_OOF = 0")
    df_ghost["MIN_PRED_OOF"] = 0

df_ghost["MIN_PRED_OOF"] = df_ghost["MIN_PRED_OOF"].fillna(0)

# ============================================================
# Prepare Model Input
# ============================================================
X = pd.DataFrame(index=df_ghost.index)
for feat in model_features:
    X[feat] = df_ghost[feat] if feat in df_ghost.columns else 0
X = X.fillna(0)

for c in ["Team_Abv", "Opponent"]:
    if c in X.columns:
        X[c] = X[c].astype("category")

# ============================================================
# Predict
# ============================================================
print("🏀 Predicting PTS...")
df_ghost["PTS_PRED"] = model.predict(X)

# ============================================================
# Save Output
# ============================================================
os.makedirs(PREDICT_PTS_STABLE, exist_ok=True)
earliest_date = df_ghost["GAME_DATE"].min().strftime("%Y%m%d")
out_file = os.path.join(PREDICT_PTS_STABLE, f"pts_preds_stable_{earliest_date}.csv")

df_ghost[[
    "Player_ID", "PLAYER_NAME", "Team_Abv", "Opponent", "Home", "GAME_DATE",
    "MIN_PRED_OOF", "PTS_PRED"
]].to_csv(out_file, index=False)

print(f"✅ Saved {len(df_ghost)} predictions to {out_file}")
