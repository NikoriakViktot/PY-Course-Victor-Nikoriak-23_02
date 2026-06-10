"""
run_dispatcher.py — Launch the Live Dispatch Room.

Usage:
    cd queue_policy_lab
    python run_dispatcher.py

Opens: http://localhost:8551
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apps.live_dispatcher.app import app

if __name__ == "__main__":
    print("🚕 Starting Live Dispatch Room on http://localhost:8551")
    app.run(debug=False, port=8551, host="0.0.0.0")
