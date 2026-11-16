"""
Rule Classifier.

Iterates through registered profiles and generates evidence based on features.
"""

from typing import List, Tuple
from app.services.classification.models import ExtractedFeatures, DocumentPrediction
from app.services.classification.profile_registry import DocumentProfileRegistry

class RuleClassifier:
    def __init__(self, registry: DocumentProfileRegistry):
        self.registry = registry

    def classify(self, features: ExtractedFeatures) -> List[DocumentPrediction]:
        predictions = []
        
        for profile in self.registry.get_all():
            score, evidence = profile.evaluate(features)
            
            # We temporarily store raw score in confidence. Aggregator will normalize it.
            pred = DocumentPrediction(
                document_type=profile.document_type,
                confidence=score, 
                evidence=evidence
            )
            predictions.append(pred)
            
        return predictions
