#!/usr/bin/env python3
"""
Minutes Prediction Model Training Script
Uses processed mins_training_data.csv and outputs trained model.
"""

import os
import pandas as pd
import lightgbm as lgb
from datetime import datetime
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pickle
import numpy as np
from paths import PROCESSED_TRAINING_MINS, MINS_HUBER_MODEL, PROCESSED_OOF

# ---------- Load Data ----------
df = pd.read_csv(PROCESSED_TRAINING_MINS)
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

# ---------- Features & Target ----------
TARGET = "MIN"
FEATURES = [
    "MIN_Roll3", "MIN_Roll5", "MIN_Roll10", "MIN_SeasonAvg",
    "Home", "Days_Rest",
    "Team_Abv"
]

X = df[FEATURES].copy()
y = df[TARGET]

# Convert categorical columns
categorical_features = ["Team_Abv"]
for cat in categorical_features:
    if cat in X.columns:
        X[cat] = X[cat].fillna("UNK").astype("category")

# ---------- Train/Validation Split ----------
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.1, random_state=42
)
print(f"Training on {len(X_train)} rows, validating on {len(X_val)} rows.")

# ---------- Train LightGBM with Huber Loss ----------
kf = KFold(n_splits=5, shuffle=True, random_state=42)
oof_preds = np.zeros(len(X))
models = []

for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
    print(f"\n📦 Fold {fold + 1}")
    X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
    y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]

    model = lgb.LGBMRegressor(
        objective="huber",
        alpha=0.9,
        learning_rate=0.05,
        num_leaves=31,
        n_estimators=1000,
        boosting_type="gbdt",
        random_state=42 + fold
    )

    model.fit(
        X_train_fold, y_train_fold,
        eval_set=[(X_val_fold, y_val_fold)],
        eval_metric="huber",
        categorical_feature=categorical_features,
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(50)]
    )

    preds = model.predict(X_val_fold)
    oof_preds[val_idx] = preds
    models.append(model)

rmse = mean_squared_error(y, oof_preds) ** 0.5
mae = mean_absolute_error(y, oof_preds)
print(f"✅ OOF RMSE: {rmse:.3f}, MAE: {mae:.3f}")

# ---------- Evaluate ----------
y_pred = model.predict(X_val)
mse = mean_squared_error(y_val, y_pred)
rmse = mse ** 0.5
mae = mean_absolute_error(y_val, y_pred)
print(f"✅ Validation RMSE: {rmse:.3f}, MAE: {mae:.3f}")

# ---------- Save OOF predictions ----------
df["MIN_PRED_OOF"] = oof_preds
df.to_csv(PROCESSED_OOF, index=False)
print(f"💾 OOF predictions saved to {PROCESSED_OOF}")

# ---------- Optionally retrain final model on all data ----------
final_model = lgb.LGBMRegressor(
    objective="huber",
    alpha=0.9,
    learning_rate=0.05,
    num_leaves=31,
    n_estimators=1000,
    boosting_type="gbdt",
    random_state=42
)
final_model.fit(X, y, categorical_feature=categorical_features)
with open(MINS_HUBER_MODEL, "wb") as f:
    pickle.dump(final_model, f)
print(f"💾 Final model saved to {MINS_HUBER_MODEL}")
