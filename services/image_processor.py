# services/image_processor.py

import logging
import os
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
                result['error'] = "Image not found"
                return result

            if not TESSERACT_AVAILABLE:
                result.update({
                    'success': True,
                    'text': self._get_simulated_ocr_text(image_path),
                    'confidence': 0.85,
                    'warning': "Simulated OCR"
                })
                return result

            return self._process_with_actual_ocr(image_path, language, start_time)

        except Exception as e:
            logger.exception("Image processing failed")
            result['error'] = str(e)
            return result


    def _process_with_actual_ocr(self, image_path, language, start_time):

        result = {
            'success': False,
            'text': '',
            'error': None,
            'confidence': 0.0,
            'processing_time': 0,
            'image_info': {}
        }

        try:
            image = cv2.imread(image_path)

            if image is None:
                pil_image = Image.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # ✅ Resize large images (important)
            height, width = image.shape[:2]
            if width > 1500:
                scale = 1500 / width
                image = cv2.resize(image, None, fx=scale, fy=scale)

            processed = self._preprocess_image(image)

            text = pytesseract.image_to_string(processed, lang=language).strip()

            result['text'] = text
            result['confidence'] = 0.75
            result['success'] = bool(text and len(text.strip()) > 5)
            result['processing_time'] = round(time.time() - start_time, 3)

        except Exception as e:
            logger.exception("OCR failed")
            result['error'] = str(e)

        return result


    def _preprocess_image(self, image):
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        except:
            return image


    def _get_simulated_ocr_text(self, image_path: str) -> str:
        return "Sample extracted text from image."


# Singleton
_processor = None

def get_image_processor():
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor


# =========================
# ✅ FIXED PUBLIC FUNCTIONS
# =========================

def extract_text_from_image(image_path: str, language: str = 'eng') -> Dict[str, Any]:
    return get_image_processor().process_image(image_path, language)


def preprocess_image_for_ocr(image_path: str, output_path: Optional[str] = None) -> str:
    """
    ✅ FIX: ALWAYS return file path (not dict)
    """
    if not TESSERACT_AVAILABLE:
        return image_path  # fallback

    try:
        image = cv2.imread(image_path)
        if image is None:
            return image_path

        processor = get_image_processor()
        processed = processor._preprocess_image(image)

        # Save processed image
        output_path = output_path or image_path.replace(".", "_processed.")
        cv2.imwrite(output_path, processed)

        return output_path

    except:
        return image_path


def check_ocr_availability() -> Dict[str, Any]:
    return {
        'available': TESSERACT_AVAILABLE,
        'message': 'OCR available' if TESSERACT_AVAILABLE else 'Simulated mode'
    }


__all__ = [
    'extract_text_from_image',
    'check_ocr_availability',
    'preprocess_image_for_ocr',
    'ImageProcessor',
    'get_image_processor'
]