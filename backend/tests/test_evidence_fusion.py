"""Unvalidated legacy fusion must never substitute an operational verdict."""
import pytest
from app.services.forensics.models import Evidence, EvidenceCategory
from app.services.evidence_fusion.config import EvidenceFusionConfig, SensitivityProfile
from app.services.evidence_fusion.fusion_service import EvidenceFusionService
from app.pipeline.context import AnalysisContext


@pytest.mark.parametrize('category,severity,profile', [
    (EvidenceCategory.LOGO, 10, SensitivityProfile.BALANCED),
    (EvidenceCategory.COPY_MOVE, 95, SensitivityProfile.STRICT),
    (EvidenceCategory.IMAGE, 90, SensitivityProfile.PERMISSIVE),
])
def test_unvalidated_fusion_never_produces_an_operational_verdict(category, severity, profile):
    evidence = Evidence(detector='controlled', category=category, severity=severity, description='Controlled fixture')
    with pytest.raises(NotImplementedError, match='not registered'):
        EvidenceFusionService(EvidenceFusionConfig(profile=profile)).fuse([evidence], AnalysisContext())
