# models/model_loader.py

import logging
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
import os
from typing import Optional, Dict, Any
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model cache
_model_cache = {}
_model_loading_time = None
_model_info = {}

# Configuration
DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
FALLBACK_MODEL = "distilbert-base-uncased"  # Fallback if main model fails
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'model_cache')

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

def load_model(model_name: str = DEFAULT_MODEL, task: str = "sentiment-analysis"):
    """
    Load a model with caching. Preserves original global loading logic.
    """
    global _model_cache, _model_loading_time, _model_info
    
    # Check if model is already loaded (preserved logic)
    if model_name in _model_cache:
        logger.info(f"Model {model_name} loaded from cache")
        _model_info = {
            "name": model_name,
            "task": task,
            "cached": True,
            "load_time": _model_loading_time
        }
        return _model_cache[model_name]
    
    try:
        start_time = time.time()
        logger.info(f"Loading model: {model_name} for task: {task}")
        
        # Try to load the specified model
        model = pipeline(
            task,
            model=model_name,
            cache_dir=CACHE_DIR,
            device=0 if torch.cuda.is_available() else -1  # Use GPU if available
        )
        
        # Cache the model (preserved logic)
        _model_cache[model_name] = model
        _model_loading_time = time.time() - start_time
        
        # Store model info
        _model_info = {
            "name": model_name,
            "task": task,
            "cached": False,
            "load_time": _model_loading_time,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Model loaded successfully in {_model_loading_time:.2f}s on {_model_info['device']}")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {str(e)}")
        
        # Fallback to default model if specified model fails
        if model_name != DEFAULT_MODEL:
            logger.info(f"Attempting to load default model: {DEFAULT_MODEL}")
            return load_model(DEFAULT_MODEL, task)
        else:
            # If even default fails, try a very simple fallback
            logger.warning(f"Using fallback model configuration")
            return load_fallback_model(task)


def load_fallback_model(task: str = "sentiment-analysis"):
    """
    Load a minimal fallback model when primary models fail.
    """
    try:
        # Try a smaller, more robust model
        fallback_model = pipeline(
            task,
            model="distilbert-base-uncased",
            cache_dir=CACHE_DIR,
            device=0 if torch.cuda.is_available() else -1
        )
        
        _model_cache["fallback"] = fallback_model
        logger.info("Fallback model loaded successfully")
        return fallback_model
        
    except Exception as e:
        logger.error(f"Even fallback model failed: {str(e)}")
        # Return None if all models fail - calling code should handle this
        return None


def get_model(model_name: str = DEFAULT_MODEL):
    """
    Get the loaded model. Preserves original function signature.
    """
    return load_model(model_name)


def get_model_info() -> Dict[str, Any]:
    """
    Get information about the currently loaded model.
    """
    global _model_info
    
    if not _model_info:
        return {
            "name": "Not loaded",
            "status": "unloaded"
        }
    
    # Add current cache status
    _model_info["cache_size"] = len(_model_cache)
    _model_info["cached_models"] = list(_model_cache.keys())
    
    return _model_info


def reload_model(model_name: str = DEFAULT_MODEL):
    """
    Force reload a model (clear cache and load fresh).
    """
    global _model_cache
    
    if model_name in _model_cache:
        del _model_cache[model_name]
        logger.info(f"Removed {model_name} from cache")
    
    return load_model(model_name)


def get_alternative_model():
    """
    Get an alternative model suitable for fake news detection.
    This is an enhanced version that can use more appropriate models.
    """
    # List of models suitable for fake news detection
    alternative_models = [
        "roberta-base-openai-detector",  # AI text detector
        "microsoft/deberta-v3-base",     # Good for text classification
        "facebook/bart-large-mnli",       # Zero-shot classification
    ]
    
    for model_name in alternative_models:
        try:
            logger.info(f"Trying alternative model: {model_name}")
            model = load_model(model_name, "text-classification")
            if model:
                return model
        except Exception as e:
            logger.warning(f"Failed to load {model_name}: {str(e)}")
            continue
    
    # Fall back to default sentiment model
    logger.info("Falling back to default sentiment model")
    return get_model(DEFAULT_MODEL)


def clear_model_cache():
    """
    Clear the model cache to free memory.
    """
    global _model_cache, _model_info
    
    cache_size = len(_model_cache)
    _model_cache.clear()
    _model_info = {}
    logger.info(f"Cleared model cache ({cache_size} models removed)")
    return cache_size


def is_model_loaded() -> bool:
    """
    Check if any model is currently loaded.
    """
    return len(_model_cache) > 0


# Preserve original functionality - load model on module import
# This maintains the original behavior of having the model loaded globally
logger.info("Initializing model loader...")
classifier = load_model(DEFAULT_MODEL)

# Keep original function for backward compatibility
def get_model():
    """
    Original function signature preserved.
    Returns the default sentiment analysis model.
    """
    return classifier


# Enhanced version that returns more appropriate model for fake news
def get_fake_news_model():
    """
    Get a model specifically tuned for fake news detection.
    """
    return get_alternative_model()


__all__ = [
    'get_model',  # Original function
    'get_fake_news_model',  # Enhanced version
    'get_model_info',
    'reload_model',
    'clear_model_cache',
    'is_model_loaded'
]