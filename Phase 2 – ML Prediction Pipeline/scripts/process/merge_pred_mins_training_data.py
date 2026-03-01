#!/usr/bin/env python3
"""
Merge OOF predicted minutes into AI training CSV
"""

import os
import pandas as pd
from paths import PROCESSED_OOF, PROCESSED_TRAINING_ALL, PROCESSED_TRAINING_WITH_MIN_PRED

# ---------- Load Data ----------
print("📥 Loading OOF minutes predictions...")
df_mins = pd.read_csv(PROCESSED_OOF)
df_mins["GAME_DATE"] = pd.to_datetime(df_mins["GAME_DATE"])

print("📥 Loading AI training data...")
df_ai = pd.read_csv(PROCESSED_TRAINING_ALL)
df_ai["GAME_DATE"] = pd.to_datetime(df_ai["GAME_DATE"])

# ---------- Merge ----------
print("🔗 Merging OOF minutes into AI training data...")
df_merged = df_ai.merge(
    df_mins[["Player_ID", "SEASON_ID", "GAME_DATE", "MIN_PRED_OOF"]],
    on=["Player_ID", "SEASON_ID", "GAME_DATE"],
    how="left"
)
df_merged["MIN_PRED_OOF"] = df_merged["MIN_PRED_OOF"].fillna(0)

# ---------- Save ----------
os.makedirs(os.path.dirname(PROCESSED_TRAINING_WITH_MIN_PRED), exist_ok=True)
df_merged.to_csv(PROCESSED_TRAINING_WITH_MIN_PRED, index=False)
print(f"💾 Merged AI training file saved to {PROCESSED_TRAINING_WITH_MIN_PRED}")
