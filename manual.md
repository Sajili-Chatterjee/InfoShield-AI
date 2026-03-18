# 🛡️ InfoShield-AI — Complete Testing Guide
---

## PART 1: ENVIRONMENT SETUP (Do this first)

### Step 1 — Verify your virtual environment is active
```bash
# You should see (.venv) at the start of your terminal prompt
# If not, activate it:

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### Step 2 — Verify ALL packages are installed
```bash
pip install -r requirements.txt
pip install lxml_html_clean   # critical fix for newspaper3k
```

### Step 3 — Create all __init__.py files (CRITICAL — without these, Python can't find your modules)
```bash
# Windows (run in your project root)
type nul > agents\__init__.py
type nul > api\__init__.py
type nul > models\__init__.py
type nul > services\__init__.py
type nul > utils\__init__.py

# Mac/Linux
touch agents/__init__.py api/__init__.py models/__init__.py services/__init__.py utils/__init__.py
```

### Step 4 — Download NLTK data
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### Step 5 — Verify your folder structure looks like this
```
InfoShield-AI/
├── agents/
│   ├── __init__.py          ✅
│   ├── claim_extractor.py   ✅
│   ├── retriever.py         ✅
│   └── scorer.py            ✅
├── api/
│   ├── __init__.py          ✅
│   └── routes.py            ✅
├── data/
│   └── knowledge_base.json  ✅
├── models/
│   ├── __init__.py          ✅
│   └── model_loader.py      ✅
├── services/
│   ├── __init__.py          ✅
│   ├── image_processor.py   ✅
│   ├── pipeline.py          ✅
│   ├── social_media_handler.py ✅
│   └── url_processor.py     ✅
├── utils/
│   └── __init__.py          ✅
├── app.py                   ✅
├── config.py                ✅
├── demo.py                  ✅
├── streamlit_app.py         ✅
└── requirements.txt         ✅
```

---

## PART 2: UNIT TESTS — Test each module in isolation

Run these one at a time. Each one should print results without errors.

### TEST A — Can Python find all your modules? (Run this FIRST)
```bash
python -c "
from agents.claim_extractor import extract_claims
from agents.retriever import retrieve_evidence
from agents.scorer import compute_score
from services.pipeline import run_pipeline
from services.url_processor import extract_text_from_url
from services.social_media_handler import extract_social_text, is_social_media_url
from services.image_processor import check_ocr_availability
from models.model_loader import get_zero_shot_classifier
print('✅ All imports successful')
"
```
Expected output: `✅ All imports successful`
If you see an ImportError, the __init__.py files in that folder are missing.

---

### TEST B — Claim Extractor
```bash
python -c "
from agents.claim_extractor import extract_claims
text = 'Scientists at WHO confirmed vaccines are safe. Experts published peer-reviewed data. Share before deleted!!'
claims = extract_claims(text)
print('Claims found:', len(claims))
for c in claims:
    print(' -', c)
"
```
Expected: 2-3 claims, NOT the 'Share before deleted' junk sentence.

---

### TEST C — Knowledge Base + Retriever
```bash
python -c "
from agents.retriever import retrieve_evidence
claims = ['vaccines are safe and effective according to scientists']
evidence = retrieve_evidence(claims)
print('Evidence items:', len(evidence))
for e in evidence:
    print(' -', e[:80])
"
```
Expected: 1-3 matching evidence items about vaccines.

---

### TEST D — Scorer (most important test)
```bash
python -c "
from agents.scorer import compute_score

# Test 1: Should score as REAL
real_text = 'According to WHO researchers, vaccines are safe and effective. Published peer-reviewed studies confirm this.'
real_claims = ['vaccines are safe according to WHO researchers']
result = compute_score(real_text, real_claims, ['Vaccines are safe and effective according to WHO.'])
print('REAL text result:', result['label'], 'confidence:', result['confidence'])
print('Signals:', result['signals'])
print()

# Test 2: Should score as FAKE
fake_text = 'SHOCKING BOMBSHELL!! Vaccines contain microchips!! Sources say deep state tracking everyone. WAKE UP SHEEPLE!!! SHARE BEFORE DELETED!!'
fake_claims = ['vaccines contain microchips claim anonymous sources']
result = compute_score(fake_text, fake_claims, [])
print('FAKE text result:', result['label'], 'confidence:', result['confidence'])
print('Signals:', result['signals'])
"
```
Expected: First → REAL, Second → FAKE.
NOTE: The zero-shot model (BART) downloads ~1.6GB on first run. This is normal.
      Subsequent runs use the cached version and are instant.

---

### TEST E — Full pipeline end-to-end
```bash
python -c "
from services.pipeline import run_pipeline

tests = [
    ('REAL', 'Scientists at the CDC confirmed that hand washing significantly reduces the spread of infectious diseases according to published research.'),
    ('FAKE', 'BREAKING: Government secretly putting mind control chemicals in tap water!! Anonymous insider confirms. SHARE BEFORE THEY DELETE THIS!!!'),
]

for expected, text in tests:
    result = run_pipeline(text, source_type='text')
    icon = 'PASS' if result['label'] == expected else 'FAIL'
    print(icon, '| Expected:', expected, '| Got:', result['label'], '| Conf:', result['confidence'])
    print('   Explanation:', result['explanation'][:150])
    print()
"
```
Expected: Both lines start with ✅

---

### TEST F — URL Processor
```bash
python -c "
from services.url_processor import extract_text_from_url

# Test with a real public news URL
url = 'https://www.bbc.com/news/health'
result = extract_text_from_url(url)
if result['text']:
    print('✅ URL extraction working')
    print('Words extracted:', len(result['text'].split()))
    print('Preview:', result['text'][:200])
else:
    print('⚠️  URL extraction failed (this may just be BBC blocking scrapers)')
    print('Error:', result['error'])
    print('This is OK — the fallback in routes.py handles this gracefully')
"
```

---

### TEST G — Social Media Detection
```bash
python -c "
from services.social_media_handler import is_social_media_url, extract_social_text

# Test detection
urls = [
    'https://www.reddit.com/r/worldnews/comments/abc123',
    'https://x.com/WHO/status/123',
    'https://www.bbc.com/news/health',
]
for url in urls:
    print(f'  {url[:50]} → social={is_social_media_url(url)}')

# Test Reddit extraction (public API, no login needed)
reddit_url = 'https://www.reddit.com/r/science/comments/1b3n4p5/climate_change_research/'
result = extract_social_text(reddit_url)
print()
if result['text']:
    print('✅ Reddit extraction working, words:', len(result['text'].split()))
else:
    print('⚠️  Reddit URL may not exist (404 is expected for demo URLs)')
    print('   Real posts work fine — error:', result['error'])
"
```

---

### TEST H — OCR / Image Processor
```bash
python -c "
from services.image_processor import check_ocr_availability
status = check_ocr_availability()
print('Tesseract available:', status['available'])
if status['available']:
    print('Version:', status['version'])
    print('✅ OCR is ready')
else:
    print('⚠️  Tesseract not installed:', status['error'])
    print('   Install: https://github.com/UB-Mannheim/tesseract/wiki')
"
```

---

## PART 3: FLASK API SERVER TESTS

### Step 1 — Start the Flask server
Open a terminal and run:
```bash
python app.py
```
You should see:
```
INFO  InfoShield-AI started in 'development' mode
INFO  Running on http://0.0.0.0:5000
```
Keep this terminal open. Open a SECOND terminal for the tests below.

---

### Step 2 — Test the health check (open in browser or run curl)

**Option A — Browser:**
Open: http://localhost:5000
Open: http://localhost:5000/health

Expected responses:
```json
{"project":"InfoShield-AI","status":"running","version":"2.0.0","endpoints":{...}}
{"status":"healthy","env":"development"}
```

**Option B — curl (Windows PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:5000/health -Method GET | Select-Object -ExpandProperty Content
```

**Option B — curl (Mac/Linux):**
```bash
curl http://localhost:5000/health
```

---

### Step 3 — Test POST /api/analyze (TEXT)

**Windows PowerShell:**
```powershell
$body = '{"text": "Scientists confirmed that vaccines are safe and effective according to peer-reviewed WHO research."}'
Invoke-WebRequest -Uri http://localhost:5000/api/analyze -Method POST -ContentType "application/json" -Body $body | Select-Object -ExpandProperty Content
```

**Mac/Linux curl:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Scientists confirmed that vaccines are safe and effective according to peer-reviewed WHO research."}'
```

Expected response:
```json
{
  "project": "InfoShield-AI",
  "label": "REAL",
  "confidence": 0.78,
  "explanation": "Zero-shot classification: 'real news'...",
  "evidence": ["Vaccines are safe and effective according to WHO..."],
  "signals": {"zero_shot_score": 0.82, "linguistic_score": 0.65, "evidence_score": 0.70}
}
```

---

### Step 4 — Test a FAKE news claim
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "BREAKING BOMBSHELL!! Vaccines secretly contain microchips!! Anonymous insiders confirm the deep state cover-up. SHARE BEFORE DELETED!!!"}'
```
Expected: `"label": "FAKE"` with low confidence.

---

### Step 5 — Test POST /api/analyze-url
```bash
curl -X POST http://localhost:5000/api/analyze-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reddit.com/r/science/comments/1b3n4p5/climate_change/"}'
```

---

### Step 6 — Test POST /api/analyze-batch
```bash
curl -X POST http://localhost:5000/api/analyze-batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"text": "NASA confirms climate change is real based on satellite data and decades of research."},
      {"text": "SHOCKING: Scientists hide the truth about flat earth. Wake up people!!!"}
    ]
  }'
```
Expected: Array of 2 results, first REAL, second FAKE.

---

### Step 7 — Test input validation (should return 400, not crash)
```bash
# Empty text — should return 400
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": ""}'

# Missing field — should return 400
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{}'

# Bad URL — should return 400
curl -X POST http://localhost:5000/api/analyze-url \
  -H "Content-Type: application/json" \
  -d '{"url": "not-a-url"}'
```

---

## PART 4: STREAMLIT UI TESTS (The Demo Interface)

Make sure Flask (`python app.py`) is still running in one terminal.
Open a second terminal and run:

```bash
streamlit run streamlit_app.py
```

Your browser will auto-open to http://localhost:8501

### UI Test Checklist:

**[ ] Text Tab:**
1. Paste: `Scientists confirm climate change is real based on 50 years of temperature data from NASA.`
2. Click Analyze
3. ✅ Should show GREEN "REAL" verdict + signal breakdown + evidence

4. Paste: `BOMBSHELL: 5G towers are spreading disease! Anonymous sources confirm government cover-up. SHARE BEFORE DELETED!!!`
5. Click Analyze
6. ✅ Should show RED "FAKE" verdict

**[ ] URL Tab:**
1. Enter: `https://www.reddit.com/r/worldnews/`
2. Click Analyze URL
3. ✅ Should extract text and show a result (REAL for factual subreddit)

4. Enter a Twitter/X URL
5. ✅ Should show a CLEAR error message (not a crash): "Twitter/X requires authentication..."

**[ ] Image Tab:**
1. Take a screenshot of any news headline
2. Upload it
3. ✅ Image preview appears
4. Click Analyze Image
5. ✅ Should show result + "Extracted Text" expandable section

**[ ] Backend Status (Sidebar):**
1. Click "Check Backend Status"
2. ✅ Should show "Backend is running ✅"
3. Stop Flask (Ctrl+C in that terminal)
4. Click again
5. ✅ Should show "Backend unreachable ❌" (not a crash/white screen)

---

## PART 5: DEMO SCRIPT TESTS

```bash
# Test all 4 scenarios
python demo.py

# Test individually
python demo.py --mode text
python demo.py --mode url
python demo.py --mode social
python demo.py --mode ocr
```

Expected: Coloured output, two text results (one REAL, one FAKE), no crashes.

---

## PART 6: FINAL CHECKLIST BEFORE GITHUB PUSH

Run through this checklist. All boxes should be ✅ before you push.

```
[ ] python -c "from services.pipeline import run_pipeline; print(run_pipeline('test vaccines WHO research')['label'])"
      → prints REAL or FAKE (not an error)

[ ] python app.py starts without errors

[ ] http://localhost:5000/health returns {"status":"healthy"}

[ ] POST /api/analyze with real news → label: REAL

[ ] POST /api/analyze with fake news → label: FAKE

[ ] POST /api/analyze with empty body → 400 error (not a 500 crash)

[ ] streamlit run streamlit_app.py opens in browser

[ ] Streamlit text analysis works end-to-end

[ ] python demo.py runs all 4 scenarios without ImportError

[ ] knowledge_base.json has at least 10 entries
```

---

## PART 7: PUSH TO GITHUB

Once all checks pass:

```bash
git add .
git commit -m "fix: complete system overhaul — correct detection logic, unified pipeline, all loopholes fixed"
git push origin main
```

---
---

# 🏆 HACKATHON
> "InfoShield-AI is a multi-agent system that detects fake news in real time
>  from any source — articles, social posts, or screenshots — using
>  zero-shot AI classification, linguistic analysis, and evidence retrieval."

---

## THE PROBLEM (30 seconds)

- Misinformation spreads **6x faster** than factual news on social media (MIT study, 2018)
- 64% of people have been exposed to a news story they suspected was fabricated
- Existing tools check only specific domains — they don't analyse **arbitrary content**
- No single tool handles text, URLs, social media, AND screenshots together

---

## THE SOLUTION

InfoShield-AI acts like a **team of AI agents**, each with a specific job:

| Agent | Job |
|---|---|
| 🔍 Input Handler | Accepts text, news URLs, Reddit posts, and screenshot images |
| ✂️ Claim Extractor | Breaks content into verifiable factual claims (not fluff) |
| 📚 Evidence Retriever | Finds supporting or contradicting facts from a knowledge base |
| 🤖 Zero-Shot Classifier | Uses BART-MNLI to classify content as "real news" vs "misinformation" |
| 📝 Linguistic Analyser | Scores writing style — flags sensational language, anonymous sources, ALL CAPS |
| ⚖️ Verdict Scorer | Combines all signals into a transparent weighted verdict |

---

## TECHNICAL HIGHLIGHTS

### Why our detection actually works (unlike most demos):
Most fake-news demos use a sentiment model and map positive→real, negative→fake.
**That is completely wrong.** InfoShield-AI uses:

1. **Zero-shot classification** (facebook/bart-large-mnli) — directly labels text as
   "real news" vs "misinformation" without any task-specific fine-tuning
2. **Linguistic fake-news pattern scoring** — 20+ regex patterns targeting the
   specific language signatures of misinformation
3. **Evidence-based retrieval scoring** — Jaccard similarity against a curated
   knowledge base of verified facts

### Transparent, explainable AI:
Every verdict comes with a full breakdown of all three signals, not just a label.
Users can see WHY content was flagged — a key requirement for trust in AI systems.

### Multi-source input (unique to InfoShield-AI):
| Input | How |
|---|---|
| Raw text | Direct pipeline |
| News URL | newspaper3k + BeautifulSoup fallback |
| Reddit | Public JSON API (no auth needed) |
| Twitter/X | Clear error with instructions (honest about limitations) |
| Screenshots | Tesseract OCR with OpenCV preprocessing |

### Robust engineering:
- Every function has a defined, consistent return shape (no more mystery crashes)
- All errors return meaningful JSON (no 500s for bad input)
- Full fallback chain: if one extractor fails, the next kicks in automatically
- Model caching — BART loads once, all requests reuse it

---

## DEMO FLOW

1. **Start with the shocker** — Paste an obvious fake claim:
   > "BOMBSHELL: 5G towers cause cancer!! Anonymous insiders confirm government hiding truth. SHARE BEFORE DELETED!!!"
   → Watch it flag FAKE with a detailed signal breakdown

2. **Then show a real claim** — paste an actual WHO statement
   → Watch it score REAL with supporting evidence cited

3. **Reddit live demo** — paste a real Reddit URL
   → Watch it extract text and analyse live

4. **Screenshot demo** — upload a screenshot of a fake headline
   → OCR extracts the text and the pipeline analyses it automatically

5. **Batch endpoint** — show the JSON API handling multiple claims at once
   → Demonstrates production-readiness

---

## HACKATHON-WORTHY

| Criteria | InfoShield-AI |
|---|---|
| **Novelty** | Multi-agent pipeline covering 4 input types, not just text |
| **Technical depth** | Zero-shot BART + linguistic scoring + evidence retrieval combined |
| **Real-world relevance** | Misinformation is one of the most critical global challenges |
| **Completeness** | Working API + Streamlit UI + CLI demo + test suite |
| **Explainability** | Every verdict is transparent — shows all contributing signals |
| **Scalability** | RESTful API design, stateless, can be deployed to any cloud |

---

## FUTURE ROADMAP

- Fine-tune a dedicated fake-news model on LIAR / FakeNewsNet datasets
- Add real-time fact-checking via Google Fact Check Tools API
- Browser extension for in-page analysis
- Database logging for analysis history and user feedback loop
- Multilingual support via mBERT or XLM-RoBERTa

---

## TECH STACK SUMMARY

```
Backend    : Python · Flask · Flask-CORS
ML / NLP   : HuggingFace Transformers (BART-MNLI) · NLTK · scikit-learn
Scraping   : newspaper3k · BeautifulSoup · PRAW (Reddit API)
OCR        : Tesseract · OpenCV · Pillow
Frontend   : Streamlit
Testing    : pytest · manual curl tests
```

---
*InfoShield-AI — Because truth deserves a shield.*