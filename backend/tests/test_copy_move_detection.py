import pytest
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.copy_move_region_analyzer import CopyMoveRegionAnalyzer
from app.services.forensics.copy_move_analyzers import CopyMoveAnalysisCache, CopyMoveFeatures, CopyMoveAnalyzerConfig
from app.services.forensics.copy_move_analyzers.orb_feature_analyzer import ORBFeatureAnalyzer
from app.services.forensics.copy_move_analyzers.translation_pattern_analyzer import TranslationPatternAnalyzer
from app.services.ocr.models import BoundingBox

def test_multiscale_cache():
    img = np.zeros((1000, 1000, 3), dtype=np.uint8)
    cache = CopyMoveAnalysisCache(img)
    
    assert cache.get_scale(1.0).shape == (1000, 1000)
    assert cache.get_scale(0.5).shape == (500, 500)
    assert cache.get_scale(0.25).shape == (250, 250)

def test_orb_analyzer():
    # Image with enough texture for ORB
    img = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
    cache = CopyMoveAnalysisCache(img)
    features = CopyMoveFeatures()
    
    analyzer = ORBFeatureAnalyzer()
    analyzer.analyze(cache, features, AnalysisContext(), CopyMoveAnalyzerConfig())
    
    assert features.keypoint_count_orb > 0

def test_translation_analyzer():
    class MockKeypoint:
        def __init__(self, pt):
            self.pt = pt
            
    class MockMatch:
        def __init__(self, q, t):
            self.queryIdx = q
            self.trainIdx = t
            
    # Mocking keypoints where m1, m2, m3 are shifted by +50, +50
    kps = [
        MockKeypoint((10, 10)), MockKeypoint((60, 60)),
        MockKeypoint((20, 20)), MockKeypoint((70, 70)),
        MockKeypoint((30, 30)), MockKeypoint((80, 80))
    ]
    
    matches = [
        MockMatch(0, 1),
        MockMatch(2, 3),
        MockMatch(4, 5)
    ]
    
    features = CopyMoveFeatures()
    features._temp_matches = {1.0: (kps, matches)}
    
    analyzer = TranslationPatternAnalyzer()
    config = CopyMoveAnalyzerConfig(minimum_match_count=2)
    
    analyzer.analyze(CopyMoveAnalysisCache(np.zeros((10,10))), features, AnalysisContext(), config)
    
    assert features.average_translation is not None
    assert features.average_translation == (50.0, 50.0)

def test_copymove_orchestrator(tmp_path):
    img_path = str(tmp_path / "test_copymove.png")
    
    # Create an image and literally copy a patch
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    # Add random texture
    img[100:200, 100:200] = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    
    # Copy move!
    img[300:400, 300:400] = img[100:200, 100:200]
    
    cv2.imwrite(img_path, img)
    
    ctx = AnalysisContext()
    ctx.preprocessed_images = [img_path]
    ctx.structured_document = {}
    
    analyzer = CopyMoveRegionAnalyzer(CopyMoveAnalyzerConfig(minimum_match_count=3))
    evidence = analyzer.detect(ctx)
    
    # The algorithms will find the duplicate
    assert len(evidence) > 0
    assert "copy-move" in evidence[0].description.lower()
