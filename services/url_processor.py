# services/url_processor.py

import logging
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse
import time
from typing import Dict, Tuple, Optional, Any
import re

from services.social_media_handler import extract_social_text, detect_platform

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REQUEST_TIMEOUT = 15
MAX_CONTENT_LENGTH = 10000  # Max characters to extract
MIN_CONTENT_LENGTH = 50  # Minimum meaningful content
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

# Common news domains that work well with newspaper3k
NEWS_DOMAINS = [
    'cnn.com', 'bbc.com', 'bbc.co.uk', 'nytimes.com', 'wsj.com', 
    'washingtonpost.com', 'theguardian.com', 'reuters.com', 'apnews.com',
    'npr.org', 'foxnews.com', 'nbcnews.com', 'abcnews.go.com', 'usatoday.com'
]


def extract_text_from_url(url: str, include_metadata: bool = False) -> Dict[str, Any]:
    """
    Extract text content from URL with multiple fallback methods.
    Preserves original logic with enhancements.
    
    Args:
        url: URL to extract text from
        include_metadata: Whether to include extraction metadata
        
    Returns:
        Dictionary with extracted text and metadata
    """
    start_time = time.time()
    logger.info(f"Extracting text from URL: {url}")
    
    result = {
        "url": url,
        "success": False,
        "text": None,
        "error": None,
        "method": None,
        "platform": None
    }
    
    # Validate URL
    if not url or not isinstance(url, str):
        result["error"] = "Invalid URL"
        return result
    
    # Parse URL for metadata
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')
    result["domain"] = domain
    
    # ---------------------------
    # 🔹 Social Media First (Preserved logic)
    # ---------------------------
    platform = detect_platform(url)
    result["platform"] = platform
    
    if platform in ["reddit", "twitter", "facebook", "instagram", "tiktok", "youtube"]:
        logger.info(f"Attempting social media extraction for {platform}")
        social_result = extract_social_text(url, include_metadata=True)
        
        if social_result.get("success"):
            result["text"] = social_result["text"]
            result["success"] = True
            result["method"] = f"social_media_{platform}"
            result["extraction_time"] = round(time.time() - start_time, 3)
            
            # Add social media metadata
            if include_metadata:
                for key, value in social_result.items():
                    if key not in ["text", "success", "error"]:
                        result[f"social_{key}"] = value
            
            logger.info(f"Successfully extracted social media text via {platform}")
            return result
        else:
            logger.debug(f"Social media extraction failed: {social_result.get('error')}")
    
    # ---------------------------
    # 🔹 News Articles (Preserved logic)
    # ---------------------------
    try:
        logger.info("Attempting news article extraction via newspaper3k")
        
        # Configure article extraction
        article = Article(url)
        article.download()
        time.sleep(0.5)  # Small delay to be respectful
        article.parse()
        
        # Check if we got meaningful content
        if article.text and len(article.text.strip()) > MIN_CONTENT_LENGTH:
            text = article.text.strip()
            
            # Truncate if too long
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH] + "..."
            
            result["text"] = text
            result["success"] = True
            result["method"] = "newspaper3k"
            result["extraction_time"] = round(time.time() - start_time, 3)
            
            # Add article metadata
            if include_metadata:
                result["article_title"] = article.title
                result["article_authors"] = article.authors
                result["article_publish_date"] = str(article.publish_date) if article.publish_date else None
                result["article_top_image"] = article.top_image
            
            logger.info(f"Successfully extracted news article ({len(text)} chars)")
            return result
            
    except Exception as e:
        logger.debug(f"Newspaper3k extraction failed: {str(e)}")
    
    # ---------------------------
    # 🔹 Generic Fallback with improvements
    # ---------------------------
    try:
        logger.info("Attempting generic fallback extraction")
        
        # Try multiple user agents
        for attempt, user_agent in enumerate(USER_AGENTS):
            try:
                headers = {
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                }
                
                res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                
                if res.status_code == 200:
                    break
                    
            except requests.RequestException as e:
                if attempt == len(USER_AGENTS) - 1:
                    raise
                time.sleep(1)
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try multiple extraction strategies
        text = ""
        
        # Strategy 1: Get all paragraphs (original logic)
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = " ".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
        
        # Strategy 2: Get article content if available
        if len(text) < MIN_CONTENT_LENGTH:
            article_tag = soup.find('article')
            if article_tag:
                text = article_tag.get_text()
        
        # Strategy 3: Get main content
        if len(text) < MIN_CONTENT_LENGTH:
            main_tag = soup.find('main')
            if main_tag:
                text = main_tag.get_text()
        
        # Strategy 4: Get all text as fallback
        if len(text) < MIN_CONTENT_LENGTH:
            text = soup.get_text()
        
        # Clean up text
        if text:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Remove common noise
            noise_patterns = [
                r'Cookie Policy',
                r'Privacy Policy',
                r'Terms of Service',
                r'Accept Cookies',
                r'Subscribe to our newsletter',
                r'Sign up for our newsletter',
                r'Click here to subscribe',
                r'Advertisement',
                r'Share on Facebook',
                r'Tweet this',
                r'Pin it'
            ]
            
            for pattern in noise_patterns:
                text = text.replace(pattern, '')
            
            # Truncate if too long
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH] + "..."
            
            # Check if we got meaningful content
            if len(text) >= MIN_CONTENT_LENGTH:
                result["text"] = text
                result["success"] = True
                result["method"] = "generic_fallback"
                result["extraction_time"] = round(time.time() - start_time, 3)
                
                logger.info(f"Successfully extracted generic content ({len(text)} chars)")
                return result
        
        result["error"] = "Could not extract meaningful content"
        return result
        
    except requests.RequestException as e:
        result["error"] = f"Request failed: {str(e)}"
        logger.error(f"Request error: {str(e)}")
        
    except Exception as e:
        result["error"] = f"Extraction failed: {str(e)}"
        logger.error(f"Generic extraction error: {str(e)}")
    
    return result


def extract_text_from_url_simple(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Simple version for backward compatibility.
    Returns (text, error) tuple.
    """
    result = extract_text_from_url(url, include_metadata=False)
    
    if result["success"]:
        return result["text"], None
    else:
        return None, result["error"]


def is_likely_news_domain(url: str) -> bool:
    """
    Check if URL is from a known news domain.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '').lower()
    
    return any(news_domain in domain for news_domain in NEWS_DOMAINS)


def extract_text_with_retry(url: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    Extract text with retry logic.
    """
    for attempt in range(max_retries + 1):
        result = extract_text_from_url(url, include_metadata=True)
        
        if result["success"]:
            return result
        
        if attempt < max_retries:
            wait_time = (attempt + 1) * 2
            logger.info(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)
    
    return result


def get_url_metadata(url: str) -> Dict[str, Any]:
    """
    Get metadata about a URL without full text extraction.
    """
    metadata = {
        "url": url,
        "success": False
    }
    
    try:
        parsed_url = urlparse(url)
        metadata["domain"] = parsed_url.netloc
        metadata["path"] = parsed_url.path
        metadata["scheme"] = parsed_url.scheme
        metadata["platform"] = detect_platform(url)
        metadata["is_news_domain"] = is_likely_news_domain(url)
        
        # Try to get page title
        headers = {"User-Agent": USER_AGENTS[0]}
        res = requests.get(url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.find('title')
            if title:
                metadata["title"] = title.get_text().strip()
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata["description"] = meta_desc['content']
            
            metadata["success"] = True
        
    except Exception as e:
        metadata["error"] = str(e)
    
    return metadata


# Preserve original function for backward compatibility
extract_text_from_url.__original__ = extract_text_from_url_simple

__all__ = [
    'extract_text_from_url_simple',  # Original function
    'extract_text_from_url',          # Enhanced version
    'extract_text_with_retry',
    'get_url_metadata',
    'is_likely_news_domain'
]