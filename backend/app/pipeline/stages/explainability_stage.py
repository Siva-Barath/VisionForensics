"""
Explainability Stage — Synthesizes human-readable, plain-language forensic findings
for non-technical investigators and legal stakeholders.
"""

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult


class ExplainabilityStage(BaseStage):
    name = "explainability"

    async def run(self, context: AnalysisContext) -> StageResult:
        # Synthesize plain-language explanation from multi-track findings
        ml_pred = context.ml_prediction or {}
        risk_tier = (context.risk_assessment or {}).get("unified_risk_tier", "UNKNOWN")
        risk_desc = (context.risk_assessment or {}).get("risk_description", "")
        is_mixed = (context.risk_assessment or {}).get("is_mixed_evidence", False) or "mixed" in risk_desc.lower()
        regions = context.detected_regions or []

        findings = []
        if risk_tier == "HIGH_RISK":
            if is_mixed:
                findings.append("ML screening threshold exceeded. Supporting forensic evidence is mixed.")
                findings.append("Statistical substrate screening flagged potential manipulation, but independent visual and metadata tracks showed mixed or baseline findings.")
            else:
                findings.append("Significant forensic tampering indicators corroborated across physical and symbolic tracks.")
                findings.append("Multiple analytical tracks independently confirm localized structural or visual tampering.")
            if regions:
                findings.append(f"{len(regions)} suspicious regions were detected requiring inspection.")
        elif risk_tier == "SUSPICIOUS":
            findings.append("Borderline or conflicting indicators were detected across analysis tracks.")
            findings.append("Manual forensic examiner review is required before verification.")
        elif risk_tier == "LOW_RISK":
            findings.append("Document characteristics are consistent with authentic reference baselines.")
            findings.append("No significant localized manipulation or structural tampering was detected.")
        else:
            findings.append("The available analysis is insufficient to determine document risk.")
            findings.append("Review incomplete or failed modules before drawing a conclusion.")

        context.explanation = " ".join(findings)
        return StageResult.success(self.name)

