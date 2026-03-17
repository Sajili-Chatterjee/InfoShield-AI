# agents/retriever.py

import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "is", "are", "on", "in", "at", "of", "and",
    "a", "an", "to", "from", "this", "that", "with",
    "for", "by", "as", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "but", "or",
    "if", "then", "else", "when", "up", "so", "than"
}

# ✅ FIX: Absolute path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_PATH = BASE_DIR / "data" / "knowledge_base.json"

KNOWLEDGE_BASE = []

def load_knowledge_base():
    global KNOWLEDGE_BASE

    try:
        if KNOWLEDGE_BASE_PATH.exists():
            with open(KNOWLEDGE_BASE_PATH, "r", encoding='utf-8') as f:
                KNOWLEDGE_BASE = json.load(f)
            logger.info(f"Loaded {len(KNOWLEDGE_BASE)} KB items")
        else:
            logger.warning("Knowledge base not found. Creating empty one.")

            # ✅ FIX: ensure directory exists
            KNOWLEDGE_BASE_PATH.parent.mkdir(parents=True, exist_ok=True)

            KNOWLEDGE_BASE = []
            with open(KNOWLEDGE_BASE_PATH, "w", encoding='utf-8') as f:
                json.dump([], f)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in knowledge base")
        KNOWLEDGE_BASE = []

    except Exception as e:
        logger.error(f"KB load failed: {e}")
        KNOWLEDGE_BASE = []


# Load once at startup
load_knowledge_base()


def clean_text(text):
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def preprocess(text):
    if not text or not isinstance(text, str):
        return set()

    text = clean_text(text)
    words = text.split()

    return set(w for w in words if w not in STOPWORDS and len(w) > 1)


def simple_similarity(claim, text):
    claim_words = preprocess(claim)
    text_words = preprocess(text)

    overlap = claim_words.intersection(text_words)

    if overlap:
        length_weight = sum(len(word) for word in overlap) / 100
        return (len(overlap) / (len(claim_words) + 1)) + length_weight

    return 0


def retrieve(claims, top_k=2):
    if not KNOWLEDGE_BASE or not claims:
        return []

    if isinstance(claims, str):
        claims = [claims]

    all_scored_items = {}

    for claim in claims:
        for item in KNOWLEDGE_BASE:

            if isinstance(item, dict):
                text = item.get("combined_text") or item.get("text", "")
                confidence = item.get("confidence", 1.0)
            else:
                text = item
                confidence = 1.0
            if not text:
                continue

            score = simple_similarity(claim, text)

# 🔥 Boost using KB confidence
            score *= confidence

            if score > 0:
                if text not in all_scored_items or score > all_scored_items[text]:
                    all_scored_items[text] = score

    # ✅ FIX: preserve ranking (no set())
    sorted_items = sorted(
        all_scored_items.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [text for text, _ in sorted_items[:top_k]]


def retrieve_with_metadata(claims, top_k=2):
    if not KNOWLEDGE_BASE or not claims:
        return []

    if isinstance(claims, str):
        claims = [claims]

    all_scored_items = {}

    for claim in claims:
        for item in KNOWLEDGE_BASE:

            if isinstance(item, dict):
                text = item.get("combined_text") or item.get("text", "")
                confidence = item.get("confidence", 1.0)
            else:
                text = item
                confidence = 1.0

            if not text:
                continue

            score = simple_similarity(claim, text)
            score *= confidence  # 🔥 boost

            if score > 0:
                metadata = {
                    'text': text,
                    'score': score,
                    'source': item.get("source", "unknown") if isinstance(item, dict) else "unknown",
                    'confidence': confidence,
                    'date': item.get("date") if isinstance(item, dict) else None,
                    'url': item.get("url") if isinstance(item, dict) else None
                }

                if text not in all_scored_items or score > all_scored_items[text]['score']:
                    all_scored_items[text] = metadata

    sorted_results = sorted(
        all_scored_items.values(),
        key=lambda x: x['score'],
        reverse=True
    )

    return sorted_results[:top_k]

def reload_knowledge_base():
    try:
        load_knowledge_base()
        return True
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        return False


__all__ = ['retrieve', 'retrieve_with_metadata', 'reload_knowledge_base']