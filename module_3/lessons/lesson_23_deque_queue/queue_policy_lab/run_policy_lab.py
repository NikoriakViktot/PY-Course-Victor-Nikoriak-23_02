"""
run_policy_lab.py — Launch the Policy Analysis Lab.

Usage:
    cd queue_policy_lab
    python run_policy_lab.py

Opens: http://localhost:8552
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apps.policy_lab.app import app

if __name__ == "__main__":
    print("📊 Starting Policy Analysis Lab on http://localhost:8552")
    app.run(debug=False, port=8552, host="0.0.0.0")
