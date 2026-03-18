"""
services/pipeline.py
Central orchestration layer. All routes call run_pipeline().
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def run_pipeline(
    text: str,
    source_type: str = "text",
    source_url: Optional[str] = None,
    ocr_confidence: float = 1.0,
) -> dict:
    """
    Run the full InfoShield analysis pipeline on *text*.

    Parameters
    ----------
    text           : pre-extracted text to analyse
    source_type    : "text" | "url" | "social_media" | "image"
    source_url     : original URL (for metadata only)
    ocr_confidence : OCR extraction confidence (used when source_type="image")
    """
    if not text or not text.strip():
        return {
            "project":     "InfoShield-AI",
            "label":       "UNKNOWN",
            "confidence":  0.0,
            "explanation": "No text provided for analysis.",
            "evidence":    [],
        }

    text = text.strip()

    # ---- Step 1: Extract claims ----
    try:
        from agents.claim_extractor import extract_claims
        claims = extract_claims(text)
    except Exception as e:
        logger.warning(f"Claim extraction failed: {e}")
        claims = [text[:500]]

    logger.debug(f"Claims extracted: {len(claims)}")

    # ---- Step 2: Retrieve evidence ----
    try:
        from agents.retriever import retrieve_evidence
        evidence = retrieve_evidence(claims)
    except Exception as e:
        logger.warning(f"Evidence retrieval failed: {e}")
        evidence = []

    logger.debug(f"Evidence items: {len(evidence)}")

    # ---- Step 3: Score ----
    try:
        from agents.scorer import compute_score
        result = compute_score(text, claims, evidence)
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        result = {
            "project":     "InfoShield-AI",
            "label":       "UNKNOWN",
            "confidence":  0.0,
            "explanation": f"Scoring error: {e}",
            "evidence":    evidence,
        }

    # ---- Step 4: Attach metadata ----
    result["source_type"] = source_type
    if source_url:
        result["source_url"] = source_url
    if source_type == "image":
        result["ocr_confidence"] = round(ocr_confidence, 4)

    return result


# -----------------------------------------------------------------------
# Backward-compat aliases so demo.py still works
# -----------------------------------------------------------------------

def analyze_text(text: str) -> dict:
    return run_pipeline(text, source_type="text")


def analyze_ocr_text(text: str, ocr_confidence: float = 1.0, source: str = "image") -> dict:
    return run_pipeline(text, source_type="image", ocr_confidence=ocr_confidence)


def analyze_with_source(text: str, url: str, source_type: str = "social_media") -> dict:
    return run_pipeline(text, source_type=source_type, source_url=url)