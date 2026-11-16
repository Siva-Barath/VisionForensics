"""
Base Analyzer, Config, and Cache for Copy-Move Detection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import cv2
import numpy as np
from dataclasses import dataclass

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .models import CopyMoveFeatures

@dataclass
class CopyMoveAnalyzerConfig:
    """Configurable thresholds for copy-move algorithms."""
    ratio_test_threshold: float = 0.75
    minimum_match_count: int = 10
    ransac_threshold: float = 5.0
    overlap_iou_threshold: float = 0.3
    cluster_distance: float = 50.0
    block_size: int = 16
    confidence_threshold: float = 0.7

class CopyMoveAnalysisCache:
    """
    Lazy-evaluation cache for multi-scale copy-move representations.
    """
    def __init__(self, original_image: np.ndarray):
        self.original = original_image
        self._gray: Optional[np.ndarray] = None
        self._pyramid: dict[float, np.ndarray] = {}
        
        self._orb_data: dict[float, tuple] = {}
        self._akaze_data: dict[float, tuple] = {}

    @property
    def gray(self) -> np.ndarray:
        if self._gray is None:
            if len(self.original.shape) == 3:
                self._gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
            else:
                self._gray = self.original.copy()
        return self._gray

    def get_scale(self, scale: float) -> np.ndarray:
        if scale == 1.0:
            return self.gray
            
        if scale not in self._pyramid:
            width = int(self.gray.shape[1] * scale)
            height = int(self.gray.shape[0] * scale)
            dim = (width, height)
            self._pyramid[scale] = cv2.resize(self.gray, dim, interpolation=cv2.INTER_AREA)
            
        return self._pyramid[scale]
        
    def get_orb(self, scale: float) -> tuple:
        """Returns (keypoints, descriptors)"""
        if scale not in self._orb_data:
            orb = cv2.ORB_create(nfeatures=2000)
            img = self.get_scale(scale)
            kps, descs = orb.detectAndCompute(img, None)
            self._orb_data[scale] = (kps, descs)
        return self._orb_data[scale]
        
    def get_akaze(self, scale: float) -> tuple:
        if scale not in self._akaze_data:
            akaze = cv2.AKAZE_create()
            img = self.get_scale(scale)
            kps, descs = akaze.detectAndCompute(img, None)
            self._akaze_data[scale] = (kps, descs)
        return self._akaze_data[scale]

class BaseCopyMoveAnalyzer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def analyze(
        self,
        cache: CopyMoveAnalysisCache,
        features: CopyMoveFeatures,
        context: AnalysisContext,
        config: CopyMoveAnalyzerConfig,
        scale: float = 1.0
    ) -> List[Evidence]:
        pass
