"""
Base Analyzer, Config, and Cache for Signature Verification.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import cv2
import numpy as np
from dataclasses import dataclass

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .models import SignatureFeatures

@dataclass
class SignatureAnalyzerConfig:
    """Configurable thresholds for signature analysis algorithms."""
    stroke_uniformity_threshold: float = 0.5
    contour_complexity_threshold: float = 10.0
    ink_density_high: float = 0.8
    ink_density_low: float = 0.05
    fragmentation_threshold: int = 50
    solidity_threshold: float = 0.95
    complexity_threshold: float = 10.0

class SignatureAnalysisCache:
    """
    Lazy-evaluation cache for shared signature representations.
    Utilizes preprocessed_images if available to avoid redundant denoising.
    """
    def __init__(self, original_crop: np.ndarray):
        self.original = original_crop
        self._gray: Optional[np.ndarray] = None
        self._binary: Optional[np.ndarray] = None
        self._skeleton: Optional[np.ndarray] = None
        self._contours: Optional[List[np.ndarray]] = None
        self._connected_components: Optional[tuple] = None
        
    @property
    def gray(self) -> np.ndarray:
        if self._gray is None:
            if len(self.original.shape) == 3:
                self._gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
            else:
                self._gray = self.original.copy()
        return self._gray

    @property
    def binary(self) -> np.ndarray:
        if self._binary is None:
            # Otsu's thresholding. Invert so ink is white (255) and bg is black (0)
            _, thresh = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            self._binary = thresh
        return self._binary

    @property
    def skeleton(self) -> np.ndarray:
        if self._skeleton is None:
            # Morphological thinning
            self._skeleton = cv2.ximgproc.thinning(self.binary)
        return self._skeleton

    @property
    def contours(self) -> List[np.ndarray]:
        if self._contours is None:
            cnts, _ = cv2.findContours(self.binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self._contours = list(cnts)
        return self._contours
        
    @property
    def connected_components(self) -> tuple:
        if self._connected_components is None:
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(self.binary, connectivity=8)
            self._connected_components = (num_labels, labels, stats, centroids)
        return self._connected_components

class BaseSignatureAnalyzer(ABC):
    """
    Abstract interface for internal signature analyzers.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the analyzer."""
        pass
        
    @abstractmethod
    def analyze(
        self,
        cache: SignatureAnalysisCache,
        features: SignatureFeatures,
        context: AnalysisContext,
        config: SignatureAnalyzerConfig
    ) -> List[Evidence]:
        """
        Evaluate the signature (via cache), populate `features`, and return a list of Evidence objects.
        """
        pass
