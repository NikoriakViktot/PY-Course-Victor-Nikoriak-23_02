from flask import Flask, jsonify
from backend.config import config
from backend.routes.analytics import analytics_bp
from backend.routes.ml import ml_bp
from backend.utils.logger import get_logger

log = get_logger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    # register blueprints
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ml_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "internal server error"}), 500

    log.info("Flask app created — routes registered")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
