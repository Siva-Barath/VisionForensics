# VisionForensics AI

**Intelligent Document Tampering Detection and Forensic Analysis Platform**

VisionForensics AI detects visual evidence of digital tampering in uploaded documents using Computer Vision, Image Forensics, OCR, Metadata Analysis, and Machine Learning — without relying on any external verification authority.

---

## Architecture

```
VisionForensics AI
├── backend/
│   ├── app/
│   │   ├── api/                  HTTP adapters only — no business logic
│   │   │   ├── health.py
│   │   │   └── upload.py
│   │   ├── config/               Pydantic-settings + .env
│   │   ├── core/                 Logging, exceptions, constants
│   │   ├── database/             SQLAlchemy session + base
│   │   ├── models/               ORM models
│   │   ├── schemas/              Pydantic request/response schemas
│   │   ├── detectors/            Forensic detector abstraction
│   │   │   ├── base_detector.py  BaseDetector ABC
│   │   │   └── registry.py       DetectorRegistry
│   │   ├── pipeline/             ★ Core pipeline engine
│   │   │   ├── context.py        AnalysisContext — shared state object
│   │   │   ├── base_stage.py     BaseStage ABC
│   │   │   ├── stage_result.py   StageResult — structured stage output
│   │   │   ├── artifact.py       Artifact — generated file descriptor
│   │   │   ├── config.py         PipelineConfig — stage enable/disable
│   │   │   ├── registry.py       PipelineRegistry
│   │   │   ├── pipeline.py       PipelineManager
│   │   │   └── stages/           One file per pipeline stage
│   │   │       ├── upload_stage.py
│   │   │       ├── preprocessing_stage.py
│   │   │       ├── ocr_stage.py
│   │   │       ├── classification_stage.py
│   │   │       │   ├── DocumentClassificationStage (Predicts DocumentType)
│   │   │       │   ├── DocumentProfileRegistry
│   │   │       │   ├── OCRFeatureExtractor
│   │   │       │   ├── LayoutFeatureExtractor
│   │   │       │   ├── ImageFeatureExtractor
│   │   │       │   ├── RuleClassifier (Yields Evidence/Explanation)
│   │   │       │   ├── ScoreAggregator (Normalizes Top-3)
│   │   │       │   └── ConfidenceEstimator
│   │   │       ├── metadata_stage.py     (Phase 2 placeholder)
│   │   │       ├── forgery_stage.py      (Phase 3 placeholder)
│   │   │       ├── risk_stage.py         (Phase 4 placeholder)
│   │   │       ├── explainability_stage.py (Phase 5 placeholder)
│   │   │       └── report_stage.py       (Phase 5 placeholder)
│   │   ├── services/             Business logic layer
│   │   │   ├── document_service.py   Orchestrates ingestion
│   │   │   ├── storage_service.py    All filesystem I/O
│   │   │   ├── pdf_service.py        PDF → image conversion
│   │   │   └── preprocessing/        ★ Image preprocessing subsystem
│   │   │       ├── preprocessor.py       PreprocessingService
│   │   │       ├── quality_analyzer.py   QualityAnalyzer
│   │   │       ├── decision_engine.py    DecisionEngine
│   │   │       ├── artifact_manager.py   ArtifactManager
│   │   │       ├── models.py             QualityMetrics, PreprocessingSummary
│   │   │       ├── pdf_converter.py      PDF → image utility
│   │   │       └── operations/
│   │   │           ├── base_operation.py BaseOperation ABC
│   │   │           ├── registry.py       OperationRegistry
│   │   │           ├── deskew.py
│   │   │           ├── perspective.py
│   │   │           ├── denoise.py
│   │   │           ├── contrast.py
│   │   │           ├── shadow.py
│   │   │           └── normalize.py
│   │   └── utils/                Pure helper functions only
│   ├── uploads/
│   ├── processed/
│   ├── reports/
│   ├── heatmaps/
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
│
└── frontend/                     React + TypeScript + Vite + Tailwind
    └── src/
        ├── components/
        ├── pages/
        ├── layouts/
        ├── services/
        ├── types/
        └── utils/
```

---

## Dependency Flow

```
HTTP Request
    │
    ▼
API Route (upload.py)          ← pure HTTP adapter, no business logic
    │
    ▼
DocumentService                ← validates, builds context, runs pipeline
    │
    ▼
PipelineManager                ← executes stages sequentially
    │
    ├── UploadStage             → StorageService (filesystem I/O)
    ├── PreprocessingStage      → PDFService (pdf2image)
    ├── OCRStage                (Phase 2)
    ├── MetadataStage           (Phase 2)
    ├── ForgeryStage            (Phase 3)
    ├── RiskStage               (Phase 4)
    ├── ExplainabilityStage     (Phase 5)
    └── ReportStage             (Phase 5)
    │
    ▼
AnalysisContext                ← single shared state object, returned to API
    │
    ▼
UploadResponse (JSON)
```

---

## AnalysisContext

`AnalysisContext` is the central data object that flows through every pipeline stage.
Every stage reads its inputs from the context and writes its outputs back to it.
No stage passes data directly to another stage.

Key fields:

| Field | Set by | Description |
|---|---|---|
| `document_id` | Created at ingestion | Unique document identifier |
| `job_id` | Created at ingestion | Unique job identifier for async tracking |
| `file_type` | DocumentService | pdf / png / jpeg |
| `stored_path` | UploadStage | Path to the raw uploaded file |
| `page_images` | PreprocessingStage | Paths to per-page PNG images |
| `ocr_result` | OCRStage (Phase 2) | Extracted text per page |
| `metadata` | MetadataStage (Phase 2) | EXIF/XMP metadata |
| `copy_move_result` | ForgeryStage (Phase 3) | Copy-move detection output |
| `risk_score` | RiskStage (Phase 4) | 0.0–1.0 confidence score |
| `heatmap_paths` | ExplainabilityStage (Phase 5) | Heatmap image paths |
| `report_path` | ReportStage (Phase 5) | Path to generated PDF report |
| `warnings` | Any stage | Non-fatal issues |
| `errors` | PipelineManager | Stage name → error message |
| `pipeline_status` | PipelineManager | pending/running/completed/failed/partial |
| `stage_results` | PipelineManager | Ordered list of StageResult objects |
| `artifacts` | Any stage | All generated files, keyed by Artifact.id |

---

## StageResult

Every stage returns a `StageResult` from its `run()` method. `PipelineManager` collects these into `AnalysisContext.stage_results`. The Risk Engine and Report Generator consume `StageResult` objects directly, keeping them decoupled from individual stage implementations.

| Field | Description |
|---|---|
| `stage_name` | Name of the stage that produced this result |
| `status` | `success` \| `skipped` \| `failed` |
| `execution_time_ms` | Wall-clock time for this stage |
| `confidence` | Optional 0.0–1.0 score (forensic stages only) |
| `artifact_ids` | IDs of `Artifact` objects registered on the context |
| `metadata` | Stage-specific structured output (key-value) |
| `warnings` | Non-fatal issues raised during execution |
| `errors` | Error messages if the stage failed |

Convenience constructors: `StageResult.success()`, `StageResult.skipped()`, `StageResult.failed()`.

---

## Artifact

Every file generated during pipeline execution is registered as an `Artifact` on `AnalysisContext` instead of scattering raw paths across fields. This gives the Report Generator and Risk Engine a uniform, typed view of all pipeline outputs.

| Field | Description |
|---|---|
| `id` | UUID — used to cross-reference from `StageResult.artifact_ids` |
| `type` | Semantic type: `original_upload`, `page_image`, `heatmap`, `ela_image`, `report`, … |
| `path` | Filesystem path to the generated file |
| `mime_type` | MIME type of the file |
| `created_by_stage` | Name of the stage that produced this artifact |
| `page_index` | 0-based page index, or `None` for document-level artifacts |

Query artifacts via `context.get_artifact_by_type("page_image")`.

---

## PipelineConfig

`PipelineConfig` controls which stages are active at runtime without changing any stage or service code.

```python
# All stages enabled (default)
PipelineConfig.full()

# Only ingest and store
PipelineConfig(enabled_stages=["upload", "preprocessing"])
```

Disabled stages are recorded as `StageResult.skipped()` on the context so consumers always have a complete picture.

---

## Detector Abstraction

Forensic algorithms are implemented as `BaseDetector` subclasses registered with `DetectorRegistry`. `ForgeryStage` calls `registry.get_detectors()` and iterates — it never imports a concrete detector class.

```python
class MyDetector(BaseDetector):
    name = "my_detector"
    supported_document_types = ["invoice"]  # empty = all types

    async def run(self, page_images, context_metadata) -> dict:
        ...

    def confidence(self, findings) -> float:
        ...
```

Register in `app/__init__.py`:

```python
_detector_registry.register(MyDetector())
```

`get_detectors(document_type)` filters by `supported_document_types` automatically.

---

## PipelineManager

`PipelineManager` accepts a `PipelineRegistry` and a `PipelineConfig`. It executes enabled stages in registration order, collecting a `StageResult` from each.

- **StageError** (recoverable): result recorded as `failed`, pipeline continues
- **PipelineError** (unrecoverable): pipeline halts, partial context returned
- Skipped stages produce a `StageResult` with `status="skipped"`
- Every stage transition is logged with duration
- Total execution time is recorded on the context

---

## How to Add a New Forensic Stage

1. Create `app/pipeline/stages/my_stage.py`:

```python
from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult

class MyStage(BaseStage):
    name = "my_stage"

    async def run(self, context: AnalysisContext) -> StageResult:
        context.my_result = run_my_analysis(context.page_images)
        return StageResult.success(self.name)
```

2. Add the result field to `AnalysisContext` in `pipeline/context.py`

3. Register the stage in `app/__init__.py`:

```python
_registry.register(MyStage())
```

That's it. No other file needs to change.

---

## Preprocessing Architecture

The preprocessing subsystem sits inside `PreprocessingStage` and is driven by `PreprocessingService`. It runs after PDF-to-image conversion and before OCR and forensic analysis.

```
PreprocessingStage
    │
    ▼
PreprocessingService          ← orchestrates per-page flow
    │
    ├── QualityAnalyzer       ← measures image quality (no modification)
    │       └── QualityMetrics
    │
    ├── DecisionEngine        ← selects operations from QualityMetrics
    │       └── OperationRegistry
    │
    ├── BaseOperation.run()   ← executes each selected operation
    │       ├── DeskewOperation
    │       ├── PerspectiveCorrectionOperation
    │       ├── DenoiseOperation
    │       ├── ContrastEnhancementOperation
    │       ├── ShadowRemovalOperation
    │       └── NormalizationOperation
    │
    └── ArtifactManager       ← saves result + registers Artifact
            └── preprocessed_image Artifact → AnalysisContext
```

### Quality Analysis

`QualityAnalyzer.analyze(image)` computes the following metrics without modifying the image:

| Metric | Method | Notes |
|---|---|---|
| `width`, `height` | `image.shape` | Pixels |
| `aspect_ratio` | `width / height` | |
| `color_channels` | `image.ndim` | 1 = gray, 3 = BGR |
| `brightness` | `np.mean(gray)` | 0–255 |
| `contrast` | `np.std(gray)` | Standard deviation |
| `blur_score` | Laplacian variance | Higher = sharper |
| `orientation` | — | Phase 3 placeholder |
| `skew_angle` | — | Phase 3 placeholder |

Results are stored in `AnalysisContext.quality_metrics` (one entry per page).

### Decision Engine

`DecisionEngine.select(metrics)` applies threshold rules to return an ordered list of operations:

| Condition | Operation selected |
|---|---|
| `blur_score < 100` | `denoise` |
| `contrast < 40` or `brightness < 50` | `contrast` |
| `brightness > 210` | `normalize` |
| `skew_angle > 0.5°` (Phase 3) | `deskew` |
| Any operation selected | `normalize` appended last |

The engine resolves operation names through `OperationRegistry` — it never instantiates operation classes directly.

### Operation Lifecycle

Every operation follows this lifecycle when `BaseOperation.run()` is called:

1. Check `enabled` flag — skip with warning if False
2. Call `validate(image)` — skip with warning if pre-conditions fail
3. Log `Operation started`
4. Call `execute(image, context)` — returns processed image
5. Log `Operation completed` with duration

`PreprocessingService` calls `run()` — never `execute()` directly.

### How to Add a Preprocessing Operation

1. Create `app/services/preprocessing/operations/my_op.py`:

```python
from app.services.preprocessing.operations.base_operation import BaseOperation

class MyOperation(BaseOperation):
    name = "my_op"
    description = "Does something useful."

    def execute(self, image, context, **kwargs):
        # transform image here
        return image
```

2. Register it in `operations/__init__.py`:

```python
registry.register(MyOperation())
```

3. Add a threshold rule in `DecisionEngine.select()` if it should be auto-selected.

That's it. No other file needs to change.

---

## OCR Architecture (Phase 3)

The OCR subsystem extracts text, confidence bounds, and structure from preprocessed images.

```
OCRStage
    │
OCRService
    │───► EngineSelector (Selects backend engine dynamically)
    │       │── EasyOCREngine (BaseEngine)
    │       │── TesseractEngine (BaseEngine)
    │       └── PaddleOCREngine (BaseEngine)
    │
    │───► PostProcessor (Cleans unicode and formats blocks)
    │
    └───► ConfidenceAnalyzer (Metrics and bounding box flagging)
            │
            └──► OCRResult -> AnalysisContext.ocr_result & ocr_summary
```

### Extending OCR
All OCR outputs are standardized into unified data models (`OCRWord`, `OCRLine`, `OCRBlock`, `OCRPage`).
To add a new OCR library:
1. Subclass `BaseEngine` in `app/services/ocr/engines/`.
2. Register it inside `EngineSelector._register_defaults()`.
3. The rest of the pipeline handles parsing, standardization, and analytics natively.

---

## Document Layout Analysis (Phase 4)

Transforms raw OCR outputs into a rich semantic representation (`StructuredDocument`).

```
LayoutAnalysisStage
    │
LayoutService
    │───► ReadingOrderResolver (Resolves column structure)
    │───► BlockGrouper (Paragraph merging via geometry)
    │───► TableDetector (Grid modeling)
    │───► FieldExtractor (Regex/Rule-based KV extraction)
    │───► StructureBuilder (Aggregates models)
    └───► LayoutValidator (Validates outputs)
            │
            └──► StructuredDocument -> AnalysisContext
```

### Models & Enums
- `DocumentType`: Future support for targeted extraction (`MARKSHEET`, `PASSPORT`, `ID_CARD`, etc.)
- `RegionType`: Used for explainability (`HEADER`, `TABLE`, `SIGNATURE`, `LOGO`, etc.)
- `StructuredDocument`: Contains lists of sections, fields, and tables ready for final reporting.

---

## Forgery Detection (Phase 5)

An extensible, rule-based framework that aggregates forensic evidence from multiple independent detectors.

```
ForgeryDetectionStage
    │
ForgeryService
    │───► DetectorRegistry
    │       │── MetadataDetector (Timestamps, Software)
    │       │── ImageArtifactDetector (Orchestrator for CV Analyzers)
    │       │     ├── BlurAnalyzer (Variance of Laplacian)
    │       │     ├── NoiseAnalyzer (MAD Noise Estimation)
    │       │     ├── ELAAnalyzer (JPEG Error Level Analysis)
    │       │     ├── EdgeAnalyzer (Canny Edge Density)
    │       │     ├── IlluminationAnalyzer (Lighting Gradients)
    │       │     ├── CompressionAnalyzer (JPEG Artifacts)
    │       │     └── EntropyAnalyzer (Local Texture Complexity)
    │       │── OCRConsistencyDetector (Confidence, Kerning)
    │       │── LayoutConsistencyDetector (Overlap, Duplicates)
    │       │── FieldConsistencyDetector (Conflicting Values)
    │       │── SignatureRegionAnalyzer (Orchestrator for CV Signature Analysis)
    │       │     ├── SignatureValidator
    │       │     ├── StrokeAnalyzer
    │       │     ├── ContourAnalyzer
    │       │     ├── InkDensityAnalyzer
    │       │     ├── SkeletonAnalyzer
    │       │     ├── ConnectedComponentAnalyzer
    │       │     ├── GeometricAnalyzer
    │       │     └── SignatureQualityAnalyzer
    │       │── CopyMoveRegionAnalyzer (Orchestrator for Copy-Move Detection)
    │       │     ├── ORBFeatureAnalyzer
    │       │     ├── AKAZEFeatureAnalyzer
    │       │     ├── DescriptorMatcher
    │       │     ├── TranslationPatternAnalyzer
    │       │     ├── GeometricConsistencyAnalyzer
    │       │     ├── DuplicateRegionClusterer
    │       │     ├── FalsePositiveFilter
    │       │     └── CopyMoveConfidenceEstimator
    │       └── LogoRegionAnalyzer (Placeholder for ML)
    │
    │───► EvidenceFusionStage
    │       │── EvidenceFusionService (Deterministic Bayesian Aggregation)
    │       │     ├── EvidenceNormalizer
    │       │     ├── WeightManager (Sensitivity Profiles)
    │       │     ├── DependencyGraph (Propagates penalties e.g. Blur -> OCR)
    │       │     ├── CorrelationAnalyzer
    │       │     ├── ConflictResolver
    │       │     ├── ConfidenceCalibrator
    │       │     ├── BayesianRiskEstimator (Decision Trace Generation)
    │       │     ├── VerdictGenerator
    │       │     └── RecommendationEngine
    │
    │───► ReportGenerationStage
    │       ├── ReportGenerationService
    │       ├── TechnicalAppendixBuilder (Integrity, Chain of Custody)
    │       ├── TraceabilityMatrix
    │       ├── ReportValidator
    │       └── ArchiveBuilder (PDF, HTML, JSON, CSV)
    │
    │───► EvaluationRunner (Phase 15: Benchmarking & Production Readiness)
    │       ├── MetricsCalculator (Cross-Document Evaluation)
    │       ├── AblationRunner & RobustnessTester
    │       ├── RegressionManager & FailureAnalyzer
    │       └── DeploymentValidator (Readiness Score)
    │
    │───► VisualEvidenceCollector (Bounding box aggregation)
    │───► EvidenceAggregator (Deduplication, Summaries)
    └───► RiskEstimator (Configurable Weighted Scoring)
            │
            └──► ForgeryReport -> AnalysisContext
```

### Adding New Detectors
The framework is completely decoupled. To add a new ML model (e.g. Copy-Move Detection):
1. Subclass `BaseDetector`.
2. Extract evidence and yield an `Evidence` object with `source=EvidenceSource.ML_MODEL`.
3. Register it in `ForgeryDetectionStage` using `registry.register(MyNewDetector())`.
4. The `ForgeryService` will automatically execute it, aggregate its evidence, and weight it in the `RiskEstimator`.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ML (future) | PyTorch, OpenCV, PaddleOCR, scikit-image |
| Database | PostgreSQL + SQLAlchemy 2 |
| Storage | Local filesystem (S3-ready structure) |

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional for Phase 1)
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/) on PATH (Windows) for PDF conversion

### PaddleOCR Setup (Phase 6)

The project leverages `PaddleOCR` as its primary OCR engine. It is lazily loaded, meaning the API will not crash if you run simple non-OCR tasks without it.

To install it:

```bash
pip install paddlepaddle paddleocr
```

Supported default configurations in `PaddleOCREngine`:
- `lang`: `"en"` (can be `"ch"`, `"fr"`, etc.)
- `use_angle_cls`: `True`
- `use_gpu`: `False` (switch to True if CUDA is configured)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python main.py
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## API Reference

### GET /api/v1/health

```json
{ "status": "healthy", "version": "1.0.0", "environment": "development" }
```

### POST /api/v1/upload

Accepted: `pdf`, `png`, `jpg`, `jpeg` — Max: 20 MB

```json
{
  "job_id": "uuid",
  "document_id": "uuid",
  "filename": "stored_name.png",
  "original_filename": "my_doc.png",
  "path": "uploads/uuid_my_doc.png",
  "type": "png",
  "size_bytes": 204800,
  "status": "processed",
  "processing_status": "completed",
  "pipeline_stage": "report",
  "page_count": 1,
  "pages": ["uploads/uuid_my_doc.png"],
  "warnings": ["OCR stage is not yet implemented (Phase 2)", "..."],
  "processing_time_ms": 12.4
}
```

---

## Running Tests

```bash
cd backend
pytest
```

---

## Future Roadmap

| Phase | Feature |
|---|---|
| 2 | OCR (EasyOCR), Metadata analysis, DB wiring |
| 3 | Copy-move detection, ELA, splicing detection |
| 4 | Risk scoring engine, heatmap generation |
| 5 | PDF report generation, explainable AI |
| 6 | Scan history dashboard, analytics |
| 7 | Authentication, multi-user, cloud storage |
