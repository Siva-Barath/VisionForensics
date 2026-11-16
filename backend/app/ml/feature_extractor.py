"""
FeatureExtractor — reads AnalysisContext and produces a FeatureVector.

Rules:
- Only reads from AnalysisContext.  Never modifies it.
- Missing / None context fields produce None feature values (not errors).
- Multi-page image forensics metrics are averaged across pages.
- fusion_calibrated_risk, fusion_posterior_risk, fusion_prior_risk,
  fusion_verdict_ordinal, and risk_score are NOT exported — they are
  the rule engine's final decisions or fixed constants (zero variance)
  and must not be used as ML training features (information leakage).
"""
from __future__ import annotations

import logging
from typing import Any

from app.pipeline.context import AnalysisContext
from app.ml.feature_vector import FeatureVector
from app.ml.feature_registry import DOCUMENT_TYPE_ORDINAL

logger = logging.getLogger(__name__)

# Evidence category name (lowercase) → ev_* feature key
_EVIDENCE_SEVERITY_MAP: dict[str, str] = {
    "metadata":  "ev_metadata",
    "image":     "ev_image",
    "ocr":       "ev_ocr",
    "layout":    "ev_layout",
    "field":     "ev_field",
    "signature": "ev_signature",
    "logo":      "ev_logo",
    "visual":    "ev_visual",
    "unknown":   "ev_unknown",
}

# EvidenceCategory value (uppercase) → evidence_category_count_* feature key
_EVIDENCE_COUNT_MAP: dict[str, str] = {
    "METADATA":  "evidence_category_count_metadata",
    "IMAGE":     "evidence_category_count_image",
    "OCR":       "evidence_category_count_ocr",
    "LAYOUT":    "evidence_category_count_layout",
    "FIELD":     "evidence_category_count_field",
    "SIGNATURE": "evidence_category_count_signature",
    "LOGO":      "evidence_category_count_logo",
    "VISUAL":    "evidence_category_count_visual",
    "UNKNOWN":   "evidence_category_count_unknown",
}


def _safe(value: Any, default: float | None = None) -> float | None:
    """Return float or default; never raises."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(metrics: list[dict], key: str) -> float | None:
    """Average a scalar key across a list of per-page metric dicts."""
    values = [_safe(m.get(key)) for m in metrics if _safe(m.get(key)) is not None]
    return sum(values) / len(values) if values else None


class FeatureExtractor:
    """Stateless extractor.  Call extract() once per AnalysisContext."""

    def extract(self, context: AnalysisContext, label: str | None = None) -> FeatureVector:
        features: dict[str, float | None] = {}

        self._extract_image_metadata(context, features)
        self._extract_image_forensics(context, features)
        self._extract_ocr(context, features)
        self._extract_layout(context, features)
        self._extract_classification(context, features)
        self._extract_signature(context, features)
        self._extract_logo(context, features)
        self._extract_copy_move(context, features)
        self._extract_evidence_severity(context, features)
        self._extract_evidence_summary(context, features)
        self._extract_fusion(context, features)

        return FeatureVector(
            document_id=context.document_id,
            original_filename=context.original_filename,
            file_type=context.file_type,
            features=features,
            label=label,
        )

    def extract_page(
        self,
        context: AnalysisContext,
        page_index: int,
        label: str | None = None,
    ) -> FeatureVector:
        """
        Extracts features for a specific page without averaging unrelated page metrics (REM-01).
        """
        features: dict[str, float | None] = {}

        self._extract_image_metadata_page(context, features, page_index)
        self._extract_image_forensics_page(context, features, page_index)
        self._extract_ocr(context, features)
        self._extract_layout(context, features)
        self._extract_classification(context, features)
        self._extract_signature(context, features)
        self._extract_logo(context, features)
        self._extract_copy_move_page(context, features, page_index)
        self._extract_evidence_severity(context, features)
        self._extract_evidence_summary(context, features)
        self._extract_fusion(context, features)

        return FeatureVector(
            document_id=context.document_id,
            original_filename=f"{context.original_filename}#page={page_index}",
            file_type=context.file_type,
            features=features,
            label=label,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_image_metadata(self, ctx: AnalysisContext, f: dict) -> None:
        qm = ctx.quality_metrics[0] if ctx.quality_metrics else None
        if qm is None:
            f["img_width"] = f["img_height"] = f["img_aspect_ratio"] = f["img_color_channels"] = None
            return
        # quality_metrics entries are QualityMetrics dataclass instances
        f["img_width"]          = _safe(getattr(qm, "width", None))
        f["img_height"]         = _safe(getattr(qm, "height", None))
        f["img_aspect_ratio"]   = _safe(getattr(qm, "aspect_ratio", None))
        f["img_color_channels"] = _safe(getattr(qm, "color_channels", None))

    def _extract_image_metadata_page(self, ctx: AnalysisContext, f: dict, page_index: int) -> None:
        qm = None
        if ctx.quality_metrics and page_index < len(ctx.quality_metrics):
            qm = ctx.quality_metrics[page_index]
        elif ctx.quality_metrics:
            qm = ctx.quality_metrics[0]
        if qm is None:
            f["img_width"] = f["img_height"] = f["img_aspect_ratio"] = f["img_color_channels"] = None
            return
        f["img_width"]          = _safe(getattr(qm, "width", None))
        f["img_height"]         = _safe(getattr(qm, "height", None))
        f["img_aspect_ratio"]   = _safe(getattr(qm, "aspect_ratio", None))
        f["img_color_channels"] = _safe(getattr(qm, "color_channels", None))

    def _extract_image_forensics(self, ctx: AnalysisContext, f: dict) -> None:
        metrics = ctx.image_forensics_metrics or []
        f["img_laplacian_variance_mean"] = _avg(metrics, "laplacian_variance")
        f["img_blur_severity_mean"]      = _avg(metrics, "blur_severity")
        f["img_noise_sigma_mean"]        = _avg(metrics, "noise_sigma")
        f["img_edge_density_mean"]       = _avg(metrics, "edge_density")
        f["img_illumination_std_mean"]   = _avg(metrics, "illumination_std")
        f["img_ela_region_count_mean"]   = _avg(metrics, "ela_region_count")
        f["img_ela_max_difference_mean"] = _avg(metrics, "ela_max_difference")
        f["img_entropy_score_mean"]      = _avg(metrics, "entropy_score")
        f["img_page_count"]              = _safe(len(metrics)) if metrics else None

    def _extract_image_forensics_page(self, ctx: AnalysisContext, f: dict, page_index: int) -> None:
        metrics = ctx.image_forensics_metrics or []
        m = metrics[page_index] if (metrics and page_index < len(metrics)) else {}
        f["img_laplacian_variance_mean"] = _safe(m.get("laplacian_variance"))
        f["img_blur_severity_mean"]      = _safe(m.get("blur_severity"))
        f["img_noise_sigma_mean"]        = _safe(m.get("noise_sigma"))
        f["img_edge_density_mean"]       = _safe(m.get("edge_density"))
        f["img_illumination_std_mean"]   = _safe(m.get("illumination_std"))
        f["img_ela_region_count_mean"]   = _safe(m.get("ela_region_count"))
        f["img_ela_max_difference_mean"] = _safe(m.get("ela_max_difference"))
        f["img_entropy_score_mean"]      = _safe(m.get("entropy_score"))
        f["img_page_count"]              = _safe(len(metrics)) if metrics else None

    def _extract_ocr(self, ctx: AnalysisContext, f: dict) -> None:
        # ocr_summary is stored as a dict (serialised OCRSummary) or None
        ocr = ctx.ocr_summary or {}
        f["ocr_average_confidence"]      = _safe(ocr.get("average_confidence"))
        f["ocr_min_confidence"]          = _safe(ocr.get("min_confidence"))
        f["ocr_max_confidence"]          = _safe(ocr.get("max_confidence"))
        f["ocr_low_confidence_fraction"] = _safe(ocr.get("low_confidence_fraction"))
        f["ocr_total_words"]             = _safe(ocr.get("total_words"))

    def _extract_layout(self, ctx: AnalysisContext, f: dict) -> None:
        # layout_summary is stored as a dict (serialised LayoutSummary) or None
        ls = ctx.layout_summary or {}
        f["layout_total_sections"] = _safe(ls.get("total_sections"))
        f["layout_total_fields"]   = _safe(ls.get("total_fields"))
        f["layout_total_tables"]   = _safe(ls.get("total_tables"))

    def _extract_classification(self, ctx: AnalysisContext, f: dict) -> None:
        cr = ctx.classification_result or {}
        # predicted_type may be a string value of the DocumentType enum
        raw_type = cr.get("predicted_type")
        if raw_type is None:
            f["classification_type_ordinal"] = None
        else:
            # Handle both enum instances and plain strings
            type_str = raw_type if isinstance(raw_type, str) else str(raw_type)
            # Strip enum class prefix if present (e.g. "DocumentType.PASSPORT" → "PASSPORT")
            if "." in type_str:
                type_str = type_str.split(".")[-1]
            f["classification_type_ordinal"] = _safe(
                DOCUMENT_TYPE_ORDINAL.get(type_str.upper())
            )
        f["classification_confidence"] = _safe(cr.get("confidence"))

    def _extract_signature(self, ctx: AnalysisContext, f: dict) -> None:
        sig = ctx.signature_features or {}
        f["sig_stroke_width_mean"]  = _safe(sig.get("stroke_width_mean"))
        f["sig_stroke_width_std"]   = _safe(sig.get("stroke_width_std"))
        f["sig_contour_count"]      = _safe(sig.get("contour_count"))
        f["sig_contour_area"]       = _safe(sig.get("contour_area"))
        f["sig_contour_perimeter"]  = _safe(sig.get("contour_perimeter"))
        f["sig_ink_density"]        = _safe(sig.get("ink_density"))
        f["sig_foreground_ratio"]   = _safe(sig.get("foreground_ratio"))
        f["sig_skeleton_length"]    = _safe(sig.get("skeleton_length"))
        f["sig_endpoint_count"]     = _safe(sig.get("endpoint_count"))
        f["sig_branch_count"]       = _safe(sig.get("branch_count"))
        f["sig_blob_count"]         = _safe(sig.get("blob_count"))
        f["sig_aspect_ratio"]       = _safe(sig.get("aspect_ratio"))
        f["sig_solidity"]           = _safe(sig.get("solidity"))
        f["sig_eccentricity"]       = _safe(sig.get("eccentricity"))
        f["sig_contrast"]           = _safe(sig.get("contrast"))
        f["sig_complexity_score"]   = _safe(sig.get("complexity_score"))

    def _extract_logo(self, ctx: AnalysisContext, f: dict) -> None:
        logo = ctx.logo_features or {}
        fp = logo.get("fingerprint") or {}
        f["logo_edge_density"]           = _safe(logo.get("edge_density"))
        f["logo_resolution_quality"]     = _safe(logo.get("resolution_quality"))
        f["logo_authenticity_score"]     = _safe(logo.get("authenticity_score"))
        f["logo_orb_keypoint_count"]     = _safe(fp.get("orb_keypoint_count"))
        f["logo_orb_descriptor_density"] = _safe(fp.get("orb_descriptor_density"))
        f["logo_symmetry_horizontal"]    = _safe(fp.get("symmetry_horizontal"))
        f["logo_symmetry_vertical"]      = _safe(fp.get("symmetry_vertical"))
        f["logo_contour_count"]          = _safe(fp.get("contour_count"))
        f["logo_contour_complexity"]     = _safe(fp.get("contour_complexity"))
        f["logo_texture_variance"]       = _safe(fp.get("texture_variance"))
        f["logo_shape_circularity"]      = _safe(fp.get("shape_circularity"))
        f["logo_shape_compactness"]      = _safe(fp.get("shape_compactness"))
        f["logo_shape_eccentricity"]     = _safe(fp.get("shape_eccentricity"))
        f["logo_aspect_ratio"]           = _safe(fp.get("aspect_ratio"))
        f["logo_solidity"]               = _safe(fp.get("solidity"))
        # Flatten Hu moments (list of 7 floats) into individual features
        hu = fp.get("hu_moments") or []
        for i in range(7):
            f[f"logo_hu_{i}"] = _safe(hu[i]) if i < len(hu) else None

    def _extract_copy_move(self, ctx: AnalysisContext, f: dict) -> None:
        cm = ctx.copy_move_features or {}
        f["cm_keypoint_count_orb"]   = _safe(cm.get("keypoint_count_orb"))
        f["cm_keypoint_count_akaze"] = _safe(cm.get("keypoint_count_akaze"))
        f["cm_descriptor_matches"]   = _safe(cm.get("descriptor_matches"))
        f["cm_inlier_matches"]       = _safe(cm.get("inlier_matches"))
        f["cm_average_region_size"]  = _safe(cm.get("average_region_size"))
        f["cm_duplicate_pair_count"] = _safe(cm.get("duplicate_pair_count"))
        f["cm_confidence"]           = _safe(cm.get("confidence"))
        f["cm_inlier_ratio"]         = _safe(cm.get("inlier_ratio"))

    def _extract_copy_move_page(self, ctx: AnalysisContext, f: dict, page_index: int) -> None:
        cm_by_page = getattr(ctx, "copy_move_features_by_page", {}) or {}
        cm = cm_by_page.get(page_index)
        if cm is None:
            # Fallback to document-level or empty dict
            cm = ctx.copy_move_features or {}
        f["cm_keypoint_count_orb"]   = _safe(cm.get("keypoint_count_orb"))
        f["cm_keypoint_count_akaze"] = _safe(cm.get("keypoint_count_akaze"))
        f["cm_descriptor_matches"]   = _safe(cm.get("descriptor_matches"))
        f["cm_inlier_matches"]       = _safe(cm.get("inlier_matches"))
        f["cm_average_region_size"]  = _safe(cm.get("average_region_size"))
        f["cm_duplicate_pair_count"] = _safe(cm.get("duplicate_pair_count"))
        f["cm_confidence"]           = _safe(cm.get("confidence"))
        f["cm_inlier_ratio"]         = _safe(cm.get("inlier_ratio"))

    def _extract_evidence_severity(self, ctx: AnalysisContext, f: dict) -> None:
        scores = ctx.evidence_category_scores or {}
        for cat_name, feat_key in _EVIDENCE_SEVERITY_MAP.items():
            f[feat_key] = _safe(scores.get(cat_name))

    def _extract_evidence_summary(self, ctx: AnalysisContext, f: dict) -> None:
        # forgery_report is a serialised dict; summary is a nested dict
        report = ctx.forgery_report or {}
        summary = report.get("summary") or {}
        f["evidence_total_count"]      = _safe(summary.get("total_evidence"))
        f["evidence_highest_severity"] = _safe(summary.get("highest_severity"))
        # category_counts keys are EvidenceCategory.value strings (uppercase)
        cat_counts: dict = summary.get("category_counts") or {}
        for cat_upper, feat_key in _EVIDENCE_COUNT_MAP.items():
            f[feat_key] = _safe(cat_counts.get(cat_upper))

    def _extract_fusion(self, ctx: AnalysisContext, f: dict) -> None:
        fm = ctx.fusion_metrics or {}
        # Excluded (leakage / constant):
        #   fusion_calibrated_risk  — final posterior
        #   fusion_posterior_risk   — final posterior
        #   fusion_prior_risk       — fixed constant 0.05
        #   fusion_verdict_ordinal  — final verdict
        f["fusion_correlation_mult"]      = _safe(fm.get("correlation_multiplier"))
        f["fusion_conflict_mult"]         = _safe(fm.get("conflict_multiplier"))
        f["fusion_calibrated_confidence"] = _safe(fm.get("calibrated_confidence"))
        f["fusion_recommendation_count"]  = _safe(fm.get("recommendation_count"))
        f["fusion_contributor_count"]     = _safe(fm.get("contributor_count"))
