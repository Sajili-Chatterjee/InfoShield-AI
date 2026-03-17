# models/predictor.py

import logging
from typing import Dict, Any, List
import time

from models.model_loader import get_model, get_fake_news_model, get_model_info

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FakeNewsPredictor:
    """
    Predictor class for fake news detection using zero-shot classification.
    """

    def __init__(self, use_fake_news_model: bool = False):
        self.use_fake_news_model = use_fake_news_model
        self.model = None
        self.model_info = {}
        self.load_model()

    def load_model(self):
        """Load appropriate model"""
        try:
            if self.use_fake_news_model:
                self.model = get_fake_news_model()
                logger.info("Loaded zero-shot fake news model")
            else:
                self.model = get_model()
                logger.info("Loaded default model")

            self.model_info = get_model_info()

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.model = None

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict using zero-shot classification (REAL vs FAKE)
        """

        if not self.model:
            return self._get_fallback_prediction("Model not loaded")

        if not text or not isinstance(text, str):
            return self._get_fallback_prediction("Invalid input")

        try:
            start_time = time.time()

            # Truncate long text
            max_length = 512
            words = text.split()
            if len(words) > max_length:
                text = ' '.join(words[:max_length])

            # ✅ ZERO-SHOT CLASSIFICATION
            candidate_labels = ["real news", "fake news"]

            result = self.model(
                text,
                candidate_labels=candidate_labels
            )

            inference_time = time.time() - start_time

            processed_result = self._process_fake_news_output(result)

            processed_result.update({
                "inference_time": round(inference_time, 3),
                "model_type": "zero_shot_fake_news",
                "text_length": len(text),
                "word_count": len(text.split())
            })

            return processed_result

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return self._get_fallback_prediction(str(e))

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results

    def _process_fake_news_output(self, model_output: Dict) -> Dict[str, Any]:
        """
        Process zero-shot output
        """

        labels = model_output.get("labels", [])
        scores = model_output.get("scores", [])

        if not labels or not scores:
            return self._get_fallback_prediction("Invalid model output")

        top_label = labels[0]
        confidence = scores[0]

        if "fake" in top_label.lower():
            final_label = "FAKE"
        else:
            final_label = "REAL"

        return {
            "label": final_label,
            "confidence": round(confidence, 3)
        }

    def _get_fallback_prediction(self, error_msg: str = "Model error") -> Dict[str, Any]:
        return {
            "label": "UNKNOWN",
            "confidence": 0.5,
            "error": error_msg,
            "fallback": True
        }

    def get_confidence_explanation(self, prediction: Dict[str, Any]) -> str:
        label = prediction.get('label', 'UNKNOWN')
        confidence = prediction.get('confidence', 0.5)

        if confidence >= 0.8:
            level = "very high"
        elif confidence >= 0.6:
            level = "high"
        elif confidence >= 0.4:
            level = "moderate"
        else:
            level = "low"

        return f"The model predicts {label} with {level} confidence ({confidence:.1%})."


# -----------------------------
# GLOBAL INSTANCES (UNCHANGED)
# -----------------------------

_default_predictor = None
_fake_news_predictor = None


def get_predictor(use_fake_news_model: bool = False):
    global _default_predictor, _fake_news_predictor

    if use_fake_news_model:
        if _fake_news_predictor is None:
            _fake_news_predictor = FakeNewsPredictor(True)
        return _fake_news_predictor
    else:
        if _default_predictor is None:
            _default_predictor = FakeNewsPredictor(False)
        return _default_predictor


def predict_text(text: str, use_fake_news_model: bool = False) -> Dict[str, Any]:
    predictor = get_predictor(use_fake_news_model)
    return predictor.predict(text)


def predict_batch(texts: List[str], use_fake_news_model: bool = False) -> List[Dict[str, Any]]:
    predictor = get_predictor(use_fake_news_model)
    return predictor.predict_batch(texts)


# 🔥 IMPORTANT FIX (BACKWARD COMPATIBILITY)

def predict(text: str) -> Dict[str, Any]:
    """
    Force use of fake news model (CRITICAL FIX)
    """
    return predict_text(text, use_fake_news_model=True)


__all__ = [
    'FakeNewsPredictor',
    'get_predictor',
    'predict_text',
    'predict_batch',
    'predict'
]