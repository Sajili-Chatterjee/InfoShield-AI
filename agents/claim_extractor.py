# agents/claim_extractor.py

import nltk
from nltk.tokenize import sent_tokenize
import re

# Ensure punkt is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_claims(text):
    """
    Extract claims from OCR text.
    Preserves core logic of sentence tokenization and filtering.
    """
    if not text or not isinstance(text, str):
        return []
    
    # Clean OCR artifacts (common issues from screenshot OCR)
    text = clean_ocr_text(text)
    
    # Tokenize into sentences
    sentences = sent_tokenize(text)

    # Basic filtering (remove very short sentences) - preserving original logic
    claims = [s.strip() for s in sentences if len(s.split()) > 3]
    
    # Additional filtering for OCR quality
    claims = [claim for claim in claims if not is_gibberish(claim)]
    
    return claims

def clean_ocr_text(text):
    """
    Clean common OCR artifacts from screenshot text.
    """
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR mistakes (optional - can be expanded)
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Remove any non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
    
    return text.strip()

def is_gibberish(text):
    """
    Check if text is likely gibberish (too many special chars, etc.)
    """
    if not text:
        return True
    
    # Calculate ratio of alphabetic characters
    alpha_count = sum(1 for c in text if c.isalpha())
    total_count = len(text.replace(' ', ''))
    
    if total_count == 0:
        return True
    
    alpha_ratio = alpha_count / total_count
    
    # If less than 60% alphabetic, likely gibberish
    return alpha_ratio < 0.6

def extract_key_claims(text, max_claims=5):
    """
    Extract the most important claims from text.
    This is a helper function that builds on the core extract_claims function.
    """
    all_claims = extract_claims(text)
    
    # If we have too many claims, prioritize by length and position
    if len(all_claims) > max_claims:
        # Score claims: longer claims often contain more substance
        # Claims at the beginning are often more important
        scored_claims = []
        for i, claim in enumerate(all_claims):
            position_score = 1.0 / (i + 1)  # Earlier claims get higher score
            length_score = len(claim.split()) / 50  # Normalize length
            total_score = position_score + length_score
            scored_claims.append((total_score, claim))
        
        # Sort by score and take top max_claims
        scored_claims.sort(reverse=True)
        key_claims = [claim for score, claim in scored_claims[:max_claims]]
    else:
        key_claims = all_claims
    
    return key_claims

# For backward compatibility, keep the original function name as the main export
# But add the key claims extractor for more focused analysis
__all__ = ['extract_claims', 'extract_key_claims', 'clean_ocr_text']