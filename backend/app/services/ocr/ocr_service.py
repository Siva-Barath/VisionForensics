"""
OCR Service.

Orchestrates the entire OCR phase by coordinating engine selection,
extraction, post-processing, and confidence analysis.
Updates the AnalysisContext with the finalized data.
"""

import time
import logging
from typing import Optional
import cv2
import numpy as np

from app.pipeline.context import AnalysisContext
from app.services.ocr.engine_selector import EngineSelector
from app.services.ocr.postprocessor import PostProcessor
from app.services.ocr.confidence_analyzer import ConfidenceAnalyzer
from app.services.ocr.models import OCRResult, OCRPage

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self, engine_name: str = "easyocr"):
        self.engine_name = engine_name
        self.selector = EngineSelector()
        self.postprocessor = PostProcessor()
        self.analyzer = ConfidenceAnalyzer()

    def process(self, context: AnalysisContext) -> None:
        """Process preprocessed images in the context through OCR."""
        start_time = time.perf_counter()
        
        logger.info("OCR Phase started | job=%s | engine=%s", context.job_id, self.engine_name)
        
        try:
            engine = self.selector.get_engine(self.engine_name)
            engine.initialize()
            if not engine.is_available():
                raise RuntimeError("OCR model initialization did not produce an executable engine")
        except Exception as e:
            msg = f"Failed to load OCR engine {self.engine_name}: {str(e)}"
            logger.error(msg)
            context.add_warning(msg)
            context.ocr_result = None
            context.ocr_summary = {"status": "FAILED", "reason": "OCR engine initialization failed"}
            return

        pages: list[OCRPage] = []
        
        for idx, img_path in enumerate(context.preprocessed_images):
            try:
                # Load the preprocessed image
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning("Failed to read image for OCR: %s", img_path)
                    continue

                # 1. Extraction
                raw_page = engine.extract_words(img)
                raw_page.page_index = idx
                
                # 2. Post-processing
                cleaned_page = self.postprocessor.process(raw_page)
                pages.append(cleaned_page)
                
            except Exception as e:
                logger.error("OCR failed on page %d: %s", idx, str(e))
                context.add_warning(f"OCR failed on page {idx}: {str(e)}")
                
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        if not pages:
            context.ocr_result = None
            context.ocr_summary = {"status": "FAILED", "reason": "No page completed OCR extraction"}
            return
        
        # Merge all pages into a dummy multi-page representation for analyzer summary
        # If there are multiple pages, we flatten blocks temporarily to get full summary
        # Alternatively, we could analyze per page or sum them up. 
        # For simplicity, we just aggregate all blocks to get one OCRSummary.
        merged_blocks = []
        for p in pages:
            merged_blocks.extend(p.blocks)
            
        dummy_page = OCRPage(page_index=0, blocks=merged_blocks)
        summary = self.analyzer.analyze(dummy_page, engine_used=self.engine_name, processing_time_ms=processing_time_ms)

        result = OCRResult(pages=pages, summary=summary)
        
        # 3. Update Context
        from dataclasses import asdict
        
        context.ocr_result = asdict(result)
        context.ocr_summary = asdict(summary)
        context.ocr_summary['status'] = 'COMPLETED' if len(pages) == len(context.preprocessed_images) else 'PARTIAL'
        
        logger.info("OCR Phase completed | job=%s | duration=%.1fms", context.job_id, processing_time_ms)
