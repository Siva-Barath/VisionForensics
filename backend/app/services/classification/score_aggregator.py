"""
Score Aggregator.

Normalizes raw scores and ranks predictions.
"""

from typing import List
from app.services.classification.models import DocumentPrediction

class ScoreAggregator:
    def aggregate(self, predictions: List[DocumentPrediction]) -> List[DocumentPrediction]:
        if not predictions:
            return []
            
        # Sort descending by raw score
        sorted_preds = sorted(predictions, key=lambda p: p.confidence, reverse=True)
        
        # Normalize scores to 0.0 - 1.0 (softmax or simple proportion)
        total_score = sum(p.confidence for p in sorted_preds)
        
        for p in sorted_preds:
            if total_score > 0:
                p.confidence = p.confidence / total_score
            else:
                p.confidence = 0.0
                
        # Return Top-3
        return sorted_preds[:3]
