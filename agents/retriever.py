# agents/retriever.py

import json
import re
from pathlib import Path

# Simple stopwords list (lightweight) - preserved
STOPWORDS = {
    "the", "is", "are", "on", "in", "at", "of", "and",
    "a", "an", "to", "from", "this", "that", "with",
    "for", "by", "as", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "but", "or",
    "if", "then", "else", "when", "up", "so", "than"
}

# Load knowledge base with error handling
KNOWLEDGE_BASE = []
KNOWLEDGE_BASE_PATH = "data/knowledge_base.json"

try:
    # Check if file exists
    if Path(KNOWLEDGE_BASE_PATH).exists():
        with open(KNOWLEDGE_BASE_PATH, "r", encoding='utf-8') as f:
            KNOWLEDGE_BASE = json.load(f)
        print(f"Loaded {len(KNOWLEDGE_BASE)} items from knowledge base")
    else:
        # Create empty knowledge base if file doesn't exist
        print(f"Warning: {KNOWLEDGE_BASE_PATH} not found. Creating empty knowledge base.")
        KNOWLEDGE_BASE = []
        # Optionally create the file
        with open(KNOWLEDGE_BASE_PATH, "w", encoding='utf-8') as f:
            json.dump([], f)
except json.JSONDecodeError:
    print(f"Error: {KNOWLEDGE_BASE_PATH} contains invalid JSON. Using empty knowledge base.")
    KNOWLEDGE_BASE = []
except Exception as e:
    print(f"Error loading knowledge base: {e}")
    KNOWLEDGE_BASE = []


def preprocess(text):
    """
    Preprocess text for matching - preserves core logic but adds cleaning.
    """
    if not text or not isinstance(text, str):
        return set()
    
    # Basic cleaning for OCR artifacts
    text = clean_text(text)
    
    # Original logic preserved
    words = text.lower().split()
    return set([w for w in words if w not in STOPWORDS and len(w) > 1])


def clean_text(text):
    """
    Clean text from OCR artifacts for better matching.
    """
    # Remove special characters but keep words
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def simple_similarity(claim, text):
    """
    Calculate similarity between claim and text - preserves core logic.
    """
    claim_words = preprocess(claim)
    text_words = preprocess(text)

    overlap = claim_words.intersection(text_words)

    # Enhanced scoring: consider length of overlapping words
    if len(overlap) > 0:
        # Add weighted score based on word length (longer words are more significant)
        length_weight = sum(len(word) for word in overlap) / 100
        return len(overlap) + length_weight
    
    return len(overlap)


def retrieve(claims, top_k=2):
    """
    Retrieve relevant information for claims - preserves core logic.
    """
    if not KNOWLEDGE_BASE:
        print("Warning: Knowledge base is empty")
        return []
    
    if not claims:
        return []
    
    # Ensure claims is a list
    if isinstance(claims, str):
        claims = [claims]
    
    results = []
    all_scored_items = {}  # To avoid duplicates with scores

    for claim in claims:
        scored = []

        for item in KNOWLEDGE_BASE:
            # Handle different knowledge base formats
            text = item.get("text", "") if isinstance(item, dict) else item
            if not text:
                continue
                
            score = simple_similarity(claim, text)
            
            # Add metadata if available
            metadata = item.get("source", "unknown") if isinstance(item, dict) else "unknown"
            
            scored.append((score, text, metadata))

        # Sort by score descending (preserved logic)
        scored.sort(reverse=True, key=lambda x: x[0])

        # Take only relevant ones (score > 0) - preserved logic
        for score, text, metadata in scored:
            if score > 0 and text not in all_scored_items:
                all_scored_items[text] = {
                    'score': score,
                    'metadata': metadata,
                    'text': text
                }

    # Convert to list and sort by score
    sorted_items = sorted(
        all_scored_items.values(), 
        key=lambda x: x['score'], 
        reverse=True
    )
    
    # Return top_k results (preserved logic)
    results = [item['text'] for item in sorted_items[:top_k]]

    return list(set(results)) if results else []


def retrieve_with_metadata(claims, top_k=2):
    """
    Enhanced retrieval that returns both text and metadata.
    This builds on the core retrieve function.
    """
    if not KNOWLEDGE_BASE or not claims:
        return []
    
    if isinstance(claims, str):
        claims = [claims]
    
    all_scored_items = {}

    for claim in claims:
        for item in KNOWLEDGE_BASE:
            text = item.get("text", "") if isinstance(item, dict) else item
            if not text:
                continue
                
            score = simple_similarity(claim, text)
            
            if score > 0:
                # Store metadata
                metadata = {
                    'score': score,
                    'source': item.get("source", "unknown") if isinstance(item, dict) else "unknown",
                    'date': item.get("date", None) if isinstance(item, dict) else None,
                    'url': item.get("url", None) if isinstance(item, dict) else None
                }
                
                if text not in all_scored_items or score > all_scored_items[text]['score']:
                    all_scored_items[text] = {
                        'text': text,
                        **metadata
                    }

    # Sort and return top_k
    sorted_results = sorted(
        all_scored_items.values(), 
        key=lambda x: x['score'], 
        reverse=True
    )
    
    return sorted_results[:top_k]


def reload_knowledge_base():
    """
    Reload knowledge base from file (useful for dynamic updates).
    """
    global KNOWLEDGE_BASE
    try:
        if Path(KNOWLEDGE_BASE_PATH).exists():
            with open(KNOWLEDGE_BASE_PATH, "r", encoding='utf-8') as f:
                KNOWLEDGE_BASE = json.load(f)
            return True
    except Exception as e:
        print(f"Error reloading knowledge base: {e}")
        return False


# Keep original exports
__all__ = ['retrieve', 'retrieve_with_metadata', 'reload_knowledge_base']