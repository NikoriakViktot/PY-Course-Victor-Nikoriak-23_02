import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    # Paths — data lives one level up from the project root (next to depression_dashboard/)
    DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR.parent / "data")))
    MODELS_DIR = BASE_DIR / "models"

    # Datasets
    STUDENT_DATASET = DATA_DIR / "Student Depression Dataset.csv"
    SLEEP_DATASET = DATA_DIR / "Sleep_health_and_lifestyle_dataset.csv"
    BURNOUT_DATASET = DATA_DIR / "mental_health_burnout_tech_2026.csv"

    # Flask
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5050))

    # ML
    RANDOM_STATE = 42
    TEST_SIZE = 0.2
    N_CLUSTERS = 4
    CONTAMINATION = 0.05          # IsolationForest outlier fraction

    # Streamlit backend URL
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5050")

config = Config()
