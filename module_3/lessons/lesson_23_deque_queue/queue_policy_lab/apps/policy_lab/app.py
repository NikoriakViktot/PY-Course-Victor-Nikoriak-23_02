"""
apps/policy_lab/app.py — Policy Analysis Lab entry point.

Run:  python run_policy_lab.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import dash

from apps.policy_lab.callbacks import register_callbacks
from apps.policy_lab.layout import build_layout

app = dash.Dash(
    __name__,
    title="Policy Analysis Lab 📊",
    assets_folder=str(_ROOT / "assets"),
    suppress_callback_exceptions=True,
    update_title=None,
)

app.layout = build_layout()
register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, port=8552, host="0.0.0.0")
