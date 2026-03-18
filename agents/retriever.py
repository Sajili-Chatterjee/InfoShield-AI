import json
import logging
import os
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_knowledge_base: List[Dict[str, Any]] = []
_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")


def reload_knowledge_base():
    global _knowledge_base
    path = os.path.abspath(_KB_PATH)
    if not os.path.exists(path):
        logger.warning(f"Knowledge base not found at {path}; using empty KB.")
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


def _tokenize(text: str) -> set:
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def _jaccard_similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def retrieve_evidence(claims: List[str], top_k: int = 5) -> List[str]:
    kb = _get_kb()
    if not kb or not claims:
        return []

    claim_tokens = _tokenize(" ".join(claims))
    scored = []

    for entry in kb:
        fact_text = entry.get("text", entry) if isinstance(entry, dict) else str(entry)
        fact_tokens = _tokenize(fact_text)
        score = _jaccard_similarity(claim_tokens, fact_tokens)
        if score > 0:
            scored.append((score, fact_text))

    scored.sort(key=lambda x: x[0], reverse=True)
    evidence = [text for _, text in scored[:top_k]]
    logger.debug(f"Retrieved {len(evidence)} evidence items for {len(claims)} claims")
    return evidence