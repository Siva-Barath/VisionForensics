"""
OCR PostProcessor.

Handles standardization of OCR output strings, unicode normalization,
whitespace cleanup, and structural ordering.
"""

import unicodedata
import re
from typing import List

from app.services.ocr.models import OCRPage, OCRBlock, OCRLine, OCRWord


class PostProcessor:
    def process(self, page: OCRPage) -> OCRPage:
        """Clean and normalize the text within an OCRPage."""
        new_blocks = []
        for block in page.blocks:
            cleaned_block = self._process_block(block)
            if cleaned_block.lines:  # Only keep blocks that still have content
                new_blocks.append(cleaned_block)
                
        # Sort blocks vertically based on ymin
        new_blocks.sort(key=self._get_block_ymin)
        
        return OCRPage(page_index=page.page_index, blocks=new_blocks)

    def _process_block(self, block: OCRBlock) -> OCRBlock:
        new_lines = []
        for line in block.lines:
            cleaned_line = self._process_line(line)
            if cleaned_line.words:
                new_lines.append(cleaned_line)
        return OCRBlock(lines=new_lines)

    def _process_line(self, line: OCRLine) -> OCRLine:
        new_words = []
        for word in line.words:
            cleaned_text = self.normalize_text(word.text)
            if cleaned_text:
                new_words.append(OCRWord(
                    text=cleaned_text,
                    confidence=word.confidence,
                    bounding_box=word.bounding_box
                ))
        return OCRLine(words=new_words)

    def normalize_text(self, text: str) -> str:
        """Normalize unicode, strip excessive whitespace."""
        if not text:
            return ""
        # Normalize unicode to compose characters
        text = unicodedata.normalize('NFKC', text)
        # Remove zero-width separators/BOM, while retaining meaningful joiners
        # used by scripts such as Devanagari.
        text = text.replace('\u200b', '').replace('\ufeff', '')
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def _get_block_ymin(self, block: OCRBlock) -> float:
        """Get the minimum y-coordinate of a block for sorting."""
        if not block.lines: return 0
        
        min_y = float('inf')
        for line in block.lines:
            for word in line.words:
                min_y = min(min_y, word.bounding_box.ymin)
                
        return min_y if min_y != float('inf') else 0
