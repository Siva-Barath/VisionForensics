import pytest
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import EvidenceCategory
from app.services.forensics.signature_region_analyzer import SignatureRegionAnalyzer
from app.services.forensics.signature_analyzers import SignatureAnalysisCache, SignatureFeatures, SignatureAnalyzerConfig
from app.services.forensics.signature_analyzers.signature_validator import SignatureValidator
from app.services.forensics.signature_analyzers.stroke_analyzer import StrokeAnalyzer

def test_signature_validator():
    validator = SignatureValidator()
    
    # Empty
    valid, msg = validator.validate(np.array([]))
    assert not valid
    
    # Too small
    crop = np.zeros((5, 5, 3), dtype=np.uint8)
    valid, msg = validator.validate(crop)
    assert not valid
    
    # Blank (no ink)
    crop = np.full((100, 100, 3), 255, dtype=np.uint8)
    valid, msg = validator.validate(crop)
    assert not valid
    
    # Valid (some ink)
    crop = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.circle(crop, (50, 50), 20, (0, 0, 0), -1)
    valid, msg = validator.validate(crop)
    assert valid

def test_stroke_analyzer():
    # Create a perfectly uniform digital stroke (e.g. MS Paint line)
    img = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.line(img, (10, 50), (90, 50), (0, 0, 0), 4) # exactly 4px thick everywhere
    
    cache = SignatureAnalysisCache(img)
    features = SignatureFeatures()
    context = AnalysisContext()
    config = SignatureAnalyzerConfig()
    
    analyzer = StrokeAnalyzer()
    evidence = analyzer.analyze(cache, features, context, config)
    
    # Uniform stroke should have very low standard deviation
    assert features.stroke_width_std is not None
    assert features.stroke_width_std < config.stroke_uniformity_threshold
    assert len(evidence) > 0
    assert "unnaturally uniform" in evidence[0].description.lower()

def test_signature_region_orchestration(tmp_path):
    # Mock preprocessed image
    img_path = str(tmp_path / "test_sig.png")
    img = np.full((500, 500, 3), 255, dtype=np.uint8)
    cv2.line(img, (50, 50), (150, 150), (0, 0, 0), 2)
    cv2.imwrite(img_path, img)
    
    ctx = AnalysisContext()
    ctx.preprocessed_images = [img_path]
    ctx.structured_document = {
        "sections": [
            {
                "region_type": "SIGNATURE",
                "bounding_box": {
                    "points": [[40, 40], [160, 40], [160, 160], [40, 160]]
                }
            }
        ]
    }
    
    analyzer = SignatureRegionAnalyzer()
    evidence = analyzer.detect(ctx)
    
    # Since it's just a single simple line, complexity will be very low
    # The complexity threshold check should fire, plus maybe others
    assert isinstance(evidence, list)
    assert len(evidence) > 0
    
    complex_evidence = [e for e in evidence if "complexity" in e.description.lower()]
    assert len(complex_evidence) > 0
