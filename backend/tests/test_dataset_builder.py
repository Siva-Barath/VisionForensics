"""
Tests for DatasetBuilder.

DocumentService.ingest() is mocked to return a synthetic AnalysisContext
so no real files or pipeline execution are needed.
"""
import csv
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from app.pipeline.context import AnalysisContext
from app.ml.dataset_builder import DatasetBuilder, CSV_COLUMNS, _EXPECTED_COLUMN_COUNT, _EXPECTED_FEATURE_COUNT, _EXPECTED_METADATA_COUNT
from app.ml.feature_registry import FEATURE_NAMES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context() -> AnalysisContext:
    ctx = AnalysisContext(original_filename="sample.png", file_type="png")
    ctx.image_forensics_metrics = [
        {
            "page_index": 0,
            "laplacian_variance": 150.0,
            "blur_severity": 20.0,
            "noise_sigma": 4.0,
            "edge_density": 0.1,
            "illumination_std": 22.0,
            "ela_region_count": 1,
            "ela_max_difference": 30.0,
            "entropy_score": 12.0,
        }
    ]
    # risk_score stays on context but is NOT exported as a feature
    ctx.risk_score = 40.0
    return ctx


def _make_service(context: AnalysisContext) -> MagicMock:
    svc = MagicMock()
    svc.ingest = AsyncMock(return_value=context)
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_input(tmp_path):
    """Create a small directory tree with fake image files."""
    (tmp_path / "forged").mkdir()
    (tmp_path / "authentic").mkdir()
    (tmp_path / "forged" / "doc1.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "authentic" / "doc2.jpg").write_bytes(b"\xff\xd8\xff")
    return tmp_path


@pytest.fixture
def output_csv(tmp_path):
    return tmp_path / "out" / "dataset.csv"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDatasetBuilderBuild:
    @pytest.mark.asyncio
    async def test_writes_csv_with_correct_columns(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        assert output_csv.exists()
        with output_csv.open() as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == set(CSV_COLUMNS)

    @pytest.mark.asyncio
    async def test_column_order_matches_csv_columns(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        with output_csv.open() as f:
            reader = csv.DictReader(f)
            assert list(reader.fieldnames) == CSV_COLUMNS

    @pytest.mark.asyncio
    async def test_column_count(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        with output_csv.open() as f:
            reader = csv.DictReader(f)
            assert len(reader.fieldnames) == _EXPECTED_COLUMN_COUNT

    @pytest.mark.asyncio
    async def test_feature_count_in_csv(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        with output_csv.open() as f:
            reader = csv.DictReader(f)
            feature_cols = [c for c in reader.fieldnames if c in set(FEATURE_NAMES)]
        assert len(feature_cols) == _EXPECTED_FEATURE_COUNT

    @pytest.mark.asyncio
    async def test_metadata_count_in_csv(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        with output_csv.open() as f:
            reader = csv.DictReader(f)
            meta_cols = [c for c in reader.fieldnames
                         if c in {"document_id", "original_filename", "file_type", "label"}]
        assert len(meta_cols) == _EXPECTED_METADATA_COUNT

    @pytest.mark.asyncio
    async def test_row_count_matches_file_count(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        count = await builder.build(tmp_input, output_csv)

        assert count == 2
        with output_csv.open() as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_label_map_applied(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(
            tmp_input,
            output_csv,
            label_map={"forged": ["forged/"], "authentic": ["authentic/"]},
        )

        with output_csv.open() as f:
            rows = {r["original_filename"]: r["label"] for r in csv.DictReader(f)}

        assert set(rows.values()) <= {"forged", "authentic"}

    @pytest.mark.asyncio
    async def test_no_label_map_gives_empty_label(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        with output_csv.open() as f:
            rows = list(csv.DictReader(f))
        assert all(r["label"] == "" for r in rows)

    @pytest.mark.asyncio
    async def test_leakage_features_absent_from_csv(self, tmp_input, output_csv):
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, output_csv)

        with output_csv.open() as f:
            reader = csv.DictReader(f)
            for leaked in ("risk_score", "fusion_calibrated_risk",
                           "fusion_posterior_risk", "fusion_prior_risk",
                           "fusion_verdict_ordinal"):
                assert leaked not in reader.fieldnames, \
                    f"Leakage feature found in CSV: {leaked}"

    @pytest.mark.asyncio
    async def test_empty_directory_returns_zero(self, tmp_path, output_csv):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        count = await builder.build(empty_dir, output_csv)
        assert count == 0

    @pytest.mark.asyncio
    async def test_ingest_failure_skips_row(self, tmp_input, output_csv):
        svc = MagicMock()
        svc.ingest = AsyncMock(side_effect=RuntimeError("pipeline error"))
        builder = DatasetBuilder(svc)
        count = await builder.build(tmp_input, output_csv)
        assert count == 0
        with output_csv.open() as f:
            rows = list(csv.DictReader(f))
        assert rows == []

    @pytest.mark.asyncio
    async def test_output_directory_created_automatically(self, tmp_input, tmp_path):
        nested_csv = tmp_path / "a" / "b" / "c" / "dataset.csv"
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        await builder.build(tmp_input, nested_csv)
        assert nested_csv.exists()

    @pytest.mark.asyncio
    async def test_csv_validation_passes_after_build(self, tmp_input, output_csv):
        """_validate_csv must not raise for a correctly built CSV."""
        svc = _make_service(_make_context())
        builder = DatasetBuilder(svc)
        # build() calls _validate_csv internally; if it raises the test fails
        count = await builder.build(tmp_input, output_csv)
        assert count == 2
