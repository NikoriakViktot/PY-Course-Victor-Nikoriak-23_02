import pandas as pd
import numpy as np
from functools import lru_cache
from backend.config import config
from backend.utils.logger import get_logger

log = get_logger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────────

def _map_sleep(val: str) -> float:
    """Convert sleep duration text to midpoint hours."""
    mapping = {
        "less than 5 hours": 4.0,
        "5-6 hours": 5.5,
        "7-8 hours": 7.5,
        "more than 8 hours": 9.0,
    }
    if pd.isna(val):
        return np.nan
    return mapping.get(str(val).strip().lower(), np.nan)


def _encode_dietary(val: str) -> int:
    mapping = {"unhealthy": 0, "moderate": 1, "healthy": 2}
    return mapping.get(str(val).strip().lower(), 1)


# ── main loader ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_student_df() -> pd.DataFrame:
    log.info("Loading Student Depression Dataset …")
    df = pd.read_csv(config.STUDENT_DATASET)
    df.columns = df.columns.str.strip()

    # --- basic cleaning ---
    df = df.dropna(subset=["Depression"])
    df["Depression"] = df["Depression"].astype(int)

    # numeric coercion
    for col in ["Academic Pressure", "Work Pressure", "CGPA",
                "Study Satisfaction", "Job Satisfaction",
                "Work/Study Hours", "Financial Stress", "Age"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # categorical encoding
    df["Gender_enc"] = (df["Gender"].str.strip().str.lower() == "female").astype(int)
    df["Family_History_enc"] = (
        df["Family History of Mental Illness"].str.strip().str.lower() == "yes"
    ).astype(int)
    df["Suicidal_enc"] = (
        df["Have you ever had suicidal thoughts ?"].str.strip().str.lower() == "yes"
    ).astype(int)
    df["Dietary_enc"] = df["Dietary Habits"].apply(_encode_dietary)
    df["Sleep_hours"] = df["Sleep Duration"].apply(_map_sleep)

    # --- feature engineering ---
    df["Risk_Score"] = (
        df["Academic Pressure"].fillna(0) * 0.3
        + df["Financial Stress"].fillna(0) * 0.3
        + df["Work/Study Hours"].fillna(0) * 0.2
        - df["Sleep_hours"].fillna(7) * 0.2
    )
    df["Pressure_Sum"] = (
        df["Academic Pressure"].fillna(0) + df["Work Pressure"].fillna(0)
    )
    df["Satisfaction_Sum"] = (
        df["Study Satisfaction"].fillna(0) + df["Job Satisfaction"].fillna(0)
    )
    df["Sleep_deficit"] = np.maximum(0, 7.0 - df["Sleep_hours"].fillna(7))

    log.info("Student dataset loaded: %d rows, %d cols", len(df), len(df.columns))
    return df


@lru_cache(maxsize=1)
def load_sleep_df() -> pd.DataFrame:
    log.info("Loading Sleep Health Dataset …")
    df = pd.read_csv(config.SLEEP_DATASET)
    df.columns = df.columns.str.strip()
    return df


@lru_cache(maxsize=1)
def load_burnout_df() -> pd.DataFrame:
    log.info("Loading Burnout Tech Dataset …")
    df = pd.read_csv(config.BURNOUT_DATASET)
    df.columns = df.columns.str.strip()
    return df
