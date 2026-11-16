import pytest
from app.pipeline.context import AnalysisContext
from app.services.forensics.models import EvidenceCategory, RiskLevel, EvidenceSource, Evidence
from app.services.forensics.detector_registry import DetectorRegistry
from app.services.forensics.metadata_detector import MetadataDetector
from app.services.forensics.ocr_consistency_detector import OCRConsistencyDetector
from app.services.forensics.layout_consistency_detector import LayoutConsistencyDetector
from app.services.forensics.field_consistency_detector import FieldConsistencyDetector
from app.services.forensics.risk_estimator import RiskEstimator
from app.services.forensics.evidence_aggregator import EvidenceAggregator
from app.services.forensics.forgery_service import ForgeryService

def test_detector_registry():
    registry = DetectorRegistry()
    d1 = MetadataDetector()
    d2 = OCRConsistencyDetector()
    registry.register(d1)
    registry.register(d2)
    assert len(registry.get_all()) == 2
    
def test_metadata_detector():
    context = AnalysisContext()
    context.metadata = {"software": "Adobe Photoshop CS6"}
    
    detector = MetadataDetector()
    evidence = detector.detect(context)
    
    assert len(evidence) == 1
    assert evidence[0].category == EvidenceCategory.METADATA
    assert evidence[0].severity == 70.0
    
def test_field_consistency_detector():
    context = AnalysisContext()
    context.structured_document = {
        "fields": [
            {"key": "Name", "value": "John Doe"},
            {"key": "Name", "value": "Jane Doe"} # Duplicate key, diff value
        ]
    }
    
    detector = FieldConsistencyDetector()
    evidence = detector.detect(context)
    
    assert len(evidence) == 1
    assert evidence[0].category == EvidenceCategory.FIELD
    assert "Conflicting values" in evidence[0].description
    
def test_evidence_aggregator():
    aggregator = EvidenceAggregator()
    ev1 = Evidence(detector="test", category=EvidenceCategory.METADATA, severity=50, description="D1")
    ev2 = Evidence(detector="test", category=EvidenceCategory.IMAGE, severity=90, description="D2")
    ev3 = Evidence(detector="test", category=EvidenceCategory.IMAGE, severity=90, description="D2") # dup
    
    unique, summary = aggregator.aggregate([ev1, ev2, ev3])
    
    assert len(unique) == 2
    assert summary.total_evidence == 2
    assert summary.highest_severity == 90
    assert summary.category_counts[EvidenceCategory.IMAGE.value] == 1
    assert summary.category_counts[EvidenceCategory.METADATA.value] == 1

def test_risk_estimator():
    estimator = RiskEstimator()
    # Mocking some evidence
    ev_meta = Evidence(detector="test", category=EvidenceCategory.METADATA, severity=100.0, description="")
    ev_image = Evidence(detector="test", category=EvidenceCategory.IMAGE, severity=50.0, description="")
    
    # The current configured weights total 115 (including VISUAL and UNKNOWN).
    # Preserve normalization and approved weights, rather than changing policy
    # to match an obsolete expectation that assumed a total of 100.
    
    assessment = estimator.estimate([ev_meta, ev_image])
    assert assessment.risk_score == pytest.approx(30.0 / 1.15)
    assert assessment.risk_label == RiskLevel.MEDIUM
    
def test_forgery_service_flow():
    registry = DetectorRegistry()
    registry.register(MetadataDetector())
    registry.register(FieldConsistencyDetector())
    
    service = ForgeryService(registry)
    
    context = AnalysisContext()
    context.metadata = {"software": "GIMP 2.10"}
    context.structured_document = {
        "fields": [
            {"key": "DOB", "value": "01/01/2000"},
            {"key": "DOB", "value": "02/02/2000"} 
        ]
    }
    
    service.process(context)
    
    assert context.forgery_report is not None
    assert context.risk_assessment is not None
    assert context.risk_label is not None
    assert context.risk_score > 0
