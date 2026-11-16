"""
OCR Visualizer Utility.

Draws bounding boxes and confidences onto the source image.
Useful for debugging and explainability.
"""

import cv2
import numpy as np

from app.services.ocr.models import OCRPage


class OCRVisualizer:
    def draw_boxes(self, image: np.ndarray, page: OCRPage, show_confidence: bool = True) -> np.ndarray:
        """
        Draw bounding boxes around detected words.
        Returns a new annotated image.
        """
        output_img = image.copy()
        
        # Color configuration (BGR format)
        box_color = (0, 255, 0)      # Green for standard boxes
        low_conf_color = (0, 0, 255) # Red for low confidence
        text_color = (255, 0, 0)     # Blue text
        
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    bbox = word.bounding_box
                    if not bbox.points:
                        continue
                        
                    # Format points for cv2.polylines
                    pts = np.array(bbox.points, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    
                    # Choose color based on confidence
                    color = low_conf_color if word.confidence < 0.6 else box_color
                    
                    cv2.polylines(output_img, [pts], isClosed=True, color=color, thickness=2)
                    
                    if show_confidence:
                        # Draw label above bounding box
                        label = f"{word.text} ({word.confidence:.2f})"
                        cv2.putText(
                            output_img, 
                            label, 
                            (bbox.xmin, max(0, bbox.ymin - 5)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.4, 
                            text_color, 
                            1
                        )
                        
        return output_img
