# app.py

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import traceback

from api.routes import api_bp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """
    Application factory function.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name:
        app.config.from_object(f'config.{config_name.capitalize()}Config')
    else:
        # Load from environment variable or default
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            app.config.from_object('config.ProductionConfig')
        elif env == 'testing':
            app.config.from_object('config.TestingConfig')
        else:
            app.config.from_object('config.DevelopmentConfig')
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ["http://localhost:3000"]),
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Log application startup
    logger.info(f"InfoShield-AI application started in {app.config['ENV']} mode")
    logger.info(f"Allowed CORS origins: {app.config.get('CORS_ORIGINS')}")
    
    return app

def register_blueprints(app):
    """Register all blueprints."""
    # Register API blueprint with /api prefix
    app.register_blueprint(api_bp, url_prefix="/api")
    logger.info("API blueprint registered")

def register_error_handlers(app):
    """Register custom error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "project": "InfoShield-AI",
            "error": "Resource not found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "project": "InfoShield-AI",
            "error": "Bad request",
            "message": str(error.description) if hasattr(error, 'description') else "Invalid request",
            "status_code": 400
        }), 400
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {str(error)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "project": "InfoShield-AI",
            "error": "Internal server error",
            "status_code": 500
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = jsonify({
            "project": "InfoShield-AI",
            "error": error.name,
            "message": error.description,
            "status_code": error.code
        })
        response.status_code = error.code
        return response
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        logger.error(f"Unhandled exception: {str(error)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "project": "InfoShield-AI",
            "error": "An unexpected error occurred",
            "status_code": 500
        }), 500

def register_commands(app):
    """Register CLI commands."""
    
    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the knowledge base."""
        from agents.retriever import reload_knowledge_base
        if reload_knowledge_base():
            logger.info("Knowledge base initialized successfully")
        else:
            logger.error("Failed to initialize knowledge base")
    
    @app.cli.command("clear-cache")
    def clear_cache_command():
        """Clear model cache."""
        from models.model_loader import clear_model_cache
        count = clear_model_cache()
        logger.info(f"Cleared {count} models from cache")
    
    @app.cli.command("test-ocr")
    def test_ocr_command():
        """Test OCR functionality."""
        import os
        from services.image_processor import extract_text_from_image
        
        test_image = "test_image.png"
        if os.path.exists(test_image):
            result = extract_text_from_image(test_image)
            if result['success']:
                logger.info(f"OCR test successful: {result['text'][:100]}...")
                logger.info(f"OCR confidence: {result.get('confidence', 0.5)}")
            else:
                logger.error(f"OCR test failed: {result.get('error')}")
        else:
            logger.warning(f"Test image {test_image} not found")

# Create the app instance FIRST, then define routes
app = create_app()

# ========== ROOT ROUTES (defined after app is created) ==========

@app.route("/")
def home():
    """Home route - returns API information"""
    return jsonify({
        "project": "InfoShield-AI",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "text_analysis",
            "url_analysis", 
            "image_analysis",
            "social_media_support",
            "ocr_extraction"
        ],
        "documentation": "/api/docs",
        "health": "/api/health"
    })

@app.route("/health")
def health():
    """Simple health check endpoint"""
    return jsonify({
        "project": "InfoShield-AI",
        "status": "healthy",
        "environment": os.environ.get('FLASK_ENV', 'development'),
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Debug mode based on environment
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Run the app
    logger.info(f"Starting InfoShield-AI server on port {port} (debug={debug})")
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=port,
        debug=debug,
        threaded=True  # Enable threading for better performance
    )