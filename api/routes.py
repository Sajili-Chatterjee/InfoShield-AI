# api/routes.py

from flask import Blueprint, request, jsonify
import logging

from services.pipeline import analyze_text, analyze_url

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint("api", __name__)


# ---------------------------
# 🔹 HEALTH CHECK
# ---------------------------
@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "InfoShield-AI API running"
    })


# ---------------------------
# 🔹 TEXT ANALYSIS
# ---------------------------
@api_bp.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({
                "error": "Missing 'text' field"
            }), 400

        text = data["text"]

        if not isinstance(text, str) or len(text.strip()) == 0:
            return jsonify({
                "error": "Invalid text input"
            }), 400

        logger.info("Processing text input")

        result = analyze_text(text)

        return jsonify(result)

    except Exception as e:
        logger.error("Text analysis failed", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


# ---------------------------
# 🔹 URL ANALYSIS (CRITICAL FIX)
# ---------------------------
@api_bp.route("/url", methods=["POST"])
def analyze_url_route():
    try:
        data = request.get_json()

        if not data or "url" not in data:
            return jsonify({
                "error": "Missing 'url' field"
            }), 400

        url = data["url"]

        if not isinstance(url, str) or not url.startswith("http"):
            return jsonify({
                "error": "Invalid URL"
            }), 400

        logger.info(f"Processing URL: {url}")

        result = analyze_url(url)

        return jsonify(result)

    except Exception as e:
        logger.error("URL analysis failed", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


# ---------------------------
# 🔹 ROOT API INFO
# ---------------------------
@api_bp.route("/", methods=["GET"])
def api_home():
    return jsonify({
        "project": "InfoShield-AI",
        "endpoints": {
            "text_analysis": "/api/analyze",
            "url_analysis": "/api/url",
            "health": "/api/health"
        },
        "status": "running"
    })