# api/schema.py

import re
from typing import Dict, Any, Tuple, List

ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/png', 'image/gif',
    'image/bmp', 'image/webp', 'image/tiff'
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024


def validate_input(data):
    if not data:
        return False, "No input data provided"

    if "text" not in data:
        return False, "Missing 'text' field"

    if not isinstance(data["text"], str):
        return False, "'text' must be a string"

    if len(data["text"].strip()) == 0:
        return False, "Text cannot be empty"

    if len(data["text"].split()) < 3:
        return False, "Text too short (min 3 words)"

    return True, None


def validate_url_input(data):
    if not data:
        return False, "No input data provided"

    if "url" not in data:
        return False, "Missing 'url' field"

    if not isinstance(data["url"], str):
        return False, "'url' must be a string"

    url = data["url"].strip()

    # ✅ FIX: allow longer TLDs
    url_pattern = re.compile(
        r'^https?://'
        r'([\w\-]+\.)+[\w\-]{2,}'
        r'(:\d+)?'
        r'(/.*)?$',
        re.IGNORECASE
    )

    if not url_pattern.match(url):
        return False, "Invalid URL format"

    return True, None


def validate_image_input(file, form_data=None):
    if not file:
        return False, "No image file provided"

    if file.filename == '':
        return False, "No image selected"

    # ✅ safer file size check
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_IMAGE_SIZE:
        return False, f"Image too large (max {MAX_IMAGE_SIZE/1024/1024}MB)"

    # MIME type check (soft validation)
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return False, f"Invalid image type"

    # Extension check
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff'}
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return False, f"Invalid file extension"

    # Form validation
    if form_data:
        if 'source' in form_data and form_data['source']:
            if not isinstance(form_data['source'], str):
                return False, "'source' must be string"

        if 'language' in form_data and form_data['language']:
            valid_languages = {'auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar'}
            if form_data['language'] not in valid_languages:
                return False, "Invalid language"

    return True, None


def validate_batch_input(data):
    if not data or "items" not in data:
        return False, "Missing batch items"

    if not isinstance(data["items"], list):
        return False, "'items' must be list"

    if len(data["items"]) == 0:
        return False, "Empty batch"

    if len(data["items"]) > 50:
        return False, "Max 50 items allowed"

    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            return False, f"Item {i} invalid"

        if "type" not in item:
            return False, f"Item {i} missing type"

        t = item["type"]

        if t not in ["text", "url", "image_url"]:
            return False, f"Invalid type at item {i}"

        if t == "text" and "content" not in item:
            return False, f"Missing content at item {i}"

        if t in ["url", "image_url"] and "url" not in item:
            return False, f"Missing URL at item {i}"

    return True, None


def format_response(result):
    response = {
        "project": "InfoShield-AI",
        "label": result.get("label", "Unknown"),
        "confidence": result.get("confidence", 0.0),
        "explanation": result.get("explanation", ""),
        "evidence": result.get("evidence", [])
    }

    # ✅ FIX: include reasoning
    if "reasoning" in result:
        response["reasoning"] = result["reasoning"]

    optional_fields = [
        "verification_score", "credibility_score", "model_score",
        "ocr_confidence", "input_type", "source", "processing_time"
    ]

    for field in optional_fields:
        if field in result:
            response[field] = result[field]

    if "warnings" in result:
        response["warnings"] = result["warnings"]

    return response


def format_error_response(error_message: str, error_code: str = None, details: Dict = None) -> Dict:
    response = {
        "project": "InfoShield-AI",
        "error": error_message,
        "success": False
    }

    if error_code:
        response["error_code"] = error_code

    if details:
        response["details"] = details

    return response


def format_health_response(status: str, features: List[str], version: str) -> Dict:
    from datetime import datetime
    return {
        "project": "InfoShield-AI",
        "status": status,
        "version": version,
        "features": features,
        "timestamp": datetime.now().isoformat()
    }


def extract_metadata_from_request(request) -> Dict:
    return {
        "ip": request.remote_addr,
        "user_agent": request.user_agent.string if request.user_agent else "unknown",
        "content_type": request.content_type,
        "method": request.method
    }


__all__ = [
    'validate_input',
    'validate_url_input',
    'validate_image_input',
    'validate_batch_input',
    'format_response',
    'format_error_response',
    'format_health_response',
    'extract_metadata_from_request'
]