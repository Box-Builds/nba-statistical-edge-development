#!/usr/bin/env python3
"""
NBA DFS Lines Grabber
- Fetches NBA player prop lines from Odds API for DFS books (Underdog / PrizePicks)
- Outputs CSV with one row per player/line containing Over & Under odds
"""

import requests
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

# ---------- CONFIG ----------
API_KEY = os.getenv("ODDS_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Missing ODDS_API_KEY environment variable.\n\n"
        "Windows (PowerShell):  $env:ODDS_API_KEY='YOUR_KEY_HERE'\n"
        "Windows (cmd):         set ODDS_API_KEY=YOUR_KEY_HERE\n"
        "Mac/Linux:             export ODDS_API_KEY='YOUR_KEY_HERE'\n"
    )
SPORT = "basketball_nba"
LOOKAHEAD_DAYS = 1
ODDS_FORMAT = "american"
DATE_FORMAT = "iso"

DFS_BOOKS = ["underdog"]  # add others if needed

MARKETS_ALL = [
    "player_points", "player_rebounds", "player_assists",
    "player_points_rebounds", "player_points_assists",
    "player_rebounds_assists", "player_points_rebounds_assists"
]
MARKETS_THREES = ["player_threes", "player_points_q1", "player_threes_alternate"]

OUTPUT_CSV = "data/underdog_lines.csv"
BASE_URL = "https://api.the-odds-api.com/v4"
# ----------------------------

def iso_to_pacific(iso_time):
    """Convert ISO datetime to Pacific Time string."""
    utc_time = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    pacific_time = utc_time.astimezone(ZoneInfo("America/Los_Angeles"))
    return pacific_time.strftime("%Y-%m-%d %I:%M %p")

def get_data(url, params):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_events():
    url = f"{BASE_URL}/sports/{SPORT}/events"
    return get_data(url, {"apiKey": API_KEY})

def process_odds_data(event, odds_data, market_name, all_lines):
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time = event.get("commence_time", "")

    event_payloads = odds_data if isinstance(odds_data, list) else [odds_data]

    for payload in event_payloads:
        for dfs_key in DFS_BOOKS:
            dfs_odds = next((b for b in payload.get("bookmakers", []) if b.get("key") == dfs_key), None)
            if not dfs_odds:
                continue

            market = next((m for m in dfs_odds.get("markets", []) if m.get("key") == market_name), None)
            if not market:
                continue

            # Group outcomes by player
            player_dict = defaultdict(dict)
            for outcome in market.get("outcomes", []):
                player = outcome.get("description")
                side = outcome.get("name")  # "Over" or "Under"
                player_dict[player][side] = {
                    "Line": outcome.get("point"),
                    "Odds": outcome.get("price")
                }

            for player, sides in player_dict.items():
                over = sides.get("Over", {})
                under = sides.get("Under", {})
                if not (over or under):
                    continue

                all_lines.append({
                    "Player": player,
                    "Market": market_name,
                    "Line": over.get("Line") or under.get("Line"),
                    "OverOdds": over.get("Odds"),
                    "UnderOdds": under.get("Odds"),
                    "Game": f"{away_team} @ {home_team}",
                    "GameTime": iso_to_pacific(commence_time)
                })

def main():
    now = datetime.now(timezone.utc)
    max_date = now + timedelta(days=LOOKAHEAD_DAYS)

    events = fetch_events()
    if not events:
        print("No events found or API error.")
        return

    # Filter for upcoming games
    filtered_events = []
    for e in events:
        try:
            et = datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
        except Exception:
            continue
        if now <= et <= max_date:
            filtered_events.append(e)

    if not filtered_events:
        print(f"No {SPORT} events in the next {LOOKAHEAD_DAYS} day(s).")
        return

    print(f"Found {len(filtered_events)} upcoming {SPORT.upper()} games.\n")

    all_lines = []

    for event in filtered_events:
        print(f"Processing: {event.get('away_team','')} @ {event.get('home_team','')} ({event.get('commence_time','')})")

        for market_group in [MARKETS_ALL, MARKETS_THREES]:
            markets_param = ",".join(market_group)
            odds_url = f"{BASE_URL}/sports/{SPORT}/events/{event['id']}/odds"
            params = {
                "apiKey": API_KEY,
                "markets": markets_param,
                "bookmakers": ",".join(DFS_BOOKS),
                "oddsFormat": ODDS_FORMAT,
                "dateFormat": DATE_FORMAT
            }

            odds_data = get_data(odds_url, params)

            if odds_data:
                for market_name in market_group:
                    process_odds_data(event, odds_data, market_name, all_lines)

    # --- Write CSV ---
    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Player", "Market", "Line", "OverOdds", "UnderOdds", "Game", "GameTime"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_lines:
            writer.writerow(row)

    print(f"\nDone! CSV saved as: {OUTPUT_CSV}, total lines: {len(all_lines)}")

if __name__ == "__main__":
    main()
