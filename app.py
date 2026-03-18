import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import traceback

from api.routes import api_bp

logger = logging.getLogger(__name__)


def create_app(config_name=None):

    app = Flask(__name__)

    # ---------------------------
    # 🔹 LOAD CONFIG SAFELY
    # ---------------------------
    try:
        if config_name:
            app.config.from_object(f'config.{config_name.capitalize()}Config')
        else:
            env = os.environ.get('FLASK_ENV', 'development')

            if env == 'production':
                app.config.from_object('config.ProductionConfig')
            elif env == 'testing':
                app.config.from_object('config.TestingConfig')
            else:
                app.config.from_object('config.DevelopmentConfig')

    except Exception as e:
        logger.warning(f"Config loading failed, using defaults: {e}")
        app.config['ENV'] = os.environ.get('FLASK_ENV', 'development')
        app.config['CORS_ORIGINS'] = ["*"]

    # ---------------------------
    # 🔹 CORS
    # ---------------------------
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ["*"]),
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # ---------------------------
    # 🔹 REGISTER
    # ---------------------------
    app.register_blueprint(api_bp, url_prefix="/api")

    register_error_handlers(app)
    register_commands(app)

    env = os.environ.get('FLASK_ENV', 'development')

    logger.info(f"App started in {env} mode")

    return app


# ---------------------------
# 🔹 ERROR HANDLERS
# ---------------------------
def register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "project": "InfoShield-AI",
            "error": "Not Found",
            "status_code": 404
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "project": "InfoShield-AI",
            "error": "Bad Request",
            "message": str(getattr(error, "description", "")),
            "status_code": 400
        }), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            "project": "InfoShield-AI",
            "error": error.name,
            "message": error.description,
            "status_code": error.code
        }), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(str(error))
        logger.error(traceback.format_exc())
        return jsonify({
            "project": "InfoShield-AI",
            "error": "Internal Server Error",
            "status_code": 500
        }), 500


# ---------------------------
# 🔹 CLI COMMANDS
# ---------------------------
def register_commands(app):

    @app.cli.command("init-db")
    def init_db():
        from agents.retriever import reload_knowledge_base
        reload_knowledge_base()
        logger.info("Knowledge base reloaded")

    @app.cli.command("clear-cache")
    def clear_cache():
        from models.model_loader import clear_model_cache
        count = clear_model_cache()
        logger.info(f"Cleared {count} models")

    @app.cli.command("test-ocr")
    def test_ocr():
        from services.image_processor import extract_text_from_image

        test_image = "test_image.png"
        if os.path.exists(test_image):
            result = extract_text_from_image(test_image)
            logger.info(result)
        else:
            logger.warning("test_image.png not found")


# ---------------------------
# 🔹 CREATE APP
# ---------------------------
app = create_app()
# Pre-load model at startup so first request doesn't crash
with app.app_context():
    try:
        from models.model_loader import get_zero_shot_classifier
        get_zero_shot_classifier()
    except Exception as e:
        logger.warning(f"Model pre-load failed: {e}")

# ---------------------------
# 🔹 ROOT ROUTES
# ---------------------------
@app.route("/")
def home():
    return jsonify({
        "project": "InfoShield-AI",
        "status": "running",
        "version": "2.0.0"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "env": os.environ.get("FLASK_ENV", "development")
    })


# ---------------------------
# 🔹 RUN SERVER
# ---------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"

    logger.info(f"Running on port {port}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )