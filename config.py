# config.py

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = 'temp_uploads'
    
    # OCR
    OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE', 'eng')
    
    # Model settings
    MODEL_CACHE_DIR = os.environ.get('MODEL_CACHE_DIR', 'model_cache')
    DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
    
    # Knowledge base
    KNOWLEDGE_BASE_PATH = os.environ.get('KNOWLEDGE_BASE_PATH', 'data/knowledge_base.json')
    
    # Request timeouts
    REQUEST_TIMEOUT = 30  # seconds
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'
    TESTING = False
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'
    TESTING = False
    
    # Stricter CORS in production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Must be set in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")
    
    # Production settings
    PROPAGATE_EXCEPTIONS = True

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    ENV = 'testing'
    TESTING = True
    CORS_ORIGINS = ['http://localhost:3000']
    
    # Use in-memory for testing
    KNOWLEDGE_BASE_PATH = 'data/test_knowledge_base.json'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}