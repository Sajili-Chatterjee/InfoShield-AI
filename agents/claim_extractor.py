# agents/claim_extractor.py

import nltk
from nltk.tokenize import sent_tokenize
import re
import logging

logger = logging.getLogger(__name__)

# Ensure punkt is available (SAFE handling for production)
def ensure_nltk_resources():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logger.warning("NLTK punkt not found. Attempting download...")
        try:
            nltk.download('punkt', quiet=True)
        except Exception as e:
            logger.error(f"Failed to download punkt: {e}")
            raise RuntimeError("NLTK resource 'punkt' is required but could not be loaded.")

# Call once (safe)
ensure_nltk_resources()


def extract_claims(text):
    """
    Extract claims from OCR text.
    Preserves core logic of sentence tokenization and filtering.
    """
    if not text or not isinstance(text, str):
        return []

    # Clean OCR artifacts
    text = clean_ocr_text(text)

    try:
        sentences = sent_tokenize(text)
    except Exception as e:
        logger.error(f"Sentence tokenization failed: {e}")
        return []

    # Basic filtering
    claims = [s.strip() for s in sentences if len(s.split()) > 3]

    # Additional filtering for OCR quality
    claims = [claim for claim in claims if not is_gibberish(claim)]

    logger.debug(f"Extracted {len(claims)} claims")

    return claims


def clean_ocr_text(text):
    """
    Clean common OCR artifacts from screenshot text.
    """
    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove non-printable characters
    text = ''.join(
        char for char in text
        if char.isprintable() or char in ['\n', '\t']
    )

    return text.strip()


def is_gibberish(text):
    """
    Check if text is likely gibberish.
    """
    if not text:
        return True

    alpha_count = sum(1 for c in text if c.isalpha())
    total_count = len(text.replace(' ', ''))

    if total_count == 0:
        return True

    alpha_ratio = alpha_count / total_count

    # Slightly relaxed threshold for real-world text
    return alpha_ratio < 0.5


def extract_key_claims(text, max_claims=5):
    """
    Extract the most important claims from text.
    """
    all_claims = extract_claims(text)

    if len(all_claims) > max_claims:
        scored_claims = []

        for i, claim in enumerate(all_claims):
            position_score = 1.0 / (i + 1)
            length_score = len(claim.split()) / 50
            total_score = position_score + length_score

            scored_claims.append((total_score, claim))

        scored_claims.sort(reverse=True)
        key_claims = [claim for score, claim in scored_claims[:max_claims]]
    else:
        key_claims = all_claims

    logger.debug(f"Selected {len(key_claims)} key claims")

    return key_claims


__all__ = ['extract_claims', 'extract_key_claims', 'clean_ocr_text']