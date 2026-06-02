from flask import Blueprint, jsonify
from backend.services.analytics_service import (
    get_summary,
    get_correlations,
    get_depression_by_group,
    get_burnout_phq9_distribution,
)
from backend.utils.logger import get_logger

log = get_logger(__name__)
analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


@analytics_bp.get("/summary")
def summary():
    return jsonify(get_summary())


@analytics_bp.get("/correlations")
def correlations():
    return jsonify(get_correlations())


@analytics_bp.get("/groups")
def groups():
    return jsonify(get_depression_by_group())


@analytics_bp.get("/burnout")
def burnout():
    return jsonify(get_burnout_phq9_distribution())
