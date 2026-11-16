"""
Report Generation Orchestrator.
"""
import logging
from typing import List, Tuple
from app.services.evidence_fusion.models import FinalForensicAssessment
from app.services.forensics.models import Evidence

from .config import ReportGenerationConfig
from .models import GeneratedReport
from .executive_summary_builder import ExecutiveSummaryBuilder
from .investigation_summary_builder import InvestigationSummaryBuilder
from .evidence_table_builder import EvidenceTableBuilder
from .region_snapshot_builder import RegionSnapshotBuilder
from .decision_trace_builder import DecisionTraceBuilder
from .recommendation_builder import RecommendationBuilder
from .technical_appendix_builder import TechnicalAppendixBuilder
from .asset_collector import AssetCollector
from .report_validator import ReportValidator
from .report_exporter import ReportExporter
from .archive_builder import ArchiveBuilder

logger = logging.getLogger(__name__)

class ReportGenerationService:
    def __init__(self, config: ReportGenerationConfig = None):
        self.config = config or ReportGenerationConfig()
        
        self.exec_summary_builder = ExecutiveSummaryBuilder()
        self.inv_summary_builder = InvestigationSummaryBuilder()
        self.evidence_builder = EvidenceTableBuilder()
        self.region_builder = RegionSnapshotBuilder()
        self.trace_builder = DecisionTraceBuilder()
        self.rec_builder = RecommendationBuilder()
        self.appendix_builder = TechnicalAppendixBuilder()
        
        self.asset_collector = AssetCollector()
        self.validator = ReportValidator()
        self.exporter = ReportExporter()
        self.archive_builder = ArchiveBuilder()

    def generate_report(self, assessment: FinalForensicAssessment, raw_evidence: List[Evidence]) -> GeneratedReport:
        raise NotImplementedError(
            "Legacy report scaffold cannot establish genuine custody or verified assets. "
            "Use the registered app.services.report_service.ReportService PDF workflow."
        )

    def export_archive(self, report: GeneratedReport) -> bytes:
        raise NotImplementedError("Legacy archive export is not implemented; mock archive bytes are prohibited")
