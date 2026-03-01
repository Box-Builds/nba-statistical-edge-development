import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os

# ---- CONFIG ----
SCRIPT_ORDER = [
    "scripts/process/nba_ai_training_data.py",
    "scripts/process/mins_training_data.py",
    "scripts/model/build_mins_model_huber.py",
    "scripts/predict/predict_mins_model.py",
    "scripts/process/merge_pred_mins_training_data.py",
    "scripts/process/pts_training_data.py",
    "scripts/model/lgbm_reb_model_exp.py",
    "scripts/model/lgbm_reb_model_stable.py",
    "scripts/model/lgbm_pts_model_exp.py",
    "scripts/model/lgbm_pts_model_stable.py",
    "scripts/model/lgbm_ast_model_exp.py",
    "scripts/model/lgbm_ast_model_stable.py",
    "scripts/model/lgbm_pts_model_new_training_data.py",
    "scripts/model/lgbm_fg3m_model_stable.py",
    "scripts/model/lgbm_fg3m_model_exp.py",
    "scripts/predict/predict_reb_model_exp.py",
    "scripts/predict/predict_reb_model_stable.py",
    "scripts/predict/predict_pts_model_exp.py",
    "scripts/predict/predict_pts_model_stable.py",
    "scripts/predict/predict_ast_model_exp.py",
    "scripts/predict/predict_ast_model_stable.py",
    "scripts/predict/predict_pts_model_new_data.py",
    "scripts/predict/predict_fg3m_model_stable.py",
    "scripts/predict/predict_fg3m_model_exp.py",
    "scripts/process/merge_latest_stable_predictions.py",
]

LOG_FILE = Path("master_pipeline_log.txt")

# ---- FUNCTIONS ----
def log(message):
    """Log to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} | {message}", flush=True)  # flush ensures immediate print in GitHub Actions
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")

def run_script(script_path):
    """Run a Python script in a subprocess and stream output live."""
    log(f"➡️ Starting {script_path}")
    start_time = datetime.now()

    # Use Popen for real-time streaming
    process = subprocess.Popen(
        [sys.executable, "-u", str(script_path)], # Use -u for unbuffered child output
        cwd=Path(__file__).parent,
        # Ensure the current directory is on the Python path for imports
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parent)}, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # Merge stderr into stdout for simple reading
        text=True # Decode output as text
    )

    # Read output line by line and print it immediately
    output = []
    for line in process.stdout:
        # Print line immediately to the main console log
        print(line, end="", flush=True) 
        output.append(line)
        
    process.wait() # Wait for the subprocess to finish
    result_code = process.returncode
    
    duration = (datetime.now() - start_time).total_seconds()

    if result_code == 0:
        log(f"✅ Finished {script_path} in {duration:.2f}s")
        return True, duration
    else:
        log(f"❌ Script {script_path} failed with code {result_code} after {duration:.2f}s")
        # Log the last few lines of output for context in the master log
        log(f"--- Subprocess Error Output (Last 10 lines) ---")
        log("".join(output[-10:]))
        log("-----------------------------")
        return False, duration


# ---- MAIN ----
if __name__ == "__main__":
    LOG_FILE.unlink(missing_ok=True)  # Clear old log

    summary = []
    for script in SCRIPT_ORDER:
        script_path = Path(script)
        if not script_path.exists():
            log(f"❌ Script not found: {script_path}. Stopping master run.")
            break

        success, duration = run_script(script_path)
        summary.append((script, success, duration))
        if not success:
            log("❌ Stopping master run due to error.")
            break

    # ---- SUMMARY ----
    log("\n🎯 Master pipeline run summary:")
    for s, success, duration in summary:
        status = "✅" if success else "❌"
        log(f"{status} {s} ({duration:.2f}s)")

    log("🎉 Master pipeline finished.")
