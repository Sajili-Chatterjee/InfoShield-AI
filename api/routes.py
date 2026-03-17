# api/routes.py

from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
import uuid

from services.pipeline import analyze_text
from services.url_processor import extract_text_from_url
from services.social_media_handler import extract_social_text, detect_platform
from services.image_processor import extract_text_from_image, check_ocr_availability, preprocess_image_for_ocr, process_image

from api.schema import (
    validate_input,
    validate_url_input,
    validate_image_input,
    format_response
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

# Configuration for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = 'temp_uploads'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ===============================
# 🔹 TEXT ANALYSIS ENDPOINT
# ===============================
@api_bp.route("/analyze", methods=["POST"])
def analyze():
    """Analyze text for fake news detection."""
    data = request.get_json()

    # Validate input
    is_valid, error = validate_input(data)
    if not is_valid:
        logger.warning(f"Invalid input: {error}")
        return jsonify({"error": error}), 400

    text = data["text"]

    try:
        result = analyze_text(text)
        response = format_response(result)
        
        # Add metadata
        response["input_type"] = "text"

        logger.info(f"Text analysis completed successfully")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


# ===============================
# 🔹 URL ANALYSIS ENDPOINT
# ===============================
@api_bp.route("/analyze-url", methods=["POST"])
def analyze_url():
    """Extract text from URL and analyze."""
    data = request.get_json()

    # Validate URL input
    is_valid, error = validate_url_input(data)
    if not is_valid:
        logger.warning(f"Invalid URL input: {error}")
        return jsonify({"error": error}), 400

    url = data["url"]
    
    # Check if it's a social media URL
    is_social, platform = is_social_media_url(url)

    try:
        # Step 1: Extract article/text from URL
        if is_social:
    # Handle social media URLs specially
            result = extract_social_text(url, include_metadata=True)
            if result.get('success'):
                text = result.get('text')
                error = None
            else:
                text = None
                error = result.get('error')
            input_subtype = f"social_media_{platform}"
        else:
            # Regular news/article URL
            text, error = extract_text_from_url(url)
            input_subtype = "news_article"

        if error:
            logger.warning(f"Failed to extract from URL {url}: {error}")
            return jsonify({
                "error": "Failed to extract content",
                "details": error
            }), 400

        # Step 2: Run AI pipeline
        result = analyze_text(text)
        response = format_response(result)

        # Include metadata
        response["source_url"] = url
        response["input_type"] = "url"
        response["input_subtype"] = input_subtype

        logger.info(f"URL analysis completed for {url}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in URL analysis: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


# ===============================
# 🔹 IMAGE ANALYSIS ENDPOINT (NEW)
# ===============================
@api_bp.route("/analyze-image", methods=["POST"])
def analyze_image():
    """
    Extract text from uploaded image/screenshot and analyze.
    This is the main endpoint for screenshot-based fake news detection.
    """
    # Check if image file is present
    if 'image' not in request.files:
        logger.warning("No image file in request")
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    
    # Check if file is selected
    if file.filename == '':
        logger.warning("Empty filename")
        return jsonify({"error": "No image selected"}), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        return jsonify({"error": f"File too large. Maximum size: {MAX_FILE_SIZE/1024/1024}MB"}), 400
    
    # Get optional source information
    source = request.form.get('source', 'unknown')
    language = request.form.get('language', 'auto')
    
    # Generate unique filename to avoid collisions
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    try:
        # Save file temporarily
        file.save(filepath)
        logger.info(f"Image saved: {filepath}")
        
        # Step 1: Process image and extract text using OCR
        ocr_result = extract_text_from_image(filepath, language)
        
        if not ocr_result['success']:
            logger.error(f"OCR failed: {ocr_result.get('error')}")
            return jsonify({
                "error": "Failed to extract text from image",
                "details": ocr_result.get('error', 'OCR processing failed')
            }), 400
        
        extracted_text = ocr_result['text']
        
        # Step 2: Process image quality analysis (optional)
        image_quality = process_image(filepath)
        
        # Step 3: Run AI pipeline on extracted text
        result = analyze_text(extracted_text)
        response = format_response(result)
        
        # Add metadata
        response["input_type"] = "image"
        response["source"] = source
        response["filename"] = filename
        response["ocr_confidence"] = ocr_result.get('confidence', 0.5)
        response["image_quality"] = image_quality
        response["text_length"] = len(extracted_text)
        
        # Include extracted text for transparency (optional)
        if request.args.get('include_text', 'false').lower() == 'true':
            response["extracted_text"] = extracted_text
        
        logger.info(f"Image analysis completed for {filename} with OCR confidence: {ocr_result.get('confidence', 0.5):.2f}")
        
        # Clean up temp file
        try:
            os.remove(filepath)
            logger.info(f"Temp file removed: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to remove temp file {filepath}: {e}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")
        # Clean up temp file if it exists
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


# ===============================
# 🔹 BATCH ANALYSIS ENDPOINT (NEW)
# ===============================
@api_bp.route("/analyze-batch", methods=["POST"])
def analyze_batch():
    """
    Analyze multiple inputs (text, URLs, or images) in one request.
    """
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({"error": "No items provided for batch analysis"}), 400
    
    items = data['items']
    results = []
    
    for i, item in enumerate(items):
        item_type = item.get('type', 'text')
        item_result = {
            'index': i,
            'type': item_type,
            'status': 'pending'
        }
        
        try:
            if item_type == 'text':
                text = item.get('content', '')
                if not text:
                    item_result['status'] = 'error'
                    item_result['error'] = 'No text content provided'
                else:
                    result = analyze_text(text)
                    item_result['status'] = 'success'
                    item_result['result'] = format_response(result)
            
            elif item_type == 'url':
                url = item.get('url', '')
                if not url:
                    item_result['status'] = 'error'
                    item_result['error'] = 'No URL provided'
                else:
                    text, error = extract_text_from_url(url)
                    if error:
                        item_result['status'] = 'error'
                        item_result['error'] = error
                    else:
                        result = analyze_text(text)
                        item_result['status'] = 'success'
                        item_result['result'] = format_response(result)
                        item_result['url'] = url
            
            elif item_type == 'image_url':
                # For images provided via URL
                image_url = item.get('url', '')
                if not image_url:
                    item_result['status'] = 'error'
                    item_result['error'] = 'No image URL provided'
                else:
                    # Download and process image from URL
                    # (Implementation would require additional function)
                    item_result['status'] = 'error'
                    item_result['error'] = 'Image URL processing not implemented yet'
            
            else:
                item_result['status'] = 'error'
                item_result['error'] = f'Unknown item type: {item_type}'
        
        except Exception as e:
            item_result['status'] = 'error'
            item_result['error'] = str(e)
        
        results.append(item_result)
    
    return jsonify({
        'batch_size': len(items),
        'results': results
    }), 200


# ===============================
# 🔹 HEALTH CHECK ENDPOINT
# ===============================
@api_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "INFOSHIELD-AI",
        "version": "1.0.0",
        "features": ["text", "url", "image"]
    }), 200


# Helper function to detect social media URLs
def is_social_media_url(url):
    """Check if URL is from social media platform."""
    social_domains = {
        'twitter.com': 'twitter',
        'x.com': 'twitter',
        'facebook.com': 'facebook',
        'instagram.com': 'instagram',
        'reddit.com': 'reddit',
        'tiktok.com': 'tiktok',
        'linkedin.com': 'linkedin',
        'youtube.com': 'youtube',
        'youtu.be': 'youtube'
    }
    
    url_lower = url.lower()
    for domain, platform in social_domains.items():
        if domain in url_lower:
            return True, platform
    
    return False, None