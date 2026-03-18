# services/image_processor.py

import logging
import os
from typing import Dict, Any, Optional
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

TESSERACT_AVAILABLE = False
pytesseract = None
Image = None
cv2 = None
np = None

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np

    # ✅ Optional: set path if needed (user can override)
    # pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

    TESSERACT_AVAILABLE = True
    logger.info("OCR libraries loaded")
except ImportError as e:
    logger.warning(f"OCR libraries not available: {e}")

    logger.warning(f"OCR libraries not available: {e}")


class ImageProcessor:


    def __init__(self):
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


    def process_image(self, image_path: str, language: str = 'eng') -> Dict[str, Any]:
        start_time = time.time()


        result = {
            'success': False,
            'text': '',
            'error': None,
            'confidence': 0.0,
            'processing_time': 0,
            'image_info': {}
        }


        try:
            if not os.path.exists(image_path):
                result['error'] = "Image file not found"
                return result

            if os.path.getsize(image_path) == 0:
                result['error'] = "Image file is empty — upload may have failed"
                return result


            if not TESSERACT_AVAILABLE:
                result.update({
                    'success': True,
                    'text': self._get_simulated_ocr_text(image_path),
                    'confidence': 0.85,
                    'warning': "Simulated OCR — Tesseract not installed"
                })
                return result


            return self._process_with_actual_ocr(image_path, language, start_time)


        except Exception as e:
            logger.exception("Image processing failed")
            logger.exception("Image processing failed")
            result['error'] = str(e)
            return result

    def _process_with_actual_ocr(self, image_path: str, language: str, start_time: float) -> Dict[str, Any]:
        result = {
            'success': False,
            'text': '',
            'error': None,
            'confidence': 0.0,
            'processing_time': 0,
            'image_info': {}
        }


        try:
            # Open directly from file path -- NO BytesIO anywhere
            pil_img = Image.open(image_path)
            pil_img.load()
            pil_img = pil_img.convert("RGB")

            # Convert to OpenCV array for preprocessing
            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # Resize large images for better OCR
            height, width = image.shape[:2]
            if width > 1500:
                scale = 1500 / width
                image = cv2.resize(image, None, fx=scale, fy=scale,
                                   interpolation=cv2.INTER_CUBIC)

            processed = self._preprocess_image(image)

            # Run OCR with per-word confidence scores
            data = pytesseract.image_to_data(
                processed,
                lang=language,
                output_type=pytesseract.Output.DICT
            )

            words, confs = [], []
            for i, word in enumerate(data.get("text", [])):
                conf = data["conf"][i]
                if isinstance(conf, (int, float)) and conf > 0 and word.strip():
                    words.append(word)
                    confs.append(conf)

            text       = " ".join(words).strip()
            confidence = round(sum(confs) / len(confs) / 100, 4) if confs else 0.0

            result['text']            = text
            result['confidence']      = confidence
            result['success']         = bool(text and len(text.strip()) > 5)
            result['processing_time'] = round(time.time() - start_time, 3)

            if not text:
                result['error'] = "OCR ran but found no readable text in the image"

        except Exception as e:
            logger.exception("OCR processing failed")
            result['error'] = str(e)


        return result

    def _preprocess_image(self, image):
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            return binary
        except Exception:
            return image

    def _get_simulated_ocr_text(self, image_path: str) -> str:
        return "Sample extracted text from image (Tesseract not installed -- simulated mode)."


# Singleton
_processor = None

def get_image_processor():
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor
def get_image_processor():
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor


# =========================
# PUBLIC FUNCTIONS
# =========================

def extract_text_from_image(image_path: str, language: str = 'eng') -> Dict[str, Any]:
    """
    Extract text from an image using OCR.
    Always returns: {"success": bool, "text": str, "confidence": float, "error": str|None}
    """
    if not os.path.exists(image_path):
        return {"success": False, "text": "", "confidence": 0.0,
                "error": f"File not found: {image_path}"}
    if os.path.getsize(image_path) == 0:
        return {"success": False, "text": "", "confidence": 0.0,
                "error": "Image file is empty -- try uploading again."}
    return get_image_processor().process_image(image_path, language)


def preprocess_image_for_ocr(image_path: str, output_path: Optional[str] = None) -> str:
    """Returns processed image file path. Always returns a path string, never a dict."""
    if not TESSERACT_AVAILABLE:
        return image_path
    try:
        image = cv2.imread(image_path)
        if image is None:
            return image_path
        processor   = get_image_processor()
        processed   = processor._preprocess_image(image)
        output_path = output_path or image_path.replace(".", "_processed.")
        cv2.imwrite(output_path, processed)
        return output_path
    except Exception:
        return image_path


def check_ocr_availability() -> Dict[str, Any]:
    if not TESSERACT_AVAILABLE:
        return {"available": False, "message": "Tesseract not installed -- running in simulated mode"}
    try:
        version = pytesseract.get_tesseract_version()
        return {"available": True, "version": str(version), "message": "OCR available"}
    except Exception as e:
        return {"available": False, "message": str(e)}


__all__ = [
    'extract_text_from_image',
    'check_ocr_availability',
    'preprocess_image_for_ocr',
    'ImageProcessor',
    'get_image_processor'
]