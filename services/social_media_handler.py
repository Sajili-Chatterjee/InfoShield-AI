# services/social_media_handler.py

import re
import requests
from bs4 import BeautifulSoup
import praw
import logging
import time
from typing import Dict, Tuple, Optional, Any
from urllib.parse import urlparse
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# 🔹 Configuration
# ---------------------------

# Reddit API Configuration (FREE API)
# In production, use environment variables
REDDIT_CONFIG = {
    "client_id": "YOUR_CLIENT_ID",  # Replace with env var in production
    "client_secret": "YOUR_CLIENT_SECRET",  # Replace with env var in production
    "user_agent": "InfoShield-AI/1.0 (Fake News Detection)"
}

# Initialize Reddit client
try:
    reddit = praw.Reddit(
        client_id=REDDIT_CONFIG["client_id"],
        client_secret=REDDIT_CONFIG["client_secret"],
        user_agent=REDDIT_CONFIG["user_agent"]
    )
    logger.info("Reddit API client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Reddit client: {e}")
    reddit = None

# Common headers for web scraping
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Platform patterns
PLATFORM_PATTERNS = {
    "reddit": [
        r"reddit\.com/r/\w+/comments/\w+",  # Reddit post
        r"reddit\.com/comments/\w+",         # Reddit comment
        r"redd\.it/\w+"                      # Reddit shortlink
    ],
    "twitter": [
        r"twitter\.com/\w+/status/\d+",      # Twitter tweet
        r"x\.com/\w+/status/\d+",            # X.com tweet
        r"t\.co/\w+"                          # Twitter shortlink
    ],
    "facebook": [
        r"facebook\.com/\d+/posts/\d+",       # Facebook post
        r"facebook\.com/\w+/posts/\d+",       # Facebook page post
        r"fb\.com/\d+",                        # Facebook shortlink
        r"facebook\.com/photo\.php\?fbid=\d+" # Facebook photo
    ],
    "instagram": [
        r"instagram\.com/p/\w+",               # Instagram post
        r"instagram\.com/reel/\w+",             # Instagram reel
        r"instagr\.am/\w+"                      # Instagram shortlink
    ],
    "tiktok": [
        r"tiktok\.com/@\w+/video/\d+",         # TikTok video
        r"tiktok\.com/\w+/video/\d+",           # TikTok alternative
        r"vm\.tiktok\.com/\w+"                   # TikTok shortlink
    ],
    "youtube": [
        r"youtube\.com/watch\?v=\w+",           # YouTube video
        r"youtu\.be/\w+",                        # YouTube shortlink
        r"youtube\.com/shorts/\w+"               # YouTube Shorts
    ],
    "linkedin": [
        r"linkedin\.com/posts/\w+",              # LinkedIn post
        r"linkedin\.com/feed/update/\w+"         # LinkedIn update
    ]
}

# Platform-specific selectors for scraping
PLATFORM_SELECTORS = {
    "twitter": [
        {"selector": "article div[lang]", "name": "tweet_text"},
        {"selector": "div.tweet-text", "name": "tweet_text_old"},
        {"selector": "div[data-testid='tweetText']", "name": "tweet_text_new"}
    ],
    "facebook": [
        {"selector": "div[data-ad-preview='message']", "name": "post_message"},
        {"selector": "div.userContent", "name": "user_content"},
        {"selector": "p[data-testid='post_message']", "name": "post_message_test"}
    ],
    "instagram": [
        {"selector": "div._a9zr", "name": "caption"},
        {"selector": "h1._a9zr", "name": "title_caption"},
        {"selector": "meta[property='og:description']", "name": "meta_description", "attribute": "content"}
    ],
    "tiktok": [
        {"selector": "div[data-e2e='video-desc']", "name": "video_description"},
        {"selector": "h1[data-e2e='video-title']", "name": "video_title"},
        {"selector": "meta[name='description']", "name": "meta_description", "attribute": "content"}
    ],
    "youtube": [
        {"selector": "meta[name='title']", "name": "meta_title", "attribute": "content"},
        {"selector": "meta[name='description']", "name": "meta_description", "attribute": "content"},
        {"selector": "#description", "name": "description"}
    ]
}


# ---------------------------
# 🔹 Reddit Extraction
# ---------------------------
def extract_reddit_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from Reddit post using PRAW API.
    Preserves original logic with enhancements.
    """
    if not reddit:
        return None, "Reddit API not initialized"
    
    try:
        logger.info(f"Extracting Reddit text from: {url}")
        submission = reddit.submission(url=url)
        
        # Get post title and content
        title = submission.title or ""
        selftext = submission.selftext or ""
        
        # Get top comments for context
        comments = []
        submission.comments.replace_more(limit=0)  # Remove "load more" comments
        for comment in submission.comments[:3]:  # Get top 3 comments
            if hasattr(comment, 'body'):
                comments.append(comment.body)
        
        # Combine text
        text_parts = [title, selftext]
        if comments:
            text_parts.append("Top comments: " + " ".join(comments[:2]))
        
        text = " ".join(text_parts).strip()
        
        if not text:
            return None, "No text content found in Reddit post"
        
        # Get metadata
        metadata = {
            "platform": "reddit",
            "post_id": submission.id,
            "author": str(submission.author) if submission.author else "unknown",
            "created_utc": submission.created_utc,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "subreddit": str(submission.subreddit),
            "url": url
        }
        
        logger.info(f"Successfully extracted Reddit text ({len(text)} chars)")
        return text, None, metadata
        
    except Exception as e:
        logger.error(f"Reddit extraction error: {str(e)}")
        return None, f"Reddit extraction failed: {str(e)}"


# ---------------------------
# 🔹 Twitter/X Extraction
# ---------------------------
def extract_twitter_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from Twitter/X post using web scraping.
    Preserves original logic with enhancements.
    """
    try:
        logger.info(f"Extracting Twitter/X text from: {url}")
        
        # Handle different URL formats
        if "t.co" in url:
            # Expand shortlink
            response = requests.head(url, allow_redirects=True, headers=DEFAULT_HEADERS)
            url = response.url
        
        # Make request with retry
        for attempt in range(3):
            try:
                res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
                if res.status_code == 200:
                    break
            except requests.RequestException as e:
                if attempt == 2:
                    raise
                time.sleep(1)
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Try multiple extraction methods
        text = ""
        
        # Method 1: Look for tweet text in meta tags
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            text = meta_desc["content"]
        
        # Method 2: Look for tweet in divs (original method)
        if len(text) < 20:
            text_blocks = soup.find_all("div", {"lang": True})
            text = " ".join([t.get_text() for t in text_blocks])
        
        # Method 3: Look for article content
        if len(text) < 20:
            article = soup.find("article")
            if article:
                text = article.get_text()
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 10:
            return None, "Could not extract tweet text"
        
        # Extract metadata
        metadata = {
            "platform": "twitter",
            "url": url,
            "extraction_method": "scraping"
        }
        
        # Try to get author/handle
        author_meta = soup.find("meta", {"property": "og:title"})
        if author_meta and author_meta.get("content"):
            metadata["author"] = author_meta["content"]
        
        logger.info(f"Successfully extracted Twitter text ({len(text)} chars)")
        return text, None, metadata
        
    except Exception as e:
        logger.error(f"Twitter extraction error: {str(e)}")
        return None, f"Twitter extraction failed: {str(e)}"


# ---------------------------
# 🔹 Facebook Extraction
# ---------------------------
def extract_facebook_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from Facebook post.
    """
    try:
        logger.info(f"Extracting Facebook text from: {url}")
        
        headers = DEFAULT_HEADERS.copy()
        headers["Accept-Language"] = "en-US,en;q=0.9"
        
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        text = ""
        
        # Try meta description
        meta_desc = soup.find("meta", {"property": "og:description"})
        if meta_desc and meta_desc.get("content"):
            text = meta_desc["content"]
        
        # Try content divs
        if len(text) < 20:
            content_divs = soup.find_all("div", {"data-ad-preview": "message"})
            text = " ".join([div.get_text() for div in content_divs])
        
        # Try user content
        if len(text) < 20:
            user_content = soup.find_all("div", {"class": "user-content"})
            text = " ".join([div.get_text() for div in user_content])
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 10:
            return None, "Could not extract Facebook post text"
        
        metadata = {
            "platform": "facebook",
            "url": url,
            "extraction_method": "scraping"
        }
        
        logger.info(f"Successfully extracted Facebook text ({len(text)} chars)")
        return text, None, metadata
        
    except Exception as e:
        logger.error(f"Facebook extraction error: {str(e)}")
        return None, f"Facebook extraction failed: {str(e)}"


# ---------------------------
# 🔹 Instagram Extraction
# ---------------------------
def extract_instagram_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text/caption from Instagram post.
    """
    try:
        logger.info(f"Extracting Instagram text from: {url}")
        
        headers = DEFAULT_HEADERS.copy()
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        text = ""
        
        # Try meta description (usually contains caption)
        meta_desc = soup.find("meta", {"property": "og:description"})
        if meta_desc and meta_desc.get("content"):
            text = meta_desc["content"]
        
        # Try caption divs
        if len(text) < 20:
            caption_divs = soup.find_all("div", {"class": "caption"})
            text = " ".join([div.get_text() for div in caption_divs])
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 10:
            return None, "Could not extract Instagram caption"
        
        metadata = {
            "platform": "instagram",
            "url": url,
            "extraction_method": "scraping"
        }
        
        logger.info(f"Successfully extracted Instagram text ({len(text)} chars)")
        return text, None, metadata
        
    except Exception as e:
        logger.error(f"Instagram extraction error: {str(e)}")
        return None, f"Instagram extraction failed: {str(e)}"


# ---------------------------
# 🔹 TikTok Extraction
# ---------------------------
def extract_tiktok_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text/description from TikTok video.
    """
    try:
        logger.info(f"Extracting TikTok text from: {url}")
        
        headers = DEFAULT_HEADERS.copy()
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        text = ""
        
        # Try meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            text = meta_desc["content"]
        
        # Try video description div
        desc_div = soup.find("div", {"data-e2e": "video-desc"})
        if desc_div:
            text = desc_div.get_text()
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 10:
            return None, "Could not extract TikTok description"
        
        metadata = {
            "platform": "tiktok",
            "url": url,
            "extraction_method": "scraping"
        }
        
        logger.info(f"Successfully extracted TikTok text ({len(text)} chars)")
        return text, None, metadata
        
    except Exception as e:
        logger.error(f"TikTok extraction error: {str(e)}")
        return None, f"TikTok extraction failed: {str(e)}"


# ---------------------------
# 🔹 YouTube Extraction
# ---------------------------
def extract_youtube_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from YouTube video (title, description).
    """
    try:
        logger.info(f"Extracting YouTube text from: {url}")
        
        headers = DEFAULT_HEADERS.copy()
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        text_parts = []
        
        # Get title
        title = soup.find("meta", {"name": "title"})
        if title and title.get("content"):
            text_parts.append(title["content"])
        
        # Get description
        desc = soup.find("meta", {"name": "description"})
        if desc and desc.get("content"):
            text_parts.append(desc["content"])
        
        text = " ".join(text_parts).strip()
        
        if len(text) < 10:
            return None, "Could not extract YouTube video information"
        
        metadata = {
            "platform": "youtube",
            "url": url,
            "extraction_method": "scraping"
        }
        
        logger.info(f"Successfully extracted YouTube text ({len(text)} chars)")
        return text, None, metadata
        
    except Exception as e:
        logger.error(f"YouTube extraction error: {str(e)}")
        return None, f"YouTube extraction failed: {str(e)}"


# ---------------------------
# 🔹 Detect Platform
# ---------------------------
def detect_platform(url: str) -> str:
    """
    Detect social media platform from URL.
    Preserves original logic with enhancements.
    """
    url_lower = url.lower()
    
    # Original detection
    if "reddit.com" in url_lower:
        return "reddit"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    
    # Enhanced detection
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return platform
    
    return "unknown"


def extract_social_text(url: str, include_metadata: bool = False) -> Dict[str, Any]:
    """
    Main function to extract text from social media URLs.
    Preserves original logic with enhancements.
    
    Args:
        url: Social media URL
        include_metadata: Whether to return metadata
        
    Returns:
        Dictionary with extracted text and metadata
    """
    platform = detect_platform(url)
    logger.info(f"Detected platform: {platform} for URL: {url}")
    
    result = {
        "platform": platform,
        "url": url,
        "success": False,
        "text": None,
        "error": None
    }
    
    # Route to appropriate extractor
    if platform == "reddit":
        text, error, metadata = extract_reddit_text(url)
        result["text"] = text
        result["error"] = error
        if metadata:
            result.update(metadata)
    
    elif platform == "twitter":
        text, error, metadata = extract_twitter_text(url)
        result["text"] = text
        result["error"] = error
        if metadata:
            result.update(metadata)
    
    elif platform == "facebook":
        text, error, metadata = extract_facebook_text(url)
        result["text"] = text
        result["error"] = error
        if metadata:
            result.update(metadata)
    
    elif platform == "instagram":
        text, error, metadata = extract_instagram_text(url)
        result["text"] = text
        result["error"] = error
        if metadata:
            result.update(metadata)
    
    elif platform == "tiktok":
        text, error, metadata = extract_tiktok_text(url)
        result["text"] = text
        result["error"] = error
        if metadata:
            result.update(metadata)
    
    elif platform == "youtube":
        text, error, metadata = extract_youtube_text(url)
        result["text"] = text
        result["error"] = error
        if metadata:
            result.update(metadata)
    
    else:
        result["error"] = f"Unsupported platform: {platform}"
    
    # Set success flag
    if result["text"] and len(result["text"].strip()) > 10:
        result["success"] = True
    
    # Remove metadata if not requested
    if not include_metadata:
        for key in list(result.keys()):
            if key not in ["platform", "url", "success", "text", "error"]:
                del result[key]
    
    return result


def extract_social_text_simple(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Simple version for backward compatibility.
    Returns (text, error) tuple.
    """
    result = extract_social_text(url, include_metadata=False)
    
    if result["success"]:
        return result["text"], None
    else:
        return None, result["error"]


# Preserve original exports
__all__ = [
    'extract_social_text_simple',  # Original function
    'extract_social_text',          # Enhanced version
    'detect_platform'
]