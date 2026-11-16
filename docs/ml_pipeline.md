# ML Pipeline — Feature Extraction & Dataset Building

## Current Feature Count

**94 numerical features** exported across 11 groups.  
Total CSV width: **98 columns** (94 features + `document_id`, `original_filename`, `file_type`, `label`).

---

## Feature Groups

| Group | Count | Source |
|---|---|---|
| Image Metadata | 4 | `context.quality_metrics[0]` |
| Image Forensics | 9 | `context.image_forensics_metrics` (page-averaged) |
| OCR | 5 | `context.ocr_summary` |
| Layout | 3 | `context.layout_summary` |
| Classification | 2 | `context.classification_result` |
| Signature | 16 | `context.signature_features` |
| Logo (scalars + 7 Hu moments) | 22 | `context.logo_features` |
| Copy-Move | 8 | `context.copy_move_features` |
| Evidence Severity | 9 | `context.evidence_category_scores` |
| Evidence Summary | 11 | `context.forgery_report["summary"]` |
| Fusion (process scalars only) | 5 | `context.fusion_metrics` |
| **Total** | **94** | |

---

## Leakage Prevention Strategy

The following features are **permanently excluded** from the exported feature vector.
They remain on `AnalysisContext` for forensic reporting and post-inference evaluation only.

| Excluded Feature | Reason |
|---|---|
| `risk_score` | Final weighted risk decision (0–100) produced by `RiskEstimator` |
| `fusion_calibrated_risk` | Final Bayesian posterior produced by `EvidenceFusionService` |
| `fusion_posterior_risk` | Final Bayesian posterior (pre-calibration) |
| `fusion_prior_risk` | Fixed constant 0.05 — zero variance, no information |
| `fusion_verdict_ordinal` | Final verdict enum index produced by `VerdictGenerator` |

`FeatureValidator` enforces this at runtime: if any of these keys appear inside a `FeatureVector`, it raises a hard validation error.

---

## Pipeline Diagram

```
HTTP Upload
    │
    ▼
DocumentService.ingest()
    │
    ▼
PipelineManager  (all stages run sequentially)
    ├── UploadStage
    ├── PreprocessingStage      → context.quality_metrics
    │                           → context.image_forensics_metrics (via ImageArtifactDetector)
    ├── OCRStage                → context.ocr_summary
    ├── LayoutAnalysisStage     → context.layout_summary
    ├── DocumentClassificationStage → context.classification_result
    ├── ForgeryDetectionStage   → context.signature_features
    │                           → context.logo_features
    │                           → context.copy_move_features
    │                           → context.evidence_category_scores
    │                           → context.forgery_report
    └── EvidenceFusionStage     → context.fusion_metrics
    │
    ▼
AnalysisContext  (complete, all fields populated)
    │
    ▼
FeatureExtractor.extract(context, label)
    │
    ▼
FeatureVector  (94 features + provenance metadata)
    │
    ├──► FeatureValidator.validate()   — hard errors + soft warnings
    │
    └──► DatasetBuilder.build()        — writes dataset.csv
                │
                └──► _validate_csv()  — structural post-write verification
```

---

## Dataset Generation Workflow

```python
from pathlib import Path
from app import document_service
from app.ml.dataset_builder import DatasetBuilder

builder = DatasetBuilder(document_service)
rows = await builder.build(
    input_dir=Path("data/raw"),
    output_csv=Path("data/dataset.csv"),
    label_map={"forged": ["forged/"], "authentic": ["authentic/"]},
)
print(f"Wrote {rows} rows.")
```

- Recursively scans `input_dir` for `.pdf`, `.png`, `.jpg`, `.jpeg`.
- Calls `DocumentService.ingest()` per file via in-memory `UploadFile` — no temp files.
- Calls `FeatureExtractor.extract()` on the returned `AnalysisContext`.
- Skips files where `ingest()` raises — logs error, continues.
- After writing, `_validate_csv()` verifies column order, column count, feature count, metadata count, and row count. Raises `RuntimeError` with a descriptive message on any mismatch.

---

## Validation Workflow

### Per-vector validation (FeatureValidator)

```python
from app.ml.feature_validator import FeatureValidator

result = FeatureValidator().validate(vector)
if not result.valid:
    print(result.errors)   # hard failures — block write
print(result.warnings)     # soft issues — log only
```

Checks performed:

| Check | Type |
|---|---|
| No duplicate names in registry | Error |
| Feature vector length == registry length | Error |
| All FEATURE_NAMES keys present | Error |
| Leakage features absent | Error |
| No NaN values | Error |
| No Infinity values | Error |
| Numeric type consistency | Error |
| Bounded features within declared ranges | Warning |
| All image forensics None (detector may not have run) | Warning |
| All OCR features None (stage may not have run) | Warning |

### Post-build CSV validation (_validate_csv)

Automatically called by `DatasetBuilder.build()`. Verifies:

1. CSV file exists
2. Column count == 98
3. Column order matches `CSV_COLUMNS` exactly
4. Feature column count == 94
5. Metadata column count == 4
6. Row count matches rows written

---

## Quality Reports

Three JSON reports are generated by `FeatureStatistics`:

### `feature_statistics.json`

Per-feature statistics for every one of the 94 features:

```json
{
  "total_rows": 500,
  "label_distribution": {"forged": 250, "authentic": 250},
  "constant_features": ["img_page_count"],
  "nearly_constant_features": ["fusion_conflict_mult"],
  "high_missing_features": ["sig_complexity_score", "logo_hu_0"],
  "features": [
    {
      "name": "img_laplacian_variance_mean",
      "valid_count": 498,
      "missing_count": 2,
      "missing_pct": 0.4,
      "mean": 312.45,
      "median": 290.1,
      "std": 88.3,
      "min": 12.0,
      "max": 980.0,
      "is_constant": false,
      "is_nearly_constant": false,
      "constant_value": null
    }
  ]
}
```

### `feature_correlation.json`

All feature pairs with |Pearson r| >= 0.95:

```json
{
  "threshold": 0.95,
  "pair_count": 3,
  "pairs": [
    {"feature_a": "ev_image", "feature_b": "evidence_highest_severity", "pearson_r": 0.971234}
  ]
}
```

### `dataset_quality.json`

Overall dataset health:

```json
{
  "total_samples": 500,
  "authentic_samples": 250,
  "forged_samples": 250,
  "class_balance_ratio": 1.0,
  "duplicate_rows": 0,
  "duplicate_document_ids": 0,
  "rows_with_nan": 0,
  "rows_with_inf": 0,
  "features_high_missing": ["sig_complexity_score"],
  "constant_features": [],
  "nearly_constant_features": [],
  "high_correlation_pairs": []
}
```

Generate all three reports:

```python
from pathlib import Path
from app.ml.feature_statistics import FeatureStatistics

stats = FeatureStatistics()
ds = stats.compute(vectors)

stats.export_statistics(ds, Path("reports/feature_statistics.json"))
stats.export_correlation(ds, Path("reports/feature_correlation.json"))
stats.export_quality(ds, vectors, Path("reports/dataset_quality.json"))

print(ds.summary())
```

---

## Adding a New Feature

1. Add a `FeatureDef` entry to the appropriate group list in `feature_registry.py`.
2. Add the corresponding read in `FeatureExtractor` under the matching `_extract_*` method.
3. If the feature has a known valid range, add it to `_BOUNDS` in `feature_validator.py`.

No other file needs to change. `FeatureStatistics` and `DatasetBuilder` pick up new features automatically via `FEATURE_NAMES`.

---

## Running the Tests

```bash
cd backend
pytest tests/test_feature_extractor.py tests/test_dataset_builder.py -v
```

---

## Backend Freeze Notice

The feature extraction pipeline is **frozen for Phase 16.2**.

- `feature_registry.py` — 94 features, deterministic order, stable column indices
- `feature_extractor.py` — read-only, stateless, no side effects
- `feature_validator.py` — enforces leakage prevention at runtime
- `dataset_builder.py` — validates CSV structure after every build
- `feature_statistics.py` — generates three quality reports

Do not modify any of these files during model training.
