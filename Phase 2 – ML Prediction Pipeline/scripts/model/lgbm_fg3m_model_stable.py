#!/usr/bin/env python3
import os
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import numpy as np
import pickle
from datetime import datetime
from paths import PROCESSED_TRAINING_WITH_MIN_PRED, FG3M_MODEL_STABLE

TARGET_STAT = "FG3M"

# ---------- Stats Relevant for 3PT ----------
raw_stats = ["FG3M", "FG3A", "FG3_PCT", "MIN"]
adv_stats = ["USG%"]
ROLLING_WINDOWS = [3, 5, 10]

# ---------- Load Training Data ----------
print("📥 Loading training CSV...")
df = pd.read_csv(PROCESSED_TRAINING_WITH_MIN_PRED)
print(f"Total rows in CSV: {len(df)}")

df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

# ---------- Prepare Features ----------
feature_cols = ["Home", "Days_Rest"]

# Rolling stats
for w in ROLLING_WINDOWS:
    feature_cols += [f"{stat}_Roll{w}" for stat in raw_stats + adv_stats]

# Season averages
feature_cols += [f"{stat}_SeasonAvg" for stat in raw_stats + adv_stats]

# Add OOF predicted minutes
feature_cols.append("MIN_PRED_OOF")

# Create feature matrix
X = df[feature_cols].copy()
y = df[TARGET_STAT]

# Ensure numeric type
X["MIN_PRED_OOF"] = X["MIN_PRED_OOF"].fillna(0).astype(float)

# ---------- Evaluation Split ----------
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.1, random_state=42
)
print(f"Training on {len(X_train)} rows, validating on {len(X_val)} rows.")

# ---------- Train LightGBM ----------
model = lgb.LGBMRegressor(
    objective='regression',
    learning_rate=0.05,
    num_leaves=31,
    n_estimators=1000
)

print("🏀 Training LightGBM...")
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    eval_metric='rmse',
    callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(50)]
)

# ---------- Evaluate ----------
y_pred = model.predict(X_val)
mae = mean_absolute_error(y_val, y_pred)
mse = mean_squared_error(y_val, y_pred)
rmse = mse ** 0.5
rae = np.mean(np.abs(y_val - y_pred) / np.abs(y_val - np.mean(y_val)))
r2 = r2_score(y_val, y_pred)

print(f"✅ Validation Metrics → MAE: {mae:.2f} | RMSE: {rmse:.2f} | RAE: {rae:.4f} | R²: {r2:.4f}")

# ---------- Save Model ----------
with open(FG3M_MODEL_STABLE, "wb") as f:
    pickle.dump(model, f)
print(f"💾 Model saved to {FG3M_MODEL_STABLE}")
