import pytest
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.logo_region_analyzer import LogoRegionAnalyzer
from app.services.forensics.logo_analyzers import LogoAnalysisCache, LogoFeatures, LogoAnalyzerConfig
from app.services.forensics.logo_analyzers.shape_analyzer import ShapeAnalyzer
from app.services.forensics.logo_analyzers.symmetry_analyzer import SymmetryAnalyzer

def test_shape_analyzer_hu_moments():
    # A perfect circle
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(img, (50, 50), 30, (255, 255, 255), -1)
    
    cache = LogoAnalysisCache(img)
    features = LogoFeatures()
    
    analyzer = ShapeAnalyzer()
    analyzer.analyze(cache, features, AnalysisContext(), LogoAnalyzerConfig())
    
    # Hu moments should be calculated
    assert features.fingerprint.hu_moments is not None
    assert len(features.fingerprint.hu_moments) == 7
    # Circle has high solidity and circularity
    assert features.fingerprint.solidity is not None
    assert features.fingerprint.solidity > 0.95
    assert features.fingerprint.shape_circularity is not None
    # Discrete OpenCV contour perimeter biases a radius-30 circle below 1.
    # It must still exceed a square (pi/4), distinguishing the foreground
    # circle from the surrounding rectangular background.
    assert 0.85 < features.fingerprint.shape_circularity <= 1.0

def test_symmetry_analyzer():
    # A symmetric cross
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (40, 10), (60, 90), (255, 255, 255), -1)
    cv2.rectangle(img, (10, 40), (90, 60), (255, 255, 255), -1)
    
    cache = LogoAnalysisCache(img)
    features = LogoFeatures()
    
    analyzer = SymmetryAnalyzer()
    analyzer.analyze(cache, features, AnalysisContext(), LogoAnalyzerConfig())
    
    # Very high horizontal symmetry
    assert features.fingerprint.symmetry_horizontal is not None
    assert features.fingerprint.symmetry_horizontal > 0.9

def test_logo_orchestrator(tmp_path):
    img_path = str(tmp_path / "test_logo.png")
    
    # A highly jagged aliased logo to trigger edge analyzer
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(10, 100, 10):
        cv2.line(img, (i, 10), (i, 100), (255,255,255), 1)
        cv2.line(img, (10, i), (100, i), (255,255,255), 1)
        
    cv2.imwrite(img_path, img)
    
    ctx = AnalysisContext()
    ctx.preprocessed_images = [img_path]
    ctx.structured_document = {
        "sections": [
            {
                "region_type": "LOGO",
                "bounding_box": {
                    "points": [[0, 0], [200, 0], [200, 200], [0, 200]]
                }
            }
        ]
    }
    
    analyzer = LogoRegionAnalyzer()
    evidence = analyzer.detect(ctx)
    
    assert isinstance(evidence, list)
    # The edge analyzer will penalize the authenticity score enough to flag it
    assert len(evidence) > 0
    assert any('jagged' in item.description.lower() or 'Authenticity Score' in item.description for item in evidence)
