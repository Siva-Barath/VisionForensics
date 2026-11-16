"""
FeatureVector — typed container for one extracted feature row.

Carries the feature dict alongside provenance metadata so DatasetBuilder
can write both to CSV without coupling to AnalysisContext.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FeatureVector:
    document_id: str
    original_filename: str
    file_type: str
    # Ordered feature values keyed by FEATURE_NAMES from FeatureRegistry.
    # Missing features are stored as None and written as empty string in CSV.
    features: dict[str, float | None] = field(default_factory=dict)
    # Ground-truth label supplied externally (e.g. "forged" / "authentic").
    # None when label is unknown.
    label: str | None = None
    auxiliary_features: dict[str, float | None] = field(default_factory=dict)

    def __post_init__(self):
        # Keep the registry's export contract while retaining supplementary
        # diagnostics. The separate frozen 18-feature schema is untouched.
        from app.ml.feature_registry import FEATURE_NAMES
        self.auxiliary_features.update({key: value for key, value in self.features.items() if key not in FEATURE_NAMES})
        self.features = {name: self.features.get(name) for name in FEATURE_NAMES}

    def to_row(self, feature_names: list[str]) -> dict:
        """Return an ordered flat dict suitable for csv.DictWriter."""
        row: dict = {
            "document_id": self.document_id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "label": self.label if self.label is not None else "",
        }
        for name in feature_names:
            v = self.features.get(name)
            row[name] = "" if v is None else v
        return row
