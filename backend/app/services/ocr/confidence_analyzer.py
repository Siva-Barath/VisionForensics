"""
Confidence Analyzer for OCR outputs.

Computes average, minimum, maximum confidence scores, and identifies 
low confidence regions without depending on a specific backend.
"""

from app.services.ocr.models import OCRPage, OCRSummary

class ConfidenceAnalyzer:
    def __init__(self, low_confidence_threshold: float = 0.5):
        self.threshold = low_confidence_threshold

    def analyze(self, page: OCRPage, engine_used: str = "unknown", processing_time_ms: float = 0.0) -> OCRSummary:
        """Analyze a page of OCR output and return a summary."""
        confidences = []
        low_conf_count = 0

        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    confidences.append(word.confidence)
                    if word.confidence < self.threshold:
                        low_conf_count += 1

        total_words = len(confidences)
        
        if total_words == 0:
            return OCRSummary(
                engine_used=engine_used,
                processing_time_ms=processing_time_ms
            )

        avg_conf = sum(confidences) / total_words
        min_conf = min(confidences)
        max_conf = max(confidences)
        low_fraction = low_conf_count / total_words

        return OCRSummary(
            average_confidence=avg_conf,
            min_confidence=min_conf,
            max_confidence=max_conf,
            low_confidence_fraction=low_fraction,
            total_words=total_words,
            engine_used=engine_used,
            processing_time_ms=processing_time_ms
        )
