"""
Base Analyzer, Config, and Cache for Logo Verification Engine.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import cv2
import numpy as np
from dataclasses import dataclass

from app.pipeline.context import AnalysisContext
from app.services.forensics.models import Evidence
from .models import LogoFeatures

@dataclass
class LogoAnalyzerConfig:
    symmetry_tolerance: float = 0.8
    edge_jaggedness_threshold: float = 0.15
    resolution_minimum: float = 10.0
    context_margin_threshold: float = 0.05
    authenticity_threshold: float = 50.0

class LogoAnalysisCache:
    """Lazy-evaluation cache supporting multi-scale analysis."""
    def __init__(self, original_crop: np.ndarray):
        self.original = original_crop
        self._gray: dict[float, np.ndarray] = {}
        self._binary: dict[float, np.ndarray] = {}
        self._contours: dict[float, List[np.ndarray]] = {}
        self._edges: dict[float, np.ndarray] = {}
        
    def get_gray(self, scale: float) -> np.ndarray:
        if scale not in self._gray:
            if scale == 1.0:
                img = self.original
            else:
                w = int(self.original.shape[1] * scale)
                h = int(self.original.shape[0] * scale)
                img = cv2.resize(self.original, (w, h), interpolation=cv2.INTER_AREA)
                
            if len(img.shape) == 3:
                self._gray[scale] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                self._gray[scale] = img.copy()
        return self._gray[scale]

    def get_binary(self, scale: float) -> np.ndarray:
        if scale not in self._binary:
            gray = self.get_gray(scale)
            # Otsu's thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            border = np.concatenate((thresh[0], thresh[-1], thresh[:, 0], thresh[:, -1]))
            if np.count_nonzero(border) > border.size / 2:
                # Support light logos on dark backgrounds without treating the
                # surrounding rectangular background as the logo contour.
                thresh = cv2.bitwise_not(thresh)
            self._binary[scale] = thresh
        return self._binary[scale]

    def get_contours(self, scale: float) -> List[np.ndarray]:
        if scale not in self._contours:
            binary = self.get_binary(scale)
            cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self._contours[scale] = list(cnts)
        return self._contours[scale]
        
    def get_edges(self, scale: float) -> np.ndarray:
        if scale not in self._edges:
            gray = self.get_gray(scale)
            self._edges[scale] = cv2.Canny(gray, 100, 200)
        return self._edges[scale]

class BaseLogoAnalyzer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def analyze(
        self,
        cache: LogoAnalysisCache,
        features: LogoFeatures,
        context: AnalysisContext,
        config: LogoAnalyzerConfig,
        scale: float = 1.0
    ) -> List[Evidence]:
        pass
