"""
Reading Order Resolver.

Sorts OCR blocks into their natural reading order (typically top-to-bottom, 
left-to-right), with support for identifying simple multi-column layouts.
"""

from app.services.ocr.models import OCRPage, OCRBlock

class ReadingOrderResolver:
    def resolve(self, page: OCRPage) -> OCRPage:
        """
        Sort blocks in natural reading order.
        For a simplistic baseline, we sort by y-coordinate, then x-coordinate.
        In a robust implementation, this would detect columns and reading flow.
        """
        sorted_blocks = sorted(page.blocks, key=self._get_sort_key)
        
        # Return a new page instance with the sorted blocks to maintain immutability
        return OCRPage(page_index=page.page_index, blocks=sorted_blocks)
        
    def _get_sort_key(self, block: OCRBlock) -> tuple[float, float]:
        """
        Returns a (y_bucket, x) tuple. We round Y to nearest 10-20 pixels
        to group inline elements on the same row.
        """
        if not block.lines or not block.lines[0].words:
            return (0.0, 0.0)
            
        first_word = block.lines[0].words[0]
        y = first_word.bounding_box.ymin
        x = first_word.bounding_box.xmin
        
        y_bucket = round(y / 15.0) * 15.0
        return (y_bucket, x)
