#!/usr/bin/env python3
"""
Phase 2 – Local Data Fetch Runner

Runs the fetch/update scripts in a safe order from the Phase 2 project root.

Usage:
  pip install -r requirements_pipeline.txt
  python run_local_fetch.py
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    ("Schedule builder", ROOT / "scripts" / "fetch" / "schedule_2025-26.py"),
    ("Roster updater",   ROOT / "scripts" / "fetch" / "Roster.py"),
    ("Games updater",    ROOT / "scripts" / "fetch" / "NBA_Games_Updater.py"),
]

def run_step(label: str, script_path: Path) -> None:
    if not script_path.exists():
        raise FileNotFoundError(f"{label} script not found: {script_path}")

    print(f"\n▶ {label}")
    print(f"  -> {script_path.relative_to(ROOT)}")

    result = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT))
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit code {result.returncode})")

def main() -> None:
    os.chdir(ROOT)
    (ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)

    print("✅ Phase 2 local fetch runner")
    print(f"   Root: {ROOT}")

    for label, script_path in SCRIPTS:
        run_step(label, script_path)

    print("\n✅ Done. Generated files should now exist under data/raw/")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)