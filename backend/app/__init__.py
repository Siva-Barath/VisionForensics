"""
VisionForensics AI — application factory and composition root.

This is the only place where concrete service instances are created and
wired together. Every other module receives its dependencies via injection.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.exceptions import register_exception_handlers

# Services
from app.services.storage_service import StorageService
from app.services.pdf_service import PDFService
from app.services.document_service import DocumentService
from app.services.preprocessing.preprocessor import PreprocessingService
from app.services.ml_inference import MLInferenceService

# Pipeline
from app.pipeline.registry import PipelineRegistry
from app.pipeline.pipeline import PipelineManager
from app.pipeline.config import PipelineConfig
from app.pipeline.stages import (
    UploadStage,
    PreprocessingStage,
    OCRStage,
    MetadataStage,
    ForgeryDetectionStage,
    DocumentClassificationStage,
    MLInferenceStage,
    RiskStage,
    ExplainabilityStage,
    ReportStage,
    LayoutAnalysisStage,
)
from app.pipeline.stages.evidence_fusion_stage import EvidenceFusionStage

configure_logging()
logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Module-level singletons — created once, shared across requests     #
# ------------------------------------------------------------------ #
_settings = get_settings()
_storage_service = StorageService(_settings)
_pdf_service = PDFService(_storage_service)
_preprocessing_service = PreprocessingService(
    output_dir=Path(_settings.processed_dir),
)
_ml_inference_service = MLInferenceService()

_registry = PipelineRegistry()
_registry.register(UploadStage(_storage_service))
_registry.register(PreprocessingStage(_pdf_service, _preprocessing_service))
_registry.register(OCRStage())
_registry.register(LayoutAnalysisStage())
_registry.register(MetadataStage())
_registry.register(ForgeryDetectionStage())
_registry.register(DocumentClassificationStage())
_registry.register(MLInferenceStage(_ml_inference_service, operational_threshold=0.40))
_registry.register(RiskStage())
_registry.register(ExplainabilityStage())
_registry.register(ReportStage())

_pipeline = PipelineManager(_registry, PipelineConfig.full())
document_service = DocumentService(_pipeline, _settings)


from app.database.session import engine
from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    _storage_service.ensure_directories()
    # Database connection probe
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
    except Exception as exc:
        logger.warning("Database connection probe failed: %s", exc)

    logger.info(
        "VisionForensics AI starting | env=%s pipeline_stages=%s",
        _settings.app_env,
        _registry.stage_names(),
    )
    yield
    logger.info("VisionForensics AI shutting down")


def create_app() -> FastAPI:
    from app.api import api_router  # local import avoids circular dependency

    app = FastAPI(
        title="VisionForensics AI",
        description="Intelligent Document Tampering Detection and Forensic Analysis Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
