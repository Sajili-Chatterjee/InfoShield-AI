# 🛡️ InfoShield-AI — Fake News Detection System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![Transformers](https://img.shields.io/badge/Transformers-4.30%2B-yellow)](https://huggingface.co/docs/transformers/)
[![License: MIT](https://img.shields.io/badge/License-MIT-red)](./LICENSE)

> An agentic AI system where multiple intelligent agents collaborate to detect, verify, and explain fake news in real time, autonomously.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [What's Done ✅](#-whats-done-)
- [What's Left to Do 🚧](#-whats-left-to-do-)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**InfoShield-AI** is a powerful fake news detection system that analyzes content from multiple sources:

| Source | Description |
|---|---|
| 📝 Direct Text | Paste or type any news content directly |
| 🔗 URLs | Analyze articles from news websites |
| 📱 Social Media | Reddit, Twitter/X, Facebook, Instagram, TikTok, YouTube |
| 📸 Screenshots | Extract and analyze text from images via OCR |

The system combines **machine learning (DistilBERT)**, **claim extraction**, **evidence retrieval**, and **verification scoring** to determine the credibility of news content.

---

## ✨ Features

### ✅ Implemented

- **Text Analysis** — Direct text input analysis using DistilBERT sentiment model
- **URL Extraction** — Multi-tier extraction from news websites and social media
- **Social Media Support** — Reddit (API), Twitter/X (scraping), Facebook, Instagram, TikTok, YouTube
- **OCR Processing** — Extract text from screenshot images using Tesseract
- **Claim Extraction** — NLTK-based sentence tokenization and filtering
- **Evidence Retrieval** — Keyword matching against an enhanced knowledge base
- **Verification Scoring** — Weighted scoring: `0.5 × model + 0.3 × verification + 0.2 × credibility`
- **RESTful API** — Complete Flask API with CORS support
- **Knowledge Base** — 10+ verified facts with metadata and sources

### 🚧 In Progress

- Frontend dashboard (React/Vue)
- Advanced model fine-tuning for fake news
- Database integration for user feedback
- Deployment scripts (Docker, cloud)

---

## 🏗️ System Architecture

```
Input (Text / URL / Social Media / Image)
          │
          ▼
  ┌─────────────────┐
  │  Input Handler  │  ← URL scraper, social media parser, OCR
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Claim Extractor │  ← NLTK sentence tokenization & filtering
  └────────┬────────┘
           │
           ▼
  ┌──────────────────────┐
  │  Evidence Retriever  │  ← Keyword matching vs. knowledge base
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │  DistilBERT Model    │  ← Sentiment / credibility prediction
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │  Verification Scorer │  ← Weighted final score + label
  └────────┬─────────────┘
           │
           ▼
     JSON Response  →  { label, confidence, explanation, evidence }
```

---

## 📁 Project Structure

```
InfoShield-AI/
├── agents/              # Agentic AI components
├── api/                 # API route definitions
├── data/                # Knowledge base and test data
├── models/              # ML model loaders and wrappers
├── scripts/             # Utility / setup scripts
├── services/            # Social media handler, OCR, URL extractor
├── utils/               # Helper functions
├── app.py               # Flask application entry point
├── config.py            # Environment-based configuration
├── streamlit_app.py     # Streamlit UI (optional)
├── demo.py              # Demo runner
├── requirements.txt     # Python dependencies
├── test_claims.py       # Claim extraction tests
├── test_model.py        # Model inference tests
├── test_pipeline.py     # End-to-end pipeline tests
├── test_retriever.py    # Evidence retrieval tests
├── test_scorer.py       # Verification scorer tests
├── test_verifier.py     # Verifier module tests
└── .gitignore
```

---

## 🔧 Installation

### Prerequisites

- Python **3.8+**
- `pip`
- Git (optional)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Sajili-Chatterjee/InfoShield-AI.git
cd InfoShield-AI
```

### Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install lxml_html_clean   # Required fix for newspaper3k
```

### Step 4 — Install Tesseract OCR *(for image analysis)*

**Windows:**
```
Download from: https://github.com/UB-Mannheim/tesseract/wiki
Install and add to PATH (default: C:\Program Files\Tesseract-OCR\tesseract.exe)
```

**Ubuntu / Debian:**
```bash
sudo apt-get update && sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract
```

### Step 5 — Download NLTK Data

```bash
python -c "import nltk; nltk.download('punkt')"
```

### Step 6 — Configure Reddit API *(optional)*

Edit `services/social_media_handler.py` and update:

```python
REDDIT_CONFIG = {
    "client_id":     "YOUR_CLIENT_ID",       # Get from reddit.com/prefs/apps
    "client_secret": "YOUR_CLIENT_SECRET",
    "user_agent":    "InfoShield-AI/1.0"
}
```

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
FLASK_ENV=development            # development | production | testing
SECRET_KEY=your-secret-key       # Change in production!
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
OCR_LANGUAGE=eng
MODEL_CACHE_DIR=model_cache
```

---

## 🚀 Running the Application

### Option 1 — Full Demo (all scenarios)

```bash
python demo.py
```

### Option 2 — Flask API Server

```bash
python app.py
```

Server starts at: **http://localhost:5000**

### Option 3 — Streamlit UI

```bash
streamlit run streamlit_app.py
```

---

## 📡 API Endpoints

**Base URL:** `http://localhost:5000`

| Endpoint | Method | Description | Body |
|---|---|---|---|
| `/` | GET | Home + API info | — |
| `/health` | GET | Health check | — |
| `/api/analyze` | POST | Analyze raw text | `{"text": "..."}` |
| `/api/analyze-url` | POST | Analyze a URL | `{"url": "https://..."}` |
| `/api/analyze-image` | POST | Analyze an image (OCR) | `multipart/form-data` with `image` field |
| `/api/analyze-batch` | POST | Batch analysis | `{"items": [...]}` |

### Example Requests

**Text:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Vaccines are safe and effective according to WHO."}'
```

**URL:**
```bash
curl -X POST http://localhost:5000/api/analyze-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.bbc.com/news/article"}'
```

**Image:**
```bash
curl -X POST http://localhost:5000/api/analyze-image \
  -F "image=@screenshot.png"
```

### Sample Response

```json
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
```

---

## 🧪 Testing

```bash
# Run all unit tests
pytest -v

# Test individual modules
python test_claims.py
python test_model.py
python test_pipeline.py
python test_retriever.py
python test_scorer.py
python test_verifier.py
```

---

## ✅ What's Done ✓

**Core Functionality**
- [x] DistilBERT model loading and inference
- [x] NLTK-based claim extraction
- [x] Evidence retrieval via keyword matching
- [x] Similarity scoring with negation detection
- [x] Weighted final scoring system

**Data & Knowledge Base**
- [x] 10+ verified facts with sources, dates, and confidence metadata
- [x] Sample test cases for all 4 input scenarios

**URL & Social Media Processing**
- [x] `newspaper3k` integration for news articles
- [x] Reddit (PRAW), Twitter/X (scraping), Facebook, Instagram, TikTok, YouTube
- [x] BeautifulSoup generic fallback

**Image Processing**
- [x] Tesseract OCR with grayscale, thresholding, denoising pre-processing
- [x] Supports PNG, JPG, JPEG, BMP, TIFF, WebP
- [x] Simulated mode (works without Tesseract installed)

**API & Server**
- [x] Complete Flask REST API with CORS
- [x] Comprehensive error handling and input validation
- [x] Environment-based config management
- [x] File upload handling with temp cleanup

---

## 🚧 What's Left to Do

**High Priority**
- [ ] React/Vue frontend dashboard (input forms, result visualization, history)

**Medium Priority**
- [ ] Fine-tune model specifically on fake news datasets
- [ ] Add zero-shot classification + ensemble methods
- [ ] Database for analysis history and user feedback
- [ ] Redis caching + async request processing

**Low Priority**
- [ ] Browser extension
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Docker + Kubernetes + CI/CD pipeline
- [ ] Cloud deployment (AWS / Azure / GCP)

---

## 🔍 Troubleshooting

**Import errors / circular imports**
```bash
# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
# Windows:
Remove-Item -Recurse -Force *\__pycache__ -ErrorAction SilentlyContinue
```

**Tesseract not found**
```
Error: TesseractOCR is not installed
Solution: Install from https://github.com/UB-Mannheim/tesseract/wiki
```

**newspaper3k lxml error**
```
ImportError: lxml.html.clean module is now a separate project
Solution: pip install lxml_html_clean
```

**HuggingFace model download slow**
```bash
export HF_TOKEN=your_token_here
```

**Reddit API errors**
```
Error: Reddit API not initialized
Solution: Add valid credentials in services/social_media_handler.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

**Guidelines:** Follow PEP 8, add docstrings to new functions, update tests and docs alongside your changes.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- [HuggingFace Transformers](https://huggingface.co/docs/transformers/) — DistilBERT model
- [NLTK](https://www.nltk.org/) — Natural language processing tools
- [newspaper3k](https://newspaper.readthedocs.io/) — Article extraction
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — Image text extraction
- [Flask](https://flask.palletsprojects.com/) — Web framework

---

*Last Updated: March 2026 — Version 2.0.0 — Status: 🟢 Backend Complete, Frontend In Progress*