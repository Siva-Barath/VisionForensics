"""
Classification Service.

Orchestrates feature extraction, rule evaluation, and aggregation to produce
a final ClassificationResult.
"""

import time
import logging

from app.pipeline.context import AnalysisContext
from app.services.classification.models import ExtractedFeatures, ClassificationResult, ClassificationSummary
from app.services.classification.profile_registry import DocumentProfileRegistry
from app.services.classification.ocr_feature_extractor import OCRFeatureExtractor
from app.services.classification.layout_feature_extractor import LayoutFeatureExtractor
from app.services.classification.image_feature_extractor import ImageFeatureExtractor
from app.services.classification.rule_classifier import RuleClassifier
from app.services.classification.score_aggregator import ScoreAggregator
from app.services.classification.confidence_estimator import ConfidenceEstimator

logger = logging.getLogger(__name__)

class ClassificationService:
    def __init__(self, registry: DocumentProfileRegistry):
        self.registry = registry
        self.ocr_extractor = OCRFeatureExtractor()
        self.layout_extractor = LayoutFeatureExtractor()
        self.image_extractor = ImageFeatureExtractor()
        self.classifier = RuleClassifier(registry)
        self.aggregator = ScoreAggregator()
        self.estimator = ConfidenceEstimator()

    def process(self, context: AnalysisContext) -> ClassificationResult:
        start_time = time.perf_counter()
        
        # 1. Feature Extraction
        features = ExtractedFeatures()
        self.ocr_extractor.extract(context, features)
        self.layout_extractor.extract(context, features)
        self.image_extractor.extract(context, features)
        
        # 2. Rule Classification (Raw Scores & Evidence)
        raw_predictions = self.classifier.classify(features)
        
        # 3. Score Aggregation (Normalization & Top-3 Ranking)
        top_3 = self.aggregator.aggregate(raw_predictions)
        
        # 4. Confidence Estimation
        final_confidence = self.estimator.estimate(top_3)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        if top_3 and top_3[0].confidence > 0:
            predicted_type = top_3[0].document_type
        else:
            from app.services.layout.models import DocumentType
            predicted_type = DocumentType.UNKNOWN
            
        summary = ClassificationSummary(
            total_features_extracted=len(features.__dict__),
            processing_time_ms=processing_time
        )
        
        logger.info(
            "Classification completed | job=%s | prediction=%s | confidence=%.2f | time=%.1fms",
            context.job_id, predicted_type.value, final_confidence, processing_time
        )
        
        return ClassificationResult(
            predicted_type=predicted_type,
            confidence=final_confidence,
            top_predictions=top_3,
            summary=summary
        )
