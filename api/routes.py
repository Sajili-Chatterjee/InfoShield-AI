# api/routes.py
#
# Image upload: use werkzeug file.save() to a tempfile path.
# This is the most reliable method — werkzeug handles stream seeking internally.
# Never touch BytesIO for images.

import os
import logging
import tempfile
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
        return _error("Text is too short (minimum 10 characters).")
    try:
        from services.pipeline import run_pipeline
        return jsonify(run_pipeline(text, source_type="text")), 200
    except Exception as e:
        logger.exception(e)
        return _error("Analysis failed.", 500)


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
            extraction = extract_social_text(url)
            source_type = "social_media"
        else:
            extraction = extract_text_from_url(url)
            source_type = "url"
        text = extraction.get("text", "").strip() if isinstance(extraction, dict) else ""
        if not text:
            return _error("Could not extract text from the URL. "
                          "The page may require login or block scraping.", 422)
        result = run_pipeline(text, source_type=source_type, source_url=url)
        result["source_url"] = url
        return jsonify(result), 200
    except Exception as e:
        logger.exception(e)
        return _error("URL analysis failed.", 500)


# ---------------------------
# POST /api/analyze-image
# ---------------------------
@api_bp.route("/analyze-image", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return _error("An image file is required (multipart field: 'image').")

    file = request.files["image"]
    if not file or file.filename == "":
        return _error("No file selected.")
    if not _allowed_file(file.filename):
        return _error(f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    ext = file.filename.rsplit(".", 1)[1].lower()
    tmp_path = None

    try:
        # Step 1: seek to start of stream (critical on Windows)
        file.stream.seek(0)

        # Step 2: read all bytes
        file_bytes = file.stream.read()
        logger.info(f"Upload received: {len(file_bytes)} bytes, ext=.{ext}")

        if len(file_bytes) == 0:
            return _error("Uploaded file is empty. Please try again.", 422)

        # Step 3: verify magic bytes match declared extension
        magic_ok, magic_msg = _verify_image_magic(file_bytes, ext)
        if not magic_ok:
            logger.warning(f"Magic bytes warning: {magic_msg}")
            # Don't fail — just warn. Some valid images have unexpected headers.

        # Step 4: write to named temp file using Python tempfile
        fd, tmp_path = tempfile.mkstemp(suffix=f".{ext}")
        try:
            os.write(fd, file_bytes)
        finally:
            os.close(fd)

        logger.info(f"Temp file written: {tmp_path} ({os.path.getsize(tmp_path)} bytes)")

        # Step 5: verify PIL can open it
        try:
            from PIL import Image as PILImage
            probe = PILImage.open(tmp_path)
            probe.verify()
            logger.debug(f"PIL.verify() passed for {tmp_path}")
        except Exception as e:
            # Try to re-save via PIL to fix any format issues
            logger.warning(f"PIL verify failed ({e}), attempting re-save")
            try:
                from PIL import Image as PILImage
                import io
                probe = PILImage.open(io.BytesIO(file_bytes))
                probe.load()
                probe = probe.convert("RGB")
                probe.save(tmp_path, format="PNG")
                logger.info("Re-saved image as PNG successfully")
                ext = "png"
            except Exception as e2:
                return _error(
                    f"The uploaded file is not a valid image ({e2}). "
                    "Please save the screenshot via Paint (Ctrl+V → Save As PNG) "
                    "and upload that file.", 422)

        # Step 6: run OCR
        from services.image_processor import extract_text_from_image
        ocr_result = extract_text_from_image(tmp_path)
        logger.info(f"OCR result: success={ocr_result.get('success')}, "
                    f"text_len={len(ocr_result.get('text', ''))}, "
                    f"confidence={ocr_result.get('confidence')}")

        if not ocr_result.get("success"):
            return _error("OCR failed: " + ocr_result.get("error", "No text found."), 422)

        text = ocr_result.get("text", "").strip()
        if not text:
            return _error("No readable text found in the image.", 422)

        # Step 7: run analysis pipeline
        from services.pipeline import run_pipeline
        result = run_pipeline(text, source_type="image")
        result["extracted_text"] = text
        result["ocr_confidence"] = ocr_result.get("confidence", 0)
        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"/analyze-image unhandled error: {e}")
        return _error(f"Image analysis failed: {str(e)}", 500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ---------------------------
# POST /api/analyze-batch
# ---------------------------
@api_bp.route("/analyze-batch", methods=["POST"])
def analyze_batch():
    data = request.get_json(silent=True)
    if not data or "items" not in data:
        return _error("Field 'items' is required.")
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
            results.append({"index": i, "error": str(e)})
    return jsonify({"project": "InfoShield-AI",
                    "results": results, "total": len(results)}), 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verify_image_magic(data: bytes, declared_ext: str):
    """Check file magic bytes match the declared extension."""
    signatures = {
        "png":  [(0, b"\x89PNG\r\n\x1a\n")],
        "jpg":  [(0, b"\xff\xd8\xff")],
        "jpeg": [(0, b"\xff\xd8\xff")],
        "bmp":  [(0, b"BM")],
        "webp": [(0, b"RIFF"), (8, b"WEBP")],
        "tiff": [(0, b"II*\x00"), (0, b"MM\x00*")],
    }
    sigs = signatures.get(declared_ext.lower(), [])
    if not sigs:
        return True, "Unknown extension — skipping magic check"
    for offset, magic in sigs:
        if data[offset:offset + len(magic)] == magic:
            return True, "OK"
    actual = data[:8].hex()
    return False, f"Magic bytes {actual} don't match .{declared_ext}"