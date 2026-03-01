#!/usr/bin/env python3
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# --- Defaults ---
DEFAULT_MASTER_CSV = "data/raw/nba_player_game_stats_full.csv"
DEFAULT_LINES_CSV = "data/prizepicks_lines.csv"
DEFAULT_OUTPUT_CSV = "output/prizepicks_lines_filtered.csv"

DEFAULT_THRESHOLD_PCT = 70
DEFAULT_ALLOWED_STATS = ("PTS", "AST", "REB", "PTS+AST", "PTS+REB", "REB+AST", "PTS+REB+AST", "FG3M")
DEFAULT_ALLOWED_LINE_TYPES = ("standard", "demon")

# PrizePicks → internal stat mapping (must match what parser outputs in Stat column)
PRIZEPICKS_MAP = {
    "3-PT Made": "FG3M",
    "Assists": "AST",
    "Points": "PTS",
    "Pts+Asts": "PTS+AST",
    "Pts+Rebs": "PTS+REB",
    "Pts+Rebs+Asts": "PTS+REB+AST",
    "Rebounds": "REB",
    "Rebs+Asts": "REB+AST",
}


def normalize_name(name: str) -> str:
    return str(name).lower().replace(".", "").replace(" ", "")


def infer_season_label(dt: pd.Timestamp) -> str:
    """Return season label like '2025-2026' using NBA season rollover in October."""
    if pd.isna(dt):
        return ""
    start_year = dt.year if dt.month < 10 else dt.year
    end_year = start_year + 1
    # If date is Oct/Nov/Dec, that's the start year; if Jan-Sep, start year is previous year.
    if dt.month < 10:
        start_year = dt.year - 1
        end_year = dt.year
    return f"{start_year}-{end_year}"


def ensure_season_column(df: pd.DataFrame) -> pd.DataFrame:
    if "SEASON" in df.columns:
        return df
    # Compute season label based on GAME_DATE
    df["SEASON"] = df["GAME_DATE"].apply(infer_season_label)
    return df


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


def pick_side(over_pct, under_pct, threshold):
    if over_pct >= threshold:
        return "Over", over_pct
    if under_pct >= threshold:
        return "Under", under_pct
    return None, None


def side_pct_for_frame(frame, side):
    return frame["over_pct"] if side == "Over" else frame["under_pct"]


def evaluate_line(master_df, player_name, stat, line, threshold, allowed_stats, season_label, team=None, game_datetime=None):
    stat = stat.upper()
    if stat not in allowed_stats:
        return None

    norm_player_name = normalize_name(player_name)

    # Filter player rows (normalize once)
    player_series = master_df["PLAYER_NAME"].astype(str).map(normalize_name)
    player_data = master_df[player_series == norm_player_name].sort_values("GAME_DATE")

    if player_data.empty:
        return None

    season_data = player_data[player_data["SEASON"] == season_label].sort_values("GAME_DATE")
    if season_data.empty:
        return None

    # Last 5
    last5_frame = compute_hit_rate_stats(season_data.tail(5), stat, line)
    side, last5_pct = pick_side(last5_frame["over_pct"], last5_frame["under_pct"], threshold)
    if side is None:
        return None

    # Last 10
    last10_pct = np.nan
    if len(season_data) >= 10:
        last10_frame = compute_hit_rate_stats(season_data.tail(10), stat, line)
        last10_pct = side_pct_for_frame(last10_frame, side)

    # Last 25
    last25_pct = np.nan
    if len(season_data) >= 25:
        last25_frame = compute_hit_rate_stats(season_data.tail(25), stat, line)
        last25_pct = side_pct_for_frame(last25_frame, side)

    # Enforce Last 10 / Last 25 thresholds (when available)
    if not np.isnan(last10_pct) and last10_pct < threshold:
        return None
    if not np.isnan(last25_pct) and last25_pct < threshold:
        return None

    # Current season
    season_frame = compute_hit_rate_stats(season_data, stat, line)
    season_pct = side_pct_for_frame(season_frame, side)
    if season_pct < threshold:
        return None

    return {
        "Player": player_name,
        "Team": team,
        "Game_DateTime": game_datetime,
        "Stat": stat,
        "Line": float(line),
        "Side": side,
        "Last 5 %": last5_pct,
        "Last 10 %": last10_pct,
        "Last 25 %": last25_pct,
        "Current Season %": season_pct,
        "Push %": last5_frame["push_pct"],
        "Season Avg MIN": season_frame["avg_min"],
    }


def main():
    ap = argparse.ArgumentParser(description="Filter PrizePicks lines using historical hit-rate rules.")
    ap.add_argument("--master", default=DEFAULT_MASTER_CSV, help="Master NBA game log CSV path")
    ap.add_argument("--lines", default=DEFAULT_LINES_CSV, help="PrizePicks lines CSV path")
    ap.add_argument("--out", default=DEFAULT_OUTPUT_CSV, help="Output CSV path")
    ap.add_argument("--season", default=None, help="Season label like '2025-2026' (optional; inferred if omitted)")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_PCT, help="Hit-rate threshold percent")
    ap.add_argument("--allow_line_types", default=",".join(DEFAULT_ALLOWED_LINE_TYPES), help="Comma list, e.g. standard,demon")
    args = ap.parse_args()

    master_path = Path(args.master)
    lines_path = Path(args.lines)
    out_path = Path(args.out)

    if not master_path.exists():
        raise FileNotFoundError(
            f"Missing master data: {master_path}\n\n"
            "This repo does not ship NBA data.\n"
            "Generate it in Phase 2 (run_local_fetch.py), then copy:\n"
            "  Phase 2/data/raw/nba_player_game_stats_full.csv\n"
            "into:\n"
            "  Phase 4/data/raw/\n"
        )

    if not lines_path.exists():
        raise FileNotFoundError(
            f"Missing lines file: {lines_path}\n\n"
            "Create it by:\n"
            "  1) Exporting a slate JSON (manual)\n"
            "  2) Running Prizepicks_lines_parser.py to build data/prizepicks_lines.csv\n"
        )

    # Load master
    df = pd.read_csv(master_path, low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    if "GAME_DATE" not in df.columns:
        raise ValueError("Master CSV missing GAME_DATE column.")
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")

    df = ensure_season_column(df)

    # Infer season if not provided
    if args.season:
        season_label = args.season
    else:
        newest = df["GAME_DATE"].max()
        season_label = infer_season_label(newest)

    allowed_line_types = tuple(s.strip().lower() for s in args.allow_line_types.split(",") if s.strip())

    # Load lines
    lines_df = pd.read_csv(lines_path)
    lines_df.columns = [c.lower() for c in lines_df.columns]

    # Required columns check (based on your parser output)
    required = {"player", "stat", "line", "line_type"}
    missing = required - set(lines_df.columns)
    if missing:
        raise ValueError(f"Lines CSV missing columns: {sorted(missing)}")

    # Filter + map stat names
    lines_df = lines_df[lines_df["line_type"].str.lower().isin(allowed_line_types)].copy()
    lines_df["stat"] = lines_df["stat"].map(PRIZEPICKS_MAP)
    lines_df = lines_df[lines_df["stat"].notna()].copy()

    results = []
    for _, row in lines_df.iterrows():
        line_type = str(row["line_type"]).lower()

        res = evaluate_line(
            master_df=df,
            player_name=row["player"],
            stat=row["stat"],
            line=row["line"],
            threshold=args.threshold,
            allowed_stats=set(DEFAULT_ALLOWED_STATS),
            season_label=season_label,
            team=row.get("team"),
            game_datetime=row.get("game_datetime"),
        )
        if not res:
            continue

        # Demon lines: ONLY allow Over
        if line_type == "demon" and res["Side"] != "Over":
            continue

        res["line_type"] = line_type
        results.append(res)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if results:
        out = pd.DataFrame(results)
        col_order = [c for c in out.columns if c != "line_type"] + ["line_type"]
        out = out[col_order]
        out.to_csv(out_path, index=False)
        print(f"Saved {len(out)} lines → {out_path} (season={season_label}, threshold={args.threshold})")
    else:
        print(f"No lines met the criteria. (season={season_label}, threshold={args.threshold})")


if __name__ == "__main__":
    main()