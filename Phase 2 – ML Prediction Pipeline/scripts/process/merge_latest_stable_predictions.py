#!/usr/bin/env python3
"""
merge_latest_stable_predictions.py

Merges the latest stable PTS, REB, AST, and FG3M predictions:
 - outputs/stable_pts/pts_preds_stable_YYYYMMDD.csv
 - outputs/stable_reb/reb_preds_stable_YYYYMMDD.csv
 - outputs/stable_ast/ast_preds_stable_YYYYMMDD.csv
 - outputs/stable_fg3m/fg3m_preds_stable_YYYYMMDD.csv

Saves merged_predictions_stable_<YYYYMMDD>.csv to PREDICT_MERGED_STABLE folder.
"""

import os
import re
import pandas as pd
from paths import PREDICT_PTS_STABLE, PREDICT_REB_STABLE, PREDICT_AST_STABLE, PREDICT_FG3M_STABLE, PREDICT_MERGED_STABLE

# ---------- Helper Functions ----------
def get_latest_file_in_dir(directory, prefix=None, suffix='.csv'):
    """Return the latest file matching prefix in a directory."""
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(suffix) and (prefix is None or f.startswith(prefix))
    ]
    return max(files, key=os.path.getmtime) if files else None

def extract_date_from_filename(filename):
    """Extract YYYYMMDD from filename using regex."""
    match = re.search(r'(\d{8})', filename)
    return match.group(1) if match else None

def normalize_columns(df, name_col='PLAYER_NAME', team_col='Team_Abv'):
    """Ensure the dataframe has standardized PLAYER_NAME and Team_Abv columns."""
    if name_col not in df.columns:
        for c in df.columns:
            if c.lower() in ('player', 'player_name', 'name'):
                df.rename(columns={c: name_col}, inplace=True)
                break
    if team_col not in df.columns:
        for c in df.columns:
            if c.lower() in ('team', 'team_abv', 'team_abbreviation'):
                df.rename(columns={c: team_col}, inplace=True)
                break
    df[name_col] = df[name_col].astype(str).str.strip()
    df[team_col] = df[team_col].astype(str).str.strip().str.upper()
    return df

def get_pred_column(df, stat):
    """Detect prediction column for a given stat."""
    col = next((c for c in df.columns if stat in c.upper() and 'PRED' in c.upper()), None)
    return col

# ---------- Main ----------
def main():
    os.makedirs(PREDICT_MERGED_STABLE, exist_ok=True)

    # Find latest stable prediction files
    pts_file = get_latest_file_in_dir(PREDICT_PTS_STABLE, prefix='pts_preds_stable_')
    reb_file = get_latest_file_in_dir(PREDICT_REB_STABLE, prefix='reb_preds_stable_')
    ast_file = get_latest_file_in_dir(PREDICT_AST_STABLE, prefix='ast_preds_stable_')
    fg3m_file = get_latest_file_in_dir(PREDICT_FG3M_STABLE, prefix='fg3m_preds_stable_')

    if not pts_file or not reb_file or not ast_file or not fg3m_file:
        print("❌ Missing required stable prediction files.")
        print("PTS:", pts_file)
        print("REB:", reb_file)
        print("AST:", ast_file)
        print("FG3M:", fg3m_file)
        return

    print("📦 Using:")
    print(" • PTS predictions:", pts_file)
    print(" • REB predictions:", reb_file)
    print(" • AST predictions:", ast_file)
    print(" • FG3M predictions:", fg3m_file)

    # Load files
    pts = normalize_columns(pd.read_csv(pts_file))
    reb = normalize_columns(pd.read_csv(reb_file))
    ast = normalize_columns(pd.read_csv(ast_file))
    fg3m = normalize_columns(pd.read_csv(fg3m_file))

    # Rename prediction columns to standard names
    for df, stat, new_col in [(pts, 'PTS', 'PTS_PRED'),
                              (reb, 'REB', 'REB_PRED'),
                              (ast, 'AST', 'AST_PRED'),
                              (fg3m, 'FG3M', 'FG3M_PRED')]:
        pred_col = get_pred_column(df, stat)
        if pred_col and pred_col != new_col:
            df.rename(columns={pred_col: new_col}, inplace=True)

    # Merge all predictions
    merged = pts[['PLAYER_NAME', 'Team_Abv', 'GAME_DATE', 'PTS_PRED']].merge(
        reb[['PLAYER_NAME', 'Team_Abv', 'GAME_DATE', 'REB_PRED']],
        on=['PLAYER_NAME', 'Team_Abv', 'GAME_DATE'], how='outer'
    ).merge(
        ast[['PLAYER_NAME', 'Team_Abv', 'GAME_DATE', 'AST_PRED']],
        on=['PLAYER_NAME', 'Team_Abv', 'GAME_DATE'], how='outer'
    ).merge(
        fg3m[['PLAYER_NAME', 'Team_Abv', 'GAME_DATE', 'FG3M_PRED']],
        on=['PLAYER_NAME', 'Team_Abv', 'GAME_DATE'], how='outer'
    )

    # Determine date from PTS file
    file_date = extract_date_from_filename(os.path.basename(pts_file))
    if not file_date:
        raise ValueError("Could not extract date from PTS file name.")

    # Save merged CSV
    out_name = f"merged_predictions_stable_{file_date}.csv"
    out_path = os.path.join(PREDICT_MERGED_STABLE, out_name)
    merged.to_csv(out_path, index=False)

    print("\n✅ Merge complete.")
    print("Saved to:", out_path)
    print(f"Rows: {len(merged)}")
    print("\n🔍 Preview:")
    print(merged.head(10))

if __name__ == "__main__":
    main()
