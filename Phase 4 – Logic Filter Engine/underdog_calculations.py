#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

# -----------------------------
# Config (defaults)
# -----------------------------
DEFAULT_MASTER_CSV = "data/raw/nba_player_game_stats_full.csv"
DEFAULT_UNDERDOG_LINES_CSV = "data/underdog_lines.csv"
DEFAULT_OUTPUT_CSV = "output/underdog_lines_filtered.csv"

DEFAULT_THRESHOLD_PCT = 70.0
DEFAULT_MIN_ODDS = -137  # minimum allowed odds for chosen side

ALLOWED_STATS = ("PTS", "AST", "REB", "PTS+REB+AST", "FG3M")

UNDERDOG_MAP = {
    "player_points": "PTS",
    "player_assists": "AST",
    "player_rebounds": "REB",
    "player_points_rebounds_assists": "PTS+REB+AST",
    "player_threes": "FG3M",
    "player_threes_alternate": "FG3M",
}

# -----------------------------
# Helpers
# -----------------------------
def normalize_name(name: str) -> str:
    return str(name).lower().replace(".", "").replace(" ", "")

def compute_season_label(game_date: pd.Timestamp) -> str:
    """Return season label like '2025-2026' based on NBA season start in Oct."""
    if pd.isna(game_date):
        return ""
    start_year = game_date.year if game_date.month < 10 else game_date.year
    end_year = start_year + 1
    return f"{start_year}-{end_year}"

def ensure_season_column(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee df has SEASON column formatted like 'YYYY-YYYY'."""
    df = df.copy()
    if "SEASON" not in df.columns:
        df["SEASON"] = df["GAME_DATE"].apply(compute_season_label)
    else:
        # normalize potential numeric/int seasons or weird formatting to string
        df["SEASON"] = df["SEASON"].astype(str)
    return df

def infer_current_season(df: pd.DataFrame) -> str:
    """Infer the most recent season present in the dataset."""
    latest_date = df["GAME_DATE"].max()
    return compute_season_label(latest_date)

def compute_hit_rate_stats(data: pd.DataFrame, stat: str, line: float):
    if len(data) == 0:
        return {"over_pct": 0, "under_pct": 0, "push_pct": 0, "avg_min": 0, "games": 0}

    if "+" in stat:
        cols = [s.strip().upper() for s in stat.split("+")]
        values = data[cols].fillna(0).sum(axis=1)
    else:
        values = data[stat].fillna(0)

    return {
        "over_pct": (values > line).mean() * 100,
        "under_pct": (values < line).mean() * 100,
        "push_pct": (values == line).mean() * 100,
        "avg_min": data["MIN"].mean(),
        "games": len(data),
    }

def pick_side(over_pct: float, under_pct: float, threshold: float):
    if over_pct >= threshold:
        return "Over", over_pct
    if under_pct >= threshold:
        return "Under", under_pct
    return None, None

def side_pct_for_frame(frame, side: str):
    return frame["over_pct"] if side == "Over" else frame["under_pct"]

def evaluate_line(
    df_master: pd.DataFrame,
    season_label: str,
    threshold_pct: float,
    min_odds: float,
    player_name: str,
    stat: str,
    line: float,
    row: pd.Series,
):
    stat = stat.upper()
    if stat not in ALLOWED_STATS:
        return None

    norm_player = normalize_name(player_name)
    player_data = df_master[df_master["PLAYER_NAME"].apply(normalize_name) == norm_player].sort_values("GAME_DATE")
    if player_data.empty:
        return None

    season_data = player_data[player_data["SEASON"] == season_label].sort_values("GAME_DATE")
    if season_data.empty:
        return None

    # ---- Last 5 ----
    last5_frame = compute_hit_rate_stats(season_data.tail(5), stat, line)
    side, last5_pct = pick_side(last5_frame["over_pct"], last5_frame["under_pct"], threshold_pct)
    if side is None:
        return None

    # ---- Last 10 ----
    if len(season_data) >= 10:
        last10_frame = compute_hit_rate_stats(season_data.tail(10), stat, line)
        last10_pct = side_pct_for_frame(last10_frame, side)
    else:
        last10_pct = np.nan

    # ---- Last 25 ----
    if len(season_data) >= 25:
        last25_frame = compute_hit_rate_stats(season_data.tail(25), stat, line)
        last25_pct = side_pct_for_frame(last25_frame, side)
    else:
        last25_pct = np.nan

    # ---- Enforce thresholds ----
    if not np.isnan(last10_pct) and last10_pct < threshold_pct:
        return None
    if not np.isnan(last25_pct) and last25_pct < threshold_pct:
        return None

    season_frame = compute_hit_rate_stats(season_data, stat, line)
    season_pct = side_pct_for_frame(season_frame, side)
    if season_pct < threshold_pct:
        return None

    # ---- Odds check ----
    # Underdog lines file should contain OverOdds/UnderOdds columns.
    over_odds = row.get("OverOdds", np.nan)
    under_odds = row.get("UnderOdds", np.nan)
    side_odds = over_odds if side == "Over" else under_odds

    if pd.notna(side_odds) and float(side_odds) < min_odds:
        return None

    return {
        "Player": player_name,
        "Market": row.get("Market"),
        "Stat": stat,
        "Line": line,
        "Side": side,
        "Odds": side_odds,
        "Game": row.get("Game"),
        "GameTime": row.get("GameTime"),
        "Last 5 %": last5_pct,
        "Last 10 %": last10_pct,
        "Last 25 %": last25_pct,
        "Current Season %": season_pct,
        "Push %": last5_frame["push_pct"],
        "Season Avg MIN": season_frame["avg_min"],
        "Season": season_label,
    }

# -----------------------------
# Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Filter Underdog DFS lines using season hit-rate logic.")
    parser.add_argument("--master", default=DEFAULT_MASTER_CSV, help="Path to master NBA game log CSV")
    parser.add_argument("--lines", default=DEFAULT_UNDERDOG_LINES_CSV, help="Path to Underdog lines CSV")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_CSV, help="Output CSV path")
    parser.add_argument("--season", default=None, help="Season label like '2025-2026' (defaults to inferred)")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_PCT, help="Hit-rate threshold percent")
    parser.add_argument("--min-odds", type=float, default=DEFAULT_MIN_ODDS, help="Minimum allowed odds for chosen side")
    args = parser.parse_args()

    # --- Load master data ---
    master_path = Path(args.master)
    if not master_path.exists():
        raise FileNotFoundError(f"Missing master CSV: {master_path}")

    df = pd.read_csv(master_path, low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
    df = ensure_season_column(df)

    season_label = args.season or infer_current_season(df)

    # --- Load lines ---
    lines_path = Path(args.lines)
    if not lines_path.exists():
        raise FileNotFoundError(f"Missing lines CSV: {lines_path}")

    lines_df = pd.read_csv(lines_path)

    # Be robust to casing
    # Expect at least: Player, Market, Line, OverOdds, UnderOdds
    col_map = {c.lower(): c for c in lines_df.columns}
    required = ["player", "market", "line", "overodds", "underodds"]
    missing = [r for r in required if r not in col_map]
    if missing:
        raise ValueError(
            f"Lines CSV is missing required columns: {missing}\n"
            f"Found columns: {list(lines_df.columns)}"
        )

    # Standardize access by using original column names via col_map
    player_col = col_map["player"]
    market_col = col_map["market"]
    line_col = col_map["line"]

    # Map markets to Stats, drop unsupported
    lines_df["Stat"] = lines_df[market_col].map(UNDERDOG_MAP)
    lines_df = lines_df[lines_df["Stat"].notna()].copy()

    results = []
    for _, row in lines_df.iterrows():
        stat = row["Stat"]
        res = evaluate_line(
            df_master=df,
            season_label=season_label,
            threshold_pct=args.threshold,
            min_odds=args.min_odds,
            player_name=row[player_col],
            stat=stat,
            line=float(row[line_col]),
            row=row,
        )
        if res:
            results.append(res)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if results:
        pd.DataFrame(results).to_csv(out_path, index=False)
        print(f"Saved {len(results)} good lines → {out_path}")
    else:
        print("No lines met the criteria.")

if __name__ == "__main__":
    main()