"""
Signature Region Validator.

Ensures the cropped region is suitable for mathematical analysis before wasting CPU cycles.
"""
import numpy as np

class SignatureValidator:
    def __init__(self, min_width=20, min_height=10, min_foreground_pixels=50):
        self.min_width = min_width
        self.min_height = min_height
        self.min_foreground_pixels = min_foreground_pixels

    def validate(self, cropped_image: np.ndarray) -> tuple[bool, str]:
        """Returns (is_valid, warning_message)."""
        if cropped_image is None or cropped_image.size == 0:
            return False, "Empty signature crop."
            
        h, w = cropped_image.shape[:2]
        
        if w < self.min_width or h < self.min_height:
            return False, f"Signature crop too small ({w}x{h})."
            
        # Basic check for completely blank patches
        # For simplicity in validation, we just do a quick intensity check without full binarization yet
        if len(cropped_image.shape) == 3:
            import cv2
            gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cropped_image
            
        # Very simple foreground check (pixels not perfectly white)
        foreground_pixels = np.count_nonzero(gray < 250)
        
        if foreground_pixels < self.min_foreground_pixels:
            return False, f"Signature crop has insufficient ink ({foreground_pixels} pixels)."
            
        return True, ""
