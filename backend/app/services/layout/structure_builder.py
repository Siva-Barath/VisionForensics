"""
Structure Builder.

Aggregates independent layout entities (paragraphs, fields, tables, headings)
into a cohesive StructuredDocument.
"""

from typing import List
from app.services.layout.models import (
    StructuredDocument, 
    StructuredSection, 
    StructuredField, 
    StructuredTable,
    DocumentType
)

class StructureBuilder:
    def build(
        self, 
        sections: List[StructuredSection], 
        fields: List[StructuredField], 
        tables: List[StructuredTable],
        document_type: DocumentType = DocumentType.UNKNOWN
    ) -> StructuredDocument:
        """
        Merge everything into a single structured representation.
        In the future, this would also handle hierarchical nesting (e.g. fields within sections).
        """
        return StructuredDocument(
            document_type=document_type,
            sections=sections,
            fields=fields,
            tables=tables,
            summary=None
        )
