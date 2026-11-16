"""
PaddleOCR Engine.

Implements the BaseEngine interface for PaddleOCR.
Handles lazy initialization, configurable parameters, and mapping of raw
PaddleOCR outputs to the project's native OCR models.
"""

import logging
from typing import Optional
import numpy as np

from app.services.ocr.engines.base_engine import BaseEngine
from app.services.ocr.models import OCRPage, OCRBlock, OCRLine, OCRWord, BoundingBox

logger = logging.getLogger(__name__)

class PaddleOCREngine(BaseEngine):
    def __init__(self, **kwargs):
        """
        Initialize the wrapper. 
        PaddleOCR model is loaded lazily on first use.
        
        Default configurations:
            - lang: "en"
            - use_angle_cls: True
            - use_gpu: False
        """
        self.config = {
            "lang": "en",
            "use_angle_cls": True,
            "use_gpu": False,
        }
        self.config.update(kwargs)
        
        self._model = None
        self._is_available = None

    def initialize(self) -> None:
        """Lazily initialize the PaddleOCR model."""
        if self._model is not None:
            return
            
        try:
            # We import here so PaddleOCR is not required just to load this file
            from paddleocr import PaddleOCR
            
            logger.info("Initializing PaddleOCR with config: %s", self.config)
            self._model = PaddleOCR(**self.config)
            self._is_available = True
        except ImportError:
            self._is_available = False
            logger.error("PaddleOCR library not installed. Please install paddleocr and paddlepaddle.")
        except Exception as e:
            self._is_available = False
            logger.error(f"Failed to initialize PaddleOCR: {str(e)}")

    def is_available(self) -> bool:
        if self._is_available is None:
            # Attempt to import without fully loading the model just to check availability
            try:
                import paddleocr
                self._is_available = True
            except ImportError:
                self._is_available = False
        return self._is_available

    def _ensure_initialized(self) -> bool:
        if self._model is None:
            self.initialize()
        return self._is_available and self._model is not None

    def extract_text(self, image: np.ndarray) -> str:
        page = self.extract_words(image)
        lines = []
        for block in page.blocks:
            for line in block.lines:
                lines.append(" ".join(w.text for w in line.words))
        return "\n".join(lines)

    def extract_words(self, image: np.ndarray) -> OCRPage:
        if not self._ensure_initialized():
            raise RuntimeError("PaddleOCR model is unavailable or failed to initialize")
            
        if image is None or not isinstance(image, np.ndarray):
            logger.warning("Invalid image provided to PaddleOCR. Returning empty OCRPage.")
            return OCRPage(page_index=0)

        try:
            # PaddleOCR ocr() returns a list of results. 
            # For a single image, it's typically a list containing one list of text boxes.
            result = self._model.ocr(image, cls=self.config.get("use_angle_cls", True))
            
            blocks = []
            
            if result and result[0]:
                for res in result[0]:
                    # Format: [[box_points], (text, confidence)]
                    # If angle classification is used, the exact format might vary slightly or be handled upstream.
                    # Standard format: [[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ('text', conf)]
                    box_pts = res[0]
                    text_data = res[1]
                    text = text_data[0]
                    confidence = float(text_data[1])
                    
                    bbox = BoundingBox(points=box_pts)
                    
                    # Note: PaddleOCR doesn't natively return individual word rotation angles in standard usage,
                    # but if cls=True it predicts text line direction. For now, we leave rotation_angle=None
                    # as a placeholder for when we compute skew geometrically or extract it.
                    word = OCRWord(
                        text=text, 
                        confidence=confidence, 
                        bounding_box=bbox,
                        rotation_angle=None
                    )
                    
                    line = OCRLine(words=[word])
                    blocks.append(OCRBlock(lines=[line]))
                    
            return OCRPage(page_index=0, blocks=blocks)
            
        except Exception as e:
            logger.error("PaddleOCR extraction failed: %s", str(e))
            raise RuntimeError("PaddleOCR extraction failed") from e

    def extract_lines(self, image: np.ndarray) -> OCRPage:
        # PaddleOCR already generally groups by line.
        return self.extract_words(image)

    def extract_blocks(self, image: np.ndarray) -> OCRPage:
        # PaddleOCR doesn't group into blocks natively.
        return self.extract_words(image)

    def extract_batch(self, images: list[np.ndarray]) -> list[OCRPage]:
        """
        Extract text from a batch of images.
        """
        if not self._ensure_initialized():
            return [OCRPage(page_index=i) for i in range(len(images))]
            
        # PaddleOCR supports list of ndarray for batching in some versions
        # We will loop over them for now until batching is explicitly tuned, 
        # but the API allows transparent optimization later.
        pages = []
        for i, img in enumerate(images):
            page = self.extract_words(img)
            page.page_index = i
            pages.append(page)
            
        return pages
