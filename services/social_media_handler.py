"""
services/social_media_handler.py
Detects and extracts text from social media URLs.
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
    )
}
REQUEST_TIMEOUT = 15

_SOCIAL_DOMAINS = {
    "reddit.com":    "reddit",
    "redd.it":       "reddit",
    "twitter.com":   "twitter",
    "x.com":         "twitter",
    "facebook.com":  "facebook",
    "fb.com":        "facebook",
    "instagram.com": "instagram",
    "tiktok.com":    "tiktok",
    "youtube.com":   "youtube",
    "youtu.be":      "youtube",
}


def is_social_media_url(url: str) -> bool:
    """Return True if *url* belongs to a known social media platform."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in _SOCIAL_DOMAINS)


def _detect_platform(url: str) -> str:
    url_lower = url.lower()
    for domain, platform in _SOCIAL_DOMAINS.items():
        if domain in url_lower:
            return platform
    return "unknown"


def extract_social_text(url: str) -> Dict:
    """
    Extract text content from a social media URL.

    Returns
    -------
    {"text": str, "platform": str, "error": str|None}
    """
    platform = _detect_platform(url)
    logger.info(f"Extracting from platform: {platform}, url: {url}")

    if platform == "reddit":
        return _extract_reddit(url)
    elif platform == "twitter":
        return _extract_twitter(url)
    elif platform == "youtube":
        return _extract_youtube(url)
    else:
        return _extract_generic_fallback(url, platform)


def _extract_reddit(url: str) -> Dict:
    """Use Reddit's public JSON API — no auth needed for public posts."""
    try:
        json_url = url.rstrip("/") + ".json"
        resp = requests.get(json_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        post     = data[0]["data"]["children"][0]["data"]
        title    = post.get("title", "")
        selftext = post.get("selftext", "")

        comments = []
        try:
            for c in data[1]["data"]["children"][:5]:
                body = c["data"].get("body", "")
                if body and body != "[deleted]":
                    comments.append(body)
        except Exception:
            pass

        text = title
        if selftext:
            text += "\n\n" + selftext
        if comments:
            text += "\n\nTop comments: " + " | ".join(comments)

        return {"text": text.strip(), "platform": "reddit", "error": None}

    except Exception as e:
        logger.warning(f"Reddit JSON API failed: {e}")
        return {"text": "", "platform": "reddit", "error": str(e)}


def _extract_twitter(url: str) -> Dict:
    """Twitter/X blocks all unauthenticated scraping — return a clear error."""
    return {
        "text": "",
        "platform": "twitter",
        "error": (
            "Twitter/X requires authentication to access tweet content. "
            "Please paste the tweet text directly instead of a URL."
        ),
    }


def _extract_youtube(url: str) -> Dict:
    """Extract video title from YouTube oEmbed API."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        resp   = requests.get(oembed_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data   = resp.json()
        title  = data.get("title", "")
        author = data.get("author_name", "")
        text   = f"YouTube video: '{title}' by {author}" if title else ""
        return {"text": text, "platform": "youtube", "error": None if text else "No title found"}
    except Exception as e:
        return {"text": "", "platform": "youtube", "error": str(e)}


def _extract_generic_fallback(url: str, platform: str) -> Dict:
    """Generic BeautifulSoup scrape — will fail for login-gated platforms."""
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text = " ".join(
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
            if len(p.get_text()) > 20
        )
        text = re.sub(r"\s{2,}", " ", text).strip()

        if not text:
            return {
                "text": "",
                "platform": platform,
                "error": f"{platform.capitalize()} requires login — cannot extract text automatically.",
            }
        return {"text": text, "platform": platform, "error": None}

    except Exception as e:
        return {"text": "", "platform": platform, "error": str(e)}