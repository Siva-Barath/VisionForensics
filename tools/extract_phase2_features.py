"""
extract_phase2_features.py

Resumable, checkpointed feature extraction for VisionForensics AI (Phase 2):
- Extracts the authoritative 18 active numerical features + 7 metadata provenance columns.
- Uses check-pointing to automatically resume without duplicating or restarting work.
- Uses 6 parallel worker processes with focused, reliable stages (preprocessing + forgery).
- Strictly preserves test-set quarantine (does NOT touch metadata_test.csv).
- Saves:
    D:\\Datasets\\TrainingDataset\\ml_phase2\\features\\train_features.csv
    D:\\Datasets\\TrainingDataset\\ml_phase2\\features\\val_features.csv
    D:\\Forgery Detection ML\\backend\\app\\ml\\artifacts\\active_feature_schema.json
"""

import os
import sys
import time
import json
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

# Add repo and backend roots to sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for p in (_REPO_ROOT, _BACKEND_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ACTIVE_FEATURES = [
    "img_width",
    "img_height",
    "img_aspect_ratio",
    "img_laplacian_variance_mean",
    "img_blur_severity_mean",
    "img_noise_sigma_mean",
    "img_edge_density_mean",
    "img_illumination_std_mean",
    "img_ela_region_count_mean",
    "img_ela_max_difference_mean",
    "img_entropy_score_mean",
    "cm_keypoint_count_akaze",
    "cm_descriptor_matches",
    "cm_inlier_matches",
    "cm_average_region_size",
    "cm_duplicate_pair_count",
    "cm_confidence",
    "cm_inlier_ratio",
]

IDENTITY_COLS = [
    "split",
    "image_name",
    "source_image",
    "document_category",
    "specimen_id",
    "forgery_type",
    "label",
]

CSV_COLUMNS = IDENTITY_COLS + ACTIVE_FEATURES

DATASET_ROOT = Path(r"D:\Datasets\TrainingDataset")
PHASE2_ROOT = DATASET_ROOT / "ml_phase2"
FEATURES_DIR = PHASE2_ROOT / "features"
ARTIFACTS_DIR = _BACKEND_ROOT / "app" / "ml" / "artifacts"

# Global worker cache
_worker_pipeline = None
_worker_extractor = None

def _init_worker():
    global _worker_pipeline, _worker_extractor
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("app").setLevel(logging.ERROR)
    logging.getLogger("pipeline").setLevel(logging.ERROR)
    
    from app.pipeline.registry import PipelineRegistry
    from app.pipeline.pipeline import PipelineManager
    from app.pipeline.config import PipelineConfig
    from app.pipeline.stages import PreprocessingStage, ForgeryDetectionStage
    from app.services.preprocessing.preprocessor import PreprocessingService
    from app.services.pdf_service import PDFService
    from app.services.storage_service import StorageService
    from app.config.settings import get_settings
    from app.ml.feature_extractor import FeatureExtractor
    
    settings = get_settings()
    storage = StorageService(settings)
    pdf_svc = PDFService(storage)
    preproc = PreprocessingService(output_dir=Path(settings.processed_dir))
    
    registry = PipelineRegistry()
    registry.register(PreprocessingStage(pdf_svc, preproc))
    registry.register(ForgeryDetectionStage())
    
    config = PipelineConfig(enabled_stages=["preprocessing", "forgery"])
    _worker_pipeline = PipelineManager(registry, config)
    _worker_extractor = FeatureExtractor()

def _process_single_image(task: dict) -> dict:
    global _worker_pipeline, _worker_extractor
    if _worker_pipeline is None:
        _init_worker()
        
    p = Path(task["image_path"])
    lbl = int(task["label"])
    label_str = "authentic" if lbl == 0 else "forged"
    
    raw = p.read_bytes()
    ext = p.suffix.lower().lstrip(".")
    file_type = "jpeg" if ext in ("jpg", "jpeg") else ext
    
    from app.pipeline.context import AnalysisContext
    ctx = AnalysisContext(
        original_filename=p.name,
        file_type=file_type,
        file_bytes=raw,
        size_bytes=len(raw),
    )
    ctx.stored_path = p
    
    ctx = asyncio.run(_worker_pipeline.run(ctx))
    vec = _worker_extractor.extract(ctx, label=label_str)
    
    clean_row = {}
    for col in IDENTITY_COLS:
        clean_row[col] = task.get(col, "")
        
    for feat in ACTIVE_FEATURES:
        val = vec.features.get(feat, None)
        clean_row[feat] = val
        
    return clean_row

def run_split_extraction(split: str, expected_count: int, num_workers: int = 6):
    manifest_path = PHASE2_ROOT / f"metadata_{split}.csv"
    out_csv = FEATURES_DIR / f"{split}_features.csv"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
        
    df_meta = pd.read_csv(manifest_path)
    all_tasks = df_meta.to_dict("records")
    
    # 1. Check for existing checkpoint
    existing_records = {}
    if out_csv.exists():
        try:
            df_existing = pd.read_csv(out_csv)
            # Ensure correct columns
            if list(df_existing.columns) == CSV_COLUMNS:
                for r in df_existing.to_dict("records"):
                    existing_records[r["image_name"]] = r
                logger.info(f"[{split.upper()}] Found existing checkpoint with {len(existing_records)} valid records.")
            else:
                logger.warning(f"[{split.upper()}] Existing CSV columns mismatch. Creating backup and restarting.")
                backup_path = out_csv.with_suffix(f".bak_{int(time.time())}")
                out_csv.rename(backup_path)
        except Exception as e:
            logger.warning(f"[{split.upper()}] Could not read existing CSV: {e}. Backing up.")
            backup_path = out_csv.with_suffix(f".corrupt_{int(time.time())}")
            out_csv.rename(backup_path)
            
    # 2. Filter remaining tasks
    remaining_tasks = [t for t in all_tasks if t["image_name"] not in existing_records]
    logger.info(f"[{split.upper()}] Total: {len(all_tasks)} | Already processed: {len(existing_records)} | Remaining: {len(remaining_tasks)}")
    
    if not remaining_tasks:
        logger.info(f"[{split.upper()}] Split already 100% complete! Skipping extraction.")
        return
        
    # Write initial header if file doesn't exist
    if not out_csv.exists() or len(existing_records) == 0:
        pd.DataFrame(columns=CSV_COLUMNS).to_csv(out_csv, index=False)
        
    start_time = time.time()
    completed = len(existing_records)
    batch_buffer = []
    failures = 0
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_task = {executor.submit(_process_single_image, task): task for task in remaining_tasks}
        
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                row = future.result()
                batch_buffer.append(row)
                completed += 1
            except Exception as exc:
                logger.error(f"[{split.upper()}] Extraction failed for {task['image_name']}: {exc}")
                failures += 1
                
            # Checkpoint flush every 25 rows or on completion
            if len(batch_buffer) >= 25 or completed == len(all_tasks):
                df_batch = pd.DataFrame(batch_buffer)[CSV_COLUMNS]
                df_batch.to_csv(out_csv, mode="a", header=False, index=False)
                batch_buffer.clear()
                
            if completed % 50 == 0 or completed == len(all_tasks):
                elapsed = time.time() - start_time
                fps = (completed - len(existing_records)) / elapsed if elapsed > 0 else 0
                logger.info(f"[{split.upper()}] Progress: {completed}/{len(all_tasks)} ({completed/len(all_tasks)*100:.1f}%) | Speed: {fps:.2f} img/s")
                
    elapsed = time.time() - start_time
    logger.info(f"[{split.upper()}] Extraction completed in {elapsed:.1f}s | Success: {completed} | Failures: {failures}")
    
    # Verification
    final_df = pd.read_csv(out_csv)
    assert len(final_df) == expected_count, f"Expected {expected_count} rows, got {len(final_df)}"
    assert final_df['image_name'].duplicated().sum() == 0, "Duplicate image records detected!"
    nulls = final_df[ACTIVE_FEATURES].isnull().sum().sum()
    assert nulls == 0, f"Detected {nulls} missing values in active features!"
    logger.info(f"[{split.upper()}] Post-extraction integrity check PASSED: exactly {len(final_df)} rows, 0 nulls, 0 duplicates.")

def main():
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Save Schema
    schema_path = ARTIFACTS_DIR / "active_feature_schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0.0",
            "feature_count": len(ACTIVE_FEATURES),
            "features": ACTIVE_FEATURES,
            "identity_columns": IDENTITY_COLS,
            "total_columns": len(CSV_COLUMNS),
        }, f, indent=2)
    logger.info(f"Saved active feature schema to {schema_path}")
    
    # 2. Extract Train (1320 rows)
    run_split_extraction("train", expected_count=1320, num_workers=6)
    
    # 3. Extract Val (280 rows)
    run_split_extraction("val", expected_count=280, num_workers=6)
    
    logger.info("=== PHASE 2 FEATURE EXTRACTION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
