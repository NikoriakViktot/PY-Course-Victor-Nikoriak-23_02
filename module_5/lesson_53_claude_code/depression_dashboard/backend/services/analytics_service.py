import pandas as pd
import numpy as np
from backend.services.data_service import load_student_df, load_burnout_df
from backend.utils.logger import get_logger

log = get_logger(__name__)

NUMERIC_FEATURES = [
    "Age", "Academic Pressure", "Work Pressure", "CGPA",
    "Study Satisfaction", "Job Satisfaction", "Sleep_hours",
    "Work/Study Hours", "Financial Stress", "Risk_Score",
    "Pressure_Sum", "Satisfaction_Sum", "Sleep_deficit",
]


def get_summary() -> dict:
    df = load_student_df()
    dep_counts = df["Depression"].value_counts().to_dict()
    return {
        "total_records": int(len(df)),
        "depression_yes": int(dep_counts.get(1, 0)),
        "depression_no": int(dep_counts.get(0, 0)),
        "depression_rate": round(dep_counts.get(1, 0) / len(df) * 100, 2),
        "avg_age": round(df["Age"].mean(), 1),
        "avg_sleep_hours": round(df["Sleep_hours"].mean(), 2),
        "avg_financial_stress": round(df["Financial Stress"].mean(), 2),
        "gender_distribution": df["Gender"].value_counts().to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "feature_stats": df[NUMERIC_FEATURES].describe().round(3).to_dict(),
    }


def get_correlations() -> dict:
    df = load_student_df()
    cols = NUMERIC_FEATURES + ["Depression"]
    corr_matrix = df[cols].corr().round(3)
    dep_corr = (
        corr_matrix["Depression"]
        .drop("Depression")
        .sort_values(key=abs, ascending=False)
        .to_dict()
    )
    return {
        "matrix": corr_matrix.to_dict(),
        "with_depression": dep_corr,
        "features": cols,
    }


def get_depression_by_group() -> dict:
    df = load_student_df()
    result = {}

    # by sleep
    result["by_sleep"] = (
        df.groupby("Sleep Duration")["Depression"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "rate", "count": "n"})
        .round(3)
        .to_dict(orient="index")
    )

    # by dietary habits
    result["by_diet"] = (
        df.groupby("Dietary Habits")["Depression"]
        .mean()
        .round(3)
        .to_dict()
    )

    # by financial stress bucket
    df["fin_stress_bucket"] = pd.cut(
        df["Financial Stress"], bins=[0, 2, 3, 4, 5], labels=["Low", "Medium", "High", "Very High"]
    )
    result["by_financial_stress"] = (
        df.groupby("fin_stress_bucket", observed=True)["Depression"]
        .mean()
        .round(3)
        .to_dict()
    )

    # by gender
    result["by_gender"] = (
        df.groupby("Gender")["Depression"]
        .mean()
        .round(3)
        .to_dict()
    )

    return result


def get_burnout_phq9_distribution() -> dict:
    df = load_burnout_df()
    return {
        "phq9_category_counts": df["phq9_category"].value_counts().to_dict(),
        "gad7_category_counts": df["gad7_category"].value_counts().to_dict(),
        "burnout_level_counts": df["burnout_level"].value_counts().to_dict(),
        "avg_phq9": round(df["phq9_score"].mean(), 2),
        "avg_gad7": round(df["gad7_score"].mean(), 2),
        "avg_burnout": round(df["burnout_score"].mean(), 2),
    }
