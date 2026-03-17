# models/predictor.py

import logging
from typing import Dict, Any, List, Optional, Union
import time
import numpy as np

from models.model_loader import get_model, get_fake_news_model, get_model_info

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FakeNewsPredictor:
    """
    Predictor class for fake news detection.
    Handles model inference and result processing.
    """
    
    def __init__(self, use_fake_news_model: bool = False):
        """
        Initialize the predictor.
        
        Args:
            use_fake_news_model: If True, use model optimized for fake news detection.
                                 If False, use default sentiment model (original behavior).
        """
        self.use_fake_news_model = use_fake_news_model
        self.model = None
        self.model_info = {}
        self.load_model()
    
    def load_model(self):
        """Load the appropriate model."""
        try:
            if self.use_fake_news_model:
                self.model = get_fake_news_model()
                logger.info("Loaded fake news optimized model")
            else:
                self.model = get_model()  # Original sentiment model
                logger.info("Loaded default sentiment model")
            
            self.model_info = get_model_info()
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.model = None
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict whether text contains fake news.
        Preserves core logic of model inference.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with prediction results
        """
        if not self.model:
            logger.error("No model loaded")
            return self._get_fallback_prediction()
        
        if not text or not isinstance(text, str):
            logger.warning(f"Invalid input text: {type(text)}")
            return self._get_fallback_prediction("Invalid input")
        
        try:
            start_time = time.time()
            
            # Truncate very long texts (model limitation)
            max_length = 512
            if len(text.split()) > max_length:
                logger.info(f"Text too long ({len(text.split())} words), truncating to {max_length} words")
                text = ' '.join(text.split()[:max_length])
            
            # Run model inference
            result = self.model(text)[0]
            
            inference_time = time.time() - start_time
            
            # Process result based on model type
            if self.use_fake_news_model:
                processed_result = self._process_fake_news_output(result)
            else:
                processed_result = self._process_sentiment_output(result)
            
            # Add metadata
            processed_result.update({
                "inference_time": round(inference_time, 3),
                "model_type": "fake_news" if self.use_fake_news_model else "sentiment",
                "text_length": len(text),
                "word_count": len(text.split())
            })
            
            logger.debug(f"Prediction completed in {inference_time:.3f}s")
            return processed_result
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return self._get_fallback_prediction(str(e))
    
    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Predict on a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of prediction results
        """
        results = []
        for i, text in enumerate(texts):
            logger.debug(f"Processing batch item {i+1}/{len(texts)}")
            result = self.predict(text)
            results.append(result)
        return results
    
    def _process_sentiment_output(self, model_output: Dict) -> Dict[str, Any]:
        """
        Process sentiment model output to fake news format.
        This is the original logic preserved.
        
        Sentiment model returns:
        - label: POSITIVE/NEGATIVE
        - score: confidence score
        """
        label = model_output.get('label', 'NEUTRAL')
        confidence = model_output.get('score', 0.5)
        
        # Map sentiment to fake news labels
        # Assuming NEGATIVE sentiment might indicate fake news
        if label == 'NEGATIVE':
            fake_news_label = 'FAKE'
            # Adjust confidence: higher sentiment confidence = higher fake news confidence
            adjusted_confidence = confidence
        elif label == 'POSITIVE':
            fake_news_label = 'REAL'
            adjusted_confidence = confidence
        else:
            fake_news_label = 'UNKNOWN'
            adjusted_confidence = 0.5
        
        return {
            "label": fake_news_label,
            "confidence": round(adjusted_confidence, 3),
            "original_label": label,
            "original_confidence": round(confidence, 3)
        }
    
    def _process_fake_news_output(self, model_output: Dict) -> Dict[str, Any]:
        """
        Process output from fake news specific model.
        """
        label = model_output.get('label', 'UNKNOWN')
        confidence = model_output.get('score', 0.5)
        
        # Handle different label formats
        if isinstance(label, str):
            label_upper = label.upper()
            if 'FAKE' in label_upper or 'FALSE' in label_upper:
                final_label = 'FAKE'
            elif 'REAL' in label_upper or 'TRUE' in label_upper:
                final_label = 'REAL'
            else:
                final_label = label_upper
        else:
            final_label = 'UNKNOWN'
        
        return {
            "label": final_label,
            "confidence": round(confidence, 3)
        }
    
    def _get_fallback_prediction(self, error_msg: str = "Model error") -> Dict[str, Any]:
        """
        Return fallback prediction when model fails.
        """
        return {
            "label": "UNKNOWN",
            "confidence": 0.5,
            "error": error_msg,
            "fallback": True
        }
    
    def get_confidence_explanation(self, prediction: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of the prediction.
        """
        label = prediction.get('label', 'UNKNOWN')
        confidence = prediction.get('confidence', 0.5)
        
        if confidence >= 0.8:
            confidence_desc = "very high"
        elif confidence >= 0.6:
            confidence_desc = "high"
        elif confidence >= 0.4:
            confidence_desc = "moderate"
        else:
            confidence_desc = "low"
        
        explanation = f"The model predicts this content is {label} with {confidence_desc} confidence ({confidence:.1%})."
        
        # Add original model info if available
        if 'original_label' in prediction:
            explanation += f" (Original sentiment: {prediction['original_label']} at {prediction['original_confidence']:.1%} confidence)"
        
        return explanation


# Global predictor instance for easy import
_default_predictor = None
_fake_news_predictor = None

def get_predictor(use_fake_news_model: bool = False):
    """
    Get or create a predictor instance.
    This maintains a similar pattern to model_loader's global instance.
    """
    global _default_predictor, _fake_news_predictor
    
    if use_fake_news_model:
        if _fake_news_predictor is None:
            _fake_news_predictor = FakeNewsPredictor(use_fake_news_model=True)
        return _fake_news_predictor
    else:
        if _default_predictor is None:
            _default_predictor = FakeNewsPredictor(use_fake_news_model=False)
        return _default_predictor


def predict_text(text: str, use_fake_news_model: bool = False) -> Dict[str, Any]:
    """
    Convenience function for single text prediction.
    """
    predictor = get_predictor(use_fake_news_model)
    return predictor.predict(text)


def predict_batch(texts: List[str], use_fake_news_model: bool = False) -> List[Dict[str, Any]]:
    """
    Convenience function for batch prediction.
    """
    predictor = get_predictor(use_fake_news_model)
    return predictor.predict_batch(texts)


# For backward compatibility - simple prediction function
def predict(text: str) -> Dict[str, Any]:
    """
    Original simple prediction function.
    Uses default sentiment model for compatibility.
    """
    return predict_text(text, use_fake_news_model=False)


__all__ = [
    'FakeNewsPredictor',
    'get_predictor',
    'predict_text',
    'predict_batch',
    'predict'  # Original function
]