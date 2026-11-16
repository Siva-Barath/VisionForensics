"""
Layout Service.

Central orchestrator for the Document Layout Analysis Framework.
Coordinates Reading Order, Grouping, Table Detection, Field Extraction,
Structure Building, and Validation.
"""

import time
import logging
from typing import Optional

from app.pipeline.context import AnalysisContext
from app.services.ocr.models import OCRResult, OCRPage
from app.services.layout.models import LayoutSummary, StructuredDocument
from app.services.layout.reading_order import ReadingOrderResolver
from app.services.layout.block_grouper import BlockGrouper
from app.services.layout.field_extractor import FieldExtractor
from app.services.layout.table_detector import TableDetector
from app.services.layout.structure_builder import StructureBuilder
from app.services.layout.validator import LayoutValidator

logger = logging.getLogger(__name__)

class LayoutService:
    def __init__(self):
        self.reading_order = ReadingOrderResolver()
        self.block_grouper = BlockGrouper()
        self.field_extractor = FieldExtractor()
        self.table_detector = TableDetector()
        self.structure_builder = StructureBuilder()
        self.validator = LayoutValidator()

    def process(self, context: AnalysisContext) -> None:
        """Process OCR results and build a structured document."""
        start_time = time.perf_counter()
        
        logger.info("Layout Analysis started | job=%s", context.job_id)
        
        if not context.ocr_result:
            msg = "No OCR result found to analyze layout."
            logger.warning(msg)
            context.add_warning(msg)
            return
            
        try:
            # For this simple prototype, we operate mostly on the first page,
            # or merge them. Let's merge them sequentially.
            all_sections = []
            all_tables = []
            
            # Since OCRResult is stored as dict in context, we parse it back
            # or treat it as is. In our framework, `OCRResult` was converted to dict.
            # To be robust, let's assume we can re-construct or we mock it.
            # Let's reconstruct for typing.
            ocr_dict = context.ocr_result
            pages_data = ocr_dict.get("pages", [])
            
            from app.services.ocr.models import OCRBlock, OCRLine, OCRWord, BoundingBox
            
            for page_data in pages_data:
                # Reconstruct OCRPage
                blocks = []
                for b_data in page_data.get("blocks", []):
                    lines = []
                    for l_data in b_data.get("lines", []):
                        words = []
                        for w_data in l_data.get("words", []):
                            bb_data = w_data.get("bounding_box", {})
                            bbox = BoundingBox(points=bb_data.get("points", []))
                            words.append(OCRWord(
                                text=w_data.get("text", ""),
                                confidence=w_data.get("confidence", 1.0),
                                bounding_box=bbox
                            ))
                        lines.append(OCRLine(words=words))
                    blocks.append(OCRBlock(lines=lines))
                
                page = OCRPage(page_index=page_data.get("page_index", 0), blocks=blocks)
                
                # 1. Reading Order
                ordered_page = self.reading_order.resolve(page)
                
                # 2. Grouping
                sections = self.block_grouper.group(ordered_page)
                all_sections.extend(sections)
                logger.debug("Grouping completed for page %d | sections=%d", page.page_index, len(sections))
                
                # 3. Table Detection
                tables = self.table_detector.detect(ordered_page)
                all_tables.extend(tables)

            # 4. Field Extraction
            fields = self.field_extractor.extract(all_sections)
            logger.debug("Field extraction completed | fields=%d", len(fields))
            
            # 5. Build Structure
            document = self.structure_builder.build(
                sections=all_sections,
                fields=fields,
                tables=all_tables
            )
            
            # 6. Validate
            warnings = self.validator.validate(document)
            for w in warnings:
                context.add_warning(f"Layout Validator: {w}")
            logger.debug("Validation completed | warnings=%d", len(warnings))
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            summary = LayoutSummary(
                total_sections=len(all_sections),
                total_fields=len(fields),
                total_tables=len(all_tables),
                warnings=warnings,
                processing_time_ms=processing_time
            )
            document.summary = summary
            
            # Update Context
            from dataclasses import asdict
            context.structured_document = asdict(document)
            context.layout_summary = asdict(summary)
            
            logger.info("Layout Analysis completed | job=%s | duration=%.1fms", context.job_id, processing_time)

        except Exception as e:
            msg = f"Layout analysis failed: {str(e)}"
            logger.error(msg)
            context.add_warning(msg)
