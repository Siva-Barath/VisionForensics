"""
Error Level Analysis (ELA) Analyzer.

Performs JPEG Error Level Analysis in memory to detect splicing or multiple
compression cycles in local regions.
"""

from typing import List
import numpy as np
import cv2

from app.pipeline.context import AnalysisContext
from app.pipeline.artifact import Artifact
from app.services.forensics.models import Evidence, EvidenceCategory, EvidenceSource, EvidenceRegion
from app.services.ocr.models import BoundingBox
from .base_analyzer import BaseImageAnalyzer, ImageAnalysisCache, ImageAnalyzerConfig

class ELAAnalyzer(BaseImageAnalyzer):
    @property
    def name(self) -> str:
        return "ela_analyzer"

    def analyze(
        self,
        image_index: int,
        cache: ImageAnalysisCache,
        context: AnalysisContext,
        config: ImageAnalyzerConfig
    ) -> List[Evidence]:
        evidence = []
        
        # 1. Recompress in memory at specified quality
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), config.ela_quality]
        result, encimg = cv2.imencode('.jpg', cache.original, encode_param)
        if not result:
            return evidence
            
        decimg = cv2.imdecode(encimg, 1)
        
        # 2. Compute absolute difference
        diff = cv2.absdiff(cache.original, decimg)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # 3. Normalize (scale max diff to 255)
        max_diff = np.max(diff_gray)
        if max_diff > 0:
            scale = 255.0 / max_diff
            ela_image = cv2.convertScaleAbs(diff_gray, alpha=scale)
        else:
            ela_image = diff_gray
            
        # 4. Detect anomalous regions (areas with much higher ELA response than surrounding)
        # Simple thresholding for now
        _, thresh = cv2.threshold(ela_image, int(config.ela_threshold * 255 / 100), 255, cv2.THRESH_BINARY)
        
        # Find contours of high ELA difference
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < (ela_image.shape[0] * ela_image.shape[1] * 0.5): # filter tiny noise and huge blocks
                x, y, w, h = cv2.boundingRect(cnt)
                regions.append(EvidenceRegion(
                    bounding_box=BoundingBox(points=[[x,y], [x+w, y], [x+w, y+h], [x, y+h]]),
                    description=f"High ELA difference area ({area} px)",
                    page_index=image_index
                ))
                
        if regions:
            # Consolidate into one Evidence object
            evidence.append(Evidence(
                detector=self.name,
                category=EvidenceCategory.IMAGE,
                severity=85.0,
                description=f"Found {len(regions)} suspicious regions with high ELA variance on Page {image_index+1}.",
                source=EvidenceSource.IMAGE,
                recommendation="Investigate for splicing or copy-move forgery.",
                regions=regions,
                page_index=image_index
            ))
            
            # (Optional) Store heatmap artifact if needed via context (would require passing paths)
            
        return evidence
