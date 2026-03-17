# models/model_loader.py

import logging
from transformers import pipeline
import torch
import os
from typing import Dict, Any
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# 🔹 Global model cache
# -------------------------------
_model_cache = {}
_model_loading_time = None
_model_info = {}

# -------------------------------
# 🔹 Configuration
# -------------------------------
DEFAULT_MODEL = "facebook/bart-large-mnli"  # ✅ FIXED MODEL
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'model_cache')

os.makedirs(CACHE_DIR, exist_ok=True)


# -------------------------------
# 🔹 Load Model (CORE FUNCTION)
# -------------------------------
def load_model(model_name: str = DEFAULT_MODEL, task: str = "zero-shot-classification"):
    """
    Load a model with caching.
    """

    global _model_cache, _model_loading_time, _model_info

    # ✅ Return cached model
    if model_name in _model_cache:
        logger.info(f"Model {model_name} loaded from cache")
        return _model_cache[model_name]

    try:
        start_time = time.time()
        logger.info(f"Loading model: {model_name} ({task})")

        model = pipeline(
            task=task,
            model=model_name,
            cache_dir=CACHE_DIR,
            device=0 if torch.cuda.is_available() else -1
        )

        _model_cache[model_name] = model
        _model_loading_time = time.time() - start_time

        _model_info = {
            "name": model_name,
            "task": task,
            "load_time": round(_model_loading_time, 2),
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        logger.info(f"Model loaded in {_model_loading_time:.2f}s")

        return model

    except Exception as e:
        logger.error(f"Model loading failed: {str(e)}")
        return None


# -------------------------------
# 🔹 Public Getters
# -------------------------------
def get_model():
    """
    Default model getter (kept for compatibility)
    """
    return load_model(DEFAULT_MODEL)


def get_fake_news_model():
    """
    Fake news model → now zero-shot BART
    """
    return load_model(DEFAULT_MODEL, task="zero-shot-classification")


def get_model_info() -> Dict[str, Any]:
    """
    Return model metadata
    """
    global _model_info

    if not _model_info:
        return {"status": "not_loaded"}

    _model_info["cache_size"] = len(_model_cache)
    return _model_info


# -------------------------------
# 🔹 Utilities
# -------------------------------
def reload_model(model_name: str = DEFAULT_MODEL):
    """
    Force reload model
    """
    if model_name in _model_cache:
        del _model_cache[model_name]
        logger.info(f"Removed {model_name} from cache")

    return load_model(model_name)


def clear_model_cache():
    """
    Clear all cached models
    """
    global _model_cache, _model_info

    count = len(_model_cache)
    _model_cache.clear()
    _model_info = {}

    logger.info(f"Cleared {count} cached models")
    return count


def is_model_loaded() -> bool:
    return len(_model_cache) > 0


# -------------------------------
# 🔹 Auto-load on import (optional)
# -------------------------------
logger.info("Initializing model loader...")
classifier = get_model()


# -------------------------------
# 🔹 Exports
# -------------------------------
__all__ = [
    'get_model',
    'get_fake_news_model',
    'get_model_info',
    'reload_model',
    'clear_model_cache',
    'is_model_loaded'
]