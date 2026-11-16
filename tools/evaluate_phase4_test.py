"""
evaluate_phase4_test.py

Phase 4: Final Held-Out Test Evaluation for VisionForensics AI:
- Strict feature and leakage audit.
- Frozen inference with random_forest.joblib and logistic_regression.joblib.
- Evaluates both models at T=0.50 and T=0.40.
- Calculates comprehensive metrics, confusion matrices, and Brier scores.
- Disaggregates performance by the 4 forgery categories.
- Disaggregates performance across the 7 quarantined physical specimens.
- Computes specimen-cluster bootstrap confidence intervals (95% CI).
- Compares Validation vs Test metrics and measures generalization gaps.
- Exports all required JSON and report artifacts.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
)

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

ARTIFACTS_DIR = _BACKEND_ROOT / "app" / "ml" / "artifacts"
DATASET_ROOT = Path(r"D:\Datasets\TrainingDataset")
PHASE2_DIR = DATASET_ROOT / "ml_phase2"
FEATURES_DIR = PHASE2_DIR / "features"

TEST_SPECIMENS = [
    "35_nor_drvlic_",
    "36_pol_drvlic_",
    "43_tur_id_",
    "44_ukr_id_",
    "45_ukr_passport_",
    "46_ury_passport_",
    "50_xpo_id_",
]

def run_feature_and_leakage_audit() -> Dict[str, Any]:
    """Verifies that test_features.csv adheres strictly to active schema and has zero leakage."""
    logger.info("=== STEP 1: STRICT TEST FEATURE & LEAKAGE AUDIT ===")
    
    schema_path = ARTIFACTS_DIR / "active_feature_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    active_feats = schema["features"]
    id_cols = schema["identity_columns"]
    
    test_csv_path = FEATURES_DIR / "test_features.csv"
    if not test_csv_path.exists():
        raise FileNotFoundError(f"Missing {test_csv_path}")
        
    df_test = pd.read_csv(test_csv_path)
    logger.info(f"Loaded test_features.csv: {df_test.shape}")
    
    # 1. Row count & Columns check
    assert len(df_test) == 280, f"Expected 280 rows, got {len(df_test)}"
    assert list(df_test.columns) == id_cols + active_feats, "Columns mismatch with active schema!"
    
    # 2. Data quality
    null_count = int(df_test[active_feats].isnull().sum().sum())
    assert null_count == 0, f"Found {null_count} nulls in test features!"
    inf_count = int(np.isinf(df_test[active_feats].values).sum())
    assert inf_count == 0, f"Found {inf_count} infinite values in test features!"
    dup_count = int(df_test["image_name"].duplicated().sum())
    assert dup_count == 0, f"Found {dup_count} duplicate image names in test set!"
    
    # 3. Label check
    labels = df_test["label"].value_counts().to_dict()
    assert labels == {0: 140, 1: 140}, f"Unexpected label balance: {labels}"
    
    # 4. Forgery categories check
    forgery_types = df_test["forgery_type"].value_counts().to_dict()
    expected_types = {"none": 140, "copy_move": 35, "text": 35, "signature": 35, "logo": 35}
    assert forgery_types == expected_types, f"Unexpected forgery types: {forgery_types}"
    
    # 5. Specimen check & isolation
    specs = sorted(df_test["specimen_id"].unique())
    assert specs == sorted(TEST_SPECIMENS), f"Test specimens mismatch! Found: {specs}"
    
    df_train = pd.read_csv(FEATURES_DIR / "train_features.csv")
    df_val = pd.read_csv(FEATURES_DIR / "val_features.csv")
    train_specs = set(df_train["specimen_id"].unique())
    val_specs = set(df_val["specimen_id"].unique())
    test_specs = set(specs)
    
    assert len(test_specs.intersection(train_specs)) == 0, "DATA LEAKAGE: Test overlaps with Train!"
    assert len(test_specs.intersection(val_specs)) == 0, "DATA LEAKAGE: Test overlaps with Val!"
    
    logger.info("Test feature audit PASSED: 280 rows, 18 features, 0 nulls, 0 infs, 0 duplicates, 0 leakage.")
    return {
        "status": "PASSED",
        "sample_count": len(df_test),
        "authentic_count": labels[0],
        "forged_count": labels[1],
        "forgery_breakdown": forgery_types,
        "specimens": specs,
        "features": active_feats,
    }

def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    y_pred = (y_prob >= threshold).astype(int)
    
    acc = accuracy_score(y_true, y_pred)
    prec_forg = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    rec_forg = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1_forg = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    
    prec_auth = precision_score(y_true, y_pred, pos_label=0, zero_division=0)
    rec_auth = recall_score(y_true, y_pred, pos_label=0, zero_division=0)
    f1_auth = f1_score(y_true, y_pred, pos_label=0, zero_division=0)
    
    try:
        auc = roc_auc_score(y_true, y_prob)
    except Exception:
        auc = 0.0
        
    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except Exception:
        pr_auc = 0.0
        
    brier = brier_score_loss(y_true, y_prob)
    
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    
    return {
        "threshold": float(threshold),
        "accuracy": float(acc),
        "roc_auc": float(auc),
        "pr_auc": float(pr_auc),
        "brier_score": float(brier),
        "forged_class (positive=1)": {
            "precision": float(prec_forg),
            "recall": float(rec_forg),
            "f1_score": float(f1_forg),
        },
        "authentic_class (negative=0)": {
            "precision": float(prec_auth),
            "recall_specificity": float(rec_auth),
            "f1_score": float(f1_auth),
        },
        "macro_metrics": {
            "precision": float((prec_auth + prec_forg) / 2.0),
            "recall": float((rec_auth + rec_forg) / 2.0),
            "f1_score": float((f1_auth + f1_forg) / 2.0),
        },
        "confusion_matrix": {
            "true_negatives (TN)": int(tn),
            "false_positives (FP)": int(fp),
            "false_negatives (FN)": int(fn),
            "true_positives (TP)": int(tp),
            "false_positive_rate (FPR)": float(fpr),
            "false_negative_rate (FNR)": float(fnr),
        }
    }

def run_cluster_bootstrap(df: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5, n_bootstraps: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Cluster bootstrap at the specimen level:
    Resamples specimen clusters with replacement to compute empirical 95% confidence intervals.
    """
    np.random.seed(seed)
    unique_clusters = df["specimen_id"].unique()
    k_clusters = len(unique_clusters)
    
    boot_auc = []
    boot_f1 = []
    boot_acc = []
    boot_fpr = []
    boot_rec = []
    
    for _ in range(n_bootstraps):
        sampled_clusters = np.random.choice(unique_clusters, size=k_clusters, replace=True)
        # Gather all rows corresponding to sampled clusters
        sample_indices = []
        for c in sampled_clusters:
            sample_indices.extend(df[df["specimen_id"] == c].index.tolist())
            
        y_b_true = y_true[sample_indices]
        y_b_prob = y_prob[sample_indices]
        y_b_pred = (y_b_prob >= threshold).astype(int)
        
        # Check if both classes present
        if len(np.unique(y_b_true)) < 2:
            continue
            
        boot_auc.append(roc_auc_score(y_b_true, y_b_prob))
        boot_f1.append(f1_score(y_b_true, y_b_pred, pos_label=1, zero_division=0))
        boot_acc.append(accuracy_score(y_b_true, y_b_pred))
        
        cm = confusion_matrix(y_b_true, y_b_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            boot_fpr.append(fp / (fp + tn) if (fp + tn) > 0 else 0.0)
            boot_rec.append(tp / (tp + fn) if (tp + fn) > 0 else 0.0)
            
    def get_ci(arr):
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "ci_95_lower": float(np.percentile(arr, 2.5)),
            "ci_95_upper": float(np.percentile(arr, 97.5)),
        }
        
    return {
        "n_bootstraps": n_bootstraps,
        "n_clusters": k_clusters,
        "threshold": threshold,
        "roc_auc": get_ci(boot_auc),
        "forged_f1": get_ci(boot_f1),
        "accuracy": get_ci(boot_acc),
        "forged_recall": get_ci(boot_rec),
        "false_positive_rate": get_ci(boot_fpr),
    }

def main():
    # 1. Audit
    audit_res = run_feature_and_leakage_audit()
    
    # 2. Load test features
    test_df = pd.read_csv(FEATURES_DIR / "test_features.csv")
    with open(ARTIFACTS_DIR / "active_feature_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    active_feats = schema["features"]
    
    # CRITICAL: strictly pass only active_feats (NO identity/metadata columns)
    X_test = test_df[active_feats].copy()
    y_test = test_df["label"].values.astype(int)
    
    # 3. Load FROZEN pipelines
    rf_pipe = joblib.load(ARTIFACTS_DIR / "random_forest.joblib")
    lr_pipe = joblib.load(ARTIFACTS_DIR / "logistic_regression.joblib")
    logger.info("Loaded frozen Random Forest and Logistic Regression models.")
    
    # 4. Model Inference
    rf_prob = rf_pipe.predict_proba(X_test)[:, 1]
    lr_prob = lr_pipe.predict_proba(X_test)[:, 1]
    
    test_df["prob_rf"] = rf_prob
    test_df["prob_lr"] = lr_prob
    
    # 5. Metrics at T=0.50 and T=0.40
    rf_metrics_05 = compute_metrics(y_test, rf_prob, threshold=0.50)
    rf_metrics_04 = compute_metrics(y_test, rf_prob, threshold=0.40)
    lr_metrics_05 = compute_metrics(y_test, lr_prob, threshold=0.50)
    lr_metrics_04 = compute_metrics(y_test, lr_prob, threshold=0.40)
    
    # 6. Forgery category breakdown
    cat_breakdown = {}
    for cat_name, cat_df in test_df.groupby("forgery_type"):
        y_cat = cat_df["label"].values.astype(int)
        rf_cat_prob = cat_df["prob_rf"].values
        lr_cat_prob = cat_df["prob_lr"].values
        
        cat_breakdown[cat_name] = {
            "sample_count": len(cat_df),
            "rf_t05_detected": int((rf_cat_prob >= 0.50).sum()),
            "rf_t05_rate": float((rf_cat_prob >= 0.50).mean()),
            "rf_t04_detected": int((rf_cat_prob >= 0.40).sum()),
            "rf_t04_rate": float((rf_cat_prob >= 0.40).mean()),
            "lr_t05_detected": int((lr_cat_prob >= 0.50).sum()),
            "lr_t05_rate": float((lr_cat_prob >= 0.50).mean()),
            "lr_t04_detected": int((lr_cat_prob >= 0.40).sum()),
            "lr_t04_rate": float((lr_cat_prob >= 0.40).mean()),
            "mean_rf_prob": float(np.mean(rf_cat_prob)),
            "mean_lr_prob": float(np.mean(lr_cat_prob)),
        }
        
    # 7. Specimen-level breakdown
    spec_breakdown = {}
    for spec_id, spec_df in test_df.groupby("specimen_id"):
        y_spec = spec_df["label"].values.astype(int)
        rf_spec_prob = spec_df["prob_rf"].values
        lr_spec_prob = spec_df["prob_lr"].values
        
        m_rf_05 = compute_metrics(y_spec, rf_spec_prob, threshold=0.50)
        m_rf_04 = compute_metrics(y_spec, rf_spec_prob, threshold=0.40)
        m_lr_05 = compute_metrics(y_spec, lr_spec_prob, threshold=0.50)
        m_lr_04 = compute_metrics(y_spec, lr_spec_prob, threshold=0.40)
        
        spec_breakdown[spec_id] = {
            "total_samples": len(spec_df),
            "authentic_samples": int((y_spec == 0).sum()),
            "forged_samples": int((y_spec == 1).sum()),
            "document_category": spec_df["document_category"].iloc[0],
            "random_forest_t05": {
                "accuracy": m_rf_05["accuracy"],
                "forged_recall": m_rf_05["forged_class (positive=1)"]["recall"],
                "authentic_recall": m_rf_05["authentic_class (negative=0)"]["recall_specificity"],
                "false_positives": m_rf_05["confusion_matrix"]["false_positives (FP)"],
                "false_negatives": m_rf_05["confusion_matrix"]["false_negatives (FN)"],
                "roc_auc": m_rf_05["roc_auc"],
            },
            "random_forest_t04": {
                "accuracy": m_rf_04["accuracy"],
                "forged_recall": m_rf_04["forged_class (positive=1)"]["recall"],
                "authentic_recall": m_rf_04["authentic_class (negative=0)"]["recall_specificity"],
                "false_positives": m_rf_04["confusion_matrix"]["false_positives (FP)"],
                "false_negatives": m_rf_04["confusion_matrix"]["false_negatives (FN)"],
            },
            "logistic_regression_t05": {
                "accuracy": m_lr_05["accuracy"],
                "forged_recall": m_lr_05["forged_class (positive=1)"]["recall"],
                "authentic_recall": m_lr_05["authentic_class (negative=0)"]["recall_specificity"],
                "false_positives": m_lr_05["confusion_matrix"]["false_positives (FP)"],
                "false_negatives": m_lr_05["confusion_matrix"]["false_negatives (FN)"],
                "roc_auc": m_lr_05["roc_auc"],
            }
        }
        
    # 8. Cluster Bootstrap Confidence Intervals (Random Forest at T=0.50 and T=0.40)
    rf_boot_05 = run_cluster_bootstrap(test_df, y_test, rf_prob, threshold=0.50, n_bootstraps=1000, seed=42)
    rf_boot_04 = run_cluster_bootstrap(test_df, y_test, rf_prob, threshold=0.40, n_bootstraps=1000, seed=42)
    lr_boot_05 = run_cluster_bootstrap(test_df, y_test, lr_prob, threshold=0.50, n_bootstraps=1000, seed=42)
    
    # 9. Validation vs Test Comparison
    with open(ARTIFACTS_DIR / "validation_results.json", "r", encoding="utf-8") as f:
        val_summary = json.load(f)
    val_rf = val_summary["random_forest_val"]
    val_lr = val_summary["logistic_regression_val"]
    
    val_vs_test = {
        "random_forest": {
            "validation_t05": {
                "accuracy": val_rf["accuracy"],
                "roc_auc": val_rf["roc_auc"],
                "pr_auc": val_rf["pr_auc"],
                "brier_score": val_rf["brier_score"],
                "forged_precision": val_rf["forged_class (positive=1)"]["precision"],
                "forged_recall": val_rf["forged_class (positive=1)"]["recall"],
                "forged_f1": val_rf["forged_class (positive=1)"]["f1_score"],
                "false_positive_rate": val_rf["confusion_matrix"]["false_positive_rate (FPR)"],
            },
            "test_t05": {
                "accuracy": rf_metrics_05["accuracy"],
                "roc_auc": rf_metrics_05["roc_auc"],
                "pr_auc": rf_metrics_05["pr_auc"],
                "brier_score": rf_metrics_05["brier_score"],
                "forged_precision": rf_metrics_05["forged_class (positive=1)"]["precision"],
                "forged_recall": rf_metrics_05["forged_class (positive=1)"]["recall"],
                "forged_f1": rf_metrics_05["forged_class (positive=1)"]["f1_score"],
                "false_positive_rate": rf_metrics_05["confusion_matrix"]["false_positive_rate (FPR)"],
            },
            "generalization_gap_t05": {
                "accuracy_gap": val_rf["accuracy"] - rf_metrics_05["accuracy"],
                "roc_auc_gap": val_rf["roc_auc"] - rf_metrics_05["roc_auc"],
                "pr_auc_gap": val_rf["pr_auc"] - rf_metrics_05["pr_auc"],
                "forged_f1_gap": val_rf["forged_class (positive=1)"]["f1_score"] - rf_metrics_05["forged_class (positive=1)"]["f1_score"],
            },
            "test_t04": {
                "accuracy": rf_metrics_04["accuracy"],
                "forged_precision": rf_metrics_04["forged_class (positive=1)"]["precision"],
                "forged_recall": rf_metrics_04["forged_class (positive=1)"]["recall"],
                "forged_f1": rf_metrics_04["forged_class (positive=1)"]["f1_score"],
                "false_positive_rate": rf_metrics_04["confusion_matrix"]["false_positive_rate (FPR)"],
            }
        },
        "logistic_regression": {
            "validation_t05": {
                "accuracy": val_lr["accuracy"],
                "roc_auc": val_lr["roc_auc"],
                "pr_auc": val_lr["pr_auc"],
                "brier_score": val_lr["brier_score"],
                "forged_precision": val_lr["forged_class (positive=1)"]["precision"],
                "forged_recall": val_lr["forged_class (positive=1)"]["recall"],
                "forged_f1": val_lr["forged_class (positive=1)"]["f1_score"],
                "false_positive_rate": val_lr["confusion_matrix"]["false_positive_rate (FPR)"],
            },
            "test_t05": {
                "accuracy": lr_metrics_05["accuracy"],
                "roc_auc": lr_metrics_05["roc_auc"],
                "pr_auc": lr_metrics_05["pr_auc"],
                "brier_score": lr_metrics_05["brier_score"],
                "forged_precision": lr_metrics_05["forged_class (positive=1)"]["precision"],
                "forged_recall": lr_metrics_05["forged_class (positive=1)"]["recall"],
                "forged_f1": lr_metrics_05["forged_class (positive=1)"]["f1_score"],
                "false_positive_rate": lr_metrics_05["confusion_matrix"]["false_positive_rate (FPR)"],
            },
            "generalization_gap_t05": {
                "accuracy_gap": val_lr["accuracy"] - lr_metrics_05["accuracy"],
                "roc_auc_gap": val_lr["roc_auc"] - lr_metrics_05["roc_auc"],
                "pr_auc_gap": val_lr["pr_auc"] - lr_metrics_05["pr_auc"],
                "forged_f1_gap": val_lr["forged_class (positive=1)"]["f1_score"] - lr_metrics_05["forged_class (positive=1)"]["f1_score"],
            },
            "test_t04": {
                "accuracy": lr_metrics_04["accuracy"],
                "forged_precision": lr_metrics_04["forged_class (positive=1)"]["precision"],
                "forged_recall": lr_metrics_04["forged_class (positive=1)"]["recall"],
                "forged_f1": lr_metrics_04["forged_class (positive=1)"]["f1_score"],
                "false_positive_rate": lr_metrics_04["confusion_matrix"]["false_positive_rate (FPR)"],
            }
        }
    }
    
    # 10. Save All Phase 4 JSON Artifacts
    # A. test_results.json
    test_results_dict = {
        "audit": audit_res,
        "random_forest": {
            "metrics_t05": rf_metrics_05,
            "metrics_t04": rf_metrics_04,
            "cluster_bootstrap_t05": rf_boot_05,
            "cluster_bootstrap_t04": rf_boot_04,
        },
        "logistic_regression": {
            "metrics_t05": lr_metrics_05,
            "metrics_t04": lr_metrics_04,
            "cluster_bootstrap_t05": lr_boot_05,
        }
    }
    with open(ARTIFACTS_DIR / "test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results_dict, f, indent=2)
    logger.info("Saved test_results.json")
    
    # B. test_confusion_matrices.json
    cm_dict = {
        "random_forest_t05": rf_metrics_05["confusion_matrix"],
        "random_forest_t04": rf_metrics_04["confusion_matrix"],
        "logistic_regression_t05": lr_metrics_05["confusion_matrix"],
        "logistic_regression_t04": lr_metrics_04["confusion_matrix"],
    }
    with open(ARTIFACTS_DIR / "test_confusion_matrices.json", "w", encoding="utf-8") as f:
        json.dump(cm_dict, f, indent=2)
    logger.info("Saved test_confusion_matrices.json")
    
    # C. test_category_breakdown.json
    with open(ARTIFACTS_DIR / "test_category_breakdown.json", "w", encoding="utf-8") as f:
        json.dump(cat_breakdown, f, indent=2)
    logger.info("Saved test_category_breakdown.json")
    
    # D. test_specimen_breakdown.json
    with open(ARTIFACTS_DIR / "test_specimen_breakdown.json", "w", encoding="utf-8") as f:
        json.dump(spec_breakdown, f, indent=2)
    logger.info("Saved test_specimen_breakdown.json")
    
    # E. validation_vs_test_comparison.json
    with open(ARTIFACTS_DIR / "validation_vs_test_comparison.json", "w", encoding="utf-8") as f:
        json.dump(val_vs_test, f, indent=2)
    logger.info("Saved validation_vs_test_comparison.json")
    
    logger.info("=== PHASE 4 EVALUATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
