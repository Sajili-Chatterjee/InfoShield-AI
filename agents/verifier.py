# agents/verifier.py

import re
from typing import List, Union, Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced negation words
NEGATION_WORDS = {
    "no", "not", "never", "none", "denies", "deny", "false", 
    "fails", "failed", "incorrect", "wrong", "untrue", "fabricated",
    "misleading", "bogus", "fake", "hoax", "myth", "debunked",
    "refutes", "refuted", "contradicts", "contradicted", "disproves",
    "disproved", "without", "lack", "lacks", "lacking", "absence"
}

# Strong negation indicators (complete reversal)
STRONG_NEGATION = {
    "completely false", "totally wrong", "entirely incorrect",
    "fabricated", "hoax", "myth", "debunked"
}


def preprocess(text):
    """
    Preprocess text for verification - preserves core logic.
    """
    if not text or not isinstance(text, str):
        return set()
    
    # Clean OCR artifacts
    text = clean_text(text)
    
    # Original logic preserved
    return set(text.lower().split())


def clean_text(text):
    """
    Clean text from OCR artifacts.
    """
    # Remove special characters but keep sentence structure
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def has_negation(text):
    """
    Check if text contains negation words - preserves core logic.
    """
    if not text:
        return False
    
    words = text.lower().split()
    
    # Original logic preserved
    has_neg = any(word in NEGATION_WORDS for word in words)
    
    # Enhanced: Check for strong negation phrases
    if not has_neg:
        text_lower = text.lower()
        has_neg = any(phrase in text_lower for phrase in STRONG_NEGATION)
    
    return has_neg


def get_negation_strength(text):
    """
    Determine how strong the negation is.
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # Check for strong negation phrases
    for phrase in STRONG_NEGATION:
        if phrase in text_lower:
            return 0.8  # Strong negation
    
    # Count negation words
    negation_count = sum(1 for word in words if word in NEGATION_WORDS)
    
    if negation_count == 0:
        return 0.0
    elif negation_count == 1:
        return 0.4
    else:
        return min(0.4 + (negation_count - 1) * 0.1, 0.7)


def compute_similarity(claim, evidence):
    """
    Compute similarity between claim and evidence - preserves core logic.
    """
    if not claim or not evidence:
        return 0.0
    
    claim_words = preprocess(claim)
    evidence_words = preprocess(evidence)

    # Original logic preserved
    overlap = claim_words.intersection(evidence_words)

    # Enhanced: Consider word positions and importance
    similarity = len(overlap) / (len(claim_words) + 1)
    
    # Boost if key terms match exactly
    if len(overlap) > 0:
        # Check for exact phrase matches
        claim_lower = claim.lower()
        evidence_lower = evidence.lower()
        if claim_lower in evidence_lower or evidence_lower in claim_lower:
            similarity = min(similarity * 1.2, 1.0)
    
    return similarity


def verify(claims, evidence_list, detailed=False):
    """
    Verify claims against evidence - preserves core logic.
    """
    # Input validation
    if not claims:
        logger.warning("No claims provided for verification")
        return 0.5 if not detailed else {"score": 0.5, "details": []}
    
    if not evidence_list:
        logger.warning("No evidence provided for verification")
        return 0.5 if not detailed else {"score": 0.5, "details": []}
    
    # Ensure lists
    if isinstance(claims, str):
        claims = [claims]
    if isinstance(evidence_list, str):
        evidence_list = [evidence_list]

    scores = []
    verification_details = [] if detailed else None

    # Original verification logic preserved
    for claim_idx, claim in enumerate(claims):
        for evidence_idx, evidence in enumerate(evidence_list):
            sim = compute_similarity(claim, evidence)

            # Original negation handling preserved
            if has_negation(evidence) and sim > 0:
                negation_strength = get_negation_strength(evidence)
                sim *= (0.4 - negation_strength * 0.2)  # Stronger negation = lower score
                
                if detailed:
                    logger.debug(f"Negation detected in evidence, adjusted similarity: {sim:.3f}")

            scores.append(sim)
            
            # Store details if requested
            if detailed:
                verification_details.append({
                    "claim": claim,
                    "evidence": evidence,
                    "similarity": sim,
                    "negation_detected": has_negation(evidence),
                    "claim_words": list(preprocess(claim)),
                    "evidence_words": list(preprocess(evidence))
                })

    # Original averaging logic preserved
    if scores:
        avg_score = sum(scores) / len(scores)
        verification_score = min(1.0, avg_score * 2)
    else:
        verification_score = 0.5

    # Return detailed or simple result
    if detailed:
        return {
            "score": round(verification_score, 3),
            "details": verification_details,
            "num_comparisons": len(scores),
            "avg_similarity": round(avg_score, 3) if scores else 0.5
        }
    
    return round(verification_score, 3)


def verify_with_metadata(claims, evidence_list_with_metadata):
    """
    Enhanced verification that uses metadata for better accuracy.
    """
    if not claims or not evidence_list_with_metadata:
        return {"score": 0.5, "verified_claims": []}
    
    # Extract just the text for basic verification
    evidence_texts = []
    evidence_metadata = []
    
    for item in evidence_list_with_metadata:
        if isinstance(item, dict):
            evidence_texts.append(item.get("text", ""))
            evidence_metadata.append({
                "source": item.get("source", "unknown"),
                "score": item.get("score", 0),
                "date": item.get("date", None)
            })
        else:
            evidence_texts.append(item)
            evidence_metadata.append({"source": "unknown", "score": 0})
    
    # Perform verification
    result = verify(claims, evidence_texts, detailed=True)
    
    # Enhance with metadata
    enhanced_details = []
    for i, detail in enumerate(result.get("details", [])):
        if i < len(evidence_metadata):
            detail["metadata"] = evidence_metadata[i]
            enhanced_details.append(detail)
    
    result["details"] = enhanced_details
    return result


def get_verification_summary(verification_result):
    """
    Generate a human-readable summary of verification results.
    """
    if not verification_result:
        return "No verification data available"
    
    score = verification_result.get("score", 0.5)
    details = verification_result.get("details", [])
    
    summary = []
    summary.append(f"Verification Score: {score:.3f}")
    summary.append(f"Based on {len(details)} claim-evidence comparisons")
    
    # Count supporting vs contradicting evidence
    supporting = 0
    contradicting = 0
    
    for detail in details:
        if detail.get("negation_detected", False):
            contradicting += 1
        elif detail.get("similarity", 0) > 0.3:
            supporting += 1
    
    summary.append(f"Supporting evidence: {supporting}")
    summary.append(f"Contradicting evidence: {contradicting}")
    
    if score > 0.7:
        summary.append("Verdict: Strongly supported by evidence")
    elif score > 0.5:
        summary.append("Verdict: Partially supported by evidence")
    elif score > 0.3:
        summary.append("Verdict: Weakly supported, possible contradictions")
    else:
        summary.append("Verdict: Not supported, likely false")
    
    return "\n".join(summary)


# Preserve original exports
__all__ = ['verify', 'verify_with_metadata', 'get_verification_summary']