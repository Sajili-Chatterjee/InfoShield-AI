import logging
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse
import time
import re
from typing import Dict, Tuple, Optional, Any

from services.social_media_handler import extract_social_text, detect_platform

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10
MAX_CONTENT_LENGTH = 10000
MIN_CONTENT_LENGTH = 50

# Added user agents for fallback
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
]


# ---------------------------
# 🔹 MAIN FUNCTION
# ---------------------------
def extract_text_from_url(url: str, include_metadata: bool = False) -> Dict[str, Any]:

    start_time = time.time()

    result = {
        "url": url,
        "success": False,
        "text": None,
        "error": None,
        "method": None,
        "platform": None
    }

    if not url or not isinstance(url, str):
        result["error"] = "Invalid URL"
        return result

    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    result["domain"] = domain

    # ---------------------------
    # 🔹 SOCIAL MEDIA
    # ---------------------------
    platform = detect_platform(url)
    result["platform"] = platform

    if platform != "unknown":
        social = extract_social_text(url, include_metadata=True)

        if social.get("success"):
            result.update({
                "text": social.get("text"),
                "success": True,
                "method": f"social_{platform}",
                "extraction_time": round(time.time() - start_time, 3)
            })
            return result

    # ---------------------------
    # 🔹 NEWSPAPER + FALLBACK FIX
    # ---------------------------
    try:
        try:
            article = Article(url)
            article.download()
            time.sleep(0.5)
            article.parse()

            if article.text and len(article.text.strip()) > MIN_CONTENT_LENGTH:
                text = article.text.strip()
                method_used = "newspaper3k"
            else:
                raise ValueError("Empty article from newspaper")

        except Exception as e:
            logger.warning(f"Newspaper failed, switching to BeautifulSoup: {e}")

            res = requests.get(
                url,
                headers={"User-Agent": USER_AGENTS[0]},
                timeout=REQUEST_TIMEOUT
            )

            soup = BeautifulSoup(res.text, "html.parser")

            # remove noise
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text() for p in paragraphs])

            text = re.sub(r"\s+", " ", text).strip()
            method_used = "beautifulsoup_fallback"

        # ---------------------------
        # 🔹 SAFETY CHECK (CRITICAL)
        # ---------------------------
        if not text or len(text) < MIN_CONTENT_LENGTH:
            return {
                "url": url,
                "success": False,
                "error": "Could not extract meaningful content"
            }

        # truncate
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH]

        result.update({
            "text": text,
            "success": True,
            "method": method_used,
            "extraction_time": round(time.time() - start_time, 3)
        })

        return result

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        result["error"] = str(e)
        return result


# ---------------------------
# 🔹 SIMPLE VERSION (IMPORTANT)
# ---------------------------
def extract_text_from_url_simple(url: str) -> Tuple[Optional[str], Optional[str]]:
    result = extract_text_from_url(url)

    if result.get("success"):
        return result.get("text"), None

    return None, result.get("error")


# ---------------------------
# 🔹 METADATA
# ---------------------------
def get_url_metadata(url: str) -> Dict[str, Any]:

    meta = {"url": url, "success": False}

    try:
        parsed = urlparse(url)
        meta["domain"] = parsed.netloc
        meta["platform"] = detect_platform(url)

        res = requests.get(url, timeout=5)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")

            title = soup.find("title")
            if title:
                meta["title"] = title.get_text()

            meta["success"] = True

    except Exception as e:
        meta["error"] = str(e)

    return meta


__all__ = [
    "extract_text_from_url",
    "extract_text_from_url_simple",
    "get_url_metadata"
]