"""
PerspectiveCorrectionOperation - Phase 3. Will correct perspective distortion.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from app.services.preprocessing.operations.base_operation import BaseOperation

if TYPE_CHECKING:
    from app.pipeline.context import AnalysisContext


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order points: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    
    # Sum of coordinates: smallest is top-left, largest is bottom-right
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Difference of coordinates: smallest is top-right, largest is bottom-left
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect


class PerspectiveCorrectionOperation(BaseOperation):
    """
    Transforms perspective-distorted document images into a top-down rectangular view.
    Uses contour detection to find the document boundaries and applies a perspective warp.
    """
    
    name = "perspective"
    description = "Corrects perspective distortion in document images."
    version = "1.0.0"

    def execute(self, image: np.ndarray, context: "AnalysisContext", **kwargs: Any) -> np.ndarray:
        start_time = time.perf_counter()
        
        self._logger.info("PerspectiveCorrectionOperation started | job=%s", context.job_id)

        # Do not modify in-place
        working_img = image.copy()
        
        # Ensure context.metadata exists
        if context.metadata is None:
            context.metadata = {}

        def _skip(reason: str, found: bool = False, area: float = 0.0) -> np.ndarray:
            self._logger.warning("Perspective correction skipped: %s | job=%s", reason, context.job_id)
            context.metadata.update({
                "perspective_applied": False,
                "document_found": found,
                "contour_area": area,
                "processing_time_ms": (time.perf_counter() - start_time) * 1000
            })
            return image.copy()

        # 1. Grayscale
        if len(working_img.shape) == 3:
            gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = working_img.copy()
            
        # 2. Gaussian Blur to reduce high frequency noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # 4. Detect contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return _skip("no contours found")
            
        # 5. Largest contour representing the document
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        doc_contour = contours[0]
        contour_area = float(cv2.contourArea(doc_contour))
        
        img_area = image.shape[0] * image.shape[1]
        
        # Validate that the contour area is reasonable (e.g. >= 10% of image area)
        if contour_area < 0.1 * img_area:
            return _skip("largest contour too small", found=False, area=contour_area)

        # 6. Approximate the contour
        peri = cv2.arcLength(doc_contour, True)
        approx = cv2.approxPolyDP(doc_contour, 0.02 * peri, True)
        
        # 7. Validate that four document corners are found
        if len(approx) != 4:
            return _skip(f"found {len(approx)} corners instead of 4", found=True, area=contour_area)
            
        self._logger.info("Document contour detected | area=%f | job=%s", contour_area, context.job_id)
        
        # 8. Order the four corner points
        pts = approx.reshape(4, 2)
        rect = _order_points(pts)
        (tl, tr, br, bl) = rect
        
        # 9. Compute the destination rectangle
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        if maxWidth <= 0 or maxHeight <= 0:
            return _skip("invalid destination dimensions", found=True, area=contour_area)

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # 10. Get perspective transform matrix
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # 11. Warp the image
        warped = cv2.warpPerspective(working_img, M, (maxWidth, maxHeight))
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        context.metadata.update({
            "perspective_applied": True,
            "document_found": True,
            "contour_area": contour_area,
            "transform_matrix": M.tolist(),
            "processing_time_ms": processing_time
        })
        
        self._logger.info("Perspective correction applied successfully | duration=%.1fms | job=%s", 
                          processing_time, context.job_id)
        
        return warped
