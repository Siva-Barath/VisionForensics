import pytest
from app.services.ocr.models import OCRPage, OCRBlock, OCRLine, OCRWord, BoundingBox
from app.services.layout.models import (
    StructuredDocument, 
    StructuredSection, 
    StructuredField, 
    RegionType
)
from app.services.layout.reading_order import ReadingOrderResolver
from app.services.layout.block_grouper import BlockGrouper
from app.services.layout.field_extractor import FieldExtractor
from app.services.layout.table_detector import TableDetector
from app.services.layout.structure_builder import StructureBuilder
from app.services.layout.validator import LayoutValidator

def _make_dummy_word(text: str, x: int, y: int) -> OCRWord:
    bbox = BoundingBox(points=[[x, y], [x+10, y], [x+10, y+10], [x, y+10]])
    return OCRWord(text=text, confidence=0.9, bounding_box=bbox)

def _make_dummy_block(text: str, x: int, y: int) -> OCRBlock:
    word = _make_dummy_word(text, x, y)
    line = OCRLine(words=[word])
    return OCRBlock(lines=[line])

def test_reading_order_resolver():
    resolver = ReadingOrderResolver()
    
    b1 = _make_dummy_block("Second", 50, 100)
    b2 = _make_dummy_block("First", 50, 20)
    b3 = _make_dummy_block("Third", 50, 200)
    
    page = OCRPage(page_index=0, blocks=[b1, b2, b3])
    ordered = resolver.resolve(page)
    
    assert ordered.blocks[0].text == "First"
    assert ordered.blocks[1].text == "Second"
    assert ordered.blocks[2].text == "Third"

def test_block_grouper():
    grouper = BlockGrouper()
    b1 = _make_dummy_block("Title", 10, 10)
    page = OCRPage(page_index=0, blocks=[b1])
    
    sections = grouper.group(page)
    assert len(sections) == 1
    # Very short single line block is identified as TITLE
    assert sections[0].region_type == RegionType.TITLE

def test_field_extractor():
    extractor = FieldExtractor()
    s1 = StructuredSection(text="Name: John Doe")
    s2 = StructuredSection(text="DOB: 01/01/2000")
    
    fields = extractor.extract([s1, s2])
    
    assert len(fields) == 2
    assert fields[0].key == "Name"
    assert fields[0].value == "John Doe"
    assert fields[1].key == "DOB"
    assert fields[1].value == "01/01/2000"

def test_layout_validator():
    validator = LayoutValidator()
    
    f1 = StructuredField(key="Name", value="John Doe")
    f2 = StructuredField(key="Name", value="Jane Doe") # Duplicate key
    f3 = StructuredField(key="DOB", value=" ") # Empty value
    
    doc = StructuredDocument(fields=[f1, f2, f3])
    warnings = validator.validate(doc)
    
    assert len(warnings) == 2
    assert any("Duplicate" in w for w in warnings)
    assert any("Empty" in w for w in warnings)
