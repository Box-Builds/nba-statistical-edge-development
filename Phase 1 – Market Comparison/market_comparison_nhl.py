import requests
from collections import defaultdict
from datetime import datetime

# --- Helper functions ---
def american_to_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)

def fmt_time(iso_str):
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return iso_str

def get_data(url, params):
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None
    return response.json()

# --- Configuration ---
api_key = "YOUR_ODDS_API_HERE"
base_url = 'https://api.the-odds-api.com/v4'
sport = 'icehockey_nhl'
odds_format = 'american'
date_format = 'iso'

TRUE_P_THRESHOLD = 0.55  # Minimum true probability to keep a bet

# ✅ Fixed NHL prop markets
prop_markets = (
    'player_points,player_assists,player_power_play_points,'
    'player_goals,player_shots_on_goal,player_blocked_shots,player_total_saves'
)

sharp_book = 'pinnacle'
dfs_books = ['prizepicks', 'underdog']
bookmakers = f"{sharp_book},{','.join(dfs_books)}"

# --- Collect events ---
events_url = f"{base_url}/sports/{sport}/events"
params = {'apiKey': api_key}
events = get_data(events_url, params)

if not events:
    print("No events found for the sport.")
    exit()

all_ev_plays = []

# --- Process each event ---
for event in events:
    event_id = event['id']
    home_team = event['home_team']
    away_team = event['away_team']
    commence_time = event['commence_time']

    odds_url = f"{base_url}/sports/{sport}/events/{event_id}/odds"
    params = {
        'apiKey': api_key,
        'markets': prop_markets,
        'bookmakers': bookmakers,
        'oddsFormat': odds_format,
        'dateFormat': date_format,
    }
    odds_data = get_data(odds_url, params)
    if not odds_data:
        continue

    if isinstance(odds_data, dict):
        bookmakers_data = odds_data.get('bookmakers', [])
    elif isinstance(odds_data, list) and len(odds_data) > 0:
        bookmakers_data = odds_data[0].get('bookmakers', [])
    else:
        continue

    sharp_odds = next((b for b in bookmakers_data if b['key'] == sharp_book), None)
    if not sharp_odds:
        continue

    for dfs_key in dfs_books:
        dfs_odds = next((b for b in bookmakers_data if b['key'] == dfs_key), None)
        if not dfs_odds:
            continue

        for market in sharp_odds.get('markets', []):
            market_key = market['key']
            dfs_market = next((m for m in dfs_odds.get('markets', []) if m['key'] == market_key), None)
            if not dfs_market:
                continue

            sharp_by_player = defaultdict(dict)
            for outcome in market['outcomes']:
                player = outcome['description']
                side = outcome['name']
                sharp_by_player[player][side] = {'price': outcome['price'], 'point': outcome['point']}

            dfs_by_player = defaultdict(dict)
            for outcome in dfs_market['outcomes']:
                player = outcome['description']
                side = outcome['name']
                dfs_by_player[player][side] = {'price': outcome['price'], 'point': outcome['point']}

            for player in set(sharp_by_player.keys()) & set(dfs_by_player.keys()):
                sharp_over = sharp_by_player[player].get('Over')
                sharp_under = sharp_by_player[player].get('Under')
                dfs_over = dfs_by_player[player].get('Over')
                dfs_under = dfs_by_player[player].get('Under')

                # Only include if DFS has both Over and Under
                if not (sharp_over and sharp_under and dfs_over and dfs_under):
                    continue

                sharp_point = sharp_over['point']
                dfs_over_point = dfs_over['point']
                dfs_under_point = dfs_under['point']

                if sharp_point is None or dfs_over_point is None or dfs_under_point is None:
                    continue

                # --- Calculate Pinnacle implied probability ---
                o_price, u_price = sharp_over['price'], sharp_under['price']
                p_o, p_u = american_to_prob(o_price), american_to_prob(u_price)
                total = p_o + p_u
                true_p_over = p_o / total

                # --- Calculate EV for DFS line ---
                ev_over = 2 * true_p_over - 1
                ev_under = 2 * (1 - true_p_over) - 1

                # Keep only the best side if true probability >= threshold
                if true_p_over >= TRUE_P_THRESHOLD and ev_over >= ev_under:
                    all_ev_plays.append({
                        'event': f"{away_team} @ {home_team}",
                        'player': player,
                        'market': market_key,
                        'side': 'Over',
                        'book': dfs_key,
                        'line': dfs_over_point,
                        'ev': ev_over,
                        'sharp_odds': f"o{o_price}/u{u_price}",
                        'true_p': true_p_over,
                        'game_time': fmt_time(commence_time)
                    })
                elif (1 - true_p_over) >= TRUE_P_THRESHOLD and ev_under > ev_over:
                    all_ev_plays.append({
                        'event': f"{away_team} @ {home_team}",
                        'player': player,
                        'market': market_key,
                        'side': 'Under',
                        'book': dfs_key,
                        'line': dfs_under_point,
                        'ev': ev_under,
                        'sharp_odds': f"o{o_price}/u{u_price}",
                        'true_p': 1 - true_p_over,
                        'game_time': fmt_time(commence_time)
                    })

# --- Sort by EV descending ---
all_ev_plays.sort(key=lambda x: x['ev'], reverse=True)

# --- Write to plain text file ---
output_file = 'nhl+ev_best_side.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    header = f"{'Player':25} {'Market':15} {'Side':6} {'Book':12} {'Line':6} {'EV':7} {'TrueProb':9} {'Game / Time'}\n"
    f.write(header)
    f.write("="*100 + "\n")
    for play in all_ev_plays:
        line = f"{play['player'][:25]:25} {play['market'][:15]:15} {play['side']:6} {play['book']:12} {str(play['line']):6} {play['ev']*100:6.2f}% {play['true_p']*100:8.1f}% {play['event']} ({play['game_time']})\n"
        f.write(line)

print(f"\n✅ Report saved as: {output_file}")
