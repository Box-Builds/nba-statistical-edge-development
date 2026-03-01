#!/usr/bin/env python3
"""
EV scanner comparing a "sharp" sportsbook to DFS apps.
- Pulls events for today + configurable lookahead days
- Requests markets in batches to reduce API calls
- Falls back to single-market requests if batch fails
- Outputs sorted +EV plays (True% >= 55%) in TXT
- Configurable thresholds and output
- Converts game times to California/Pacific time
"""

import requests
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from itertools import islice
from zoneinfo import ZoneInfo

# ---------- CONFIG ----------
API_KEY = "YOUR_ODDS_API_HERE"
SPORT = "americanfootball_nfl"
LOOKAHEAD_DAYS = 4
ODDS_FORMAT = "american"
DATE_FORMAT = "iso"

SHARP_BOOK = "fanduel"
DFS_BOOKS = ["prizepicks", "underdog"]
BOOKMAKERS = f"{SHARP_BOOK},{','.join(DFS_BOOKS)}"

MARKETS = [
    "player_anytime_td",
    "player_rush_yds",
    "player_rush_reception_yds",
    "player_rush_attempts",
    "player_receptions",
    "player_pass_yds",
    "player_pass_tds",
    "player_pass_completions",
    "player_pass_attempts"
]

ALWAYS_KEEP_DIFF = 0.5
FLAG_THRESHOLD = 1.5
TRUE_PROB_THRESHOLD = 0.55  # Only keep plays with True% >= 55%

OUTPUT_FILE_BASE = "NFL"
OUTPUT_FILE = f"{OUTPUT_FILE_BASE}_{datetime.now().strftime('%Y-%m-%d')}.txt"

BASE_URL = "https://api.the-odds-api.com/v4"
# ----------------------------

def american_to_prob(odds):
    try:
        odds = float(odds)
    except Exception:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return -odds / (-odds + 100.0)

def get_data(url, params):
    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    if response.status_code == 422:
        return None
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None
    try:
        return response.json()
    except Exception as e:
        print(f"Failed parsing JSON: {e}")
        return None

def fetch_events():
    url = f"{BASE_URL}/sports/{SPORT}/events"
    return get_data(url, {"apiKey": API_KEY})

def iso_to_pacific(iso_time):
    utc_time = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    pacific_time = utc_time.astimezone(ZoneInfo("America/Los_Angeles"))
    return pacific_time.strftime("%Y-%m-%d %I:%M %p")

def chunked(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            break
        yield chunk

def process_odds_data(event, odds_data, market_name, all_ev_plays):
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time = event.get("commence_time", "")

    event_payloads = odds_data if isinstance(odds_data, list) else [odds_data]

    for payload in event_payloads:
        bookmakers_data = payload.get("bookmakers", [])
        if not bookmakers_data:
            continue

        sharp_odds = next((b for b in bookmakers_data if b.get("key") == SHARP_BOOK), None)
        if not sharp_odds:
            continue

        for dfs_key in DFS_BOOKS:
            dfs_odds = next((b for b in bookmakers_data if b.get("key") == dfs_key), None)
            if not dfs_odds:
                continue

            sharp_markets = sharp_odds.get("markets", [])
            dfs_markets = dfs_odds.get("markets", [])
            if not sharp_markets or not dfs_markets:
                continue

            sharp_market = next((m for m in sharp_markets if m.get("key") == market_name), None)
            dfs_market = next((m for m in dfs_markets if m.get("key") == market_name), None)
            if not sharp_market or not dfs_market:
                continue

            sharp_by_player = defaultdict(dict)
            for outcome in sharp_market.get("outcomes", []):
                player = outcome.get("description")
                side = outcome.get("name")
                sharp_by_player[player][side] = {"price": outcome.get("price"), "point": outcome.get("point")}

            dfs_by_player = defaultdict(dict)
            for outcome in dfs_market.get("outcomes", []):
                player = outcome.get("description")
                side = outcome.get("name")
                dfs_by_player[player][side] = {"price": outcome.get("price"), "point": outcome.get("point")}

            common_players = set(sharp_by_player.keys()) & set(dfs_by_player.keys())
            for player in common_players:
                sharp_over = sharp_by_player[player].get("Over")
                sharp_under = sharp_by_player[player].get("Under")
                dfs_over = dfs_by_player[player].get("Over")
                dfs_under = dfs_by_player[player].get("Under")

                if not (dfs_over or dfs_under):
                    continue

                sharp_point = (sharp_over.get("point") if sharp_over else None) or (sharp_under.get("point") if sharp_under else None)
                dfs_point = (dfs_over.get("point") if dfs_over else None) or (dfs_under.get("point") if dfs_under else None)
                if sharp_point is None or dfs_point is None:
                    continue

                diff = dfs_point - sharp_point

                # Determine sharp-favored side
                sharp_favored = None
                if sharp_over and sharp_under:
                    sharp_favored = "Over" if sharp_over["price"] < sharp_under["price"] else "Under"
                elif sharp_over:
                    sharp_favored = "Over"
                elif sharp_under:
                    sharp_favored = "Under"

                # Keep play logic
                keep_play = False
                if abs(diff) <= ALWAYS_KEEP_DIFF:
                    keep_play = True
                else:
                    if sharp_favored == "Over" and dfs_point < sharp_point:
                        keep_play = True
                    elif sharp_favored == "Under" and dfs_point > sharp_point:
                        keep_play = True
                if not keep_play:
                    continue

                o_price = sharp_over.get("price") if sharp_over else None
                u_price = sharp_under.get("price") if sharp_under else None
                p_o = american_to_prob(o_price)
                p_u = american_to_prob(u_price)
                if p_o is None or p_u is None or (p_o + p_u) == 0:
                    continue
                true_p_over = p_o / (p_o + p_u)
                ev_over = 2 * true_p_over - 1
                ev_under = 2 * (1 - true_p_over) - 1

                dfs_o_price = dfs_over.get("price") if dfs_over else None
                dfs_u_price = dfs_under.get("price") if dfs_under else None
                dfs_p_over = american_to_prob(dfs_o_price) if dfs_o_price else None
                dfs_p_under = american_to_prob(dfs_u_price) if dfs_u_price else None

                dfs_favored = None
                if dfs_p_over is not None and dfs_p_under is not None:
                    dfs_favored = "Over" if dfs_p_over > dfs_p_under else "Under"
                elif dfs_p_over is not None:
                    dfs_favored = "Over"
                elif dfs_p_under is not None:
                    dfs_favored = "Under"

                flag = "FLAG" if abs(diff) > FLAG_THRESHOLD else ""

                # Always set Side = sharp_favored
                side_to_take = sharp_favored
                true_p_side = true_p_over if side_to_take=="Over" else 1 - true_p_over

                # Only keep plays above TRUE_PROB_THRESHOLD
                if true_p_side < TRUE_PROB_THRESHOLD:
                    continue

                play_common = {
                    "event": f"{away_team} @ {home_team}",
                    "player": player,
                    "market": market_name,
                    "book": dfs_key,
                    "dfs_point": dfs_point,
                    "sharp_point": sharp_point,
                    "dfs_price_over": dfs_o_price,
                    "dfs_price_under": dfs_u_price,
                    "sharp_price_over": o_price,
                    "sharp_price_under": u_price,
                    "dfs_favored": dfs_favored,
                    "sharp_favored": sharp_favored,
                    "diff": diff,
                    "diff_flag": flag,
                    "side": side_to_take,
                    "game_time": iso_to_pacific(commence_time),
                    "ev": ev_over if side_to_take=="Over" else ev_under,
                    "true_p": true_p_side
                }

                all_ev_plays.append(play_common)

def main():
    now = datetime.now(timezone.utc)
    max_date = now + timedelta(days=LOOKAHEAD_DAYS)

    events = fetch_events()
    if not events:
        print("No events found or API error.")
        return

    filtered_events = []
    for e in events:
        try:
            et = datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
        except Exception:
            continue
        if now <= et <= max_date:
            filtered_events.append(e)

    if not filtered_events:
        print(f"No {SPORT} events within the next {LOOKAHEAD_DAYS} days.")
        return

    print(f"Found {len(filtered_events)} upcoming {SPORT.upper()} games (today + next {LOOKAHEAD_DAYS} days).\n")

    all_ev_plays = []

    for event in filtered_events:
        print(f"Processing: {event.get('away_team','')} @ {event.get('home_team','')} ({event.get('commence_time','')})")
        for market_group in chunked(MARKETS, 4):
            markets_param = ",".join(market_group)
            odds_url = f"{BASE_URL}/sports/{SPORT}/events/{event['id']}/odds"
            params = {
                "apiKey": API_KEY,
                "markets": markets_param,
                "bookmakers": BOOKMAKERS,
                "oddsFormat": ODDS_FORMAT,
                "dateFormat": DATE_FORMAT,
            }

            odds_data = get_data(odds_url, params)

            if odds_data is None:
                for single_market in market_group:
                    params["markets"] = single_market
                    odds_data_single = get_data(odds_url, params)
                    if odds_data_single:
                        process_odds_data(event, odds_data_single, single_market, all_ev_plays)
            else:
                for market_name in market_group:
                    process_odds_data(event, odds_data, market_name, all_ev_plays)

    # Sort plays by EV
    all_ev_plays.sort(key=lambda x: x["ev"], reverse=True)
    flagged_plays = [p for p in all_ev_plays if p.get("diff_flag")]
    normal_plays = [p for p in all_ev_plays if not p.get("diff_flag")]

    # --- Write TXT file ---
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        header = (
            f"{'Player':25} {'Market':25} {'Side':6} {'Book':12} "
            f"{'DFS Pt':7} {'Sharp Pt':8} {'DFS Fav':8} {'Sharp Fav':9} {'DFSPrice(O/U)':18} "
            f"{'SharpPrice(O/U)':18} {'EV%':7} {'True%':7} {'Flag':6} {'Game / Time'}\n"
        )
        f.write(header)
        f.write("=" * 180 + "\n")

        for p in flagged_plays + normal_plays:
            dfs_price_pair = f"{p.get('dfs_price_over')}/{p.get('dfs_price_under')}"
            sharp_price_pair = f"{p.get('sharp_price_over')}/{p.get('sharp_price_under')}"
            flag_display = "***" if p.get("diff_flag") else ""
            line = (
                f"{p['player'][:25]:25} {p['market'][:25]:25} {p['side']:6} {p['book']:12} "
                f"{p['dfs_point']:7.1f} {p['sharp_point']:8.1f} {str(p['dfs_favored']):8} {str(p['sharp_favored']):9} "
                f"{dfs_price_pair:18} {sharp_price_pair:18} {p['ev']*100:6.2f}% {p['true_p']*100:6.1f}% {flag_display:6} "
                f"{p['event']} ({p['game_time']})\n"
            )
            f.write(line)

    print()
    print(f"Finished scanning. Total plays: {len(all_ev_plays)}, Flagged plays: {len(flagged_plays)}")
    print(f"TXT report saved as: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

