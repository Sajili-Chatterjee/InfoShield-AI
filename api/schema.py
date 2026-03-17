# api/schema.py

import re
from typing import Dict, Any, Tuple, Optional, List

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 
    'image/bmp', 'image/webp', 'image/tiff'
}

# Maximum image size (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

def validate_input(data):
    """
    Validate incoming request JSON for text analysis
    """
    if not data:
        return False, "No input data provided"

    if "text" not in data:
        return False, "Missing 'text' field"

    if not isinstance(data["text"], str):
        return False, "'text' must be a string"

    if len(data["text"].strip()) == 0:
        return False, "Text cannot be empty"
    
    # Optional: Check minimum text length for meaningful analysis
    if len(data["text"].split()) < 3:
        return False, "Text too short for meaningful analysis (minimum 3 words)"

    return True, None


def validate_url_input(data):
    """
    Validate incoming request JSON for URL analysis
    """
    if not data:
        return False, "No input data provided"

    if "url" not in data:
        return False, "Missing 'url' field"

    if not isinstance(data["url"], str):
        return False, "'url' must be a string"

    url = data["url"].strip()
    
    # More comprehensive URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Invalid URL format. URL must start with http:// or https://"

    return True, None


def validate_image_input(file, form_data=None):
    """
    Validate image upload for screenshot analysis
    """
    if not file:
        return False, "No image file provided"
    
    # Check if filename exists
    if file.filename == '':
        return False, "No image selected"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset position
    
    if size > MAX_IMAGE_SIZE:
        return False, f"Image too large. Maximum size is {MAX_IMAGE_SIZE/1024/1024}MB"
    
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return False, f"Invalid image type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
    
    # Validate file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff'}
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return False, f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
    
    # Validate form data if provided
    if form_data:
        # Optional source field validation
        if 'source' in form_data and form_data['source']:
            if not isinstance(form_data['source'], str):
                return False, "'source' must be a string"
        
        # Optional language field validation
        if 'language' in form_data and form_data['language']:
            valid_languages = {'auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar'}
            if form_data['language'] not in valid_languages:
                return False, f"Invalid language. Supported: {', '.join(valid_languages)}"
    
    return True, None


def validate_batch_input(data):
    """
    Validate batch processing input
    """
    if not data:
        return False, "No input data provided"
    
    if "items" not in data:
        return False, "Missing 'items' field for batch processing"
    
    if not isinstance(data["items"], list):
        return False, "'items' must be a list"
    
    if len(data["items"]) == 0:
        return False, "Batch items list cannot be empty"
    
    if len(data["items"]) > 50:  # Limit batch size
        return False, "Batch size too large. Maximum 50 items per request"
    
    # Validate each item
    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            return False, f"Item {i} must be an object"
        
        if "type" not in item:
            return False, f"Item {i} missing 'type' field"
        
        item_type = item["type"]
        if item_type not in ["text", "url", "image_url"]:
            return False, f"Item {i} has invalid type. Must be 'text', 'url', or 'image_url'"
        
        if item_type == "text" and "content" not in item:
            return False, f"Item {i} of type 'text' missing 'content' field"
        
        if item_type in ["url", "image_url"] and "url" not in item:
            return False, f"Item {i} of type '{item_type}' missing 'url' field"
    
    return True, None


def format_response(result):
    """
    Standard API response format with enhanced fields
    """
    # Base response structure (preserving original fields)
    response = {
        "project": "InfoShield-AI",
        "label": result.get("label", "Unknown"),
        "confidence": result.get("confidence", 0.0),
        "explanation": result.get("explanation", ""),
        "evidence": result.get("evidence", [])
    }
    
    # Add optional fields if they exist in result
    optional_fields = [
        "verification_score", "credibility_score", "model_score",
        "ocr_confidence", "input_type", "source", "processing_time"
    ]
    
    for field in optional_fields:
        if field in result:
            response[field] = result[field]
    
    # Add warnings if any
    if "warnings" in result and result["warnings"]:
        response["warnings"] = result["warnings"]
    
    # Add detailed breakdown if available
    if "score_breakdown" in result:
        response["score_breakdown"] = result["score_breakdown"]
    
    return response


def format_error_response(error_message: str, error_code: str = None, details: Dict = None) -> Dict:
    """
    Standardized error response format
    """
    error_response = {
        "project": "InfoShield-AI",
        "error": error_message,
        "success": False
    }
    
    if error_code:
        error_response["error_code"] = error_code
    
    if details:
        error_response["details"] = details
    
    return error_response


def format_health_response(status: str, features: List[str], version: str) -> Dict:
    """
    Format health check response
    """
    return {
        "project": "InfoShield-AI",
        "status": status,
        "version": version,
        "features": features,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


def extract_metadata_from_request(request) -> Dict:
    """
    Extract metadata from request for logging/tracking
    """
    metadata = {
        "ip": request.remote_addr,
        "user_agent": request.user_agent.string if request.user_agent else "unknown",
        "content_type": request.content_type,
        "method": request.method
    }
    
    # Add auth info if available
    if hasattr(request, 'auth_token'):
        metadata["auth_token"] = request.auth_token
    
    return metadata


# Preserve original exports
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