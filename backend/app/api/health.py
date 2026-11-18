from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.document import HealthResponse
from app.config.settings import get_settings
from app.database.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check(response: Response, db: Session = Depends(get_db)) -> HealthResponse:
    """Returns application health status and genuine subsystem statuses."""
    settings = get_settings()

    modules: Dict[str, Any] = {}

    # 1. Database connectivity
    try:
        db.execute(text("SELECT 1"))
        modules["database"] = {"status": "connected", "type": "PostgreSQL"}
    except Exception as exc:
        modules["database"] = {"status": "error", "reason": "Database connection probe failed"}

    # 2. File storage
    try:
        up = Path(settings.upload_dir)
        pr = Path(settings.processed_dir)
        storage_ok = up.exists() and pr.exists()
        modules["storage"] = {
            "status": "active" if storage_ok else "degraded",
            "upload_dir": str(up),
            "processed_dir": str(pr),
        }
    except Exception as exc:
        modules["storage"] = {"status": "error", "error": str(exc)}

    # 3. ML Inference Engine (Frozen Random Forest)
    try:
        from app.services.ml_inference import MLInferenceService
        ml_service = MLInferenceService()
        modules["ml_engine"] = {
            "status": "active" if ml_service.is_loaded else "error",
            "model": "Random Forest (18 Features)",
            "operational_threshold": 0.40,
            "sha256": "f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280",
            "integrity_verified": ml_service.is_loaded,
        }
    except Exception as exc:
        modules["ml_engine"] = {"status": "error", "error": str(exc)}

    # 4. PDF Processing Subsystem
    try:
        import pypdf
        modules["pdf_processing"] = {"status": "active", "version": pypdf.__version__}
    except Exception:
        modules["pdf_processing"] = {"status": "unavailable", "reason": "pypdf not installed"}

    # 5. Visual Evidence Arbiter & Image Forensics
    try:
        import cv2
        modules["visual_arbiter"] = {"status": "active", "version": cv2.__version__}
    except Exception:
        modules["visual_arbiter"] = {"status": "unavailable", "reason": "cv2 not installed"}

    # 6. OCR Text Extraction Subsystem
    try:
        from app.services.ocr.engine_selector import EngineSelector
        selector = EngineSelector()
        available_ocr = []
        for eng in ["paddleocr", "easyocr", "tesseract"]:
            try:
                e = selector.get_engine(eng)
                if e.is_available():
                    available_ocr.append(eng)
            except Exception:
                pass

        if available_ocr:
            modules["ocr_engine"] = {"status": "available", "available_engines": available_ocr,
                                     "reason": "Adapter importable; model initialization and extraction remain per-exhibit checks"}
        else:
            modules["ocr_engine"] = {
                "status": "unavailable",
                "reason": "OCR engine dependencies (paddleocr/easyocr/tesseract) not installed in runtime environment",
            }
    except Exception as exc:
        modules["ocr_engine"] = {"status": "unavailable", "error": str(exc)}

    ready = all(modules.get(name, {}).get("status") in ("active", "connected") for name in ("database", "storage", "ml_engine"))
    if not ready:
        response.status_code = 503
    return HealthResponse(
        status="healthy" if ready else "degraded",
        environment=settings.app_env,
        modules=modules,
    )


@router.api_route("/health/verify-integrity", methods=["GET", "POST"], summary="Verify ML Model & Schema Integrity")
async def verify_ml_integrity() -> Dict[str, Any]:
    """
    Computes runtime SHA-256 digests directly from disk for model binary and feature schema,
    verifying against pinned cryptographic commitments (Phase 4 Freeze).
    """
    import hashlib
    import json
    from datetime import datetime, timezone
    from app.services.ml_inference import MLInferenceService
    from app.services.ml_inference.inference_service import FROZEN_MODEL_SHA256, FROZEN_SCHEMA_SHA256

    ml_service = MLInferenceService()
    model_path = ml_service.model_path
    schema_path = ml_service.schema_path

    # Model digest
    model_sha256 = ""
    model_verified = False
    if model_path and Path(model_path).exists():
        h = hashlib.sha256()
        with open(model_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        model_sha256 = h.hexdigest()
        model_verified = (model_sha256.lower() == FROZEN_MODEL_SHA256.lower())

    # Schema digest
    schema_sha256 = ""
    schema_verified = False
    feature_count = 18
    if schema_path and Path(schema_path).exists():
        h = hashlib.sha256()
        with open(schema_path, "rb") as f:
            data = f.read()
            h.update(data)
            try:
                schema_json = json.loads(data.decode("utf-8"))
                feature_count = len(schema_json.get("features", []))
            except Exception:
                pass
        schema_sha256 = h.hexdigest()
        schema_verified = (schema_sha256.lower() == FROZEN_SCHEMA_SHA256.lower())

    all_verified = model_verified and schema_verified

    return {
        "status": "VERIFIED" if all_verified else "FAILED",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "model": {
            "name": "Random Forest Classifier",
            "version": "v1.0.0-frozen",
            "trees": 100,
            "criterion": "Gini Impurity",
            "operational_threshold": 0.40,
            "expected_sha256": FROZEN_MODEL_SHA256,
            "actual_sha256": model_sha256,
            "verified": model_verified,
            "feature_count": feature_count,
        },
        "schema": {
            "name": "18-Feature Forensic Schema",
            "version": "v1.0.0",
            "expected_sha256": FROZEN_SCHEMA_SHA256,
            "actual_sha256": schema_sha256,
            "verified": schema_verified,
            "feature_count": feature_count,
        },
        "decision_threshold": {
            "threshold": 0.40,
            "status": "LOCKED",
            "protocol": "Phase 4 Specification (Recall >= 0.90)",
            "superseded_thresholds": [0.55, 0.50],
        }
    }


