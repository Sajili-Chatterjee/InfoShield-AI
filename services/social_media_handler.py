import re
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ---------------------------
# 🔹 SAFE REQUEST
# ---------------------------
def fetch_html(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.text
        return None
    except:
        return None


# ---------------------------
# 🔹 REDDIT (SCRAPING VERSION)
# ---------------------------
def extract_reddit_text(url: str) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
    html = fetch_html(url)
    if not html:
        return None, "Failed to fetch Reddit page", None

    soup = BeautifulSoup(html, "html.parser")

    text_parts = []

    # Title
    title = soup.find("h1")
    if title:
        text_parts.append(title.get_text())

    # Content (Reddit post body)
    content = soup.find("div", {"data-click-id": "text"})
    if content:
        text_parts.append(content.get_text())

    text = " ".join(text_parts).strip()

    if len(text) < 10:
        return None, "Could not extract Reddit content", None

    metadata = {
        "platform": "reddit",
        "url": url
    }

    return text, None, metadata


# ---------------------------
# 🔹 GENERIC SCRAPER (ALL PLATFORMS)
# ---------------------------
def extract_generic_text(url: str, platform: str):
    html = fetch_html(url)
    if not html:
        return None, "Request failed", None

    soup = BeautifulSoup(html, "html.parser")

    text = ""

    # Try meta description (best method)
    meta = soup.find("meta", {"property": "og:description"}) or \
           soup.find("meta", {"name": "description"})

    if meta and meta.get("content"):
        text = meta["content"]

    # Fallback
    if len(text) < 20:
        text = soup.get_text()

    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) < 10:
        return None, f"Could not extract {platform} content", None

    metadata = {
        "platform": platform,
        "url": url
    }

    return text, None, metadata


# ---------------------------
# 🔹 PLATFORM DETECTION
# ---------------------------
def detect_platform(url: str) -> str:
    url = url.lower()

    if "reddit.com" in url:
        return "reddit"
    elif "twitter.com" in url or "x.com" in url:
        return "twitter"
    elif "facebook.com" in url:
        return "facebook"
    elif "instagram.com" in url:
        return "instagram"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"

    return "unknown"


# ---------------------------
# 🔹 MAIN FUNCTION
# ---------------------------
def extract_social_text(url: str, include_metadata=False):

    platform = detect_platform(url)

    result = {
        "platform": platform,
        "url": url,
        "success": False,
        "text": None,
        "error": None
    }

    try:
        if platform == "reddit":
            text, error, metadata = extract_reddit_text(url)
        else:
            text, error, metadata = extract_generic_text(url, platform)

        result["text"] = text
        result["error"] = error

        if metadata:
            result.update(metadata)

        if text and len(text.strip()) > 10:
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    # Remove metadata if not needed
    if not include_metadata:
        result = {
            "platform": result["platform"],
            "url": result["url"],
            "success": result["success"],
            "text": result["text"],
            "error": result["error"]
        }

    return result


# ---------------------------
# 🔹 SIMPLE WRAPPER
# ---------------------------
def extract_social_text_simple(url: str):
    result = extract_social_text(url)

    if result["success"]:
        return result["text"], None
    return None, result["error"]