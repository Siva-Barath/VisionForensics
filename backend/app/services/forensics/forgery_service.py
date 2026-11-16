"""
Forgery Service.

Central orchestrator for the Forgery Detection Framework.
Runs all registered detectors, aggregates evidence, computes risk,
and builds the final ForgeryReport.
"""

import time
import logging
from typing import Optional

from app.pipeline.context import AnalysisContext
from app.services.forensics.detector_registry import DetectorRegistry
from app.services.forensics.visual_evidence_collector import VisualEvidenceCollector
from app.services.forensics.evidence_aggregator import EvidenceAggregator
from app.services.forensics.risk_estimator import RiskEstimator
from app.services.forensics.models import ForgeryReport

logger = logging.getLogger(__name__)

class ForgeryService:
    def __init__(self, registry: DetectorRegistry):
        self.registry = registry
        self.aggregator = EvidenceAggregator()
        self.risk_estimator = RiskEstimator()
        self.visual_collector = VisualEvidenceCollector()

    def process(self, context: AnalysisContext) -> None:
        """Process the document context through all forensic detectors."""
        start_time = time.perf_counter()
        logger.info("Forgery Detection started | job=%s", context.job_id)
        
        all_evidence = []
        
        # 1. Run all registered independent detectors
        for detector in self.registry.get_all():
            try:
                logger.debug("Running detector: %s", detector.name)
                d_start = time.perf_counter()
                warnings_before = len(context.warnings)
                
                evidence = detector.detect(context)
                all_evidence.extend(evidence)
                outcome = "PARTIAL" if len(context.warnings) > warnings_before else "COMPLETED"
                reason = "Detector executed; findings are screening indicators, not proof of forgery."
                if detector.name in ("ocr_consistency_detector", "field_consistency_detector", "layout_consistency_detector") and context.ocr_result is None:
                    outcome, reason = "UNAVAILABLE", "Required OCR extraction was not available."
                if detector.name in ("signature_region_analyzer", "logo_region_analyzer"):
                    category = "SIGNATURE" if detector.name.startswith("signature") else "LOGO"
                    sections = (context.structured_document or {}).get("sections", [])
                    if not any(section.get("region_type") == category for section in sections):
                        outcome, reason = "NOT APPLICABLE", "No supported region was identified for visual morphology examination."
                if detector.name in ("image_artifact_detector", "copy_move_region_analyzer") and not context.preprocessed_images:
                    outcome, reason = "UNAVAILABLE", "No valid page images were available."
                context.module_execution[detector.name] = {"status": outcome, "reason": reason, "evidence_count": len(evidence)}
                
                d_time = (time.perf_counter() - d_start) * 1000
                logger.debug("Detector %s completed | evidence=%d | duration=%.1fms", 
                             detector.name, len(evidence), d_time)
                             
            except Exception as e:
                msg = f"Detector '{detector.name}' failed: {str(e)}"
                logger.error(msg)
                context.add_warning(msg)
                context.module_execution[detector.name] = {"status": "FAILED", "reason": "Detector execution failed; review processing warnings."}
                
        # 2. Aggregate Evidence
        unique_evidence, summary = self.aggregator.aggregate(all_evidence)
        
        # 3. Estimate Risk
        risk_assessment = self.risk_estimator.estimate(unique_evidence)
        
        # 4. Extract Visuals (Populated into context separately or kept in evidence)
        visual_regions = self.visual_collector.collect(unique_evidence)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        report = ForgeryReport(
            evidence_list=unique_evidence,
            summary=summary,
            risk_assessment=risk_assessment,
            processing_time_ms=processing_time
        )
        
        # 5. Update Context
        from dataclasses import asdict
        
        context.forgery_report = asdict(report)
        context.risk_assessment = asdict(risk_assessment)
        
        # Overwrite legacy context fields for compatibility
        context.detected_regions = visual_regions
        context.risk_score = risk_assessment.risk_score
        context.risk_label = risk_assessment.risk_label.value

        # Expose per-category max severity for ML feature extraction
        context.evidence_category_scores = {
            cat.value: float(sev)
            for cat, sev in self.risk_estimator.last_max_severity.items()
        }
        
        logger.info(
            "Forgery Detection completed | job=%s | evidence=%d | risk=%s (%.1f) | duration=%.1fms", 
            context.job_id, summary.total_evidence, risk_assessment.risk_label.value, 
            risk_assessment.risk_score, processing_time
        )
