"""
api/routes.py
All Flask API route definitions for InfoShield-AI.
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff", "webp"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _error(msg, code=400):
    return jsonify({"project": "InfoShield-AI", "error": msg, "status_code": code}), code


# ---------------------------
# POST /api/analyze
# ---------------------------
@api_bp.route("/analyze", methods=["POST"])
def analyze_text():
    data = request.get_json(silent=True)
    if not data or not data.get("text", "").strip():
        return _error("Field 'text' is required and must not be empty.")

    text = data["text"].strip()
    if len(text) < 10:
        return _error("Text is too short to analyze (minimum 10 characters).")

    try:
        from services.pipeline import run_pipeline
        result = run_pipeline(text, source_type="text")
        return jsonify(result), 200
    except Exception as e:
        logger.exception(f"/analyze error: {e}")
        return _error("Analysis failed. Please try again.", 500)


# ---------------------------
# POST /api/analyze-url
# ---------------------------
@api_bp.route("/analyze-url", methods=["POST"])
def analyze_url():
    data = request.get_json(silent=True)
    if not data or not data.get("url", "").strip():
        return _error("Field 'url' is required.")

    url = data["url"].strip()
    if not url.startswith(("http://", "https://")):
        return _error("URL must start with http:// or https://")

    try:
        from services.url_processor import extract_text_from_url
        from services.social_media_handler import is_social_media_url, extract_social_text
        from services.pipeline import run_pipeline

        if is_social_media_url(url):
            extraction  = extract_social_text(url)
            source_type = "social_media"
        else:
            extraction  = extract_text_from_url(url)
            source_type = "url"

        text = extraction.get("text", "").strip() if isinstance(extraction, dict) else ""

        if not text:
            return _error(
                "Could not extract text from the provided URL. "
                "The page may be behind a paywall, require login, or block scraping.",
                422,
            )

        result = run_pipeline(text, source_type=source_type, source_url=url)
        result["source_url"] = url
        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"/analyze-url error: {e}")
        return _error("URL analysis failed. Please try again.", 500)


# ---------------------------
# POST /api/analyze-image
@api_bp.route("/analyze-image", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return _error("An image file is required (multipart field: 'image').")

    file = request.files["image"]
    if file.filename == "":
        return _error("No file selected.")
    if not _allowed_file(file.filename):
        return _error(f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    upload_folder = current_app.config.get("UPLOAD_FOLDER", "temp_uploads")
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(file.filename)
    tmp_path = os.path.join(upload_folder, filename)
    tmp_path = os.path.abspath(tmp_path)  # FIX: always use absolute path

    try:
        # FIX: read all bytes first, then save via PIL to guarantee valid format
        file_bytes = file.read()
        if len(file_bytes) == 0:
            return _error("Uploaded file is empty — please try again.", 422)

        from PIL import Image as PILImage
        import io
        bio = io.BytesIO(file_bytes)
        bio.seek(0)
        pil_img = PILImage.open(bio)
        pil_img.verify()          # verify it's a real image before doing anything
        bio.seek(0)               # verify() exhausts the stream, reset again
        pil_img = PILImage.open(bio).convert("RGB")
        pil_img = pil_img.convert("RGB")
        pil_img.save(tmp_path, format="PNG")  # re-save as clean PNG

        # Verify it saved correctly
        saved_size = os.path.getsize(tmp_path)
        logger.info(f"Image saved to {tmp_path} ({saved_size} bytes)")

        if saved_size == 0:
            return _error("Image failed to save on server.", 422)

        from services.image_processor import extract_text_from_image
        ocr_result = extract_text_from_image(tmp_path)

        if not ocr_result.get("success"):
            return _error(
                "OCR failed: " + ocr_result.get("error", "Could not extract text."),
                422,
            )

        text = ocr_result.get("text", "").strip()
        if not text:
            return _error("No readable text found in the image.", 422)

        from services.pipeline import run_pipeline
        result = run_pipeline(text, source_type="image")
        result["extracted_text"] = text
        result["ocr_confidence"] = ocr_result.get("confidence", 0)
        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"/analyze-image error: {e}")
        return _error(f"Image analysis failed: {str(e)}", 500)
    finally:
        # FIX: only delete after response is built
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ---------------------------
# POST /api/analyze-batch
# ---------------------------
@api_bp.route("/analyze-batch", methods=["POST"])
def analyze_batch():
    data = request.get_json(silent=True)
    if not data or "items" not in data:
        return _error("Field 'items' (list of objects with 'text') is required.")

    items = data["items"]
    if not isinstance(items, list) or len(items) == 0:
        return _error("'items' must be a non-empty list.")
    if len(items) > 10:
        return _error("Batch limit is 10 items per request.")

    from services.pipeline import run_pipeline
    results = []
    for i, item in enumerate(items):
        try:
            text = item.get("text", "").strip()
            if not text:
                results.append({"index": i, "error": "Empty text"})
                continue
            result = run_pipeline(text, source_type="text")
            result["index"] = i
            results.append(result)
        except Exception as e:
            logger.warning(f"Batch item {i} failed: {e}")
            results.append({"index": i, "error": str(e)})

    return jsonify({
        "project": "InfoShield-AI",
        "results": results,
        "total":   len(results),
    }), 200