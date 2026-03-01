import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path

MASTER_CSV = "data/raw/nba_player_game_stats_full.csv"
CACHE_FILE = "lambda_cache.json"

if not Path(MASTER_CSV).exists():
    st.error(
        "Missing data file: data/raw/nba_player_game_stats_full.csv\n\n"
        "This app does not ship NBA data.\n\n"
        "Generate it in Phase 2, then copy it here:\n"
        "1) In Phase 2: run `python run_local_fetch.py`\n"
        "2) Copy Phase 2's data/raw/nba_player_game_stats_full.csv\n"
        "   into Phase 3's data/raw/\n\n"
        "Then restart this Streamlit app."
    )
    st.stop()

# Load master data
df = pd.read_csv(MASTER_CSV, low_memory=False)
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
df.columns = [c.upper() for c in df.columns]

# Correct NBA season labeling
def get_nba_season(date):
    if pd.isna(date):
        return np.nan
    return date.year + 1 if date.month >= 10 else date.year

df['SEASON'] = df['GAME_DATE'].apply(get_nba_season)

# Load or initialize λ cache
try:
    with open(CACHE_FILE, "r") as f:
        lambda_cache = json.load(f)
except FileNotFoundError:
    lambda_cache = {}

# ---- Helper functions ----
def get_relevant_stats(stat_name):
    stat_name = stat_name.upper()
    mapping = {
        'PTS': ['TS%', 'eFG%', 'USG%', 'TOV%'],
        'REB': ['USG%', 'PER'],
        'AST': ['AST%', 'USG%', 'TOV%'],
        'TOV': ['TOV%', 'USG%'],
        'STL': ['PER'],
        'BLK': ['PER'],
        'FG3M': [],
    }
    return mapping.get(stat_name, [])

def get_stat_series(data, stat):
    """Return a Series of stat values, handling combo stats like 'PTS+REB'."""
    stat = stat.upper()
    if '+' in stat:
        cols = [s.strip().upper() for s in stat.split('+')]
        return data[cols].sum(axis=1).fillna(0)
    else:
        return data[stat].fillna(0)

# ---- Lambda tuning ----
def tune_lambda(player_data, stat, lambdas=np.linspace(0.01, 0.3, 30)):
    player_data = player_data[player_data['MIN'] > 0].sort_values('GAME_DATE')
    if player_data.empty:
        return None, None

    today = pd.Timestamp.today()
    player_data['DAYS_AGO'] = (today - player_data['GAME_DATE']).dt.days

    best_lambda, best_score = None, float('inf')

    for l in lambdas:
        preds, actuals = [], []
        for idx, row in player_data.iterrows():
            prev_games = player_data[player_data['GAME_DATE'] < row['GAME_DATE']]
            if len(prev_games) == 0:
                continue

            weights = np.exp(-l * prev_games['DAYS_AGO']) * prev_games['MIN']
            for adv_stat in get_relevant_stats(stat):
                if adv_stat in prev_games.columns:
                    prev_games[adv_stat] = prev_games[adv_stat].fillna(1.0)
                    if adv_stat == 'TOV%':
                        weights *= 1 / (prev_games[adv_stat] + 1e-5)
                    else:
                        weights *= prev_games[adv_stat]

            prev_stat_values = get_stat_series(prev_games, stat)
            pred_value = (prev_stat_values * weights).sum() / weights.sum()
            preds.append(pred_value)

            actual_value = get_stat_series(pd.DataFrame([row]), stat).iloc[0]
            actuals.append(actual_value)

        if len(preds) == 0:
            continue
        mae = np.mean(np.abs(np.array(preds) - np.array(actuals)))
        if mae < best_score:
            best_score = mae
            best_lambda = l
    return best_lambda, best_score

def get_lambda(player_name, stat, player_data):
    key = f"{player_name.lower()}_{stat.upper()}"
    cached = lambda_cache.get(key)
    latest_game_date = player_data['GAME_DATE'].max()
    recalc_needed = cached is None or pd.to_datetime(cached['last_game_date']) < latest_game_date

    if recalc_needed:
        lambda_decay, score = tune_lambda(player_data, stat)
        if lambda_decay is None:
            lambda_decay = 0.1
        lambda_cache[key] = {
            'lambda': lambda_decay,
            'last_game_date': latest_game_date.strftime('%Y-%m-%d')
        }
        with open(CACHE_FILE, "w") as f:
            json.dump(lambda_cache, f)
    else:
        lambda_decay = cached['lambda']
        score = None
    return lambda_decay, score

# ---- Hit rate + Avg MIN functions ----
def compute_hit_rate_stats(data, stat, line, last_n=None):
    """Compute hit rate stats (Over/Under/Push, Avg MIN, total games) for a player/stat."""
    if last_n is not None:
        data = data.tail(last_n)
    total_games = len(data)
    if total_games == 0:
        return ["N/A"] * 5

    values = get_stat_series(data, stat)

    over_count = (values > line).sum()
    under_count = (values < line).sum()
    push_count = (values == line).sum()

    over_text = f"Over {over_count / total_games * 100:5.2f}% ({over_count})"
    under_text = f"Under {under_count / total_games * 100:5.2f}% ({under_count})"
    push_text = f"Push {push_count / total_games * 100:5.2f}% ({push_count})"
    avg_min_text = f"Avg MIN {data['MIN'].mean():4.1f}"

    return [over_text, under_text, push_text, avg_min_text, f"({total_games} games)"]

def format_hit_rate_table(player_data, stat, line):
    """Format hit rate stats as a table for last 5,10,25 games, per season, and full dataset."""
    rows = []

    # Last N games
    for n in [5, 10, 25]:
        label = f"Last {n:>2} Games:"
        row = [label] + compute_hit_rate_stats(player_data, stat, line, last_n=n)
        rows.append(row)

    # Per season
    seasons = sorted(player_data['SEASON'].dropna().unique())
    for season in seasons:
        label = f"{season-1}-{season}:"
        season_data = player_data[player_data['SEASON']==season]
        row = [label] + compute_hit_rate_stats(season_data, stat, line)
        rows.append(row)

    # Full dataset
    label = "Full Dataset:"
    row = [label] + compute_hit_rate_stats(player_data, stat, line)
    rows.append(row)

    # Compute max widths for each column
    col_widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]

    # Build formatted lines
    formatted_lines = []
    for r in rows:
        line = " | ".join(str(r[i]).ljust(col_widths[i]) for i in range(len(r)))
        formatted_lines.append(line)

    return "\n".join(formatted_lines)

# ---- Advanced weighted OU ----
def advanced_weighted_ou(player_name, stat, line):
    stat_upper = stat.upper()
    player_data = df[(df['PLAYER_NAME'].str.lower() == player_name.lower()) & (df['MIN'] > 0)].copy()
    if player_data.empty:
        return f"No data found for player: {player_name}"

    lambda_decay, score = get_lambda(player_name, stat_upper, player_data)
    score_info = f"(MAE: {score:.3f})" if score is not None else "(cached λ)"

    today = pd.Timestamp.today()
    player_data.sort_values('GAME_DATE', inplace=True)
    player_data['DAYS_AGO'] = (today - player_data['GAME_DATE']).dt.days

    # Weighted projection
    player_data['WEIGHT'] = np.exp(-lambda_decay * player_data['DAYS_AGO']) * player_data['MIN']
    for adv_stat in get_relevant_stats(stat_upper):
        if adv_stat in player_data.columns:
            player_data[adv_stat] = player_data[adv_stat].fillna(1.0)
            if adv_stat == 'TOV%':
                player_data['WEIGHT'] *= 1 / (player_data[adv_stat] + 1e-5)
            else:
                player_data['WEIGHT'] *= player_data[adv_stat]

    weighted_stat = (get_stat_series(player_data, stat_upper) * player_data['WEIGHT']).sum() / player_data['WEIGHT'].sum()

    output = []
    output.append(f"Using λ = {lambda_decay:.3f} {score_info} for {stat_upper}")
    output.append(f"{player_name} - {stat_upper} vs line {line}")
    output.append(f"Weighted {stat_upper} projection (Experimental): {weighted_stat:.2f}\n")

    # Add formatted hit rate table
    output.append(format_hit_rate_table(player_data, stat_upper, line))

    return "\n".join(output)

# ---- Streamlit UI ----
st.title("NBA Advanced Weighted Over/Under Calculator")

player_names = sorted(df['PLAYER_NAME'].dropna().unique())
player_input = st.text_input("Player Name")

matching_players = [p for p in player_names if player_input.lower() in p.lower()] if player_input else player_names
selected_player = st.selectbox("Select Player (or type full name above)", matching_players)

if player_input.strip() in player_names:
    selected_player = player_input.strip()

stat_options = ['PTS', 'REB', 'AST', 'TOV', 'STL', 'BLK', 'FG3M', 'PTS+REB', 'PTS+AST', 'AST+REB', 'PTS+REB+AST']
stat = st.selectbox("Stat", stat_options)

line = st.number_input("Line", value=0.0, format="%.1f")

if st.button("Calculate"):
    if selected_player.strip() and stat.strip() and line > 0:
        result = advanced_weighted_ou(selected_player.strip(), stat.strip().upper(), line)
        st.text_area("Results", value=result, height=500)
    else:
        st.warning("Please enter valid inputs for all fields.")