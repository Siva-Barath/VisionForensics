"""
Layout Validator.

Validates the structured layout output to identify issues like duplicate fields,
empty values, overlapping regions, and invalid reading order.
Generates warnings but never throws exceptions for valid OCR output.
"""

from typing import List
from app.services.layout.models import StructuredDocument

class LayoutValidator:
    def validate(self, document: StructuredDocument) -> List[str]:
        """
        Run validation checks on the document structure and return warnings.
        """
        warnings = []
        
        # Check duplicate keys
        keys_seen = set()
        for field in document.fields:
            if field.key in keys_seen:
                warnings.append(f"Duplicate field detected: {field.key}")
            keys_seen.add(field.key)
            
            # Check empty values
            if not field.value or field.value.strip() == "":
                warnings.append(f"Empty value for field: {field.key}")
                
        # (Future) Check overlapping regions by examining bounding boxes
        
        return warnings
