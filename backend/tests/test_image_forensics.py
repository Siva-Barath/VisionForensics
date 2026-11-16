import pytest
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import EvidenceCategory, EvidenceSource
from app.services.forensics.image_artifact_detector import ImageArtifactDetector
from app.services.forensics.image_analyzers.base_analyzer import ImageAnalyzerConfig, ImageAnalysisCache
from app.services.forensics.image_analyzers import (
    BlurAnalyzer, NoiseAnalyzer, ELAAnalyzer, EdgeAnalyzer, IlluminationAnalyzer, EntropyAnalyzer
)

@pytest.fixture
def base_context():
    ctx = AnalysisContext()
    ctx.preprocessed_images = []
    return ctx

@pytest.fixture
def config():
    return ImageAnalyzerConfig()

def test_cache_lazy_evaluation():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cache = ImageAnalysisCache(img)
    
    # Should evaluate and cache
    assert cache._gray is None
    gray = cache.gray
    assert cache._gray is not None
    assert gray.shape == (100, 100)
    
    assert cache._laplacian is None
    lap = cache.laplacian
    assert cache._laplacian is not None

def test_blur_analyzer(config, base_context):
    # Create a sharp image (high variance of laplacian)
    sharp_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(sharp_img, (20, 20), (80, 80), (255, 255, 255), -1)
    
    # Create a blurred image
    blur_img = cv2.GaussianBlur(sharp_img, (21, 21), 0)
    
    analyzer = BlurAnalyzer()
    
    # Sharp should not flag blur
    evidence1 = analyzer.analyze(0, ImageAnalysisCache(sharp_img), base_context, config)
    assert len(evidence1) == 0
    
    # Blur should flag
    evidence2 = analyzer.analyze(0, ImageAnalysisCache(blur_img), base_context, config)
    assert len(evidence2) > 0
    assert evidence2[0].category == EvidenceCategory.IMAGE
    assert "blurred" in evidence2[0].description.lower()

def test_noise_analyzer(config, base_context):
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Add heavy gaussian noise
    noise = np.random.normal(0, 50, img.shape).astype(np.uint8)
    noisy_img = cv2.add(img, noise)
    
    analyzer = NoiseAnalyzer()
    evidence = analyzer.analyze(0, ImageAnalysisCache(noisy_img), base_context, config)
    
    assert len(evidence) > 0
    assert "noise" in evidence[0].description.lower()

def test_edge_analyzer(config, base_context):
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # One-pixel checkerboards alias under the detector's Gaussian/Canny
    # smoothing. Use resolvable stripes and verify the fixture precondition.
    img[:, (np.arange(100) // 3) % 2 == 0] = 255
    assert np.count_nonzero(ImageAnalysisCache(img).canny) / 10000 > 0.3
    
    analyzer = EdgeAnalyzer()
    evidence = analyzer.analyze(0, ImageAnalysisCache(img), base_context, config)
    
    assert len(evidence) > 0
    assert "edge density" in evidence[0].description.lower()

def test_image_artifact_detector_orchestration(base_context, tmp_path):
    # Mock an image file
    img_path = str(tmp_path / "test.png")
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    cv2.imwrite(img_path, img)
    
    base_context.preprocessed_images = [img_path]
    
    detector = ImageArtifactDetector()
    evidence = detector.detect(base_context)
    
    # Should run all analyzers and return some evidence (e.g. noise analyzer might flag perfectly smooth img)
    assert isinstance(evidence, list)
