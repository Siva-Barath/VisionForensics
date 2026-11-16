import pytest
from app.pipeline.context import AnalysisContext
from app.services.classification.models import ExtractedFeatures
from app.services.layout.models import DocumentType
from app.services.classification.profile_registry import DocumentProfileRegistry
from app.services.classification.ocr_feature_extractor import OCRFeatureExtractor
from app.services.classification.layout_feature_extractor import LayoutFeatureExtractor
from app.services.classification.rule_classifier import RuleClassifier
from app.services.classification.score_aggregator import ScoreAggregator
from app.services.classification.confidence_estimator import ConfidenceEstimator
from app.services.classification.classification_service import ClassificationService

@pytest.fixture
def empty_context():
    return AnalysisContext()

def test_ocr_feature_extractor(empty_context):
    empty_context.structured_document = {
        "sections": [{"text": "Hello world passport"}]
    }
    extractor = OCRFeatureExtractor()
    features = ExtractedFeatures()
    extractor.extract(empty_context, features)
    assert "passport" in features.ocr_text_lower

def test_layout_feature_extractor(empty_context):
    empty_context.structured_document = {
        "tables": [{}, {}],
        "fields": [{}, {}, {}],
        "sections": [
            {"region_type": "SIGNATURE"},
            {"region_type": "LOGO"}
        ]
    }
    extractor = LayoutFeatureExtractor()
    features = ExtractedFeatures()
    extractor.extract(empty_context, features)
    assert features.table_count == 2
    assert features.field_count == 3
    assert features.signature_regions == 1
    assert features.logo_regions == 1

def test_rule_classifier_marksheet():
    features = ExtractedFeatures()
    features.ocr_text_lower = "cgpa 9.0 semester 8 university"
    features.table_count = 1
    
    registry = DocumentProfileRegistry()
    classifier = RuleClassifier(registry)
    predictions = classifier.classify(features)
    
    # Find marksheet prediction
    marksheet_pred = next(p for p in predictions if p.document_type == DocumentType.MARKSHEET)
    assert marksheet_pred.confidence > 0  # 15*3 + 20 = 65 points roughly
    assert len(marksheet_pred.evidence) > 0
    
def test_score_aggregator_top_3():
    registry = DocumentProfileRegistry()
    classifier = RuleClassifier(registry)
    aggregator = ScoreAggregator()
    
    # Highly ambiguous features matching multiple profiles slightly
    features = ExtractedFeatures()
    features.ocr_text_lower = "passport invoice cgpa"
    
    preds = classifier.classify(features)
    top_3 = aggregator.aggregate(preds)
    
    assert len(top_3) == 3
    # Check normalized sum
    assert sum(p.confidence for p in top_3) > 0.0

def test_classification_service(empty_context):
    empty_context.structured_document = {
        "sections": [{"text": "nationality date of birth <<<<<<<<<"}],
        "tables": []
    }
    registry = DocumentProfileRegistry()
    service = ClassificationService(registry)
    
    result = service.process(empty_context)
    assert result.predicted_type == DocumentType.PASSPORT
    assert result.confidence > 0.5
    assert len(result.top_predictions) <= 3
