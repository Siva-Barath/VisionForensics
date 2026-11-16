"""
Document Profile Registry for the Classification Engine.

Defines the expected traits and rules for each DocumentType and manages 
their evaluation against extracted features.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from app.services.layout.models import DocumentType
from app.services.classification.models import ExtractedFeatures, ClassificationEvidence

logger = logging.getLogger(__name__)

class BaseDocumentProfile(ABC):
    @property
    @abstractmethod
    def document_type(self) -> DocumentType:
        pass

    @abstractmethod
    def evaluate(self, features: ExtractedFeatures) -> Tuple[float, List[ClassificationEvidence]]:
        """
        Evaluate extracted features and return a raw score along with the 
        evidence explaining the score.
        """
        pass

class MarksheetProfile(BaseDocumentProfile):
    @property
    def document_type(self) -> DocumentType:
        return DocumentType.MARKSHEET

    def evaluate(self, features: ExtractedFeatures) -> Tuple[float, List[ClassificationEvidence]]:
        score = 0.0
        evidence = []
        
        expected_keywords = ["cgpa", "semester", "credits", "grade", "roll number", "university"]
        for kw in expected_keywords:
            if kw in features.ocr_text_lower:
                score += 15.0
                evidence.append(ClassificationEvidence(f"Keyword: {kw}", 15.0, f"Found expected marksheet keyword: '{kw}'"))
                
        if features.table_count > 0:
            score += 20.0
            evidence.append(ClassificationEvidence("Tables", 20.0, f"Detected {features.table_count} tables (common in marksheets)"))
            
        return score, evidence

class PassportProfile(BaseDocumentProfile):
    @property
    def document_type(self) -> DocumentType:
        return DocumentType.PASSPORT

    def evaluate(self, features: ExtractedFeatures) -> Tuple[float, List[ClassificationEvidence]]:
        score = 0.0
        evidence = []
        
        expected_keywords = ["passport", "nationality", "date of birth", "surname", "given names", "sex"]
        for kw in expected_keywords:
            if kw in features.ocr_text_lower:
                score += 20.0
                evidence.append(ClassificationEvidence(f"Keyword: {kw}", 20.0, f"Found passport keyword: '{kw}'"))
                
        # Look for MRZ indicators (many <<<<)
        if "<<" in features.ocr_text_lower:
            score += 40.0
            evidence.append(ClassificationEvidence("MRZ", 40.0, "Detected Machine Readable Zone (MRZ) patterns"))
            
        if features.aspect_ratio > 1.2: # Passports are often landscape when scanned open
            score += 10.0
            evidence.append(ClassificationEvidence("Aspect Ratio", 10.0, "Landscape aspect ratio matches open passport"))
            
        return score, evidence

class InvoiceProfile(BaseDocumentProfile):
    @property
    def document_type(self) -> DocumentType:
        return DocumentType.INVOICE

    def evaluate(self, features: ExtractedFeatures) -> Tuple[float, List[ClassificationEvidence]]:
        score = 0.0
        evidence = []
        
        expected_keywords = ["invoice", "gst", "tax", "amount", "total", "bill to", "vendor"]
        for kw in expected_keywords:
            if kw in features.ocr_text_lower:
                score += 15.0
                evidence.append(ClassificationEvidence(f"Keyword: {kw}", 15.0, f"Found invoice keyword: '{kw}'"))
                
        if features.table_count > 0:
            score += 15.0
            evidence.append(ClassificationEvidence("Tables", 15.0, "Tables present (likely line items)"))
            
        return score, evidence

class DocumentProfileRegistry:
    def __init__(self):
        self._profiles: Dict[DocumentType, BaseDocumentProfile] = {}
        # Pre-register default profiles
        self.register(MarksheetProfile())
        self.register(PassportProfile())
        self.register(InvoiceProfile())

    def register(self, profile: BaseDocumentProfile) -> None:
        self._profiles[profile.document_type] = profile
        logger.debug("Registered classification profile for: %s", profile.document_type.value)

    def get_all(self) -> List[BaseDocumentProfile]:
        return list(self._profiles.values())
