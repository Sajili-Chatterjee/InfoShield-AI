# services/image_processor.py
#
# Completely rewritten OCR module.
# Key design: accepts ONLY a real file path — never BytesIO anywhere.
# Multiple preprocessing strategies with automatic fallback.

import logging
import os
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

TESSERACT_AVAILABLE = False
CV2_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    TESSERACT_AVAILABLE = True
    logger.info("pytesseract + Pillow loaded")
except ImportError as e:
    logger.warning(f"pytesseract/Pillow unavailable: {e}")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
    logger.info("OpenCV loaded")
except ImportError as e:
    logger.warning(f"OpenCV unavailable (PIL-only mode): {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_ocr_availability() -> Dict[str, Any]:
    if not TESSERACT_AVAILABLE:
        return {"available": False,
                "message": "Tesseract not installed. Install from https://github.com/UB-Mannheim/tesseract/wiki"}
    try:
        version = pytesseract.get_tesseract_version()
        return {"available": True, "version": str(version), "message": "OCR ready"}
    except Exception as e:
        return {"available": False, "message": str(e)}


def extract_text_from_image(image_path: str, language: str = "eng") -> Dict[str, Any]:
    """
    Extract text from a real file path using Tesseract OCR.
    Tries 5 preprocessing strategies automatically.
    Never uses BytesIO — always reads from disk path.
    """
    # Pre-flight checks
    if not image_path or not os.path.exists(image_path):
        return _fail(f"File not found: {image_path}")

    size = os.path.getsize(image_path)
    if size == 0:
        return _fail("Image file is empty — upload failed. Try again.")

    logger.info(f"OCR starting on: {image_path} ({size} bytes)")

    # Verify PIL can open it before doing anything else
    try:
        probe = Image.open(image_path)
        probe.verify()
        logger.debug(f"PIL verify passed for: {image_path}")
    except Exception as e:
        return _fail(f"Image file is not a valid image: {e}. "
                     f"Save via Paint (Ctrl+V -> Save As PNG) instead of clipboard.")

    if not TESSERACT_AVAILABLE:
        return {"success": True, "text": "Simulated OCR (Tesseract not installed).",
                "confidence": 0.85, "error": None, "simulated": True}

    # Try strategies in order — return first success
    strategies = [
        ("PIL direct",          _pil_direct),
        ("PIL enhanced",        _pil_enhanced),
        ("PIL greyscale",       _pil_greyscale),
        ("OpenCV adaptive",     _opencv_adaptive),
        ("OpenCV Otsu",         _opencv_otsu),
    ]

    last_error = "No strategies attempted"
    for name, fn in strategies:
        try:
            result = fn(image_path, language)
            if result.get("success") and result.get("text", "").strip():
                logger.info(f"OCR succeeded with strategy: [{name}]")
                return result
            logger.debug(f"[{name}] returned no text, trying next")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[{name}] failed: {e}")

    return _fail(f"All OCR strategies failed. Last error: {last_error}")


# ---------------------------------------------------------------------------
# Strategies — each opens directly from file path
# ---------------------------------------------------------------------------

def _pil_direct(path: str, lang: str) -> Dict:
    """Simplest: open file path directly, convert to RGB, run OCR."""
    img = Image.open(path)
    img.load()
    img = img.convert("RGB")
    return _tesseract(img, lang)


def _pil_enhanced(path: str, lang: str) -> Dict:
    """Contrast + sharpness boost. Helps low-contrast screenshots."""
    img = Image.open(path)
    img.load()
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return _tesseract(img, lang)


def _pil_greyscale(path: str, lang: str) -> Dict:
    """Pure greyscale — sometimes cleanest for screenshots."""
    img = Image.open(path)
    img.load()
    img = img.convert("L")
    return _tesseract(img, lang)


def _opencv_adaptive(path: str, lang: str) -> Dict:
    """OpenCV adaptive threshold — best for mixed-background screenshots."""
    if not CV2_AVAILABLE:
        raise RuntimeError("OpenCV not installed")
    img = cv2.imread(path)
    if img is None:
        # cv2.imread can fail on some paths — use PIL to load then convert
        pil = Image.open(path).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    # Scale up small images
    h, w = img.shape[:2]
    if w < 800:
        img = cv2.resize(img, None, fx=800/w, fy=800/w,
                         interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return _tesseract(Image.fromarray(processed), lang)


def _opencv_otsu(path: str, lang: str) -> Dict:
    """OpenCV Otsu binarisation — good for clean high-contrast images."""
    if not CV2_AVAILABLE:
        raise RuntimeError("OpenCV not installed")
    img = cv2.imread(path)
    if img is None:
        pil = Image.open(path).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return _tesseract(Image.fromarray(processed), lang)


# ---------------------------------------------------------------------------
# Core Tesseract runner
# ---------------------------------------------------------------------------

def _tesseract(pil_img, lang: str) -> Dict:
    """Run pytesseract on a PIL image. Returns structured result."""
    # PSM 6 = uniform block of text (best for news screenshots)
    # PSM 3 = fully automatic (fallback)
    for psm in ["--psm 6", "--psm 3", "--psm 11"]:
        try:
            data = pytesseract.image_to_data(
                pil_img, lang=lang, config=psm,
                output_type=pytesseract.Output.DICT,
            )
            words, confs = [], []
            for i, word in enumerate(data.get("text", [])):
                conf = data["conf"][i]
                if isinstance(conf, (int, float)) and int(conf) > 30 and word.strip():
                    words.append(word.strip())
                    confs.append(float(conf))
            text = " ".join(words).strip()
            if text:
                confidence = round(sum(confs) / len(confs) / 100.0, 4)
                return {"success": True, "text": text,
                        "confidence": confidence, "error": None}
        except Exception as e:
            logger.debug(f"Tesseract PSM {psm} failed: {e}")
            continue

    return {"success": False, "text": "", "confidence": 0.0,
            "error": "Tesseract ran but found no text"}


def _fail(msg: str) -> Dict:
    logger.error(f"OCR failed: {msg}")
    return {"success": False, "text": "", "confidence": 0.0, "error": msg}


# ---------------------------------------------------------------------------
# Backward compat
# ---------------------------------------------------------------------------

def preprocess_image_for_ocr(image_path: str, output_path: Optional[str] = None) -> str:
    if not CV2_AVAILABLE or not os.path.exists(image_path):
        return image_path
    try:
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        out = cv2.adaptiveThreshold(gray, 255,
               cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        dest = output_path or image_path.replace(".", "_processed.")
        cv2.imwrite(dest, out)
        return dest
    except Exception:
        return image_path


class ImageProcessor:
    def __init__(self):
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

    def process_image(self, image_path: str, language: str = 'eng') -> Dict[str, Any]:
        return extract_text_from_image(image_path, language)


_processor = None

def get_image_processor():
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor


__all__ = ['extract_text_from_image', 'check_ocr_availability',
           'preprocess_image_for_ocr', 'ImageProcessor', 'get_image_processor']