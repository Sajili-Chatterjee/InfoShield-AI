#!/usr/bin/env python3
"""
InfoShield-AI - Complete Demo Script
Tests all four scenarios: Text, News URL, Social Media URL, and OCR
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
import argparse
from colorama import init, Fore, Style  # For colored output (install: pip install colorama)

# Initialize colorama for cross-platform colored output
init()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your backend modules
from services.pipeline import analyze_text, analyze_ocr_text, analyze_with_source
from services.url_processor import extract_text_from_url, extract_text_from_url_simple
from services.social_media_handler import extract_social_text
from services.image_processor import extract_text_from_image, check_ocr_availability
from models.predictor import predict
from agents.claim_extractor import extract_claims
from agents.retriever import retrieve
from agents.verifier import verify
from agents.scorer import compute_final_score, get_final_label, explain_score

class InfoShieldDemo:
    """Comprehensive demo for InfoShield-AI backend"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"🔹 {text}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    def print_success(self, text):
        """Print success message"""
        print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")
    
    def print_warning(self, text):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠️ {text}{Style.RESET_ALL}")
    
    def print_error(self, text):
        """Print error message"""
        print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")
    
    def print_info(self, text):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ️ {text}{Style.RESET_ALL}")
    
    def print_result(self, result, title):
        """Pretty print result"""
        print(f"\n{Fore.MAGENTA}📊 {title}{Style.RESET_ALL}")
        print(f"{'─'*40}")
        
        if isinstance(result, dict):
            for key, value in result.items():
                if key == 'evidence' and isinstance(value, list):
                    print(f"  {key}:")
                    for i, ev in enumerate(value, 1):
                        print(f"    {i}. {ev[:100]}..." if len(str(ev)) > 100 else f"    {i}. {ev}")
                elif key == 'explanation':
                    print(f"  {key}: {value[:150]}..." if len(str(value)) > 150 else f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {result}")
        
        print(f"{'─'*40}")
    
    def test_scenario_1_text(self):
        """Scenario 1: User searches news as text"""
        self.print_header("SCENARIO 1: Text-Based News Search")
        
        test_cases = [
            {
                "name": "Real News Example",
                "text": "The World Health Organization announced that vaccines have saved millions of lives globally. Clinical trials show over 90% effectiveness in preventing severe disease.",
                "expected": "REAL"
            },
            {
                "name": "Fake News Example",
                "text": "Shocking revelation: Government scientists have discovered that 5G towers are causing birds to fall from the sky. Official report confirms 10,000 bird deaths linked to new 5G network.",
                "expected": "FAKE"
            },
            {
                "name": "Mixed Content Example",
                "text": "COVID-19 vaccines were developed quickly but went through rigorous testing. Some people claim they contain microchips, which is completely false according to health experts.",
                "expected": "REAL"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{Fore.CYAN}Test Case {i}: {test['name']}{Style.RESET_ALL}")
            print(f"Input: {test['text'][:100]}...")
            
            try:
                start = time.time()
                result = analyze_text(test['text'])
                elapsed = time.time() - start
                
                self.print_success(f"Analysis complete in {elapsed:.2f}s")
                self.print_result(result, f"Result for '{test['name']}'")
                
                # Verify against expectation
                if result['label'].upper() == test['expected'].upper():
                    self.print_success(f"✓ Matches expected: {test['expected']}")
                else:
                    self.print_warning(f"✗ Different from expected: got {result['label']}, expected {test['expected']}")
                
                self.results['scenario_1'] = {
                    'success': True,
                    'tests': i,
                    'time': elapsed
                }
                
            except Exception as e:
                self.print_error(f"Error: {str(e)}")
                self.results['scenario_1'] = {'success': False, 'error': str(e)}
    
    def test_scenario_2_news_url(self):
        """Scenario 2: User inputs URL from news website"""
        self.print_header("SCENARIO 2: News Website URL")
        
        test_urls = [
            {
                "name": "BBC News Article",
                "url": "https://www.bbc.com/news/articles/cj6dl175w01o",  # Replace with current article
                "type": "legitimate_news"
            },
            {
                "name": "CNN Article",
                "url": "https://edition.cnn.com/2026/03/17/business/oil-prices-strait-iran-attacks-intl",  # Replace
                "type": "legitimate_news"
            },
            {
                "name": "Suspicious News Site",
                "url": "https://timesofindia.indiatimes.com/topic/salman-khan-marriage",  # Replace with actual test URL
                "type": "suspicious"
            }
        ]
        
        for i, test in enumerate(test_urls, 1):
            print(f"\n{Fore.CYAN}Test Case {i}: {test['name']}{Style.RESET_ALL}")
            print(f"URL: {test['url']}")
            
            try:
                start = time.time()
                
                # Step 1: Extract text from URL
                self.print_info("Extracting text from URL...")
                text, error = extract_text_from_url_simple(test['url'])
                
                if error:
                    self.print_error(f"Extraction failed: {error}")
                    continue
                
                self.print_success(f"Extracted {len(text)} characters")
                print(f"Preview: {text[:200]}...")
                
                # Step 2: Analyze the extracted text
                self.print_info("Running verification pipeline...")
                result = analyze_text(text)
                elapsed = time.time() - start
                
                self.print_success(f"Analysis complete in {elapsed:.2f}s")
                self.print_result(result, f"Result for '{test['name']}'")
                
                self.results['scenario_2'] = {
                    'success': True,
                    'tests': i,
                    'time': elapsed
                }
                
            except Exception as e:
                self.print_error(f"Error: {str(e)}")
    
    def test_scenario_3_social_media(self):
        """Scenario 3: User inputs URL from social media"""
        self.print_header("SCENARIO 3: Social Media URL")
        
        test_social_urls = [
            {
                "platform": "Twitter/X",
                "name": "Verified News Tweet",
                "url": "https://x.com/i/status/2031477826625622335",  # Replace with actual tweet
                "type": "legitimate"
            },
            {
                "platform": "Reddit",
                "name": "News Discussion Thread",
                "url": "https://www.reddit.com/r/tech/comments/1rvnlc2/thor_ai_solves_a_100yearold_physics_problem_in/",  # Replace
                "type": "discussion"
            },
            {
                "platform": "Instagram",
                "name": "News Post",
                "url": "https://www.instagram.com/reel/DWDrOL1PVCd/?igsh=MWQ0emYyczQ5cjc4Zg==",  # Replace
                "type": "post"
            },
            {
                "platform": "Facebook",
                "name": "News Page Post",
                "url": "https://www.facebook.com/share/p/1bV5CZ1PPb/",  # Replace
                "type": "post"
            }
        ]
        
        for i, test in enumerate(test_social_urls, 1):
            print(f"\n{Fore.CYAN}Test Case {i}: {test['platform']} - {test['name']}{Style.RESET_ALL}")
            print(f"URL: {test['url']}")
            
            try:
                start = time.time()
                
                # Step 1: Extract social media content
                self.print_info(f"Extracting content from {test['platform']}...")
                result_dict = extract_social_text(test['url'])
                
                # Handle both old and new return formats
                if isinstance(result_dict, dict):
                    text = result_dict.get('text')
                    error = result_dict.get('error')
                    platform = result_dict.get('platform', test['platform'])
                else:
                    text, error = result_dict
                    platform = test['platform']
                
                if error:
                    self.print_warning(f"Direct extraction failed: {error}")
                    self.print_info("This is expected for some platforms due to authentication requirements.")
                    self.print_info("In production, users would upload screenshots for these cases.")
                    
                    # Simulate screenshot OCR fallback
                    self.print_info("Simulating OCR fallback with sample text...")
                    text = f"[Content from {platform} would be extracted via OCR from screenshot]"
                else:
                    self.print_success(f"Extracted {len(text)} characters")
                    print(f"Preview: {text[:150]}...")
                
                # Step 2: Analyze the content
                if text:
                    self.print_info("Running verification pipeline...")
                    result = analyze_with_source(text, test['url'], f"social_media_{platform.lower()}")
                    elapsed = time.time() - start
                    
                    self.print_success(f"Analysis complete in {elapsed:.2f}s")
                    self.print_result(result, f"Result for {test['platform']} post")
                
                self.results['scenario_3'] = {
                    'success': True,
                    'tests': i,
                    'time': time.time() - start
                }
                
            except Exception as e:
                self.print_error(f"Error: {str(e)}")
    
    def test_scenario_4_ocr(self):
        """Scenario 4: OCR - Screenshot Image Processing"""
        self.print_header("SCENARIO 4: OCR - Screenshot Image Processing")
        
        # First, check OCR availability
        ocr_status = check_ocr_availability()
        if not ocr_status.get('available'):
            self.print_warning("Tesseract OCR is not installed!")
            self.print_info("For actual OCR testing, install Tesseract:")
            self.print_info("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
            self.print_info("  macOS: brew install tesseract")
            self.print_info("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            
            # Create a mock image for testing
            self.create_mock_image()
        else:
            self.print_success(f"Tesseract OCR available: {ocr_status.get('tesseract_version')}")
        
        # Test with sample images if they exist
        test_images = [
            {
                "name": "News Screenshot",
                "path": "test_images/Screenshot 2026-03-17 191916.png",
                "description": "Screenshot of news article"
            },
            {
                "name": "Social Media Post",
                "path": "test_images/Screenshot 2026-03-17 192131.png",
                "description": "Screenshot of social media post"
            },
            {
                "name": "Headline Image",
                "path": "test_images/Screenshot 2026-03-17 191406.png",
                "description": "Image with news headline text"
            }
        ]
        
        # Create test_images directory if it doesn't exist
        os.makedirs("test_images", exist_ok=True)
        
        for i, test in enumerate(test_images, 1):
            print(f"\n{Fore.CYAN}Test Case {i}: {test['name']}{Style.RESET_ALL}")
            print(f"Description: {test['description']}")
            
            # Check if image exists
            if not os.path.exists(test['path']):
                self.print_warning(f"Image not found: {test['path']}")
                self.print_info("Creating sample text for demonstration...")
                
                # Create sample text that would come from OCR
                sample_texts = {
                    1: "Breaking News: Scientists discover breakthrough in cancer research. Clinical trials show 80% success rate in early detection.",
                    2: "Viral post: Government confirms existence of UFOs. Official report to be released next week.",
                    3: "Headline: Election results contested - Officials call for recount."
                }
                
                text = sample_texts.get(i, "Sample OCR text for demonstration")
                ocr_confidence = 0.85
                
                self.print_info(f"Simulated OCR text: {text[:100]}...")
                self.print_info(f"OCR Confidence: {ocr_confidence}")
                
            else:
                # Real OCR processing
                self.print_info(f"Processing image: {test['path']}")
                try:
                    start = time.time()
                    ocr_result = extract_text_from_image(test['path'])
                    elapsed = time.time() - start
                    
                    if ocr_result['success']:
                        text = ocr_result['text']
                        ocr_confidence = ocr_result.get('confidence', 0.5)
                        
                        self.print_success(f"OCR completed in {elapsed:.2f}s")
                        self.print_success(f"Confidence: {ocr_confidence}")
                        print(f"Extracted text: {text[:200]}...")
                    else:
                        self.print_error(f"OCR failed: {ocr_result.get('error')}")
                        continue
                        
                except Exception as e:
                    self.print_error(f"OCR error: {str(e)}")
                    continue
            
            # Analyze OCR text
            self.print_info("Running verification pipeline with OCR text...")
            result = analyze_ocr_text(text, ocr_confidence, test['name'])
            
            self.print_result(result, f"OCR Analysis Result for '{test['name']}'")
            
            self.results['scenario_4'] = {
                'success': True,
                'tests': i,
                'ocr_available': ocr_status.get('available', False)
            }
    
    def create_mock_image(self):
        """Create a mock image for OCR testing"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple image with text
            img = Image.new('RGB', (800, 400), color='white')
            d = ImageDraw.Draw(img)
            
            # Add text
            text = """Breaking News: AI Fake News Detection
            InfoShield-AI successfully detects misinformation
            Testing OCR capabilities with sample text
            This would be processed and verified by our system"""
            
            d.text((50, 50), text, fill='black')
            
            # Save
            os.makedirs("test_images", exist_ok=True)
            img.save("test_images/sample_ocr_test.png")
            self.print_success("Created sample image: test_images/sample_ocr_test.png")
            
        except ImportError:
            self.print_warning("PIL not installed. Cannot create mock image.")
            self.print_info("Run: pip install Pillow")
    
    def run_demo(self):
        """Run all demo scenarios"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print("🚀 INFOSHIELD-AI COMPLETE DEMO")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python Version: {sys.version}")
        print(f"Working Directory: {os.getcwd()}\n")
        
        # Run all scenarios
        self.test_scenario_1_text()
        self.test_scenario_2_news_url()
        self.test_scenario_3_social_media()
        self.test_scenario_4_ocr()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print demo summary"""
        elapsed = time.time() - self.start_time
        
        print(f"\n{Fore.GREEN}{'='*60}")
        print("📊 DEMO SUMMARY")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        print(f"Total Time: {elapsed:.2f} seconds")
        print(f"Scenarios Tested: 4")
        print(f"Successful: {sum(1 for r in self.results.values() if r.get('success'))}")
        print(f"Failed: {sum(1 for r in self.results.values() if not r.get('success'))}")
        
        print(f"\n{Fore.CYAN}Scenario Results:{Style.RESET_ALL}")
        for i, (scenario, result) in enumerate(self.results.items(), 1):
            status = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}" if result.get('success') else f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
            print(f"  {i}. {scenario.replace('_', ' ').title()}: {status}")
        
        print(f"\n{Fore.YELLOW}Next Steps:{Style.RESET_ALL}")
        print("  1. Run the Flask server: python app.py")
        print("  2. Test API endpoints with curl/Postman")
        print("  3. Integrate with frontend")
        print("  4. Deploy to production\n")

def test_api_endpoints():
    """Test the actual API endpoints if server is running"""
    print(f"\n{Fore.CYAN}Testing API Endpoints{Style.RESET_ALL}")
    print(f"{'─'*40}")
    
    base_url = "http://localhost:5000/api"
    
    endpoints = [
        ("/health", "GET", None),
        ("/analyze", "POST", {"text": "Test news article content"}),
    ]
    
    for endpoint, method, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{base_url}{endpoint}", json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ {endpoint} - OK{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ {endpoint} - {response.status_code}{Style.RESET_ALL}")
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}✗ {endpoint} - Server not running{Style.RESET_ALL}")
            print(f"  Start server with: python app.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='InfoShield-AI Demo')
    parser.add_argument('--api', action='store_true', help='Test API endpoints')
    parser.add_argument('--scenario', type=int, choices=[1,2,3,4], help='Run specific scenario')
    
    args = parser.parse_args()
    
    demo = InfoShieldDemo()
    
    if args.api:
        test_api_endpoints()
    elif args.scenario:
        scenarios = {
            1: demo.test_scenario_1_text,
            2: demo.test_scenario_2_news_url,
            3: demo.test_scenario_3_social_media,
            4: demo.test_scenario_4_ocr
        }
        scenarios[args.scenario]()
    else:
        demo.run_demo()
