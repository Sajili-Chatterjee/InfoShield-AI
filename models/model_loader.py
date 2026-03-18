"""
models/model_loader.py
Loads and caches HuggingFace models used for analysis.
"""

import logging
import threading

logger = logging.getLogger(__name__)
logger.info("Initializing model loader...")

_model_cache: dict = {}
_cache_lock = threading.Lock()


def get_zero_shot_classifier():
    """
    Returns a zero-shot classification pipeline.
    Labels: ["real news", "misinformation"]
    """
    return _load_model(
        key="zero_shot",
        task="zero-shot-classification",
        model_name="facebook/bart-large-mnli",
    )


def get_sentiment_pipeline():
    """
    Returns a sentiment pipeline (supplementary credibility signal).
    """
    return _load_model(
        key="sentiment",
        task="sentiment-analysis",
        model_name="distilbert-base-uncased-finetuned-sst-2-english",
    )


def clear_model_cache() -> int:
    """Evict all cached models. Returns number of models cleared."""
    with _cache_lock:
        count = len(_model_cache)
        _model_cache.clear()
    logger.info(f"Cleared {count} cached model(s)")
    return count


def _load_model(key: str, task: str, model_name: str):
    """Load a model and cache it. Returns cached version on subsequent calls."""
    with _cache_lock:
        if key in _model_cache:
            return _model_cache[key]

    logger.info(f"Loading model: {model_name} ({task})")
    try:
        import time
        from transformers import pipeline as hf_pipeline
        t0    = time.time()
        model = hf_pipeline(task, model=model_name)
        elapsed = round(time.time() - t0, 2)
        with _cache_lock:
            _model_cache[key] = model
        logger.info(f"Model loaded in {elapsed}s")
        return model
    except Exception as e:
        logger.error(f"Failed to load model '{model_name}': {e}")
        raise RuntimeError(f"Model load failed for '{model_name}': {e}") from e