"""
models.py — Data structures and Pydantic schemas for the ML Inference Service.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class RiskTier(str, Enum):
    LOW_RISK = "LOW_RISK"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    UNKNOWN = "UNKNOWN"

class InferenceStatus(str, Enum):
    SUCCESS = "SUCCESS"
    DEGRADED = "DEGRADED"
    ML_UNAVAILABLE = "ML_UNAVAILABLE"

class ForensicLimitationNotice(BaseModel):
    code: str
    severity: str  # INFO | WARNING | CRITICAL
    message: str

class MLPredictionResult(BaseModel):
    status: InferenceStatus = Field(..., description="Inference execution status")
    predicted_class: Optional[str] = Field(None, description="AUTHENTIC or FORGED at operational threshold")
    forgery_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Frozen model class-1 screening score; not a document-wide authenticity probability")
    operational_threshold: float = Field(0.40, description="Active decision threshold applied for predicted_class")
    alternative_threshold: float = Field(0.50, description="Configurable alternative decision threshold")
    predicted_class_alt: Optional[str] = Field(None, description="Predicted class at alternative threshold (T=0.50)")
    risk_tier: RiskTier = Field(RiskTier.UNKNOWN, description="Operational three-tier screening risk classification")
    risk_description: str = Field("", description="Authoritative description of the risk classification")
    model_name: str = Field("RandomForestClassifier", description="Underlying model algorithm")
    model_version: str = Field("1.0.0-rf-midv500-18feat", description="Serialized model artifact version")
    feature_completeness: float = Field(1.0, ge=0.0, le=1.0, description="Proportion of the 18 active features available")
    feature_vector: Dict[str, Optional[float]] = Field(default_factory=dict, description="Active 18 forensic features supplied")
    imputed_features: Dict[str, float] = Field(default_factory=dict, description="Explicit record of any imputed features")
    top_contributing_features: Dict[str, float] = Field(default_factory=dict, description="Top features driving the prediction")
    warnings: List[str] = Field(default_factory=list, description="Feature extraction or inference warnings")
    limitations: List[ForensicLimitationNotice] = Field(default_factory=list, description="Forensic decision support disclaimers")
    inference_duration_ms: float = Field(0.0, description="Inference execution latency in milliseconds")
