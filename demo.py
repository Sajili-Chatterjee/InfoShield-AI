import os
import sys
import time
from datetime import datetime
import argparse

# Safe color import
try:
    from colorama import init, Fore, Style
    init()
except:
    class Dummy:
        RESET_ALL = ""
    Fore = Style = Dummy()

# Project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports
from services.pipeline import analyze_text, analyze_ocr_text, analyze_with_source
from services.url_processor import extract_text_from_url_simple
from services.social_media_handler import extract_social_text
from services.image_processor import extract_text_from_image, check_ocr_availability


class InfoShieldDemo:

    def __init__(self):
        self.start_time = time.time()

    def print_header(self, text):
        print(f"\n{'='*60}\n{text}\n{'='*60}")

    def print_safe(self, label, value):
        print(f"{label}: {value if value else 'N/A'}")

    # ======================
    # SCENARIO 1: TEXT
    # ======================
    def test_text(self):
        self.print_header("SCENARIO 1: TEXT")

        text = """The World Health Organization confirms that vaccines are safe and effective."""

        try:
            result = analyze_text(text)
            print(result)
        except Exception as e:
            print("Error:", e)

    # ======================
    # SCENARIO 2: URL (KEPT)
    # ======================
    def test_url(self):
        self.print_header("SCENARIO 2: URL")

        url = "https://www.bbc.com/news/articles/cj6dl175w01o"

        try:
            text, error = extract_text_from_url_simple(url)

            # 🔥 FALLBACK ADDED (IMPORTANT)
            if error or not text:
                print("⚠️ URL extraction failed, using fallback demo text")
                text = """BBC reports that global vaccination programs have significantly reduced disease spread."""

            result = analyze_text(text)
            print(result)

        except Exception as e:
            print("Error:", e)

    # ======================
    # SCENARIO 3: SOCIAL (KEPT)
    # ======================
    def test_social(self):
        self.print_header("SCENARIO 3: SOCIAL MEDIA")

        url = "https://x.com/i/status/2031477826625622335"

        try:
            res = extract_social_text(url)

            text = None

            if isinstance(res, dict):
                text = res.get("text")

            # 🔥 FALLBACK (VERY IMPORTANT)
            if not text:
                print("⚠️ Social extraction failed, using fallback text")
                text = """Viral post falsely claims vaccines contain microchips. Experts confirm this is misinformation."""

            result = analyze_with_source(text, url, "social_media")
            print(result)

        except Exception as e:
            print("Error:", e)

    # ======================
    # SCENARIO 4: OCR
    # ======================
    def test_ocr(self):
        self.print_header("SCENARIO 4: OCR")

        status = check_ocr_availability()
        print("OCR Available:", status.get("available"))

        image = "test.png"

        try:
            if os.path.exists(image):
                ocr = extract_text_from_image(image)

                if ocr.get("success"):
                    text = ocr.get("text")
                    conf = ocr.get("confidence", 0.5)
                else:
                    print("⚠️ OCR failed, using fallback text")
                    text = "Climate change is supported by scientific consensus."
                    conf = 0.8
            else:
                print("⚠️ Image not found, using fallback OCR text")
                text = "Climate change is supported by scientific consensus."
                conf = 0.8

            result = analyze_ocr_text(text, conf, "image")
            print(result)

        except Exception as e:
            print("Error:", e)

    # ======================
    def run(self):
        print("\n🚀 INFOSHIELD DEMO START\n")
        print("Time:", datetime.now())

        self.test_text()
        self.test_url()
        self.test_social()
        self.test_ocr()

        print("\n✅ DEMO COMPLETE\n")


# ======================
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "text", "url", "social", "ocr"], default="all")

    args = parser.parse_args()

    demo = InfoShieldDemo()

    if args.mode == "text":
        demo.test_text()
    elif args.mode == "url":
        demo.test_url()
    elif args.mode == "social":
        demo.test_social()
    elif args.mode == "ocr":
        demo.test_ocr()
    else:
        demo.run()