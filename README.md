# 🛡️ InfoShield-AI - Fake News Detection System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![Transformers](https://img.shields.io/badge/Transformers-4.30%2B-yellow)](https://huggingface.co/docs/transformers/)
[![License](https://img.shields.io/badge/License-MIT-red)](LICENSE)

## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [What's Done ✅](#-whats-done-)
- [What's Left to Do 🚧](#-whats-left-to-do-)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Overview

InfoShield-AI is a powerful fake news detection system that analyzes content from multiple sources:
- 📝 **Direct text input**
- 🔗 **News website URLs**
- 📱 **Social media posts** (Reddit, Twitter/X, Facebook, Instagram, TikTok, YouTube)
- 📸 **Screenshot images** (via OCR)

The system uses a combination of machine learning (DistilBERT), claim extraction, evidence retrieval, and verification scoring to determine the credibility of news content.

## ✨ Features

### ✅ **Implemented Features**
- **Text Analysis**: Direct text input analysis using DistilBERT sentiment model
- **URL Extraction**: Multi-tier extraction from news websites and social media
- **Social Media Support**: Reddit (API), Twitter/X (scraping), Facebook, Instagram, TikTok, YouTube
- **OCR Processing**: Extract text from screenshot images using Tesseract
- **Claim Extraction**: NLTK-based sentence tokenization and filtering
- **Evidence Retrieval**: Keyword matching against enhanced knowledge base
- **Verification Scoring**: Weighted scoring (0.5 model + 0.3 verification + 0.2 credibility)
- **RESTful API**: Complete Flask API with CORS support
- **Knowledge Base**: 10+ verified facts with metadata and sources

### 🚧 **In Progress**
- Frontend dashboard (React/Vue)
- Advanced model fine-tuning for fake news
- Database integration for user feedback
- Deployment scripts (Docker, cloud)


## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/InfoShield-AI.git
cd InfoShield-AI
Step 2: Create Virtual Environment
bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
Step 3: Install Dependencies
bash
pip install --upgrade pip
pip install -r requirements.txt
Step 4: Install Tesseract OCR (for image processing)
Windows:

Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

Install and add to PATH

Default path: C:\Program Files\Tesseract-OCR\tesseract.exe

Ubuntu/Debian:

bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-eng  # English language
macOS:

bash
brew install tesseract
Step 5: Download NLTK Data
bash
python -c "import nltk; nltk.download('punkt')"
Step 6: Configure Reddit API (Optional)
Edit services/social_media_handler.py and update:

python
REDDIT_CONFIG = {
    "client_id": "YOUR_CLIENT_ID",      # Get from reddit.com/prefs/apps
    "client_secret": "YOUR_CLIENT_SECRET",
    "user_agent": "InfoShield-AI/1.0"
}
⚙️ Configuration
Create a .env file in the project root:

bash
# .env
FLASK_ENV=development           # development, production, testing
SECRET_KEY=your-secret-key      # Change in production
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
OCR_LANGUAGE=eng                 # Default OCR language
MODEL_CACHE_DIR=model_cache      # Model cache directory
🚀 Running the Application
1️⃣ Run the Demo (Test All Scenarios)
bash
python demo_all_scenarios.py
2️⃣ Run Specific Demo Scenarios
bash
# Test only text input
python demo_all_scenarios.py --scenario 1

# Test only URL extraction
python demo_all_scenarios.py --scenario 2

# Test only social media
python demo_all_scenarios.py --scenario 3

# Test only OCR
python demo_all_scenarios.py --scenario 4
3️⃣ Start the Flask Server
bash
python app.py
Server will start at: http://localhost:5000

4️⃣ Quick Interactive Test
bash
python quick_test.py
📡 API Endpoints
Base URL: http://localhost:5000
Endpoint	Method	Description	Request Body
/	GET	Home page with API info	-
/health	GET	Health check	-
/api/analyze	POST	Analyze text	{"text": "news content"}
/api/analyze-url	POST	Analyze URL	{"url": "https://..."}
/api/analyze-image	POST	Analyze image	multipart/form-data with image field
/api/analyze-batch	POST	Batch analysis	{"items": [...]}
📝 Example Requests
Text Analysis:

bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Vaccines are safe and effective according to WHO."}'
URL Analysis:

bash
curl -X POST http://localhost:5000/api/analyze-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.bbc.com/news"}'
Image Analysis:

bash
curl -X POST http://localhost:5000/api/analyze-image \
  -F "image=@test_images/sample.png" \
  -F "source=test"
📤 Sample Response
json
{
  "project": "InfoShield-AI",
  "label": "REAL",
  "confidence": 0.85,
  "explanation": "Model predicted 'POSITIVE' with confidence 0.92. Verification score is 0.87, based on 2 retrieved evidence items.",
  "evidence": [
    "Vaccines are safe and effective according to WHO.",
    "The World Health Organization coordinates international public health responses."
  ]
}
🧪 Testing
Test Import Resolution
bash
python test_imports.py
Test API Endpoints (with server running)
bash
python -c "import requests; print(requests.get('http://localhost:5000/health').json())"
Run Unit Tests
bash
pytest tests/ -v
✅ What's Done ✓
Core Functionality
Model Loading: DistilBERT model for sentiment analysis

Claim Extraction: NLTK-based sentence tokenization

Evidence Retrieval: Keyword matching with enhanced knowledge base

Verification Logic: Similarity scoring with negation detection

Scoring System: Weighted combination (model + verification + credibility)

Data & Knowledge Base
Knowledge Base: 10+ verified facts with metadata (sources, dates, confidence)

Sample Data: Test cases for all scenarios

URL Processing
News Extraction: newspaper3k integration

Social Media: Reddit (PRAW), Twitter/X (scraping), Facebook, Instagram, TikTok, YouTube

Generic Fallback: BeautifulSoup with multiple strategies

Image Processing
OCR Integration: Tesseract with preprocessing (grayscale, thresholding, denoising)

Format Support: PNG, JPG, JPEG, BMP, TIFF, WebP

Confidence Scoring: OCR confidence calculation

Simulated Mode: Works even without Tesseract installed

API & Server
Flask Application: Complete REST API with CORS

Error Handling: Comprehensive error handlers

Input Validation: Schema validation for all endpoints

Configuration: Environment-based config management

File Upload: Image upload handling with temp cleanup

Testing & Demo
Demo Script: Complete demo covering all 4 scenarios

Quick Test: Interactive test script

Import Testing: Circular import resolution

All Scenarios Passed: Text, URL, Social Media, OCR ✓

🚧 What's Left to Do
High Priority
Frontend Development: React/Vue dashboard with:

User-friendly input forms

Results visualization

History tracking

Responsive design

Medium Priority
Model Enhancement:

Fine-tune model specifically for fake news

Add zero-shot classification

Implement ensemble methods

Database Integration:

Store analysis history

User feedback collection

Analytics dashboard

Performance Optimization:

Async processing for multiple requests

Redis caching

CDN for static assets

Low Priority
Additional Features:

Browser extension

Mobile app

Multi-language support

Fact-checking API integration

Social media monitoring

Deployment:

Docker containerization

Kubernetes orchestration

Cloud deployment (AWS/Azure/GCP)

CI/CD pipeline

🔍 Troubleshooting
Common Issues & Solutions
1. Import Errors

bash
# Clear Python cache
Remove-Item -Recurse -Force *\__pycache__ -ErrorAction SilentlyContinue
# or on Linux/Mac
find . -type d -name "__pycache__" -exec rm -rf {} +
2. Tesseract Not Found

text
Error: TesseractOCR is not installed
Solution: Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
3. Newspaper3k Error

text
ImportError: lxml.html.clean module is now a separate project
Solution: pip install lxml_html_clean
4. Model Download Issues

bash
# Set HuggingFace token for faster downloads
export HF_TOKEN=your_token_here
5. Reddit API Errors

text
Error: Reddit API not initialized
Solution: Add valid credentials in social_media_handler.py
🤝 Contributing
Fork the repository

Create a feature branch (git checkout -b feature/AmazingFeature)

Commit changes (git commit -m 'Add AmazingFeature')

Push to branch (git push origin feature/AmazingFeature)

Open a Pull Request

Development Guidelines
Follow PEP 8 style guide

Add docstrings for new functions

Update tests for new features

Update documentation

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
HuggingFace for Transformers library

NLTK for NLP tools

Newspaper3k for article extraction

Tesseract for OCR capabilities

Flask for web framework

📞 Contact & Support
Project Lead: [Your Name]

Email: your.email@example.com

GitHub Issues: https://github.com/yourusername/InfoShield-AI/issues

🎉 Quick Start Summary
bash
# 1. Clone and setup
git clone <repo>
cd InfoShield-AI
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install lxml_html_clean

# 3. Test everything
python test_imports.py
python demo_all_scenarios.py

# 4. Run the server
python app.py

# 5. Open browser to http://localhost:5000
All 4 scenarios are now PASSING! ✅ Ready for frontend integration and production deployment.

Last Updated: March 17, 2026
Version: 2.0.0
Status: 🟢 Production Ready (Backend Complete)