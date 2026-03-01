#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd

pd.set_option("display.max_columns", 500)


def parse_prizepicks_projections(json_path: Path, max_level: int = 3) -> pd.DataFrame:
    with json_path.open("r", encoding="utf-8") as f:
        resp = json.load(f)

    if "data" not in resp:
        raise ValueError("Invalid input JSON: missing top-level key 'data'.")

    data = pd.json_normalize(resp["data"], max_level=max_level)

    included = pd.json_normalize(resp.get("included", []), max_level=max_level)

    # Keep only new_player rows (if any)
    if not included.empty and "type" in included.columns:
        players_raw = included[included["type"] == "new_player"].copy()
    else:
        players_raw = pd.DataFrame()

    # Ensure required columns exist (avoid KeyError)
    required_player_cols = ["id", "attributes.name", "attributes.team", "attributes.team_name"]
    players_raw = players_raw.reindex(columns=required_player_cols)

    players = players_raw.rename(
        columns={
            "id": "player_id",
            "attributes.name": "player_name",
            "attributes.team": "team_abbreviation",
            "attributes.team_name": "team_name",
        }
    )

    # Merge player metadata onto projections
    if "relationships.new_player.data.id" in data.columns:
        data = pd.merge(
            data,
            players,
            how="left",
            left_on="relationships.new_player.data.id",
            right_on="player_id",
        )
    else:
        # Still return the data, but warn via empty merge cols
        data["player_name"] = None
        data["team_abbreviation"] = None
        data["team_name"] = None

    return data


def build_lines_csv(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = [
        "player_name",
        "team_abbreviation",
        "attributes.stat_type",
        "attributes.line_score",
        "attributes.start_time",
        "attributes.odds_type",
    ]
    df = df.reindex(columns=required_cols).copy()

    df["line_type"] = (
        df["attributes.odds_type"]
        .map({"standard": "standard", "demon": "demon", "goblin": "goblin"})
        .fillna("standard")
    )

    df = df.rename(
        columns={
            "player_name": "Player",
            "team_abbreviation": "Team",
            "attributes.stat_type": "Stat",
            "attributes.line_score": "Line",
            "attributes.start_time": "Game_DateTime",
        }
    )

    df["Line"] = pd.to_numeric(df["Line"], errors="coerce")

    return df[["Player", "Team", "Stat", "Line", "line_type", "Game_DateTime"]]


def main():
    parser = argparse.ArgumentParser(description="Parse PrizePicks projections JSON into a lines CSV.")
    parser.add_argument(
        "--input",
        default="data/sample_prizepicks_api.json",
        help="Path to PrizePicks projections JSON (default: data/sample_prizepicks_api.json)",
    )
    parser.add_argument(
        "--output",
        default="data/prizepicks_lines.csv",
        help="Output CSV path (default: data/prizepicks_lines.csv)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input JSON not found: {input_path}\n\n"
            "Tip: For the public repo, use the included sample JSON:\n"
            "  data/sample_prizepicks_api.json\n"
            "Or save your own exported slate JSON to:\n"
            "  data/prizepicks_api.json\n"
            "and run:\n"
            "  python Prizepicks_lines_parser.py --input data/prizepicks_api.json"
        )

    df = parse_prizepicks_projections(input_path)
    lines_df = build_lines_csv(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines_df.to_csv(output_path, index=False)
    print(f"CSV saved: {output_path} ({len(lines_df)} rows)")


if __name__ == "__main__":
    main()