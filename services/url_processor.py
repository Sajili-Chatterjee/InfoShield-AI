"""
services/url_processor.py
Extracts clean article text from a news URL.
"""

import logging
import re
import requests
from typing import Dict

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 15


def extract_text_from_url(url: str) -> Dict:
    """
    Try newspaper3k first; fall back to BeautifulSoup scraping.

    Returns
    -------
    {"text": str, "title": str, "error": str|None}
    """
    result = _try_newspaper(url)
    if result["text"]:
        return result

    logger.info(f"newspaper3k failed for {url}, trying BeautifulSoup fallback")
    return _try_beautifulsoup(url)


def extract_text_from_url_simple(url: str):
    """Backward-compat wrapper — returns (text, error) tuple."""
    result = extract_text_from_url(url)
    return result["text"], result["error"]


def _try_newspaper(url: str) -> Dict:
    try:
        import lxml_html_clean  # noqa: F401
        import newspaper
        article = newspaper.Article(url, request_timeout=REQUEST_TIMEOUT)
        article.headers = HEADERS
        article.download()
        article.parse()
        text  = (article.text  or "").strip()
        title = (article.title or "").strip()
        if len(text) < 50:
            return {"text": "", "title": title, "error": "Article text too short"}
        return {"text": text, "title": title, "error": None}
    except ImportError:
        logger.warning("lxml_html_clean missing — run: pip install lxml_html_clean")
        return {"text": "", "title": "", "error": "lxml_html_clean not installed"}
    except Exception as e:
        return {"text": "", "title": "", "error": str(e)}


def _try_beautifulsoup(url: str) -> Dict:
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for tag in soup(["script", "style", "nav", "header", "footer",
                          "aside", "form", "button", "iframe"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else ""

        article_body = (
            soup.find("article")
            or soup.find(class_=re.compile(r"article|content|story|post", re.I))
            or soup.find("main")
        )
        container  = article_body or soup.find("body")
        paragraphs = container.find_all("p") if container else []
        text = " ".join(
            p.get_text(" ", strip=True)
            for p in paragraphs
            if len(p.get_text()) > 30
        )
        text = re.sub(r"\s{2,}", " ", text).strip()

        if len(text) < 50:
            return {"text": "", "title": title, "error": "Could not extract meaningful text"}

        return {"text": text, "title": title, "error": None}

    except Exception as e:
        logger.error(f"BeautifulSoup extraction failed for {url}: {e}")
        return {"text": "", "title": "", "error": str(e)}