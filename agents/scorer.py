"""
agents/scorer.py — v2
Combines multiple signals into a final credibility verdict.

CHANGES v2:
- Zero-shot weight: 50% -> 40%
- Linguistic weight: 25% -> 35%
- Hard override: ling_score < 0.25 caps final score at 0.50 (FAKE)
  Prevents BART from overriding obvious sensational/fake writing style.
"""

import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_SENSATIONAL = re.compile(
    r"\b(shocking|bombshell|breaking|exposed|secret|they don.t want you|"
    r"cover.?up|mainstream media|deep state|wake up|sheeple|plandemic|"
    r"miracle|cure|banned|censored|urgent|alert|hoax|conspiracy|"
    r"you won.t believe|share before|deleted|truth revealed|"
    r"what they don.t tell you|hidden agenda)\b",
    re.IGNORECASE,
)
_CREDIBLE_SOURCES = re.compile(
    r"\b(according to|researchers|scientists|study|journal|published|"
    r"university|institute|data shows|report|survey|peer.reviewed|"
    r"WHO|CDC|NIH|NASA|BBC|Reuters|AP|AFP|government|official|"
    r"confirmed|evidence|analysis|university|harvard|oxford|stanford)\b",
    re.IGNORECASE,
)
_EXCESSIVE_CAPS    = re.compile(r"\b[A-Z]{4,}\b")
_EXCESSIVE_PUNCT   = re.compile(r"[!?]{2,}")
_ANONYMOUS_SOURCES = re.compile(
    r"\b(sources say|insiders claim|anonymous|unnamed|some people|"
    r"many believe|people are saying|word on the street|everyone knows)\b",
    re.IGNORECASE,
)


def _linguistic_score(text: str) -> float:
    if not text:
        return 0.5
    words = len(text.split()) or 1
    fake_hits = (
        len(_SENSATIONAL.findall(text))
        + len(_EXCESSIVE_CAPS.findall(text)) * 0.7
        + len(_EXCESSIVE_PUNCT.findall(text)) * 0.7
        + len(_ANONYMOUS_SOURCES.findall(text)) * 1.2
    )
    real_hits = len(_CREDIBLE_SOURCES.findall(text))
    fake_rate = min(fake_hits / (words / 10), 1.0)
    real_rate = min(real_hits / (words / 10), 1.0)
    score = 0.5 - (fake_rate * 0.45) + (real_rate * 0.3)
    return round(max(0.0, min(1.0, score)), 4)


def _evidence_score(claims: List[str], evidence: List[str]) -> float:
    if not evidence or not claims:
        return 0.5
    def tokens(t):
        return set(re.findall(r"\b[a-z]{3,}\b", t.lower()))
    ev_tokens: set = set()
    for e in evidence:
        ev_tokens |= tokens(e)
    supported = sum(1 for c in claims if tokens(c) & ev_tokens)
    return round(supported / len(claims), 4)


def compute_score(
    text: str,
    claims: List[str],
    evidence: List[str],
) -> Dict[str, Any]:
    # ---- Signal 1: Zero-shot (40%) ----
    zs_score = 0.5
    zs_label = "unavailable"
    try:
        from models.model_loader import get_zero_shot_classifier
        classifier = get_zero_shot_classifier()
        out       = classifier(text[:1024], candidate_labels=["real news", "misinformation"])
        label_map = dict(zip(out["labels"], out["scores"]))
        zs_score  = round(label_map.get("real news", 0.5), 4)
        zs_label  = out["labels"][0]
    except Exception as e:
        logger.warning(f"Zero-shot classifier unavailable: {e}")

    # ---- Signal 2: Linguistic (35%) ----
    ling_score = _linguistic_score(text)

    # ---- Signal 3: Evidence (25%) ----
    ev_score = _evidence_score(claims, evidence)

    # ---- Weighted combination ----
    final_score = round(0.40 * zs_score + 0.35 * ling_score + 0.25 * ev_score, 4)

    # ---- Hard override for extremely sensational text ----
    override_note = ""
    if ling_score < 0.25:
        final_score = min(final_score, 0.50)
        override_note = (
            f" WARNING: Sensational language override applied "
            f"(linguistic score {ling_score:.2f} < 0.25) — capped as FAKE."
        )

    final_score = round(max(0.0, min(1.0, final_score)), 4)
    label       = "REAL" if final_score >= 0.55 else "FAKE"
    confidence  = round(final_score if label == "REAL" else (1.0 - final_score), 4)

    explanation = (
        f"Zero-shot classification: '{zs_label}' (score {zs_score:.2f}). "
        f"Linguistic credibility score: {ling_score:.2f}. "
        f"Evidence support score: {ev_score:.2f} "
        f"({len(evidence)} evidence item(s) retrieved). "
        f"Final weighted score: {final_score:.2f} -> verdict: {label}."
        f"{override_note}"
    )

    return {
        "project":     "InfoShield-AI",
        "label":       label,
        "confidence":  confidence,
        "explanation": explanation,
        "evidence":    evidence,
        "signals": {
            "zero_shot_score":  zs_score,
            "linguistic_score": ling_score,
            "evidence_score":   ev_score,
            "final_score":      final_score,
        },
    }