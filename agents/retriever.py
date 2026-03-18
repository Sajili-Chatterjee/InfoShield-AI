# agents/retriever.py
#
# FIXES:
# 1. Stop words removed from tokenization — "the/is/are/on/to/a/of" were
#    causing false matches between completely unrelated content.
# 2. Minimum similarity threshold added — evidence is only returned if
#    Jaccard score >= MIN_SCORE. Previously top-k was returned even when
#    score was 0.001 (one common word overlap).
# 3. TF-IDF style term weighting added — rare/specific words (iran, trump,
#    vaccine, climate) score higher than common words.
# 4. Returns empty list [] when no evidence is genuinely relevant,
#    rather than returning the least-bad match.

import json
import logging
import os
import re
import math
from collections import Counter
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_knowledge_base: List[Dict[str, Any]] = []
_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")

# Minimum Jaccard similarity to count as relevant evidence
# 0.08 means at least ~8% of meaningful words must overlap
MIN_SCORE = 0.08

# Common English stop words — excluded from matching
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "that", "this", "these", "those", "it", "its", "not", "no",
    "as", "if", "up", "out", "so", "he", "she", "we", "they",
    "his", "her", "our", "their", "about", "also", "can", "into",
    "than", "then", "when", "there", "what", "which", "who", "how",
    "all", "any", "more", "most", "other", "some", "such", "only",
    "after", "before", "now", "just", "over", "under", "between",
    "through", "during", "while", "because", "since", "per", "new",
}


# -----------------------------------------------------------------------
# Knowledge-base management
# -----------------------------------------------------------------------

def reload_knowledge_base():
    global _knowledge_base
    path = os.path.abspath(_KB_PATH)
    if not os.path.exists(path):
        logger.warning(f"Knowledge base not found at {path}")
        _knowledge_base = []
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _knowledge_base = data if isinstance(data, list) else data.get("facts", [])
        logger.info(f"Loaded {len(_knowledge_base)} knowledge-base entries")
    except Exception as e:
        logger.error(f"Failed to load knowledge base: {e}")
        _knowledge_base = []


def _get_kb() -> List[Dict[str, Any]]:
    if not _knowledge_base:
        reload_knowledge_base()
    return _knowledge_base


# -----------------------------------------------------------------------
# Tokenization — strips stop words and short tokens
# -----------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """
    Return meaningful word tokens only.
    - Lowercase
    - Only alphabetic words 3+ chars
    - Stop words removed
    """
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def _token_set(text: str) -> set:
    return set(_tokenize(text))


# -----------------------------------------------------------------------
# Scoring — Jaccard with IDF boost for rare/specific terms
# -----------------------------------------------------------------------

def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union        = len(a | b)
    return intersection / union if union > 0 else 0.0


def _build_idf(kb: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Build inverse-document-frequency weights from the knowledge base.
    Words that appear in many KB entries get lower weight.
    Rare/specific words (iran, vaccine, climate) get higher weight.
    """
    N = len(kb) or 1
    doc_freq: Counter = Counter()
    for entry in kb:
        text = entry.get("text", entry) if isinstance(entry, dict) else str(entry)
        for word in _token_set(text):
            doc_freq[word] += 1
    return {word: math.log(N / freq) for word, freq in doc_freq.items()}


def _weighted_overlap(claim_tokens: set, fact_tokens: set,
                      idf: Dict[str, float]) -> float:
    """
    IDF-weighted overlap score.
    Words that are rare in the KB (specific topics) contribute more to the score.
    """
    common = claim_tokens & fact_tokens
    if not common:
        return 0.0
    all_tokens = claim_tokens | fact_tokens
    # Weighted intersection / weighted union
    w_inter = sum(idf.get(w, 1.0) for w in common)
    w_union  = sum(idf.get(w, 1.0) for w in all_tokens)
    return w_inter / w_union if w_union > 0 else 0.0


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------

def retrieve_evidence(claims: List[str], top_k: int = 5) -> List[str]:
    """
    Return knowledge-base entries that are genuinely relevant to the claims.

    Returns empty list [] if no entry meets the MIN_SCORE threshold.
    This prevents unrelated evidence from polluting the verdict.
    """
    kb = _get_kb()
    if not kb or not claims:
        return []

    # Build IDF weights from KB
    idf = _build_idf(kb)

    # Combine all claim tokens into one pool
    claim_tokens = set()
    for c in claims:
        claim_tokens |= _token_set(c)

    if not claim_tokens:
        logger.debug("No meaningful tokens found in claims")
        return []

    scored: List[tuple] = []

    for entry in kb:
        fact_text   = entry.get("text", entry) if isinstance(entry, dict) else str(entry)
        fact_tokens = _token_set(fact_text)

        if not fact_tokens:
            continue

        # Use IDF-weighted overlap as primary score
        score = _weighted_overlap(claim_tokens, fact_tokens, idf)

        # Only include entries that meet the minimum threshold
        if score >= MIN_SCORE:
            scored.append((score, fact_text))

    if not scored:
        logger.debug(
            f"No evidence met MIN_SCORE={MIN_SCORE} threshold for claims: "
            f"{[c[:60] for c in claims[:2]]}"
        )
        return []

    # Sort by relevance, return top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    evidence = [text for _, text in scored[:top_k]]

    logger.debug(
        f"Retrieved {len(evidence)} evidence items "
        f"(top score: {scored[0][0]:.3f}) for {len(claims)} claims"
    )
    return evidence