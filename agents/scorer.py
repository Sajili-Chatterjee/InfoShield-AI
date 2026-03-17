# agents/scorer.py

import logging
from typing import Dict, List, Union, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_credibility(evidence_list, source_quality=None):
    """
    Enhanced credibility scoring with source quality consideration.
    Preserves original scoring logic while adding enhancements.
    """
    # Original logic preserved
    if not evidence_list:
        return 0.3

    # Enhanced: Consider quality of sources if available
    quality_boost = 0.0
    if source_quality and len(evidence_list) > 0:
        # Average source quality (assuming quality scores 0-1)
        avg_quality = sum(source_quality) / len(source_quality)
        quality_boost = avg_quality * 0.1  # Max 10% boost from quality

    # Original logic with enhancement
    if len(evidence_list) >= 2:
        return min(0.8 + quality_boost, 1.0)  # Cap at 1.0
    else:
        return min(0.6 + quality_boost, 1.0)  # Cap at 1.0


def compute_final_score(model_output, verification_score, evidence_list, 
                        source_quality=None, ocr_confidence=None):
    """
    Enhanced final score computation with OCR confidence consideration.
    Preserves original weighting logic.
    """
    # Input validation
    if not isinstance(model_output, dict):
        logger.error(f"Invalid model_output type: {type(model_output)}")
        model_output = {"label": "Unknown", "confidence": 0.5}
    
    # Ensure required keys exist
    if "label" not in model_output:
        model_output["label"] = "Unknown"
    if "confidence" not in model_output:
        model_output["confidence"] = 0.5

    # Original model score calculation preserved
    if model_output["label"].lower() == "fake":
        model_score = 1 - model_output["confidence"]
    else:
        model_score = model_output["confidence"]

    # Get credibility score with source quality
    credibility_score = compute_credibility(evidence_list, source_quality)

    # Original weights preserved
    base_score = (
        0.5 * model_score +
        0.3 * verification_score +
        0.2 * credibility_score
    )

    # Enhanced: Adjust for OCR confidence if available
    if ocr_confidence is not None and 0 <= ocr_confidence <= 1:
        # Lower confidence in OCR should slightly reduce overall confidence
        ocr_factor = 0.5 + (ocr_confidence * 0.5)  # Range: 0.5 to 1.0
        final_score = base_score * ocr_factor
    else:
        final_score = base_score

    # Ensure score is within bounds
    final_score = max(0.0, min(1.0, final_score))

    return round(final_score, 3)


def compute_weighted_score(scores_dict: Dict[str, float], weights_dict: Dict[str, float]) -> float:
    """
    Compute weighted score from multiple components.
    Helper function for flexible scoring.
    """
    if not scores_dict or not weights_dict:
        return 0.0
    
    total_weight = sum(weights_dict.values())
    if total_weight == 0:
        return 0.0
    
    weighted_sum = 0.0
    for key, score in scores_dict.items():
        if key in weights_dict and score is not None:
            weighted_sum += score * weights_dict[key]
    
    return weighted_sum / total_weight


def get_final_label(score, threshold=0.6, confidence_levels=False):
    """
    Convert score → Fake / Real with optional confidence levels.
    Preserves original threshold logic.
    """
    # Original logic preserved
    if score >= threshold:
        label = "Real"
    else:
        label = "Fake"
    
    # Enhanced: Add confidence level if requested
    if confidence_levels:
        if score >= 0.8:
            confidence = "High"
        elif score >= 0.6:
            confidence = "Medium"
        elif score >= 0.4:
            confidence = "Low"
        else:
            confidence = "Very Low"
        
        return {
            "label": label,
            "confidence_level": confidence,
            "score": score,
            "threshold": threshold
        }
    
    return label


def get_confidence_score(model_output: Dict, verification_results: List, 
                        evidence_count: int) -> Dict[str, float]:
    """
    Calculate confidence scores for different components.
    Useful for debugging and transparency.
    """
    confidence = {
        "model_confidence": model_output.get("confidence", 0.5),
        "verification_confidence": calculate_verification_confidence(verification_results),
        "evidence_confidence": calculate_evidence_confidence(evidence_count)
    }
    
    # Overall confidence
    confidence["overall"] = (
        0.5 * confidence["model_confidence"] +
        0.3 * confidence["verification_confidence"] +
        0.2 * confidence["evidence_confidence"]
    )
    
    return confidence


def calculate_verification_confidence(verification_results: List) -> float:
    """
    Calculate confidence based on verification results.
    """
    if not verification_results:
        return 0.3
    
    # Count successful verifications
    successful = sum(1 for r in verification_results if r.get("verified", False))
    total = len(verification_results)
    
    if total == 0:
        return 0.3
    
    ratio = successful / total
    return min(0.3 + (ratio * 0.7), 1.0)  # Range: 0.3 to 1.0


def calculate_evidence_confidence(evidence_count: int) -> float:
    """
    Calculate confidence based on amount of evidence.
    """
    if evidence_count == 0:
        return 0.3
    elif evidence_count == 1:
        return 0.6
    elif evidence_count == 2:
        return 0.8
    else:
        return 0.9


def explain_score(model_score: float, verification_score: float, 
                  credibility_score: float, ocr_confidence: float = None) -> str:
    """
    Generate human-readable explanation of the score.
    Useful for transparency in the UI.
    """
    explanation = []
    
    explanation.append(f"Model confidence: {model_score:.2f}")
    explanation.append(f"Verification score: {verification_score:.2f}")
    explanation.append(f"Evidence credibility: {credibility_score:.2f}")
    
    if ocr_confidence is not None:
        explanation.append(f"OCR quality: {ocr_confidence:.2f}")
    
    total_score = compute_final_score(
        {"label": "Real" if model_score > 0.5 else "Fake", 
         "confidence": abs(model_score - 0.5) * 2 if model_score != 0.5 else 0.5},
        verification_score,
        [],  # evidence_list not needed for explanation
        None,  # source_quality
        ocr_confidence
    )
    
    explanation.append(f"Final score: {total_score:.2f}")
    explanation.append(f"Final verdict: {get_final_label(total_score)}")
    
    return "\n".join(explanation)


# Preserve original exports
__all__ = [
    'compute_credibility', 
    'compute_final_score', 
    'get_final_label',
    'get_confidence_score',
    'explain_score'
]