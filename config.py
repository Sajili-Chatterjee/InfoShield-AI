import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def parse_origins(value: str, default=None):
    """
    Safely parse CORS origins
    """
    if not value:
        return default or ["*"]
    
    origins = [o.strip() for o in value.split(",") if o.strip()]
    return origins if origins else (default or ["*"])


class Config:
    """Base configuration."""

    # ---------------------------
    # 🔹 Flask
    # ---------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # ---------------------------
    # 🔹 CORS
    # ---------------------------
    CORS_ORIGINS = parse_origins(
        os.environ.get('CORS_ORIGINS'),
        default=["http://localhost:3000"]
    )

    # ---------------------------
    # 🔹 File Uploads
    # ---------------------------
    UPLOAD_FOLDER = str(BASE_DIR / "temp_uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # ---------------------------
    # 🔹 OCR
    # ---------------------------
    OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE', 'eng')

    # ---------------------------
    # 🔹 Model
    # ---------------------------
    MODEL_CACHE_DIR = str(BASE_DIR / "model_cache")
    DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

    # ---------------------------
    # 🔹 Knowledge Base
    # ---------------------------
    KNOWLEDGE_BASE_PATH = str(BASE_DIR / "data" / "knowledge_base.json")

    # ---------------------------
    # 🔹 Requests
    # ---------------------------
    REQUEST_TIMEOUT = 30

    # ---------------------------
    # 🔹 Logging
    # ---------------------------
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'
    TESTING = False
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    TESTING = False

    CORS_ORIGINS = parse_origins(os.environ.get('CORS_ORIGINS'), default=[])

    PROPAGATE_EXCEPTIONS = True

    @staticmethod
    def validate():
        if not os.environ.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY must be set in production")


class TestingConfig(Config):
    DEBUG = True
    ENV = 'testing'
    TESTING = True
    CORS_ORIGINS = ["http://localhost:3000"]

    KNOWLEDGE_BASE_PATH = str(BASE_DIR / "data" / "test_knowledge_base.json")


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}