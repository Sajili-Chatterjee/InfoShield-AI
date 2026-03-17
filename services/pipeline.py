# services/pipeline.py

import logging
from typing import Dict, Any

from models.predictor import predict
from models.utils import clean_text
from agents.claim_extractor import extract_claims
from agents.retriever import retrieve
from agents.verifier import verify
from agents.scorer import final_score
from agents.realtime_retriever import fetch_real_time_news

from services.url_processor import extract_text_from_url_simple

logger = logging.getLogger(__name__)


# ---------------------------
# 🔹 CORE PIPELINE
# ---------------------------
def run_pipeline(input_data: str) -> Dict[str, Any]:

    # ---------------------------
    # 🔗 HANDLE URL INPUT
    # ---------------------------
    if input_data.startswith("http"):

        text, error = extract_text_from_url_simple(input_data)

        if error or not text:
            return {
                "label": "Unknown",
                "confidence": 0.5,
                "error": f"URL extraction failed: {error}",
                "evidence": [],
                "explanation": "Could not extract content from URL."
            }

    else:
        text = input_data

    # ---------------------------
    # 🧹 CLEAN TEXT
    # ---------------------------
    if not text or not isinstance(text, str):
        return {
            "label": "Unknown",
            "confidence": 0.5,
            "error": "Invalid input text",
            "evidence": [],
            "explanation": "Input text is invalid."
        }

    text = clean_text(text)

    # 🔥 LIMIT TEXT SIZE (CRITICAL FIX)
    if len(text) > 2000:
        text = text[:2000]

    try:
        # ---------------------------
        # 🤖 MODEL PREDICTION
        # ---------------------------
        prediction = predict(text)

        # FIX: handle dict output properly
        model_label = prediction.get("label", "UNKNOWN")
        model_score = prediction.get("confidence", 0.5)

        # ---------------------------
        # 🧩 CLAIM EXTRACTION
        # ---------------------------
        claims = extract_claims(text)
        if not claims:
            claims = [text[:100]]

        all_evidence = []
        verification_scores = []
        reasoning_steps = []

        # ---------------------------
        # 🌐 REAL-TIME NEWS
        # ---------------------------
        realtime_evidence = fetch_real_time_news(text[:100])
        realtime_score = 0.7 if realtime_evidence else 0.3

        # ---------------------------
        # 🔁 PROCESS CLAIMS
        # ---------------------------
        for claim in claims:
            evidence = retrieve(claim)
            score = verify(claim, evidence)

            reasoning_steps.append({
                "claim": claim,
                "evidence": evidence if evidence else ["No KB evidence"],
                "verification_score": score
            })

            all_evidence.extend(evidence)
            verification_scores.append(score)

        verification_score = (
            sum(verification_scores) / len(verification_scores)
            if verification_scores else 0.3
        )

        # ---------------------------
        # 📊 FINAL SCORE
        # ---------------------------
        final = final_score(
            model_score,
            verification_score,
            0.5,  # default credibility
            realtime_score
        )

        final_label = "Fake" if final < 0.5 else "Real"

        if not realtime_evidence:
            final *= 0.7

        # ---------------------------
        # 🧠 EXPLANATION
        # ---------------------------
        explanation = f"""
AI Decision Breakdown:

✔ Model Output: {model_label}
✔ Model Confidence: {round(model_score,2)}
✔ Verification Score: {round(verification_score,2)}
✔ Real-Time Evidence: {"Found" if realtime_evidence else "Not Found"}

Conclusion: This news is classified as {final_label}.
"""

        return {
            "label": final_label,
            "confidence": round(final, 2),
            "reasoning": reasoning_steps,
            "evidence": list(set(all_evidence + realtime_evidence))[:5],
            "explanation": explanation
        }

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")

        return {
            "label": "Unknown",
            "confidence": 0.5,
            "error": str(e),
            "evidence": [],
            "explanation": "Pipeline failed during processing."
        }


# ---------------------------
# 🔹 PUBLIC FUNCTIONS
# ---------------------------
def analyze_text(text: str) -> Dict[str, Any]:
    return run_pipeline(text)


def analyze_url(url: str) -> Dict[str, Any]:
    return run_pipeline(url)


def analyze_ocr_text(text: str, confidence: float, source: str) -> Dict[str, Any]:
    result = run_pipeline(text)

    # adjust confidence using OCR quality
    result["confidence"] = round(result["confidence"] * confidence, 2)
    result["source"] = source

    return result