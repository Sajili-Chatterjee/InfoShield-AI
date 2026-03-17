# services/pipeline.py

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.predictor import predict, predict_text, get_predictor
from agents.claim_extractor import extract_claims, extract_key_claims, clean_ocr_text
from agents.retriever import retrieve, retrieve_with_metadata, reload_knowledge_base
from agents.verifier import verify, verify_with_metadata, get_verification_summary
from agents.scorer import (
    compute_final_score, 
    get_final_label,
    compute_credibility,
    explain_score,
    get_confidence_score
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_text(text: str, options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Main pipeline for text analysis.
    Preserves original logic while adding enhancements.
    
    Args:
        text: Input text to analyze
        options: Optional configuration dictionary
            - use_fake_news_model: bool (default: False)
            - include_details: bool (default: False)
            - max_claims: int (default: 5)
            - ocr_confidence: float (optional)
            - source: str (optional)
    
    Returns:
        Dictionary with analysis results
    """
    start_time = time.time()
    options = options or {}
    
    logger.info("Starting text analysis pipeline")
    
    # Step 0: Preprocess text (clean OCR artifacts if present)
    if options.get('ocr_confidence') is not None:
        # Text likely comes from OCR, clean it
        cleaned_text = clean_ocr_text(text)
        logger.debug(f"Cleaned OCR text (length: {len(cleaned_text)})")
    else:
        cleaned_text = text
    
    # Step 1: Model prediction (preserved with enhancement)
    logger.debug("Step 1: Running model prediction")
    use_fake_news_model = options.get('use_fake_news_model', False)
    
    if use_fake_news_model:
        model_output = predict_text(cleaned_text, use_fake_news_model=True)
    else:
        # Original behavior preserved
        model_output = predict(cleaned_text)
    
    logger.debug(f"Model prediction: {model_output.get('label')} "
                f"with confidence {model_output.get('confidence'):.3f}")
    
    # Step 2: Extract claims (preserved)
    logger.debug("Step 2: Extracting claims")
    max_claims = options.get('max_claims', 5)
    
    if options.get('extract_key_claims', False):
        claims = extract_key_claims(cleaned_text, max_claims=max_claims)
    else:
        # Original behavior preserved
        claims = extract_claims(cleaned_text)
    
    logger.debug(f"Extracted {len(claims)} claims")
    
    # Step 3: Retrieve evidence (preserved with enhancement)
    logger.debug("Step 3: Retrieving evidence")
    use_metadata = options.get('use_metadata', False)
    
    if use_metadata:
        evidence_with_metadata = retrieve_with_metadata(claims, top_k=2)
        evidence = [item['text'] for item in evidence_with_metadata]
        source_quality = [item.get('score', 0.5) for item in evidence_with_metadata]
    else:
        # Original behavior preserved
        evidence = retrieve(claims, top_k=2)
        source_quality = None
    
    logger.debug(f"Retrieved {len(evidence)} evidence items")
    
    # Step 4: Verification (preserved with enhancement)
    logger.debug("Step 4: Verifying claims against evidence")
    include_verification_details = options.get('include_verification_details', False)
    
    if include_verification_details:
        verification_result = verify_with_metadata(claims, evidence_with_metadata if use_metadata else evidence)
        verification_score = verification_result.get('score', 0.5)
        verification_details = verification_result.get('details', [])
    else:
        # Original behavior preserved
        verification_score = verify(claims, evidence)
        verification_details = []
    
    logger.debug(f"Verification score: {verification_score:.3f}")
    
    # Step 5: Final scoring (preserved)
    logger.debug("Step 5: Computing final score")
    
    # Get OCR confidence if available
    ocr_confidence = options.get('ocr_confidence')
    
    final_score = compute_final_score(
        model_output,
        verification_score,
        evidence,
        source_quality=source_quality,
        ocr_confidence=ocr_confidence
    )
    
    final_label = get_final_label(final_score)
    
    # Step 6: Generate explanation (preserved but enhanced)
    logger.debug("Step 6: Generating explanation")
    
    # Original explanation format preserved
    base_explanation = (
        f"Model predicted '{model_output.get('label', 'UNKNOWN')}' "
        f"with confidence {model_output.get('confidence', 0.5):.3f}. "
        f"Verification score is {verification_score:.3f}, "
        f"based on {len(evidence)} retrieved evidence items."
    )
    
    # Enhanced explanation if requested
    if options.get('detailed_explanation', False):
        detailed_explanation = explain_score(
            model_output.get('confidence', 0.5),
            verification_score,
            compute_credibility(evidence, source_quality),
            ocr_confidence
        )
        explanation = detailed_explanation
    else:
        explanation = base_explanation
    
    # Build result (preserving original fields)
    result = {
        "label": final_label,
        "confidence": final_score,
        "explanation": explanation,
        "evidence": evidence
    }
    
    # Add enhanced fields if requested
    if options.get('include_details', False):
        # Get confidence breakdown
        confidence_scores = get_confidence_score(
            model_output,
            verification_details,
            len(evidence)
        )
        
        result.update({
            "pipeline_time": round(time.time() - start_time, 3),
            "timestamp": datetime.now().isoformat(),
            "model_output": {
                "label": model_output.get('label'),
                "confidence": model_output.get('confidence'),
                "original_label": model_output.get('original_label'),
                "original_confidence": model_output.get('original_confidence')
            },
            "claims": claims[:3] if claims else [],  # Show top 3 claims
            "verification_score": verification_score,
            "credibility_score": compute_credibility(evidence, source_quality),
            "confidence_breakdown": confidence_scores,
            "stats": {
                "num_claims": len(claims),
                "num_evidence": len(evidence),
                "verification_matches": len(verification_details)
            }
        })
        
        # Add verification summary if available
        if include_verification_details:
            result["verification_summary"] = get_verification_summary(verification_result)
    
    # Add source info if provided
    if 'source' in options:
        result["source"] = options['source']
    
    # Add OCR info if available
    if ocr_confidence is not None:
        result["ocr_confidence"] = ocr_confidence
    
    logger.info(f"Pipeline completed in {time.time() - start_time:.2f}s")
    
    return result


def analyze_with_source(text: str, source: str, source_type: str = "text") -> Dict[str, Any]:
    """
    Analyze text with source information.
    
    Args:
        text: Input text
        source: Source of the text (URL, platform, etc.)
        source_type: Type of source (url, social_media, image, etc.)
    
    Returns:
        Analysis results with source metadata
    """
    options = {
        'source': source,
        'source_type': source_type,
        'include_details': True
    }
    
    result = analyze_text(text, options)
    
    # Add source-specific metadata
    result["input_source"] = source
    result["input_type"] = source_type
    
    return result


def analyze_ocr_text(text: str, ocr_confidence: float, source: str = None) -> Dict[str, Any]:
    """
    Specialized function for text extracted via OCR.
    
    Args:
        text: OCR extracted text
        ocr_confidence: Confidence score from OCR (0-1)
        source: Optional source description
    
    Returns:
        Analysis results with OCR metadata
    """
    options = {
        'ocr_confidence': ocr_confidence,
        'clean_ocr': True,
        'include_details': True,
        'detailed_explanation': True
    }
    
    if source:
        options['source'] = source
    
    return analyze_text(text, options)


def analyze_batch(texts: List[str], options: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Analyze multiple texts in batch.
    
    Args:
        texts: List of texts to analyze
        options: Options to pass to each analysis
    
    Returns:
        List of analysis results
    """
    results = []
    for i, text in enumerate(texts):
        logger.info(f"Processing batch item {i+1}/{len(texts)}")
        result = analyze_text(text, options)
        result["batch_index"] = i
        results.append(result)
    return results


def reload_pipeline_knowledge_base() -> bool:
    """
    Reload the knowledge base used by the retriever.
    Useful for updating the pipeline without restart.
    """
    return reload_knowledge_base()


def get_pipeline_info() -> Dict[str, Any]:
    """
    Get information about the pipeline and its components.
    """
    return {
        "name": "InfoShield-AI Pipeline",
        "version": "2.0.0",
        "components": [
            "Model Predictor",
            "Claim Extractor",
            "Evidence Retriever",
            "Verifier",
            "Scorer"
        ],
        "features": [
            "OCR Support",
            "Source Attribution",
            "Detailed Explanations",
            "Batch Processing"
        ],
        "knowledge_base_size": len(__import__('agents.retriever').retriever.KNOWLEDGE_BASE)
    }


# Preserve original function for backward compatibility
__all__ = [
    'analyze_text',  # Original function (enhanced but backward compatible)
    'analyze_with_source',
    'analyze_ocr_text',
    'analyze_batch',
    'reload_pipeline_knowledge_base',
    'get_pipeline_info'
]