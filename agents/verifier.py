# agents/verifier.py

import re
from typing import List
import logging

logger = logging.getLogger(__name__)

NEGATION_WORDS = {
    "no", "not", "never", "none", "denies", "deny", "false",
    "fails", "failed", "incorrect", "wrong", "untrue", "fabricated",
    "misleading", "bogus", "fake", "hoax", "myth", "debunked",
    "refutes", "refuted", "contradicts", "contradicted", "disproves",
    "disproved", "without", "lack", "lacks", "lacking", "absence"
}

STRONG_NEGATION = {
    "completely false", "totally wrong", "entirely incorrect",
    "fabricated", "hoax", "myth", "debunked"
}


def clean_text(text):
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def preprocess(text):
    if not text or not isinstance(text, str):
        return set()

    text = clean_text(text)
    return set(text.lower().split())


def has_negation(text):
    if not text:
        return False

    words = text.lower().split()
    if any(word in NEGATION_WORDS for word in words):
        return True

    text_lower = text.lower()
    return any(phrase in text_lower for phrase in STRONG_NEGATION)


def get_negation_strength(text):
    if not text:
        return 0.0

    text_lower = text.lower()

    for phrase in STRONG_NEGATION:
        if phrase in text_lower:
            return 0.8

    words = text_lower.split()
    count = sum(1 for w in words if w in NEGATION_WORDS)

    if count == 0:
        return 0.0
    elif count == 1:
        return 0.4
    else:
        return min(0.4 + (count - 1) * 0.1, 0.7)


def compute_similarity(claim, evidence):
    if not claim or not evidence:
        return 0.0

    claim_words = preprocess(claim)
    evidence_words = preprocess(evidence)

    if not claim_words:
        return 0.0  # ✅ FIX: avoid division issues

    overlap = claim_words.intersection(evidence_words)
    similarity = len(overlap) / (len(claim_words) + 1)

    # Phrase boost
    claim_lower = claim.lower()
    evidence_lower = evidence.lower()
    if claim_lower in evidence_lower or evidence_lower in claim_lower:
        similarity = min(similarity * 1.2, 1.0)

    return similarity


def verify(claims, evidence_list, detailed=False):

    if not claims:
        return 0.5 if not detailed else {"score": 0.5, "details": []}

    if not evidence_list:
        return 0.5 if not detailed else {"score": 0.5, "details": []}

    if isinstance(claims, str):
        claims = [claims]
    if isinstance(evidence_list, str):
        evidence_list = [evidence_list]

    scores = []
    verification_details = [] if detailed else None

    for claim in claims:
        for evidence in evidence_list:

            sim = compute_similarity(claim, evidence)

            neg_flag = has_negation(evidence)  # ✅ compute once

            if neg_flag and sim > 0:
                neg_strength = get_negation_strength(evidence)
                factor = max(0.1, 0.4 - neg_strength * 0.2)  # ✅ clamp
                sim *= factor

            scores.append(sim)

            if detailed:
                verification_details.append({
                    "claim": claim,
                    "evidence": evidence,
                    "similarity": sim,
                    "negation_detected": neg_flag
                })

    if scores:
        avg_score = sum(scores) / len(scores)
        verification_score = min(1.0, avg_score * 2)
    else:
        verification_score = 0.5

    if detailed:
        return {
            "score": round(verification_score, 3),
            "details": verification_details,
            "num_comparisons": len(scores),
            "avg_similarity": round(avg_score, 3) if scores else 0.5
        }

    return round(verification_score, 3)


def verify_with_metadata(claims, evidence_list_with_metadata):

    if not claims or not evidence_list_with_metadata:
        return {"score": 0.5, "verified_claims": []}

    evidence_texts = []
    metadata = []

    for item in evidence_list_with_metadata:
        if isinstance(item, dict):
            evidence_texts.append(item.get("text", ""))
            metadata.append(item)
        else:
            evidence_texts.append(item)
            metadata.append({})

    result = verify(claims, evidence_texts, detailed=True)

    for i, detail in enumerate(result.get("details", [])):
        if i < len(metadata):
            detail["metadata"] = metadata[i]

    return result


def get_verification_summary(result):

    if not result:
        return "No verification data available"

    score = result.get("score", 0.5)
    details = result.get("details", [])

    supporting = sum(1 for d in details if d.get("similarity", 0) > 0.3)
    contradicting = sum(1 for d in details if d.get("negation_detected"))

    summary = [
        f"Score: {score:.3f}",
        f"Comparisons: {len(details)}",
        f"Supporting: {supporting}",
        f"Contradicting: {contradicting}"
    ]

    if score > 0.7:
        summary.append("Verdict: Strongly supported")
    elif score > 0.5:
        summary.append("Verdict: Partially supported")
    elif score > 0.3:
        summary.append("Verdict: Weak support")
    else:
        summary.append("Verdict: Likely false")

    return "\n".join(summary)


__all__ = ['verify', 'verify_with_metadata', 'get_verification_summary']