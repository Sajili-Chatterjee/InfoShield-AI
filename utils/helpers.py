import re

def clean_text(text):
    """
    Basic text cleaning (used across pipeline)
    """
    if not text or not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def get_domain_score(url):
    trusted = ["bbc.com", "reuters.com", "thehindu.com", "ndtv.com"]

    for t in trusted:
        if t in url:
            return 0.9

    return 0.4