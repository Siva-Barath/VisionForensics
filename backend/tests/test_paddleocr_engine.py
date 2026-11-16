import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.services.ocr.engines.paddleocr_engine import PaddleOCREngine

@pytest.fixture
def dummy_image():
    return np.zeros((100, 100, 3), dtype=np.uint8)

def test_paddleocr_lazy_initialization():
    engine = PaddleOCREngine()
    assert engine._model is None
    
    # Adapter unit test: inject the dependency instead of importing the user's
    # optional native PaddleX/Faiss installation during mock setup.
    MockPaddleOCR = MagicMock()
    with patch.dict('sys.modules', {'paddleocr': MagicMock(PaddleOCR=MockPaddleOCR)}):
        engine.initialize()
        MockPaddleOCR.assert_called_once_with(lang="en", use_angle_cls=True, use_gpu=False)
        assert engine._is_available is True
        assert engine._model is not None

def test_paddleocr_missing_library():
    engine = PaddleOCREngine()
    
    # Simulate missing paddleocr library by making it raise ImportError
    with patch.dict('sys.modules', {'paddleocr': None}):
        engine.initialize()
        
    assert engine._is_available is False
    assert engine._model is None

def test_extract_words_maps_correctly(dummy_image):
    engine = PaddleOCREngine()
    
    # Mocking PaddleOCR output format: [[[x,y],...], ('text', conf)]
    mock_result = [
        [
            [[10.0, 10.0], [50.0, 10.0], [50.0, 30.0], [10.0, 30.0]],
            ("Hello", 0.95)
        ],
        [
            [[60.0, 10.0], [100.0, 10.0], [100.0, 30.0], [60.0, 30.0]],
            ("World", 0.88)
        ]
    ]
    
    mock_model = MagicMock()
    mock_model.ocr.return_value = [mock_result]
    
    engine._model = mock_model
    engine._is_available = True
    
    page = engine.extract_words(dummy_image)
    
    assert page.page_index == 0
    assert len(page.blocks) == 2  # Our simple mapper maps each result to one block/line/word for now
    
    word1 = page.blocks[0].lines[0].words[0]
    assert word1.text == "Hello"
    assert word1.confidence == 0.95
    assert word1.rotation_angle is None
    assert word1.bounding_box.points == [[10.0, 10.0], [50.0, 10.0], [50.0, 30.0], [10.0, 30.0]]

def test_extract_batch(dummy_image):
    engine = PaddleOCREngine()
    mock_model = MagicMock()
    mock_model.ocr.return_value = []
    
    engine._model = mock_model
    engine._is_available = True
    
    pages = engine.extract_batch([dummy_image, dummy_image])
    assert len(pages) == 2
    assert pages[0].page_index == 0
    assert pages[1].page_index == 1

def test_extract_invalid_image():
    engine = PaddleOCREngine()
    engine._is_available = True
    engine._model = MagicMock()
    
    page = engine.extract_words(None)
    assert len(page.blocks) == 0
    
    page = engine.extract_words("not an image")
    assert len(page.blocks) == 0
