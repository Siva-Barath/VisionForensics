"""
Field Extractor.

Rule-based framework for identifying key-value pairs (e.g., Name, DOB, CGPA).
Matches patterns in structured sections to extract structured data fields.
"""

import re

from app.services.layout.models import StructuredSection, StructuredField

class FieldExtractor:
    def __init__(self):
        # A simple registry of regex patterns for generic field extraction
        # e.g. "Name: John Doe", "DOB: 01/01/2000"
        self.patterns = [
            (r"(?i)^(Name)\s*[:\-]?\s*(.+)$", "Name"),
            (r"(?i)^(DOB|Date of Birth)\s*[:\-]?\s*(.+)$", "DOB"),
            (r"(?i)^(CGPA|GPA)\s*[:\-]?\s*(.+)$", "CGPA"),
        ]

    def extract(self, sections: list[StructuredSection]) -> list[StructuredField]:
        """Extract fields from a list of text sections."""
        fields = []
        
        for section in sections:
            # We process line by line to find key-value structures
            for line_text in section.text.split('\n'):
                line_text = line_text.strip()
                if not line_text:
                    continue
                    
                for pattern, key_override in self.patterns:
                    match = re.search(pattern, line_text)
                    if match:
                        key_raw = match.group(1).strip()
                        value_raw = match.group(2).strip()
                        key_name = key_override or key_raw
                        
                        fields.append(StructuredField(
                            key=key_name,
                            value=value_raw,
                            # Bounding boxes could be extracted by locating 
                            # the corresponding words in the section.words list
                            key_bbox=section.bounding_box,
                            value_bbox=section.bounding_box,
                            confidence=1.0
                        ))
                        break # Only one pattern should match a line
                        
        return fields
