import os
import yaml

# ------------------------
# Base directory (project root)
# ------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load config
CONFIG_FILE = os.path.join(BASE_DIR, 'config.yml')
with open(CONFIG_FILE, 'r') as f:
    cfg = yaml.safe_load(f)

# ------------------------
# Raw data
# ------------------------
RAW_GAMES = os.path.join(BASE_DIR, cfg['raw_games'])
RAW_GAMES_BACKUP = os.path.join(BASE_DIR, cfg['raw_games_backup'])
RAW_LINEUPS_MASTER = os.path.join(BASE_DIR, cfg['raw_lineups_master'])
RAW_ROSTERS = os.path.join(BASE_DIR, cfg['raw_rosters'])
RAW_SCHEDULE = os.path.join(BASE_DIR, cfg['raw_schedule'])
FAILED_PLAYERS = os.path.join(BASE_DIR, cfg['failed_players'])

# ------------------------
# Processed data
# ------------------------
PROCESSED_DIR = os.path.join(BASE_DIR, cfg['processed_dir'])
PROCESSED_TRAINING_PTS = os.path.join(BASE_DIR, cfg['processed_training_pts'])
PROCESSED_TRAINING_WITH_MIN_PRED = os.path.join(BASE_DIR, cfg['processed_training_with_min_pred'])
PROCESSED_TRAINING_ALL = os.path.join(BASE_DIR, cfg['processed_training_all'])
PROCESSED_TRAINING_MINS = os.path.join(BASE_DIR, cfg['processed_training_mins'])
PROCESSED_OOF = os.path.join(BASE_DIR, cfg['processed_oof'])
PROCESSED_FEATURE_IMPORTANCE_DIR = os.path.join(BASE_DIR, cfg['processed_feature_importance_dir'])
PROCESSED_FEATURE_IMPORTANCE_ARCHIVE = os.path.join(BASE_DIR, cfg['processed_feature_importance_archive'])

# ------------------------
# Models
# ------------------------
PTS_MODEL_EXP = os.path.join(BASE_DIR, cfg['pts_model_exp'])
PTS_MODEL_NEW_DATA = os.path.join(BASE_DIR, cfg['pts_model_new_data'])
PTS_MODEL_STABLE = os.path.join(BASE_DIR, cfg['pts_model_stable'])

REB_MODEL_EXP = os.path.join(BASE_DIR, cfg['reb_model_exp'])
REB_MODEL_STABLE = os.path.join(BASE_DIR, cfg['reb_model_stable'])

AST_MODEL_EXP = os.path.join(BASE_DIR, cfg['ast_model_exp'])
AST_MODEL_STABLE = os.path.join(BASE_DIR, cfg['ast_model_stable'])

FG3M_MODEL_EXP = os.path.join(BASE_DIR, cfg['fg3m_model_exp'])
FG3M_MODEL_STABLE = os.path.join(BASE_DIR, cfg['fg3m_model_stable'])

MINS_HUBER_MODEL = os.path.join(BASE_DIR, cfg['mins_huber_model'])

# ------------------------
# Prediction outputs
# ------------------------
PREDICT_AST_STABLE = os.path.join(BASE_DIR, cfg['predict_ast_stable'])
PREDICT_AST_EXP = os.path.join(BASE_DIR, cfg['predict_ast_exp'])

PREDICT_PTS_STABLE = os.path.join(BASE_DIR, cfg['predict_pts_stable'])
PREDICT_PTS_EXP = os.path.join(BASE_DIR, cfg['predict_pts_exp'])
PREDICT_PTS_NEW_DATA = os.path.join(BASE_DIR, cfg['predict_pts_new_data'])

PREDICT_REB_STABLE = os.path.join(BASE_DIR, cfg['predict_reb_stable'])
PREDICT_REB_EXP = os.path.join(BASE_DIR, cfg['predict_reb_exp'])

PREDICT_FG3M_STABLE = os.path.join(BASE_DIR, cfg['predict_fg3m_stable'])
PREDICT_FG3M_EXP = os.path.join(BASE_DIR, cfg['predict_fg3m_exp'])

PREDICT_MINS = os.path.join(BASE_DIR, cfg['predict_mins'])

PREDICT_MERGED_STABLE = os.path.join(BASE_DIR, cfg['predict_merged_stable'])
