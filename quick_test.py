#!/usr/bin/env python3
"""
Quick test for each scenario
"""

import sys
sys.path.insert(0, '.')

from services.pipeline import analyze_text
from services.url_processor import extract_text_from_url_simple
from services.social_media_handler import extract_social_text
from services.image_processor import extract_text_from_image

def test_text():
    """Test text input"""
    text = input("Enter news text: ")
    result = analyze_text(text)
    print(f"\nResult: {result['label']} (confidence: {result['confidence']})")
    print(f"Explanation: {result['explanation']}")

def test_url():
    """Test URL input"""
    url = input("Enter URL: ")
    text, error = extract_text_from_url_simple(url)
    if error:
        print(f"Error: {error}")
        return
    result = analyze_text(text)
    print(f"\nResult: {result['label']} (confidence: {result['confidence']})")
    print(f"Evidence: {result['evidence']}")

def test_social():
    """Test social media URL"""
    url = input("Enter social media URL: ")
    result_dict = extract_social_text(url)
    
    if isinstance(result_dict, dict):
        text = result_dict.get('text')
        if result_dict.get('success'):
            print(f"Extracted: {text[:100]}...")
        else:
            print(f"Note: {result_dict.get('error')}")
            print("For real testing, use screenshot OCR method")
    else:
        text, error = result_dict
        if error:
            print(f"Error: {error}")
            return
    
    if text:
        result = analyze_text(text)
        print(f"\nResult: {result['label']} (confidence: {result['confidence']})")

def test_ocr():
    """Test OCR"""
    path = input("Enter image path: ")
    result = extract_text_from_image(path)
    
    if result['success']:
        print(f"Extracted text: {result['text'][:200]}...")
        print(f"OCR Confidence: {result['confidence']}")
        
        analysis = analyze_text(result['text'])
        print(f"\nAnalysis Result: {analysis['label']}")
    else:
        print(f"OCR failed: {result.get('error')}")

if __name__ == "__main__":
    print("1. Text Input")
    print("2. News URL")
    print("3. Social Media URL")
    print("4. OCR Image")
    
    choice = input("\nSelect scenario (1-4): ")
    
    scenarios = {
        '1': test_text,
        '2': test_url,
        '3': test_social,
        '4': test_ocr
    }
    
    if choice in scenarios:
        scenarios[choice]()
    else:
        print("Invalid choice")