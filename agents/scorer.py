# agents/scorer.py

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def compute_credibility(evidence_list, source_quality=None):

    if not evidence_list:
        return 0.3

    quality_boost = 0.0
    if source_quality and len(evidence_list) > 0:
        avg_quality = sum(source_quality) / len(source_quality)
        quality_boost = avg_quality * 0.1

    if len(evidence_list) >= 2:
        return min(0.8 + quality_boost, 1.0)
    else:
        return min(0.6 + quality_boost, 1.0)


def compute_final_score(
    model_output,
    verification_score,
    evidence_list,
    source_quality=None,
    ocr_confidence=None,
    realtime_evidence=None
):

    # ✅ Handle BOTH formats (tuple + dict)
    if isinstance(model_output, tuple):
        label, confidence = model_output
        model_output = {"label": label, "confidence": confidence}

    if not isinstance(model_output, dict):
        logger.error("Invalid model_output format")
        model_output = {"label": "Unknown", "confidence": 0.5}

    model_output.setdefault("label", "Unknown")
    model_output.setdefault("confidence", 0.5)

    # Model score
    if model_output["label"].lower() == "fake":
        model_score = 1 - model_output["confidence"]
    else:
        model_score = model_output["confidence"]

    # Safe defaults
    verification_score = verification_score if isinstance(verification_score, (int, float)) else 0.3
    evidence_list = evidence_list if isinstance(evidence_list, list) else []

    credibility_score = compute_credibility(evidence_list, source_quality)

    # Real-time score
    if realtime_evidence:
        realtime_score = min(0.7 + (len(realtime_evidence) * 0.1), 1.0)
    else:
        realtime_score = 0.3

    # Weighted score
    base_score = (
    0.2 * model_score +
    0.4 * verification_score +
    0.25 * credibility_score +
    0.15 * realtime_score
)

    # Confidence calibration (softened)
    if not evidence_list:
        base_score *= 0.8

    if not realtime_evidence:
        base_score *= 0.9  # less aggressive than before

    # OCR adjustment
    if ocr_confidence is not None and 0 <= ocr_confidence <= 1:
        base_score *= (0.5 + 0.5 * ocr_confidence)

    final_score_value = max(0.0, min(1.0, base_score))

    return round(final_score_value, 3)


# ✅ CRITICAL FIX: alias for pipeline
def final_score(*args, **kwargs):
    return compute_final_score(*args, **kwargs)


def compute_weighted_score(scores_dict: Dict[str, float], weights_dict: Dict[str, float]) -> float:
    if not scores_dict or not weights_dict:
        return 0.0

    total_weight = sum(weights_dict.values())
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(
        score * weights_dict.get(key, 0)
        for key, score in scores_dict.items()
        if score is not None
    )

    return weighted_sum / total_weight


def get_final_label(score, threshold=0.6, confidence_levels=False):

    label = "Real" if score >= threshold else "Fake"

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


def get_confidence_score(model_output: Dict, verification_results: List, evidence_count: int):

    confidence = {
        "model_confidence": model_output.get("confidence", 0.5),
        "verification_confidence": calculate_verification_confidence(verification_results),
        "evidence_confidence": calculate_evidence_confidence(evidence_count)
    }

    confidence["overall"] = (
        0.5 * confidence["model_confidence"] +
        0.3 * confidence["verification_confidence"] +
        0.2 * confidence["evidence_confidence"]
    )

    return confidence


def calculate_verification_confidence(verification_results: List) -> float:

    if not verification_results:
        return 0.3

    successful = sum(1 for r in verification_results if r.get("verified", False))
    total = len(verification_results)

    if total == 0:
        return 0.3

    return min(0.3 + (successful / total) * 0.7, 1.0)


def calculate_evidence_confidence(evidence_count: int) -> float:

    if evidence_count == 0:
        return 0.3
    elif evidence_count == 1:
        return 0.6
    elif evidence_count == 2:
        return 0.8
    else:
        return 0.9


def explain_score(
    model_score: float,
    verification_score: float,
    credibility_score: float,
    realtime_score: float = None,
    ocr_confidence: float = None
) -> str:

    explanation = [
        f"Model: {model_score:.2f}",
        f"Verification: {verification_score:.2f}",
        f"Credibility: {credibility_score:.2f}"
    ]

    if realtime_score is not None:
        explanation.append(f"Realtime: {realtime_score:.2f}")

    if ocr_confidence is not None:
        explanation.append(f"OCR: {ocr_confidence:.2f}")

    final_estimate = (
        0.4 * model_score +
        0.25 * verification_score +
        0.2 * credibility_score +
        (0.15 * realtime_score if realtime_score else 0)
    )

    explanation.append(f"Final: {final_estimate:.2f}")
    explanation.append(f"Verdict: {get_final_label(final_estimate)}")

    return "\n".join(explanation)


__all__ = [
    'compute_credibility',
    'compute_final_score',
    'final_score',
    'get_final_label',
    'get_confidence_score',
    'explain_score'
]