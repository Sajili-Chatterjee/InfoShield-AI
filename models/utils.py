import re

def clean_text(text: str) -> str:
    """
    Basic text cleaning for NLP pipeline
    """

    if not text:
        return ""

    # lower case
    text = text.lower()

    # remove urls
    text = re.sub(r"http\S+|www\S+", "", text)

    # remove special characters
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text