"""
Base class for all forgery detectors.
"""

from abc import ABC, abstractmethod
from typing import List
from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence

class BaseDetector(ABC):
    """
    Abstract interface for a forgery detector.
    Every detector runs independently and yields a list of Evidence objects.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the detector (e.g., 'metadata_detector')."""
        pass
        
    @abstractmethod
    def detect(self, context: AnalysisContext) -> List[Evidence]:
        """
        Analyze the AnalysisContext (which holds preprocessed images, OCR results, 
        StructuredDocument, etc.) and return detected Evidence.
        """
        pass
