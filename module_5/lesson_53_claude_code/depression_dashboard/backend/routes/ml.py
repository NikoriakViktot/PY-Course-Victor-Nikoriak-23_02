from flask import Blueprint, jsonify, request
from backend.services.ml_service import (
    predict_depression,
    get_clusters,
    get_anomalies,
    get_feature_importance,
    train_all,
)
from backend.utils.logger import get_logger

log = get_logger(__name__)
ml_bp = Blueprint("ml", __name__, url_prefix="/api")


@ml_bp.post("/predict")
def predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    try:
        result = predict_depression(data)
        return jsonify(result)
    except Exception as e:
        log.exception("Prediction failed")
        return jsonify({"error": str(e)}), 500


@ml_bp.get("/clusters")
def clusters():
    return jsonify(get_clusters())


@ml_bp.get("/anomalies")
def anomalies():
    return jsonify(get_anomalies())


@ml_bp.get("/feature-importance")
def feature_importance():
    return jsonify(get_feature_importance())


@ml_bp.post("/train")
def train():
    """Re-train all models. Call once after data changes."""
    try:
        metrics = train_all()
        return jsonify({"status": "ok", "metrics": metrics})
    except Exception as e:
        log.exception("Training failed")
        return jsonify({"error": str(e)}), 500
