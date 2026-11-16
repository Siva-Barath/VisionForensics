"""
Confidence Estimator.

Estimates final confidence based on ambiguity among top predictions.
"""

from typing import List
from app.services.classification.models import DocumentPrediction

class ConfidenceEstimator:
    def estimate(self, top_predictions: List[DocumentPrediction]) -> float:
        """
        Adjusts the top prediction's confidence based on the margin 
        between the 1st and 2nd prediction.
        """
        if not top_predictions:
            return 0.0
            
        if len(top_predictions) == 1:
            return top_predictions[0].confidence
            
        p1 = top_predictions[0]
        p2 = top_predictions[1]
        
        # If the top prediction is e.g. 0.4 and the next is 0.35, it's very ambiguous.
        margin = p1.confidence - p2.confidence
        
        # Simple penalty for low margin
        if margin < 0.1:
            return max(0.0, p1.confidence - 0.2)
            
        return p1.confidence
