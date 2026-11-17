"""
risk_stage.py — Three-Track Forensic Risk Synthesis Stage (Phase 8R).

Synthesizes:
Track 1: ML physical substrate analysis (Random Forest 18 features, T=0.40)
Track 2: Symbolic & semantic integrity (Metadata, OCR consistency, Layout geometry)
Track 3: Independent Visual Evidence Arbiter (Copy-Move clones, pixel duplication — REM-03)
Non-destructive JPEG Quality Qualification (REM-04)

Maintains independent visibility and auditable decision traces for all three tracks.
Never double-counts evidence or overrides calibrated Track 1 probabilities.
"""

import logging
from typing import Dict, Any, List, Optional

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.ml_inference.models import RiskTier
from app.services.forensics.jpeg_quality_estimator import inspect_compression_quality

logger = logging.getLogger(__name__)

# Non-pixel symbolic categories owned exclusively by Track 2
SYMBOLIC_CATEGORIES = {"METADATA", "OCR", "LAYOUT", "FIELD", "metadata", "ocr", "layout", "field"}


class RiskStage(BaseStage):
    """
    Three-track forensic risk synthesis stage (REM-02, REM-03, REM-04).
    """

    name = "risk"
    description = "Synthesizes ML physical forensics, symbolic rules, and visual clone evidence into a unified risk assessment."
    version = "3.0.0"
    dependencies = ["forgery", "ml_inference"]

    async def run(self, context: AnalysisContext) -> StageResult:
        logger.info("RiskStage started | job=%s", context.job_id)
        warnings: List[str] = []

        # ========================================================
        # TRACK 1: ML Physical Substrate Analysis
        # ========================================================
        ml_pred: Optional[Dict[str, Any]] = context.ml_prediction
        ml_available = False
        ml_prob: Optional[float] = None
        ml_tier = RiskTier.UNKNOWN.value
        ml_status = "UNAVAILABLE"
        ml_class: Optional[str] = None

        if ml_pred:
            ml_status = ml_pred.get("status", "UNAVAILABLE")
            if ml_status in ("SUCCESS", "DEGRADED"):
                ml_available = True
                ml_prob = ml_pred.get("forgery_probability")
                ml_tier = ml_pred.get("risk_tier", RiskTier.UNKNOWN.value)
                ml_class = ml_pred.get("predicted_class")
            else:
                warnings.append(f"Track 1 (ML Substrate): Model inference was {ml_status}.")
        else:
            warnings.append("Track 1 (ML Substrate): No ML prediction found on context.")

        # ========================================================
        # TRACK 2: Symbolic & Semantic Integrity
        # ========================================================
        symbolic_evidence_items: List[Dict[str, Any]] = []
        symbolic_max_severity = 0.0
        symbolic_available = True

        scores = context.evidence_category_scores or {}
        for cat, sev in scores.items():
            if cat in SYMBOLIC_CATEGORIES and sev > 0:
                symbolic_evidence_items.append({
                    "category": cat.upper(),
                    "severity": float(sev),
                })
                if float(sev) > symbolic_max_severity:
                    symbolic_max_severity = float(sev)

        # Check metadata anomalies directly
        if context.metadata:
            flags = context.metadata.get("anomalies", []) or context.metadata.get("warnings", [])
            if flags and symbolic_max_severity < 40.0:
                symbolic_max_severity = max(symbolic_max_severity, 45.0)
                symbolic_evidence_items.append({
                    "category": "METADATA",
                    "severity": 45.0,
                    "description": "; ".join(flags) if isinstance(flags, list) else str(flags),
                })

        # Check OCR status
        if context.ocr_result is None:
            symbolic_evidence_items.append({
                "category": "OCR_STATUS",
                "severity": 0.0,
                "description": "OCR text extraction was unavailable or bypassed.",
            })

        # ========================================================
        # JPEG Quality Non-Destructive Qualification (REM-04)
        # ========================================================
        comp_info = inspect_compression_quality(context)
        context.compression_qualification = comp_info
        is_heavy_compression = comp_info.get("is_heavily_compressed", False)
        est_q = comp_info.get("estimated_quality")

        # ========================================================
        # TRACK 3: Independent Visual Evidence Arbiter (REM-03)
        # ========================================================
        # Evaluates copy-move and visual pixel duplication evidence independently
        visual_evidence_items: List[Dict[str, Any]] = []
        cm_features = context.copy_move_features or {}
        cm_inliers = float(cm_features.get("inlier_matches") or 0.0)
        cm_conf = float(cm_features.get("confidence") or 0.0)
        cm_pairs = int(cm_features.get("duplicate_pair_count") or 0)

        # Count visual copy-move regions across pages
        detected_cm_regions = [
            r for r in (context.detected_regions or [])
            if str(r.get("category", "")).upper() == "COPY_MOVE"
        ]

        # False positive filtering: requires minimum inlier density and confidence
        # Severe JPEG compression (Q < 40) creates 15-25 spurious block-corner matches on 8x8 DCT grid lines.
        # Condition threshold on compression quality:
        if is_heavy_compression:
            is_verified_copy_move = (
                (cm_inliers >= 30.0 and cm_conf >= 0.85)
                or (cm_pairs >= 2 and cm_conf >= 0.85 and cm_inliers >= 20.0)
            )
        else:
            is_verified_copy_move = (
                (cm_inliers >= 15.0 and cm_conf >= 0.80)
                or (len(detected_cm_regions) >= 1 and cm_conf >= 0.80 and cm_inliers >= 12.0)
            )

        visual_tier = RiskTier.LOW_RISK
        visual_severity = 0.0

        if is_verified_copy_move:
            # Multiple duplicate clusters (>= 2 pairs) or extensive inlier density (>= 40)
            # elevate to HIGH_RISK; isolated single duplicate pair elevates to SUSPICIOUS
            if cm_pairs >= 2 or cm_inliers >= 40.0:
                visual_tier = RiskTier.HIGH_RISK
                visual_severity = 90.0
                visual_finding = (
                    f"Verified copy-move forgery clusters detected "
                    f"({cm_pairs} pairs, {int(cm_inliers)} inliers, confidence={cm_conf:.2f})."
                )
            else:
                visual_tier = RiskTier.SUSPICIOUS
                visual_severity = 50.0
                visual_finding = (
                    f"Suspicious duplicate region detected "
                    f"({cm_pairs} pair, {int(cm_inliers)} inliers, confidence={cm_conf:.2f})."
                )
            for r in detected_cm_regions:
                visual_evidence_items.append({
                    "detector": r.get("detector"),
                    "page_index": r.get("page_index", 0),
                    "severity": r.get("severity", 90.0),
                    "confidence": r.get("confidence", cm_conf),
                    "description": r.get("description", "Copy-move duplication detected"),
                })
        else:
            visual_finding = "No verified copy-move or visual clone clusters detected."

        context.visual_evidence = {
            "available": True,
            "detected_clusters": cm_pairs,
            "max_cluster_confidence": cm_conf,
            "total_inlier_matches": int(cm_inliers),
            "copy_move_confirmed": is_verified_copy_move,
            "visual_tier": visual_tier.value,
            "evidence_items": visual_evidence_items,
        }

        # Check borderline compression artifact qualification gate
        is_compression_borderline = False
        if (
            is_heavy_compression
            and ml_prob is not None
            and (0.40 <= ml_prob <= 0.45)
            and not is_verified_copy_move
            and symbolic_max_severity < 30.0
        ):
            is_compression_borderline = True
            logger.info(
                "REM-04 Borderline qualification active | job=%s | P_ML=%.4f | est_Q=%.1f",
                context.job_id,
                ml_prob,
                est_q or 0.0,
            )
            # Qualify Track 1 predicted class to avoid False Positive binary verdict
            if ml_pred:
                ml_pred["predicted_class"] = "AUTHENTIC"
                ml_pred["risk_tier"] = RiskTier.SUSPICIOUS.value
                ml_class = "AUTHENTIC"
                ml_tier = RiskTier.SUSPICIOUS.value

        # Attach limitation notice if heavy compression detected
        if is_heavy_compression and ml_pred:
            limits = ml_pred.setdefault("limitations", [])
            notice_msg = comp_info.get("compression_notice") or "Heavy JPEG compression artifacts detected."
            # Avoid duplicate notices
            if not any(item.get("code") == "HEAVY_COMPRESSION_ARTIFACTS" for item in limits):
                limits.append({
                    "code": "HEAVY_COMPRESSION_ARTIFACTS",
                    "severity": "WARNING",
                    "message": notice_msg,
                })

        # ========================================================
        # UNIFIED RISK SYNTHESIS & AUDITABLE DECISION TRACE
        # ========================================================
        decision_trace: List[Dict[str, Any]] = []

        # Step 1: Record Track 1 (ML)
        if ml_available and ml_prob is not None:
            trace_finding = f"Random Forest forgery probability = {ml_prob:.4f} ({ml_tier})"
            if is_compression_borderline:
                trace_finding += f" [QUALIFIED: Severe compression Q={est_q:.0f}]"
            decision_trace.append({
                "track": "Track 1: ML Physical Substrate",
                "finding": trace_finding,
                "features_considered": "18 active numerical features (ELA, blur, noise, Laplacian, AKAZE)",
            })
        else:
            decision_trace.append({
                "track": "Track 1: ML Physical Substrate",
                "finding": "ML physical substrate analysis unavailable. Operating in degraded symbolic mode.",
                "features_considered": "None",
            })

        # Step 2: Record Track 2 (Symbolic)
        if symbolic_evidence_items:
            decision_trace.append({
                "track": "Track 2: Symbolic & Semantic Integrity",
                "finding": f"Max symbolic severity = {symbolic_max_severity:.1f}/100 across {len(symbolic_evidence_items)} findings",
                "evidence_items": symbolic_evidence_items,
            })
        else:
            decision_trace.append({
                "track": "Track 2: Symbolic & Semantic Integrity",
                "finding": "No symbolic, metadata, or layout anomalies detected.",
                "evidence_items": [],
            })

        # Step 3: Record Track 3 (Visual Evidence Arbiter)
        decision_trace.append({
            "track": "Track 3: Visual Evidence Arbiter",
            "finding": visual_finding,
            "evidence_items": visual_evidence_items,
            "features_considered": f"Copy-move clusters={cm_pairs}, inliers={int(cm_inliers)}, conf={cm_conf:.2f}",
        })

        # Step 4: Record Compression Qualification if applicable
        if is_heavy_compression:
            decision_trace.append({
                "track": "Non-Destructive Media Qualification",
                "finding": f"Detected heavy JPEG DCT compression (estimated Q={est_q:.0f} < 40).",
                "description": comp_info.get("compression_notice"),
            })

        # Step 5: Synthesize Unified Operational Risk Tier
        is_corroborated_tampering = (
            visual_tier == RiskTier.HIGH_RISK
            or symbolic_max_severity >= 60.0
            or (ml_prob is not None and ml_prob >= 0.75)
        )

        if is_corroborated_tampering:
            unified_tier = RiskTier.HIGH_RISK
            risk_description = "Significant forensic tampering indicators corroborated across physical and symbolic tracks."
            overall_verdict = "SUSPICIOUS / HIGH_RISK"
        elif (
            (not is_compression_borderline and ml_prob is not None and ml_prob >= 0.40)
            or (ml_class == "FORGED" and not is_compression_borderline)
            or (symbolic_max_severity >= 40.0)
        ):
            unified_tier = RiskTier.HIGH_RISK
            risk_description = "ML screening threshold exceeded. Supporting forensic evidence is mixed."
            overall_verdict = "SUSPICIOUS / HIGH_RISK"
        elif is_compression_borderline:
            unified_tier = RiskTier.SUSPICIOUS
            risk_description = (
                f"Document exhibits severe JPEG compression artifacts (Q={est_q:.0f}) with borderline ML elevation. "
                f"Manual forensic review is required to verify physical substrate."
            )
            overall_verdict = "SUSPICIOUS / COMPRESSION_DEGRADED"
        elif (
            (ml_prob is not None and ml_prob >= 0.30)
            or (symbolic_max_severity >= 30.0)
            or (visual_tier == RiskTier.SUSPICIOUS)
        ):
            unified_tier = RiskTier.SUSPICIOUS
            risk_description = "Document requires manual forensic investigation."
            overall_verdict = "SUSPICIOUS / REVIEW_REQUIRED"
        elif (
            ml_available
            and ml_prob is not None
            and ml_prob < 0.30
            and symbolic_max_severity < 30.0
            and visual_tier == RiskTier.LOW_RISK
        ):
            unified_tier = RiskTier.LOW_RISK
            risk_description = "Preliminary screening indicates relatively low forgery risk. This is not a guarantee of authenticity."
            overall_verdict = "LOW_RISK / AUTHENTIC"
        else:
            unified_tier = RiskTier.UNKNOWN
            risk_description = "Risk classification could not be determined due to incomplete forensic pipeline execution."
            overall_verdict = "INCONCLUSIVE"

        # Calculate composite display score
        effective_ml_score = (ml_prob * 100.0) if (ml_prob is not None and not is_compression_borderline) else (35.0 if is_compression_borderline else 0.0)
        composite_display_score = round(max(effective_ml_score, symbolic_max_severity, visual_severity), 1)

        decision_trace.append({
            "track": "Synthesis Arbiter",
            "finding": f"Unified Risk Tier: {unified_tier.value} | Verdict: {overall_verdict}",
            "description": risk_description,
        })

        # Update context
        context.risk_score = composite_display_score
        context.risk_label = unified_tier.value.lower()
        context.risk_assessment = {
            "unified_risk_tier": unified_tier.value,
            "risk_description": risk_description,
            "overall_verdict": overall_verdict,
            "composite_display_score": composite_display_score,
            "is_corroborated_tampering": is_corroborated_tampering,
            "is_mixed_evidence": (unified_tier == RiskTier.HIGH_RISK and not is_corroborated_tampering),
            "track_1_ml": {
                "available": ml_available,
                "status": ml_status,
                "forgery_probability": ml_prob,
                "risk_tier": ml_tier,
                "operational_threshold": ml_pred.get("operational_threshold", 0.40) if ml_pred else 0.40,
                "predicted_class": ml_class,
            },
            "track_2_symbolic": {
                "available": symbolic_available,
                "symbolic_severity_score": round(symbolic_max_severity, 1),
                "symbolic_evidence": symbolic_evidence_items,
            },
            "track_3_visual": context.visual_evidence,
            "compression_qualification": comp_info,
            "decision_trace": decision_trace,
        }

        logger.info(
            "Risk synthesis complete | job=%s | tier=%s | composite_score=%.1f | ml_prob=%s | visual_tier=%s | comp_borderline=%s",
            context.job_id,
            unified_tier.value,
            composite_display_score,
            f"{ml_prob:.4f}" if ml_prob is not None else "None",
            visual_tier.value,
            is_compression_borderline,
        )

        return StageResult.success(self.name, warnings=warnings)
