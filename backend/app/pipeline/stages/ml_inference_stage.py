"""
ml_inference_stage.py — Phase 5 pipeline stage for supervised ML forgery prediction.
Integrates the frozen Random Forest model into the VisionForensics AI pipeline.
Enhanced in Phase 8R (REM-01 & REM-02) for per-page inference and safe risk aggregation.
"""

from typing import Optional, List, Dict, Any
import logging
import math

from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.services.ml_inference import MLInferenceService, InferenceStatus, RiskTier
from app.services.ml_inference.inference_service import RISK_DESCRIPTIONS

logger = logging.getLogger(__name__)


class MLInferenceStage(BaseStage):
    """
    Pipeline stage that extracts the authoritative 18 active numerical features
    and executes per-page and document inference using the frozen Random Forest model.
    """

    name = "ml_inference"
    description = "Evaluates document features using the frozen Random Forest baseline model."
    version = "2.0.0"
    dependencies = ["forgery"]

    def __init__(
        self,
        service: Optional[MLInferenceService] = None,
        operational_threshold: float = 0.40,
        alternative_threshold: float = 0.50,
    ) -> None:
        super().__init__()
        self._service = service or MLInferenceService()
        self._operational_threshold = operational_threshold
        self._alternative_threshold = alternative_threshold

    async def run(self, context: AnalysisContext) -> StageResult:
        logger.info(
            "MLInferenceStage started | job=%s | threshold=%.2f",
            context.job_id,
            self._operational_threshold,
        )

        try:
            # Determine page count
            num_pages = max(
                1,
                len(context.page_images)
                or len(context.preprocessed_images)
                or len(context.quality_metrics)
                or (context.page_count or 1),
            )

            context.pages_ml = []
            page_results: List[Any] = []

            # -------------------------------------------------------------
            # Stage 1 (REM-01): Per-Page ML Inference
            # -------------------------------------------------------------
            for page_idx in range(num_pages):
                try:
                    p_res = self._service.predict_page(
                        context,
                        page_index=page_idx,
                        operational_threshold=self._operational_threshold,
                        alternative_threshold=self._alternative_threshold,
                    )
                    page_results.append((page_idx, p_res))
                    context.pages_ml.append({
                        "page_index": page_idx,
                        "forgery_probability": p_res.forgery_probability,
                        "predicted_class": p_res.predicted_class,
                        "risk_tier": p_res.risk_tier.value,
                        "status": p_res.status.value,
                        "feature_completeness": p_res.feature_completeness,
                        "top_contributing_features": p_res.top_contributing_features,
                        "imputed_features": p_res.imputed_features,
                    })
                except Exception as p_err:
                    logger.warning("Per-page inference failed on page %d: %s", page_idx, p_err)
                    context.pages_ml.append({
                        "page_index": page_idx,
                        "forgery_probability": None,
                        "predicted_class": None,
                        "risk_tier": RiskTier.UNKNOWN.value,
                        "status": "ERROR",
                        "feature_completeness": 0.0,
                        "top_contributing_features": {},
                        "imputed_features": {},
                    })

            # -------------------------------------------------------------
            # Stage 2 (REM-02): Multi-Page Risk Aggregation
            # -------------------------------------------------------------
            if num_pages == 1:
                # Single-page document: preserve exact existing behavior
                doc_pred = self._service.predict(
                    context,
                    operational_threshold=self._operational_threshold,
                    alternative_threshold=self._alternative_threshold,
                )
                raw_prediction = doc_pred.model_dump(mode="json")
                raw_page_index = 0
                raw_selection_method = "single_page"
            else:
                # Multi-page aggregation gate
                valid_pages = [
                    (idx, res) for (idx, res) in page_results
                    if res.status in (InferenceStatus.SUCCESS, InferenceStatus.DEGRADED)
                    and res.forgery_probability is not None
                ]

                if not valid_pages:
                    # All page inferences failed: fallback to standard predict
                    doc_pred = self._service.predict(
                        context,
                        operational_threshold=self._operational_threshold,
                        alternative_threshold=self._alternative_threshold,
                    )
                    raw_prediction = doc_pred.model_dump(mode="json")
                    raw_page_index = None
                    raw_selection_method = "document_feature_fallback"
                else:
                    # Find candidate page with max probability
                    cand_idx, cand_res = max(valid_pages, key=lambda x: x[1].forgery_probability)
                    raw_prediction = cand_res.model_dump(mode="json")
                    raw_page_index = cand_idx
                    raw_selection_method = "maximum_page_probability"
                    p_max = cand_res.forgery_probability

                    # Historical heuristic corroboration gate, not a formal
                    # statistical correction. Preserve approved policy values.
                    t_n = min(0.75, self._operational_threshold + 0.07 * math.log(num_pages))

                    # Count visual regions on candidate page
                    v_k = sum(
                        1 for r in (context.detected_regions or [])
                        if int(r.get("page_index", 0)) == cand_idx
                    )

                    # Multi-page decision gate
                    if p_max >= t_n:
                        doc_class = "FORGED"
                        doc_tier = RiskTier.HIGH_RISK
                    elif p_max >= self._operational_threshold and v_k >= 1:
                        doc_class = "FORGED"
                        doc_tier = RiskTier.HIGH_RISK
                    elif p_max >= self._operational_threshold and v_k == 0:
                        doc_class = "AUTHENTIC"
                        doc_tier = RiskTier.SUSPICIOUS
                    elif p_max >= 0.30:
                        doc_class = "AUTHENTIC"
                        doc_tier = RiskTier.SUSPICIOUS
                    else:
                        doc_class = "AUTHENTIC"
                        doc_tier = RiskTier.LOW_RISK

                    # Clone candidate result as document base to preserve schema & contributors
                    doc_pred = cand_res.model_copy(deep=True)
                    doc_pred.forgery_probability = p_max
                    doc_pred.predicted_class = doc_class
                    doc_pred.risk_tier = doc_tier
                    doc_pred.risk_description = RISK_DESCRIPTIONS[doc_tier]
                    doc_pred.warnings.append(
                        f"Multi-page aggregation: evaluated {num_pages} pages. "
                        f"Candidate page {cand_idx + 1} exhibited peak P_ML={p_max:.4f} (T_N={t_n:.4f}, visual_regions={v_k})."
                    )

            # Store serializable prediction payload on AnalysisContext
            context.ml_prediction = doc_pred.model_dump()
            context.raw_ml_prediction = {
                **raw_prediction,
                "source_page_index": raw_page_index,
                "selection_method": raw_selection_method,
                "is_document_probability": False,
            }

            if doc_pred.status == InferenceStatus.ML_UNAVAILABLE:
                logger.warning(
                    "ML inference unavailable | job=%s | warnings=%s",
                    context.job_id,
                    doc_pred.warnings,
                )
                return StageResult.success(self.name, warnings=doc_pred.warnings)

            if doc_pred.status == InferenceStatus.DEGRADED:
                logger.warning(
                    "ML inference degraded | job=%s | completeness=%.2f",
                    context.job_id,
                    doc_pred.feature_completeness,
                )
                return StageResult.success(self.name, warnings=doc_pred.warnings)

            logger.info(
                "ML inference complete | job=%s | pages=%d | class=%s | prob=%.4f | tier=%s",
                context.job_id,
                num_pages,
                doc_pred.predicted_class,
                doc_pred.forgery_probability,
                doc_pred.risk_tier.value,
            )
            return StageResult.success(self.name, warnings=doc_pred.warnings)

        except Exception as e:
            err_msg = f"Unexpected failure during ML inference: {str(e)}"
            logger.exception(err_msg)
            context.add_warning(err_msg)
            return StageResult.success(self.name, warnings=[err_msg])
