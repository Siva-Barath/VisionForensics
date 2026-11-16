"""
Logo Region Validator.
"""
import numpy as np

class LogoValidator:
    def __init__(self, min_width=20, min_height=20):
        self.min_width = min_width
        self.min_height = min_height

    def validate(self, cropped_image: np.ndarray) -> tuple[bool, str]:
        if cropped_image is None or cropped_image.size == 0:
            return False, "Empty logo crop."
            
        h, w = cropped_image.shape[:2]
        
        if w < self.min_width or h < self.min_height:
            return False, f"Logo crop too small ({w}x{h})."
            
        return True, ""
