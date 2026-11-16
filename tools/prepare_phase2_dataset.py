"""
prepare_phase2_dataset.py

Generates the Phase 2 isolated ML dataset:
- Deterministically selects 20 authentic frames per specimen (frames 05 and 15 across 10 conditions).
- Generates 20 localized forgeries per specimen (5 copy_move, 5 text, 5 signature, 5 logo).
- Partitions into 33 train, 7 val, 7 test specimens.
- Saves generated forgeries in D:\\Datasets\\TrainingDataset\\ml_phase2\\<split>_forged\\
- Writes provenance manifests: metadata_train.csv, metadata_val.csv, metadata_test.csv
- Leaves all original dataset files 100% untouched.
"""

import os
import sys
import cv2
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.generators.copy_move import CopyMoveGenerator
from tools.generators.text import TextGenerator
from tools.generators.signature import SignatureGenerator
from tools.generators.logo import LogoGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DATASET_ROOT = Path(r"D:\Datasets\TrainingDataset")
AUTH_ROOT = DATASET_ROOT / "authentic"
OUT_ROOT = DATASET_ROOT / "ml_phase2"

# 47 Document Specimen Partition
SPLITS = {
    "train": {
        "driving_license": [
            "02_aut_drvlic_new_", "12_deu_drvlic_new_", "13_deu_drvlic_old_", "19_esp_drvlic_",
            "23_fin_drvlic_", "26_hrv_drvlic_", "29_irn_drvlic_", "38_rou_drvlic_"
        ],
        "id_card": [
            "01_alb_id_", "03_aut_id_old_", "04_aut_id_", "07_chl_id_", "09_chn_id_",
            "10_cze_id_", "14_deu_id_new_", "15_deu_id_old_", "20_esp_id_new_", "21_esp_id_old_",
            "22_est_id_", "24_fin_id_", "33_mac_id_"
        ],
        "passport": [
            "05_aze_passport_", "06_bra_passport_", "11_cze_passport_", "16_deu_passport_new_",
            "17_deu_passport_old_", "18_dza_passport_", "25_grc_passport_", "27_hrv_passport_",
            "28_hun_passport_", "32_lva_passport_", "34_mda_passport_", "39_rus_internalpassport_"
        ]
    },
    "val": {
        "driving_license": [
            "30_ita_drvlic_", "31_jpn_drvlic_"
        ],
        "id_card": [
            "37_prt_id_", "40_srb_id_", "42_svk_id_"
        ],
        "passport": [
            "41_srb_passport_", "48_usa_passportcard_"
        ]
    },
    "test": {
        "driving_license": [
            "35_nor_drvlic_", "36_pol_drvlic_"
        ],
        "id_card": [
            "43_tur_id_", "44_ukr_id_", "50_xpo_id_"
        ],
        "passport": [
            "45_ukr_passport_", "46_ury_passport_"
        ]
    }
}

CONDITIONS = ["CA", "CS", "HA", "HS", "KA", "KS", "PA", "PS", "TA", "TS"]
FRAME_INDICES = ["05", "15"]

GENERATORS = {
    "copy_move": CopyMoveGenerator(),
    "text": TextGenerator(),
    "signature": SignatureGenerator(),
    "logo": LogoGenerator(),
}

def get_20_authentic_frames(category: str, doc_id: str) -> list[Path]:
    cat_dir = AUTH_ROOT / category
    frames = []
    for cond in CONDITIONS:
        for idx in FRAME_INDICES:
            target_name = f"{doc_id}{cond}{idx}.tif"
            p = cat_dir / target_name
            if p.exists():
                frames.append(p)
            else:
                raise FileNotFoundError(f"Missing expected authentic frame: {p}")
    frames.sort()
    return frames

def build_dataset():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    
    total_authentic = 0
    total_forged = 0
    
    for split_idx, (split, categories) in enumerate(SPLITS.items()):
        logger.info(f"--- Processing Split: {split.upper()} ---")
        split_forged_dir = OUT_ROOT / f"{split}_forged"
        split_forged_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_rows = []
        doc_count = 0
        
        for category, doc_list in categories.items():
            (split_forged_dir / category).mkdir(parents=True, exist_ok=True)
            for doc_idx, doc_id in enumerate(doc_list):
                doc_count += 1
                auth_frames = get_20_authentic_frames(category, doc_id)
                assert len(auth_frames) == 20, f"Expected 20 frames for {doc_id}, found {len(auth_frames)}"
                
                # 1. Record authentic frames
                for f_idx, auth_path in enumerate(auth_frames):
                    manifest_rows.append({
                        "split": split,
                        "image_name": auth_path.name,
                        "image_path": str(auth_path),
                        "source_image": auth_path.name,
                        "source_path": str(auth_path),
                        "document_category": category,
                        "specimen_id": doc_id,
                        "forgery_type": "none",
                        "label": 0,
                        "generator": "none",
                    })
                    total_authentic += 1
                
                # 2. Generate 20 forgeries (5 each of copy_move, text, signature, logo)
                forgery_types = ["copy_move"] * 5 + ["text"] * 5 + ["signature"] * 5 + ["logo"] * 5
                
                for f_idx, (auth_path, forger_name) in enumerate(zip(auth_frames, forgery_types)):
                    gen = GENERATORS[forger_name]
                    # Seed uniquely and deterministically
                    seed = 100000 + split_idx * 10000 + doc_idx * 100 + f_idx
                    rng = np.random.default_rng(seed)
                    
                    img = cv2.imread(str(auth_path))
                    if img is None:
                        raise ValueError(f"Failed to read image {auth_path}")
                        
                    forged_img, meta = gen.apply(img, rng)
                    
                    # Ensure modification actually occurred
                    diff = cv2.absdiff(img, forged_img)
                    non_zero = np.count_nonzero(diff)
                    if non_zero == 0:
                        raise RuntimeError(f"Zero modification generated for {auth_path.name} with {forger_name}!")
                        
                    out_filename = f"{auth_path.stem}_{forger_name}.tif"
                    out_path = split_forged_dir / category / out_filename
                    
                    cv2.imwrite(str(out_path), forged_img)
                    
                    manifest_rows.append({
                        "split": split,
                        "image_name": out_filename,
                        "image_path": str(out_path),
                        "source_image": auth_path.name,
                        "source_path": str(auth_path),
                        "document_category": category,
                        "specimen_id": doc_id,
                        "forgery_type": forger_name,
                        "label": 1,
                        "generator": gen.__class__.__name__,
                    })
                    total_forged += 1
        
        # Save split manifest
        df_manifest = pd.DataFrame(manifest_rows)
        manifest_path = OUT_ROOT / f"metadata_{split}.csv"
        df_manifest.to_csv(manifest_path, index=False)
        logger.info(f"Split {split.upper()} complete | Docs: {doc_count} | Manifest saved to {manifest_path} | Rows: {len(df_manifest)} (Auth: {len(df_manifest[df_manifest['label']==0])}, Forged: {len(df_manifest[df_manifest['label']==1])})")

    logger.info(f"=== ALL SPLITS GENERATED ===")
    logger.info(f"Total Authentic registered: {total_authentic}")
    logger.info(f"Total Forgeries created:   {total_forged}")
    logger.info(f"Grand Total Dataset Size:   {total_authentic + total_forged}")

if __name__ == "__main__":
    build_dataset()
