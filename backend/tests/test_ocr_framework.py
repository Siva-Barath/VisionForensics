import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.pipeline.context import AnalysisContext
from app.services.ocr.engine_selector import EngineSelector
from app.services.ocr.ocr_service import OCRService
from app.services.ocr.postprocessor import PostProcessor
from app.services.ocr.confidence_analyzer import ConfidenceAnalyzer
from app.services.ocr.models import OCRPage, OCRBlock, OCRLine, OCRWord, BoundingBox
from app.services.ocr.engines.base_engine import BaseEngine
from app.services.ocr.visualizer import OCRVisualizer


class DummyEngine(BaseEngine):
    def initialize(self) -> None: pass
    def is_available(self) -> bool: return True
    def extract_text(self, image: np.ndarray) -> str: return "Dummy"
    def extract_words(self, image: np.ndarray) -> OCRPage:
        # Returns a dummy page
        box = BoundingBox(points=[[0, 0], [10, 0], [10, 10], [0, 10]])
        word1 = OCRWord(text="Hello", confidence=0.9, bounding_box=box)
        word2 = OCRWord(text="World", confidence=0.4, bounding_box=box)
        line = OCRLine(words=[word1, word2])
        block = OCRBlock(lines=[line])
        return OCRPage(page_index=0, blocks=[block])
    def extract_lines(self, image: np.ndarray) -> OCRPage:
        return OCRPage(page_index=0)
    def extract_blocks(self, image: np.ndarray) -> OCRPage:
        return OCRPage(page_index=0)


def test_engine_selector_registration():
    selector = EngineSelector()
    selector.register("dummy", DummyEngine)
    engine = selector.get_engine("dummy")
    assert isinstance(engine, DummyEngine)

    with pytest.raises(ValueError):
        selector.get_engine("non_existent")


def test_postprocessor_normalization():
    processor = PostProcessor()
    
    # Test unicode normalization and whitespace
    text = "Hello \u3000   World\u200b  !"
    cleaned = processor.normalize_text(text)
    assert cleaned == "Hello World !"


def test_confidence_analyzer():
    analyzer = ConfidenceAnalyzer(low_confidence_threshold=0.5)
    
    box = BoundingBox()
    word1 = OCRWord(text="A", confidence=0.9, bounding_box=box)
    word2 = OCRWord(text="B", confidence=0.4, bounding_box=box)
    word3 = OCRWord(text="C", confidence=0.2, bounding_box=box)
    
    page = OCRPage(page_index=0, blocks=[OCRBlock(lines=[OCRLine(words=[word1, word2, word3])])])
    
    summary = analyzer.analyze(page, engine_used="test")
    
    assert summary.total_words == 3
    assert summary.average_confidence == (0.9 + 0.4 + 0.2) / 3
    assert summary.min_confidence == 0.2
    assert summary.max_confidence == 0.9
    assert summary.low_confidence_fraction == 2 / 3


@patch("cv2.imread")
def test_ocr_service(mock_imread):
    # Mock imread to return a dummy image
    mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    
    context = AnalysisContext()
    context.preprocessed_images = ["path/to/img1.png"]
    
    service = OCRService(engine_name="dummy")
    service.selector.register("dummy", DummyEngine)
    
    service.process(context)
    
    assert context.ocr_result is not None
    assert context.ocr_summary is not None
    assert context.ocr_summary["engine_used"] == "dummy"
    assert context.ocr_summary["total_words"] == 2
    assert context.ocr_summary["low_confidence_fraction"] == 0.5


def test_ocr_visualizer():
    visualizer = OCRVisualizer()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    box = BoundingBox(points=[[10, 10], [50, 10], [50, 30], [10, 30]])
    word = OCRWord(text="Test", confidence=0.95, bounding_box=box)
    page = OCRPage(page_index=0, blocks=[OCRBlock(lines=[OCRLine(words=[word])])])
    
    annotated = visualizer.draw_boxes(img, page)
    # Ensure drawing happened and didn't crash
    assert annotated.shape == img.shape
    assert not np.array_equal(annotated, img) # The image was modified

