"""Block artificial custody histories and fake archives from the legacy path."""
import pytest
from app.services.report_generation.report_service import ReportGenerationService


def test_legacy_report_cannot_manufacture_custody():
    with pytest.raises(NotImplementedError, match="genuine custody"):
        ReportGenerationService().generate_report(None, [])


def test_legacy_archive_cannot_return_mock_bytes():
    with pytest.raises(NotImplementedError, match="mock archive bytes"):
        ReportGenerationService().export_archive(None)


def test_registered_pdf_service_is_separate_from_legacy_scaffold():
    from app.api.reports import _report_service
    from app.services.report_service import ReportService
    assert isinstance(_report_service, ReportService)
