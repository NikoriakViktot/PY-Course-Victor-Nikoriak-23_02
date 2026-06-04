"""Entry point for the Flask backend.

Run from the depression_dashboard/ directory:
    python run_backend.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app import create_app
from backend.config import config
from backend.services.ml_service import train_all

if __name__ == "__main__":
    # auto-train if no saved model exists
    model_path = config.MODELS_DIR / "classifier.pkl"
    if not model_path.exists():
        print("No saved model found — training now (may take ~30s)…")
        metrics = train_all()
        print(f"Training done: AUC={metrics['auc']}")

    app = create_app()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
