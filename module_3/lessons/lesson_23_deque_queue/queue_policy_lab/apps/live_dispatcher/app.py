"""
apps/live_dispatcher/app.py — Live Dispatch Room entry point.

Run:  python run_dispatcher.py
  or  cd queue_policy_lab && python -m apps.live_dispatcher.app
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import dash

from apps.live_dispatcher.callbacks import register_callbacks
from apps.live_dispatcher.layout import build_layout

app = dash.Dash(
    __name__,
    title="Live Dispatch Room 🚕",
    assets_folder=str(_ROOT / "assets"),
    suppress_callback_exceptions=True,
    update_title=None,
)

app.layout = build_layout()
register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, port=8551, host="0.0.0.0")
