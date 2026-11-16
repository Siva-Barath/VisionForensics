"""
OCR Feature Extractor.

Extracts text, keywords, and phrase frequency from OCR results.
"""

from app.pipeline.context import AnalysisContext
from app.services.classification.models import ExtractedFeatures

class OCRFeatureExtractor:
    def extract(self, context: AnalysisContext, features: ExtractedFeatures) -> None:
        ocr_text = []
        
        # Grab text from structured document or OCR result
        doc = context.structured_document
        if doc and "sections" in doc:
            for sec in doc["sections"]:
                text = sec.get("text", "")
                if text:
                    ocr_text.append(text.lower())
        else:
            # Fallback to OCR summary
            summary = context.ocr_summary
            if summary and "text" in summary:
                ocr_text.append(summary["text"].lower())
                
        features.ocr_text_lower = " ".join(ocr_text)
