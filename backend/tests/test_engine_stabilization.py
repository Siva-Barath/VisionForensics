"""Negative regressions. Only temporary files and injected sessions are used.

These tests never authenticate against, mutate, or tamper with the live database
or historical exhibits. Frozen artifact bytes are only read or copied to tmp_path.
"""
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, UploadFile
from starlette.requests import Request

from app.core.exhibit_integrity import require_exhibit_integrity
from app.core.exceptions import FileTooLargeError, PipelineError, StorageError, VisionForensicsError
from app.pipeline.context import AnalysisContext
from app.pipeline.stages.explainability_stage import ExplainabilityStage
from app.pipeline.stages.preprocessing_stage import PreprocessingStage
from app.services.document_service import DocumentService
from app.services.ml_inference import inference_service as inference
from app.services.preprocessing.pdf_converter import convert_pdf_to_images


ARTIFACTS = Path(__file__).resolve().parents[1] / 'app/ml/artifacts'


def test_frozen_artifact_and_exact_input_contract():
    service = inference.MLInferenceService()
    assert service.is_loaded, service.load_error
    assert list(service.model.feature_names_in_) == service.feature_preparer.active_features
    assert list(service.model.classes_) == [0, 1]
    assert hashlib.sha256(service.model_path.read_bytes()).hexdigest() == inference.FROZEN_MODEL_SHA256


@pytest.mark.parametrize('changed', ['random_forest.joblib', 'active_feature_schema.json'])
def test_tampered_artifact_rejected_before_deserialization(tmp_path, monkeypatch, changed):
    for name in ['random_forest.joblib', 'active_feature_schema.json']:
        (tmp_path / name).write_bytes((ARTIFACTS / name).read_bytes())
    target = tmp_path / changed
    if changed.endswith('.json'):
        schema = json.loads(target.read_text())
        schema['features'][0], schema['features'][1] = schema['features'][1], schema['features'][0]
        target.write_text(json.dumps(schema))
    else:
        target.write_bytes(target.read_bytes() + b'UNTRUSTED')
    load = Mock(side_effect=AssertionError('untrusted executable bytes were loaded'))
    monkeypatch.setattr(inference.joblib, 'load', load)
    service = inference.MLInferenceService(tmp_path)
    assert not service.is_loaded
    assert 'SHA-256' in service.load_error
    assert service.model is None
    load.assert_not_called()


@pytest.mark.parametrize('defect,code,state', [('missing', 410, 'MISSING'), ('digest', 409, 'UNVERIFIABLE'), ('tampered', 409, 'TAMPERED')])
def test_exhibit_access_fails_closed(tmp_path, monkeypatch, defect, code, state):
    path = tmp_path / 'original.bin'
    digest = hashlib.sha256(b'ORIGINAL').hexdigest()
    if defect != 'missing':
        path.write_bytes(b'CHANGED' if defect == 'tampered' else b'ORIGINAL')
    document = SimpleNamespace(id='controlled', file_path=str(path), sha256_hash=None if defect == 'digest' else digest)
    audit = Mock()
    monkeypatch.setattr('app.core.exhibit_integrity.AuditService.ingestion_digest', lambda *args: digest)
    monkeypatch.setattr('app.core.exhibit_integrity.AuditService.record_custody_event', audit)
    with pytest.raises(HTTPException) as error:
        require_exhibit_integrity(document, object(), 'analyst', '127.0.0.1')
    assert error.value.status_code == code
    assert audit.call_args.kwargs['status'] == state
    assert path.read_bytes() != b'' if path.exists() else True


def test_valid_original_returns_exact_bytes(tmp_path, monkeypatch):
    path = tmp_path / 'original.bin'
    path.write_bytes(b'ORIGINAL')
    doc = SimpleNamespace(id='controlled', file_path=str(path), sha256_hash=hashlib.sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr('app.core.exhibit_integrity.AuditService.ingestion_digest', lambda *args: doc.sha256_hash)
    assert require_exhibit_integrity(doc, object()).read_bytes() == b'ORIGINAL'


@pytest.mark.asyncio
@pytest.mark.parametrize('url', ['/api/v1/documents', '/api/v1/documents?token=not-accepted'])
async def test_no_anonymous_or_query_token_fallback(monkeypatch, url):
    from app.core.auth import get_current_user
    path, _, query = url.partition('?')
    request = Request({'type': 'http', 'method': 'GET', 'path': path, 'headers': [], 'query_string': query.encode()})
    repo = Mock()
    monkeypatch.setattr('app.core.auth.UserRepository', repo)
    with pytest.raises(HTTPException) as error:
        await get_current_user(request, credentials=None, db=object())
    assert error.value.status_code == 401
    repo.return_value.get_by_email.assert_not_called()
    repo.return_value.create_user.assert_not_called()


@pytest.mark.asyncio
async def test_upload_read_is_bounded():
    from app.utils.file_validator import validate_upload
    stream = SimpleNamespace(filename='oversize.png', read=AsyncMock(return_value=b'x' * 1025))
    with pytest.raises(FileTooLargeError):
        await validate_upload(stream, 1024)
    stream.read.assert_awaited_once_with(1025)


@pytest.mark.asyncio
async def test_persistence_failure_is_not_acknowledged_or_cached(tmp_path, monkeypatch):
    from app.services import document_service as module
    original = tmp_path / 'original.bin'
    original.write_bytes(b'ORIGINAL')
    context = AnalysisContext(stored_path=original)
    pipeline = SimpleNamespace(run=AsyncMock(return_value=context))
    session = Mock(side_effect=RuntimeError('controlled unavailable database'))
    service = DocumentService(pipeline, SimpleNamespace(max_file_size_bytes=1024), session_factory=session)
    monkeypatch.setattr(module, 'validate_upload', AsyncMock(return_value=(b'ORIGINAL', 'png')))
    with pytest.raises(VisionForensicsError) as error:
        await service.ingest(UploadFile(filename='test.png', file=io.BytesIO(b'ORIGINAL')))
    assert error.value.status_code == 503
    assert not service._analysis_cache
    assert original.read_bytes() == b'ORIGINAL'


def test_corrupt_pdf_never_becomes_synthetic_page(tmp_path):
    source = tmp_path / 'corrupt.pdf'
    source.write_bytes(b'%PDF-1.7\nTHIS IS NOT A RENDERABLE PDF')
    output = tmp_path / 'pages'
    with pytest.raises(StorageError):
        convert_pdf_to_images(source, output, 'controlled-corrupt')
    assert not list(output.glob('*.png'))


def test_large_pdf_raster_is_bounded(tmp_path):
    from pypdf import PdfWriter
    from PIL import Image
    source = tmp_path / 'large.pdf'
    writer = PdfWriter()
    writer.add_blank_page(width=20000, height=10000)
    with source.open('wb') as handle:
        writer.write(handle)
    pages = convert_pdf_to_images(source, tmp_path / 'pages', 'controlled-large')
    assert len(pages) == 1
    with Image.open(pages[0]) as image:
        assert max(image.size) <= 2048


@pytest.mark.asyncio
async def test_pdf_render_failure_halts_before_forensics():
    pdf = SimpleNamespace(convert=Mock(side_effect=StorageError('controlled render error')))
    preprocessor = SimpleNamespace(process=Mock())
    context = AnalysisContext(file_type='pdf', stored_path=Path('controlled.pdf'))
    with pytest.raises(PipelineError):
        await PreprocessingStage(pdf, preprocessor).run(context)
    preprocessor.process.assert_not_called()
    assert not context.page_images


@pytest.mark.parametrize('engine_name', ['EasyOCREngine', 'TesseractEngine'])
def test_unimplemented_ocr_never_fabricates_text(engine_name):
    from app.services.ocr import engines
    engine = getattr(engines, engine_name)()
    assert engine.is_available() is False
    with pytest.raises(RuntimeError):
        engine.extract_text(None)
    with pytest.raises(RuntimeError):
        engine.extract_words(None)


@pytest.mark.asyncio
@pytest.mark.parametrize('risk', [None, {}, {'unified_risk_tier': 'UNKNOWN'}])
async def test_unknown_analysis_never_explains_authenticity(risk):
    context = AnalysisContext(risk_assessment=risk)
    await ExplainabilityStage().run(context)
    assert 'insufficient' in context.explanation
    assert 'consistent with authentic' not in context.explanation


@pytest.fixture
def isolated_sessions():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.session import Base
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


def test_complete_analysis_survives_cache_miss(tmp_path, isolated_sessions):
    from app.services.context_snapshot import snapshot_context
    from app.services.preprocessing.models import QualityMetrics
    from app.pipeline.artifact import Artifact
    source = tmp_path / 'controlled-original.png'
    source.write_bytes(b'ORIGINAL')
    context = AnalysisContext(stored_path=source, original_filename=source.name, file_type='png',
                              page_count=2, page_images=['page0', 'page1'],
                              preprocessed_images=['derived0', 'derived1'])
    context.pages_ml = [{'page_index': 0, 'forgery_probability': .12}, {'page_index': 1, 'forgery_probability': .82}]
    context.ml_prediction = {'status': 'SUCCESS', 'forgery_probability': .82, 'risk_tier': 'HIGH_RISK',
                             'feature_vector': {'img_ela_max_difference_mean': 19.0}}
    context.quality_metrics = [QualityMetrics(width=100, height=200), QualityMetrics(width=300, height=400)]
    context.risk_assessment = {'unified_risk_tier': 'HIGH_RISK', 'overall_verdict': 'REVIEW'}
    context.metadata = {'fields': {'Producer': 'controlled fixture'}}
    context.compression_qualification = {'is_jpeg': False}
    context.visual_evidence = {'available': True, 'detected_clusters': 2}
    context.ocr_summary = {'status': 'UNAVAILABLE'}
    context.copy_move_features_by_page = {1: {'inlier_matches': 16}}
    context.risk_score = 82.0
    context.artifacts = [Artifact(type='original_upload', path=str(source))]
    expected = snapshot_context(context)
    writer = DocumentService(None, SimpleNamespace(), session_factory=isolated_sessions)
    writer._persist_to_database(context, hashlib.sha256(source.read_bytes()).hexdigest())
    # A fresh service has an empty cache and must rebuild from persisted state.
    reader = DocumentService(None, SimpleNamespace(), session_factory=isolated_sessions)
    restored = reader.get_context(context.document_id)
    assert snapshot_context(restored) == expected
    assert restored.analysis_version == 1
    assert restored.quality_metrics[1].width == 300


def test_ingest_transaction_rolls_back_every_record(tmp_path, isolated_sessions, monkeypatch):
    from sqlalchemy import text
    source = tmp_path / 'original.bin'
    source.write_bytes(b'ORIGINAL')
    context = AnalysisContext(stored_path=source, file_type='png')
    def fail_analysis(*args, **kwargs):
        raise RuntimeError('controlled failure after document/page/custody flush')
    monkeypatch.setattr('app.services.document_service.DocumentRepository.save_analysis', fail_analysis)
    service = DocumentService(None, SimpleNamespace(), session_factory=isolated_sessions)
    with pytest.raises(VisionForensicsError):
        service._persist_to_database(context, hashlib.sha256(source.read_bytes()).hexdigest())
    with isolated_sessions() as db:
        for table in ['documents', 'document_pages', 'analyses', 'exhibit_custody_logs']:
            assert db.execute(text('SELECT count(*) FROM ' + table)).scalar() == 0
    assert source.read_bytes() == b'ORIGINAL'


def test_report_matches_persisted_analysis_score_version_and_page_count(tmp_path, isolated_sessions, monkeypatch):
    from PIL import Image
    from pypdf import PdfReader
    from app.models.document import Document
    from app.services.report_service import ReportService
    source = tmp_path / 'controlled.png'
    Image.new('RGB', (100, 150), 'white').save(source)
    context = AnalysisContext(stored_path=source, file_type='png', original_filename=source.name,
                              page_count=1, pipeline_status='completed', document_status='processed')
    context.risk_score = 73.2
    context.risk_assessment = {'unified_risk_tier': 'HIGH_RISK', 'overall_verdict': 'REVIEW',
                               'composite_display_score': 73.2}
    context.ml_prediction = {'status': 'SUCCESS', 'forgery_probability': .732}
    document_service = DocumentService(None, SimpleNamespace(), session_factory=isolated_sessions)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    document_service._persist_to_database(context, digest)
    document_service._persist_to_database(context, digest)
    monkeypatch.setattr('app.document_service', document_service)
    service = ReportService()
    service.settings = SimpleNamespace(reports_dir=str(tmp_path / 'reports'))
    with isolated_sessions() as db:
        report = service.generate_report(db, db.get(Document, context.document_id))
        assert report.analysis_version == 2
        assert report.metadata_snapshot['composite_risk_score'] == 73.2
        pdf_bytes = Path(report.file_path).read_bytes()
        assert hashlib.sha256(pdf_bytes).hexdigest() == report.sha256_hash
        assert len(PdfReader(io.BytesIO(pdf_bytes)).pages) == report.page_count


def test_authorization_filter_precedes_pagination(isolated_sessions):
    from app.repositories.document_repository import DocumentRepository
    with isolated_sessions() as db:
        repo = DocumentRepository(db)
        repo.save_document('owned', 'owned.png', 'owned.png', 'owned.png', 'png', 10, uploader_id='analyst-a')
        repo.save_document('other-newer', 'other.png', 'other.png', 'other.png', 'png', 10, uploader_id='analyst-b')
        user = SimpleNamespace(id='analyst-a', role='FORENSIC_ANALYST')
        assert [doc.id for doc in repo.list_documents(limit=1, user=user)] == ['owned']
        assert repo.list_documents(skip=1, limit=1, user=user) == []


@pytest.mark.asyncio
async def test_health_does_not_claim_failed_database_or_model_is_healthy(tmp_path, monkeypatch):
    from fastapi import Response
    from app.api.health import health_check
    monkeypatch.setattr('app.api.health.get_settings', lambda: SimpleNamespace(
        upload_dir=str(tmp_path), processed_dir=str(tmp_path), app_env='test'))
    monkeypatch.setattr('app.services.ml_inference.MLInferenceService', lambda: SimpleNamespace(is_loaded=False))
    selector = Mock()
    selector.get_engine.side_effect = RuntimeError('optional adapter unavailable')
    monkeypatch.setattr('app.services.ocr.engine_selector.EngineSelector', lambda: selector)
    db = SimpleNamespace(execute=Mock(side_effect=RuntimeError('connection secret must not be exposed')))
    response = Response()
    health = await health_check(response, db)
    assert response.status_code == 503
    assert health.status == 'degraded'
    assert health.modules['database']['status'] == 'error'
    assert health.modules['ml_engine']['status'] == 'error'
    assert health.modules['ml_engine']['integrity_verified'] is False
    assert 'secret' not in health.model_dump_json()


@pytest.mark.asyncio
async def test_raw_ml_survives_jpeg_heuristic_without_policy_change():
    from PIL import Image
    from app.services.ml_inference.models import MLPredictionResult, InferenceStatus, RiskTier
    from app.pipeline.stages.ml_inference_stage import MLInferenceStage
    from app.pipeline.stages.risk_stage import RiskStage
    buffer = io.BytesIO()
    Image.new('RGB', (64, 64), 'white').save(buffer, format='JPEG', quality=20)
    prediction = MLPredictionResult(status=InferenceStatus.SUCCESS, forgery_probability=.42,
        predicted_class='FORGED', risk_tier=RiskTier.SUSPICIOUS, risk_description='controlled', operational_threshold=.40)
    service = SimpleNamespace(predict_page=lambda *a, **k: prediction.model_copy(deep=True),
                              predict=lambda *a, **k: prediction.model_copy(deep=True))
    context = AnalysisContext(file_type='jpeg', file_bytes=buffer.getvalue())
    await MLInferenceStage(service).run(context)
    await RiskStage().run(context)
    assert context.raw_ml_prediction['predicted_class'] == 'FORGED'
    assert context.raw_ml_prediction['forgery_probability'] == .42
    assert context.raw_ml_prediction['operational_threshold'] == .40
    assert context.raw_ml_prediction['is_document_probability'] is False
    assert context.ml_prediction['predicted_class'] == 'AUTHENTIC'
    assert context.risk_assessment['unified_risk_tier'] == 'SUSPICIOUS'


@pytest.mark.asyncio
async def test_raw_max_page_selection_is_explicit_and_unmodified():
    from app.services.ml_inference.models import MLPredictionResult, InferenceStatus, RiskTier
    from app.pipeline.stages.ml_inference_stage import MLInferenceStage
    def predict_page(context, page_index, **kwargs):
        probability = [.12, .42][page_index]
        return MLPredictionResult(status=InferenceStatus.SUCCESS, forgery_probability=probability,
            predicted_class='FORGED' if probability >= .40 else 'AUTHENTIC',
            risk_tier=RiskTier.SUSPICIOUS, risk_description='controlled', operational_threshold=.40)
    context = AnalysisContext(file_type='pdf', page_count=2)
    await MLInferenceStage(SimpleNamespace(predict_page=predict_page)).run(context)
    assert context.raw_ml_prediction['source_page_index'] == 1
    assert context.raw_ml_prediction['selection_method'] == 'maximum_page_probability'
    assert context.raw_ml_prediction['predicted_class'] == 'FORGED'
    assert context.ml_prediction['predicted_class'] == 'AUTHENTIC'
    assert context.raw_ml_prediction['is_document_probability'] is False


def test_cases_and_totals_are_real_and_scoped(isolated_sessions):
    from app.api.cases import create_case, get_case, workspace_stats, CaseInput
    from app.repositories.document_repository import DocumentRepository
    user = SimpleNamespace(id='analyst-a', role='FORENSIC_ANALYST')
    other = SimpleNamespace(id='analyst-b', role='FORENSIC_ANALYST')
    with isolated_sessions() as db:
        case = create_case(CaseInput(title='Controlled case', notes='Controlled notes', priority='urgent'), user, db)
        assert case['priority'] == 'URGENT'
        assert get_case(case['id'], user, db)['notes'] == 'Controlled notes'
        with pytest.raises(HTTPException):
            get_case(case['id'], other, db)
        repo = DocumentRepository(db)
        for idx in range(120):
            repo.save_document(str(idx), 'sample.png', 'sample.png', 'sample.png', 'png', 10,
                               case_id=case['id'], uploader_id=user.id, status='processed')
        assert workspace_stats(user, db)['total_cases'] == 1
        assert workspace_stats(user, db)['total_documents'] == 120
        assert workspace_stats(user, db)['examined_documents'] == 120
        assert workspace_stats(other, db)['total_documents'] == 0


def test_upload_case_details_share_the_exhibit_transaction(tmp_path, isolated_sessions):
    from app.models.document import Document
    from app.models.case import Case
    source = tmp_path / 'original.bin'
    source.write_bytes(b'ORIGINAL')
    context = AnalysisContext(stored_path=source, file_type='png')
    service = DocumentService(None, SimpleNamespace(), session_factory=isolated_sessions)
    service._persist_to_database(context, hashlib.sha256(source.read_bytes()).hexdigest(), uploader_id='analyst-a',
                                case_details={'title': 'Case from intake', 'notes': 'Retained notes', 'priority': 'urgent'})
    with isolated_sessions() as db:
        document = db.get(Document, context.document_id)
        case = db.get(Case, document.case_id)
        assert case.title == 'Case from intake'
        assert case.description == 'Retained notes'
        assert case.lead_investigator_id == 'analyst-a'


def test_mutable_document_hash_cannot_replace_ingestion_anchor(tmp_path, monkeypatch):
    path = tmp_path / 'changed.bin'
    path.write_bytes(b'CHANGED')
    doc = SimpleNamespace(id='controlled', file_path=str(path), sha256_hash=hashlib.sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr('app.core.exhibit_integrity.AuditService.ingestion_digest', lambda *args: hashlib.sha256(b'ORIGINAL').hexdigest())
    monkeypatch.setattr('app.core.exhibit_integrity.AuditService.record_custody_event', Mock())
    with pytest.raises(HTTPException) as error:
        require_exhibit_integrity(doc, object())
    assert error.value.status_code == 409
    assert 'TAMPERING_ALARM' in error.value.detail


def test_real_ela_map_is_derived_and_hashed(tmp_path, monkeypatch):
    from PIL import Image, ImageDraw
    from app.services.forensics.image_artifact_detector import ImageArtifactDetector
    source = tmp_path / 'controlled.png'
    image = Image.new('RGB', (200, 160), 'white')
    ImageDraw.Draw(image).rectangle((20, 20, 80, 80), fill=(30, 75, 115))
    image.save(source)
    original = source.read_bytes()
    monkeypatch.setattr('app.services.forensics.image_artifact_detector.get_settings', lambda: SimpleNamespace(heatmaps_dir=str(tmp_path / 'heatmaps')))
    context = AnalysisContext(stored_path=source, preprocessed_images=[str(source)])
    ImageArtifactDetector().detect(context)
    artifact = next(item for item in context.artifacts if item.type == 'ela_heatmap')
    content = Path(artifact.path).read_bytes()
    assert hashlib.sha256(content).hexdigest() == artifact.sha256_hash
    assert source.read_bytes() == original
    with Image.open(io.BytesIO(content)) as heatmap:
        assert heatmap.size == image.size
        assert heatmap.format == 'PNG'


@pytest.mark.asyncio
async def test_changed_derived_heatmap_is_not_served(tmp_path, monkeypatch):
    from app.api.documents import get_ela_heatmap
    from app.pipeline.artifact import Artifact
    source = tmp_path / 'original.bin'
    source.write_bytes(b'ORIGINAL')
    derived = tmp_path / 'heatmap.png'
    derived.write_bytes(b'CHANGED')
    context = AnalysisContext(artifacts=[Artifact(type='ela_heatmap', path=str(derived), page_index=0,
        sha256_hash=hashlib.sha256(b'EXPECTED MAP').hexdigest())])
    monkeypatch.setattr('app.api.documents.check_document_access', lambda *args: SimpleNamespace(id='controlled'))
    monkeypatch.setattr('app.api.documents.require_exhibit_integrity', lambda *args: source)
    monkeypatch.setattr('app.document_service', SimpleNamespace(get_context=lambda *args: context))
    request = Request({'type': 'http', 'method': 'GET', 'path': '/', 'headers': [], 'query_string': b'', 'client': ('127.0.0.1', 1)})
    with pytest.raises(HTTPException) as error:
        await get_ela_heatmap('controlled', request, 0, SimpleNamespace(id='analyst'), object())
    assert error.value.status_code == 409
    assert source.read_bytes() == b'ORIGINAL'
