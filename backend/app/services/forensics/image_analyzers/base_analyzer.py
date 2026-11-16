"""
Base Analyzer, Config, and Cache for Image Artifact Detection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import cv2
import numpy as np
from dataclasses import dataclass

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence

@dataclass
class ImageAnalyzerConfig:
    """Configurable thresholds for image analysis algorithms."""
    blur_threshold: float = 100.0
    noise_threshold_high: float = 50.0
    noise_threshold_low: float = 2.0
    ela_quality: int = 90
    ela_threshold: float = 30.0
    entropy_window: int = 9
    entropy_threshold: float = 2.0
    illumination_patch_size: int = 16
    illumination_std_threshold: float = 40.0
    edge_canny_lower: int = 100
    edge_canny_upper: int = 200

class ImageAnalysisCache:
    """
    Lazy-evaluation cache for shared image representations.
    Prevents redundant conversions (e.g. grayscale) across multiple analyzers.
    """
    def __init__(self, original_image: np.ndarray):
        self.original = original_image
        self._gray: Optional[np.ndarray] = None
        self._laplacian: Optional[np.ndarray] = None
        self._sobel_x: Optional[np.ndarray] = None
        self._sobel_y: Optional[np.ndarray] = None
        self._canny: Optional[np.ndarray] = None
        
    @property
    def gray(self) -> np.ndarray:
        if self._gray is None:
            if len(self.original.shape) == 3:
                self._gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
            else:
                self._gray = self.original.copy()
        return self._gray

    @property
    def laplacian(self) -> np.ndarray:
        if self._laplacian is None:
            self._laplacian = cv2.Laplacian(self.gray, cv2.CV_64F)
        return self._laplacian

    @property
    def sobel_x(self) -> np.ndarray:
        if self._sobel_x is None:
            self._sobel_x = cv2.Sobel(self.gray, cv2.CV_64F, 1, 0, ksize=3)
        return self._sobel_x

    @property
    def sobel_y(self) -> np.ndarray:
        if self._sobel_y is None:
            self._sobel_y = cv2.Sobel(self.gray, cv2.CV_64F, 0, 1, ksize=3)
        return self._sobel_y

    @property
    def canny(self) -> np.ndarray:
        if self._canny is None:
            self._canny = cv2.Canny(self.gray, 100, 200) # Basic default, could use config
        return self._canny

class BaseImageAnalyzer(ABC):
    """
    Abstract interface for internal image analyzers.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the analyzer."""
        pass
        
    @abstractmethod
    def analyze(
        self,
        image_index: int,
        cache: ImageAnalysisCache,
        context: AnalysisContext,
        config: ImageAnalyzerConfig
    ) -> List[Evidence]:
        """
        Evaluate the image (via cache) and return a list of Evidence objects.
        image_index allows linking evidence back to specific pages/images.
        """
        pass
