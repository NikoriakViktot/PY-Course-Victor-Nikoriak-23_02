import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from backend.config import config
from backend.services.data_service import load_student_df
from backend.utils.logger import get_logger

log = get_logger(__name__)

FEATURES = [
    "Age", "Academic Pressure", "Work Pressure",
    "Study Satisfaction", "Job Satisfaction",
    "Sleep_hours", "Work/Study Hours", "Financial Stress",
    "Gender_enc", "Family_History_enc", "Suicidal_enc", "Dietary_enc",
    "Risk_Score", "Pressure_Sum", "Satisfaction_Sum", "Sleep_deficit",
]
TARGET = "Depression"

MODEL_PATH = config.MODELS_DIR / "classifier.pkl"
CLUSTER_PATH = config.MODELS_DIR / "kmeans.pkl"
ANOMALY_PATH = config.MODELS_DIR / "isolation_forest.pkl"
SCALER_PATH = config.MODELS_DIR / "scaler.pkl"


def _ensure_models_dir():
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── Training ─────────────────────────────────────────────────────────────────

def train_all() -> dict:
    df = load_student_df()
    X = df[FEATURES].copy()
    y = df[TARGET]

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_imp = imputer.fit_transform(X)
    X_scaled = scaler.fit_transform(X_imp)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE, stratify=y,
    )

    # --- Classifier ---
    clf = RandomForestClassifier(
        n_estimators=200, max_depth=12,
        random_state=config.RANDOM_STATE, n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    report = classification_report(y_test, y_pred, output_dict=True)
    auc = roc_auc_score(y_test, y_prob)
    log.info("Classifier AUC=%.4f | Acc=%.4f", auc, report["accuracy"])

    # --- KMeans clustering ---
    kmeans = KMeans(
        n_clusters=config.N_CLUSTERS,
        random_state=config.RANDOM_STATE, n_init=10,
    )
    kmeans.fit(X_scaled)

    # --- IsolationForest ---
    iso = IsolationForest(
        contamination=config.CONTAMINATION,
        random_state=config.RANDOM_STATE,
    )
    iso.fit(X_scaled)

    _ensure_models_dir()
    artifacts = {
        "imputer": imputer,
        "scaler": scaler,
        "classifier": clf,
        "kmeans": kmeans,
        "isolation_forest": iso,
        "features": FEATURES,
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(artifacts, f)

    log.info("All models saved to %s", config.MODELS_DIR)
    return {
        "auc": round(auc, 4),
        "accuracy": round(report["accuracy"], 4),
        "f1_depressed": round(report["1"]["f1-score"], 4),
        "feature_importance": dict(zip(FEATURES, clf.feature_importances_.tolist())),
    }


def _load_artifacts() -> dict:
    if not MODEL_PATH.exists():
        log.info("No saved models found — training now …")
        train_all()
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


# ── Inference ─────────────────────────────────────────────────────────────────

def predict_depression(input_data: dict) -> dict:
    arts = _load_artifacts()
    row = pd.DataFrame([input_data])[arts["features"]]
    X_imp = arts["imputer"].transform(row)
    X_scaled = arts["scaler"].transform(X_imp)
    prob = arts["classifier"].predict_proba(X_scaled)[0]
    label = int(arts["classifier"].predict(X_scaled)[0])
    return {
        "prediction": label,
        "probability_depressed": round(float(prob[1]), 4),
        "probability_not_depressed": round(float(prob[0]), 4),
        "risk_level": _risk_label(prob[1]),
    }


def _risk_label(prob: float) -> str:
    if prob >= 0.75:
        return "High"
    if prob >= 0.5:
        return "Medium"
    return "Low"


# ── Clustering ────────────────────────────────────────────────────────────────

def get_clusters() -> dict:
    arts = _load_artifacts()
    df = load_student_df()
    X = df[arts["features"]].copy()
    X_imp = arts["imputer"].transform(X)
    X_scaled = arts["scaler"].transform(X_imp)

    labels = arts["kmeans"].predict(X_scaled)

    pca = PCA(n_components=2, random_state=config.RANDOM_STATE)
    coords = pca.fit_transform(X_scaled)

    result_df = df[["Age", "Depression", "Risk_Score", "Sleep_hours",
                     "Financial Stress", "Academic Pressure"]].copy()
    result_df["cluster"] = labels
    result_df["pca_x"] = coords[:, 0]
    result_df["pca_y"] = coords[:, 1]

    cluster_profiles = (
        result_df.groupby("cluster")[
            ["Age", "Risk_Score", "Sleep_hours", "Financial Stress",
             "Academic Pressure", "Depression"]
        ]
        .mean()
        .round(3)
        .to_dict(orient="index")
    )

    return {
        "points": result_df[["pca_x", "pca_y", "cluster", "Depression",
                              "Risk_Score", "Age"]].to_dict(orient="records"),
        "cluster_profiles": cluster_profiles,
        "n_clusters": config.N_CLUSTERS,
        "explained_variance": round(float(pca.explained_variance_ratio_.sum()), 4),
    }


# ── Anomaly Detection ─────────────────────────────────────────────────────────

def get_anomalies() -> dict:
    arts = _load_artifacts()
    df = load_student_df()
    X = df[arts["features"]].copy()
    X_imp = arts["imputer"].transform(X)
    X_scaled = arts["scaler"].transform(X_imp)

    scores = arts["isolation_forest"].decision_function(X_scaled)
    preds = arts["isolation_forest"].predict(X_scaled)   # -1 = anomaly

    result_df = df[["Age", "Depression", "Risk_Score", "Sleep_hours",
                     "Financial Stress", "Academic Pressure", "Gender"]].copy()
    result_df["anomaly_score"] = scores
    result_df["is_anomaly"] = (preds == -1).astype(int)

    anomalies = result_df[result_df["is_anomaly"] == 1].copy()
    return {
        "total_anomalies": int(anomalies["is_anomaly"].sum()),
        "anomaly_rate": round(float((preds == -1).mean()) * 100, 2),
        "anomalies": anomalies.head(200).to_dict(orient="records"),
        "depression_in_anomalies": round(float(anomalies["Depression"].mean()), 4),
    }


# ── Feature importance ────────────────────────────────────────────────────────

def get_feature_importance() -> dict:
    arts = _load_artifacts()
    clf = arts["classifier"]
    importance = dict(zip(arts["features"], clf.feature_importances_.tolist()))
    return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
