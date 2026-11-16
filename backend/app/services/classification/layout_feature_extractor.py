"""
Layout Feature Extractor.

Evaluates the StructuredDocument for layout signals.
"""

from app.pipeline.context import AnalysisContext
from app.services.classification.models import ExtractedFeatures

class LayoutFeatureExtractor:
    def extract(self, context: AnalysisContext, features: ExtractedFeatures) -> None:
        doc = context.structured_document
        
        if not doc:
            return
            
        # Count structural elements
        features.table_count = len(doc.get("tables", []))
        features.field_count = len(doc.get("fields", []))
        features.section_count = len(doc.get("sections", []))
        
        # Look for specific region types
        sig_count = 0
        logo_count = 0
        
        for sec in doc.get("sections", []):
            rt = sec.get("region_type")
            if rt == "SIGNATURE":
                sig_count += 1
            elif rt == "LOGO":
                logo_count += 1
                
        features.signature_regions = sig_count
        features.logo_regions = logo_count
