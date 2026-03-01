#!/usr/bin/env python3
"""
Create a streamlined training dataset for minutes prediction.
Uses only historical training data for now — no DFS or lineup merges.
"""

import pandas as pd
from paths import PROCESSED_TRAINING_ALL, PROCESSED_TRAINING_MINS

# ---------- LOAD DATA ----------
print(f"📥 Loading AI training data from {PROCESSED_TRAINING_ALL} ...")
training_df = pd.read_csv(PROCESSED_TRAINING_ALL)
training_df["GAME_DATE"] = pd.to_datetime(training_df["GAME_DATE"])

# ---------- SELECT TRAINING COLUMNS FOR MINS MODEL ----------
mins_cols = [
    'Player_ID', 'PLAYER_NAME', 'Team_Abv', 'SEASON_ID', 'GAME_DATE', 'Opponent', 'Home', 'Days_Rest',
    'MIN_Roll3', 'MIN_Roll5', 'MIN_Roll10', 'MIN_SeasonAvg', 'MIN_vs_Opp', 'MIN'
]

mins_training_df = training_df[mins_cols].copy()

# ---------- SAVE ----------
mins_training_df.to_csv(PROCESSED_TRAINING_MINS, index=False)
print(f"✅ Mins training data saved to {PROCESSED_TRAINING_MINS}")
