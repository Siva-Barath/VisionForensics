"""
Image Feature Extractor.

Analyzes lightweight visual features from the images.
"""
import cv2
from app.pipeline.context import AnalysisContext
from app.services.classification.models import ExtractedFeatures

class ImageFeatureExtractor:
    def extract(self, context: AnalysisContext, features: ExtractedFeatures) -> None:
        # Number of pages
        features.page_count = context.page_count or len(context.preprocessed_images)
        
        # Determine aspect ratio of first page
        if context.preprocessed_images:
            try:
                img = cv2.imread(context.preprocessed_images[0])
                if img is not None:
                    h, w = img.shape[:2]
                    if h > 0:
                        features.aspect_ratio = float(w) / float(h)
            except Exception:
                pass
