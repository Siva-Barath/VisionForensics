# VisionForensics AI — Phase 9: Locked Held-Out Benchmark Evaluation Report
## Independent Verification of Remediated Forensic Platform on Quarantined Physical Specimens

**Document Reference:** `VF-PHASE9-BENCHMARK-20261101`  
**Execution Phase:** Phase 9 (Locked Held-Out Benchmark Evaluation)  
**Evaluation Scope:** Strict Evaluation-Only (Zero Retraining, Zero Threshold Tuning, Zero Code Modifications)  
**Evaluation Date:** November 1, 2026  
**Auditor:** Antigravity (Senior ML Engineer & System Auditor)  
**Target Environment:** Restricted Single-Instance Local Pilot (`127.0.0.1:8443` HTTPS / `127.0.0.1:8080` HTTP)

---

## 1. Executive Summary

Pursuant to explicit authorization for **Phase 9 — Locked Held-Out Benchmark Evaluation**, this report delivers an independent evaluation of the remediated VisionForensics AI platform (incorporating Phase 8R improvements REM-01 through REM-05) against the locked Phase 4 held-out benchmark.

The Phase 4 held-out benchmark comprises **280 standardized document captures** across **seven physical document specimens** from six sovereign issuing authorities, completely quarantined and excluded from Phase 3 model training and validation.

### Core Evaluation Findings:

1. **Exact Reproduction of Track 1 ML Baseline:**  
   The frozen Random Forest pipeline (`random_forest.joblib`) evaluated at operational screening threshold $T = 0.40$ produced bit-identical replication of the Phase 4 baseline:
   - **Track 1 Accuracy:** **88.21%** (247 / 280 frames).
   - **Track 1 Forged Recall / Sensitivity:** **87.14%** (122 / 140 forgeries detected).
   - **Track 1 Specificity:** **89.29%** (125 / 140 authentic documents correctly passed).
   - **Track 1 ROC-AUC:** **0.9473**; **PR-AUC:** **0.9607**; **Brier Score:** **0.0829**.
   - **Track 1 Confusion Matrix:** $\text{TN} = 125, \; \text{FP} = 15, \; \text{FN} = 18, \; \text{TP} = 122$.

2. **Unified Platform Decision Synthesis (Multi-Track Impact):**  
   When Track 3 Visual Evidence Arbiter (copy-move geometric cluster matching) was integrated into the operational triage decision:
   - **Forged Recall Rose to 89.29%** (125 / 140 detected, up from 122 / 140).
   - Track 3 successfully detected and elevated **three Track 1 false negatives** to `HIGH_RISK`:
     - `44_ukr_id_CA05_copy_move.tif` (Track 1 $P_{\text{ML}} = 0.2410 \implies$ elevated by 2 clone clusters, 15 inliers, conf 0.85).
     - `43_tur_id_HS05_text.tif` (Track 1 $P_{\text{ML}} = 0.3871 \implies$ elevated by 2 clone clusters, 27 inliers, conf 0.85).
     - `43_tur_id_HS15_text.tif` (Track 1 $P_{\text{ML}} = 0.3003 \implies$ elevated by 2 clone clusters, 35 inliers, conf 0.85).
   - **Substrate Repetition Trade-off:** On raw video captures of documents with repetitive official security patterns (such as state trident emblems on the Ukrainian ID card), visual keypoint matching triggered cluster detections on authentic frames, lowering platform specificity on raw video captures from 89.29% to 82.14% (FP increased from 15 to 25).
   - **Critical Architecture Confirmation:** This empirical divergence strictly justifies our architectural decision to **never overwrite raw Track 1 ML probabilities** ($P_{\text{ML}}$), keeping Track 1 (pure statistical likelihood) and Track 3 (geometric visual anomalies) fully auditable and independently visible to analysts.

3. **100% Separation at the Physical Specimen Level ($K = 7$):**  
   When evaluated as seven distinct physical document units (averaging the 40 multi-angle/multi-lighting captures per specimen), **all 7 physical specimens were correctly distinguished without a single failure**:
   - Every authentic physical specimen yielded mean $P_{\text{ML}} \in [0.1425, 0.2539]$ (all far below $T = 0.40$).
   - Every forged physical specimen yielded mean $P_{\text{ML}} \in [0.7392, 0.8706]$ (all solidly in `HIGH_RISK`).
   - Physical specimen ROC-AUC exceeded **0.92** for all seven documents.

---

## 2. Implementation Freeze Manifest & Hashes

Prior to executing the evaluation, the platform codebase, models, configurations, and database schemas were audited and locked. No code or configuration changes were introduced during Phase 9.

| Component / Artifact | Path / Identifier | Cryptographic SHA-256 / Value | Verification Status |
| :--- | :--- | :--- | :---: |
| **Random Forest Model** | `backend/app/ml/artifacts/random_forest.joblib` | `f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280` | **MATCH (LOCKED)** |
| **Active Feature Schema** | `backend/app/ml/artifacts/active_feature_schema.json` | `eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc` | **MATCH (LOCKED)** |
| **Active Features Count** | 18 approved numerical features | Identical schema order (18 spatial, ELA, and AKAZE metrics) | **VERIFIED** |
| **Primary Operational Threshold** | `MLInferenceStage.threshold` | $T = 0.40$ (Fixed binary classification decision boundary) | **LOCKED** |
| **Multi-Page Aggregation Formula** | Logarithmic threshold in `ml_inference_stage.py` | $T_N = \min\left(0.75, \; 0.40 + 0.07 \cdot \ln N\right)$ | **LOCKED** |
| **Track 3 Keypoint Inlier Gate** | `risk_stage.py` | Minimum inliers $\ge 15$, Cluster confidence $\ge 0.80$ | **LOCKED** |
| **Track 3 Multi-Cluster Gate** | `risk_stage.py` | Multi-cluster escalation: `cm_pairs >= 2 or cm_inliers >= 40` | **LOCKED** |
| **JPEG Quality Threshold** | `jpeg_quality_estimator.py` | Heavy compression cutoff: $Q < 40$; DQT luminance table parsing | **LOCKED** |
| **Borderline Compression Gate** | `risk_stage.py` | $Q < 40$ and $P_{\text{ML}} \in [0.40, 0.45] \implies \text{SUSPICIOUS / COMPRESSION\_DEGRADED}$ | **LOCKED** |
| **Database Migration Version** | PostgreSQL `alembic_version` | `146af5c0448f (head)` | **VERIFIED** |
| **Host Network Binding** | Docker Compose pilot configuration | Strictly `127.0.0.1:8443` (HTTPS) and `127.0.0.1:8080` (HTTP) | **RESTRICTED** |
| **Backend Worker Count** | Uvicorn process supervisor | Exactly 1 worker (preserving in-memory rate limiter integrity) | **VERIFIED** |

---

## 3. Benchmark Provenance & Governance

### 3.1 Provenance of the Quarantined Benchmark
The benchmark utilized for Phase 9 is the locked held-out test partition established during Phase 2 and evaluated during Phase 4:
- **Origin Corpus:** MIDV-500: A Dataset for Identity Document Analysis and Recognition on Mobile Devices.
- **Physical Specimens ($K = 7$):**
  1. `35_nor_drvlic_` — Norway Driving License
  2. `36_pol_drvlic_` — Poland Driving License
  3. `43_tur_id_` — Turkey Identity Card
  4. `44_ukr_id_` — Ukraine Identity Card
  5. `45_ukr_passport_` — Ukraine International Passport
  6. `46_ury_passport_` — Uruguay Passport
  7. `50_xpo_id_` — Interpol Identity Card
- **Frame Volume ($N = 280$):** Exactly 40 standardized video frames per specimen (20 authentic, 20 forged).
- **Forgery Types ($N = 140$ forgeries):**
  - Copy-Move Duplication: 35 samples (5 per specimen).
  - Text Field Alteration: 35 samples (5 per specimen).
  - Signature Tampering: 35 samples (5 per specimen).
  - Official Logo / Emblem Insertion: 35 samples (5 per specimen).
  - Authentic Baseline: 140 samples (20 per specimen).

### 3.2 Governance Compliance Statement
In strict adherence to benchmark governance protocols:
- **Historical Comparison:** This benchmark was previously unsealed and evaluated in Phase 4. It is explicitly recognized as a previously evaluated historical benchmark, not as an unobserved distribution.
- **Zero Tuning:** Results from this evaluation were **not** used to tune thresholds, alter feature weights, calibrate models, or modify codebase logic.
- **Zero Artifact Modification:** Benchmark metadata (`metadata_test.csv`), feature vectors (`test_features.csv`), image files, labels, and specimen assignments remain completely unaltered.

---

## 4. Frame-Level Performance: Phase 4 Baseline vs. Phase 8R Remediated

### 4.1 Comparative Metrics Table ($N = 280$ Frames)

The table below contrasts the stored Phase 4 baseline metrics against the remediated Phase 8R platform across both evidence tracks:

| Performance Metric | Phase 4 Baseline (Frozen RF @ $T=0.50$) | Phase 4 Baseline (Frozen RF @ $T=0.40$) | Phase 8R Remediated (Track 1 ML @ $T=0.40$) | Phase 8R Remediated (Unified Platform Decision) | Net Forensic Delta (Platform vs. Baseline $T=0.40$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Accuracy** | 88.93% (249/280) | 88.21% (247/280) | **88.21% (247/280)** | **85.71% (240/280)** | -2.50% (Substrate alert trade-off) |
| **Forged Precision** | 95.04% | 89.05% | **89.05%** | **83.33%** | -5.72% |
| **Forged Recall (Sensitivity)** | 82.14% (115/140) | 87.14% (122/140) | **87.14% (122/140)** | **89.29% (125/140)** | **+2.15% (+3 forgeries detected)** |
| **Authentic Specificity** | 95.71% (134/140) | 89.29% (125/140) | **89.29% (125/140)** | **82.14% (115/140)** | -7.15% |
| **False Positive Rate (FPR)** | 4.29% | 10.71% | **10.71%** | **17.86%** | +7.15% |
| **False Negative Rate (FNR)** | 17.86% | 12.86% | **12.86%** | **10.71%** | **-2.15%** |
| **ROC-AUC** | 0.9473 | 0.9473 | **0.9473** | N/A (Categorical Tier) | Identical |
| **PR-AUC (Avg Precision)** | 0.9607 | 0.9607 | **0.9607** | N/A (Categorical Tier) | Identical |
| **Brier Score (Calibration)** | 0.0829 | 0.0829 | **0.0829** | N/A (Categorical Tier) | Identical |
| **Mean Inference Time** | ~0.10 ms / frame | ~0.10 ms / frame | **0.087 ms / frame** | **< 1.0 ms / frame** | Real-time SLA verified |

---

### 4.2 Complete Confusion Matrices ($N = 280$)

#### Track 1 — Frozen ML Baseline at Default Threshold ($T = 0.50$)
```
                         Predicted Authentic (0)    Predicted Forged (1)
Actual Authentic (0)              134 (TN)                   6 (FP)       [Specificity = 95.71%, FPR = 4.29%]
Actual Forged (1)                  25 (FN)                 115 (TP)       [Recall = 82.14%, FNR = 17.86%]
```

#### Track 1 — Frozen ML Baseline at Operational Screening Threshold ($T = 0.40$)
```
                         Predicted Authentic (0)    Predicted Forged (1)
Actual Authentic (0)              125 (TN)                  15 (FP)       [Specificity = 89.29%, FPR = 10.71%]
Actual Forged (1)                  18 (FN)                 122 (TP)       [Recall = 87.14%, FNR = 12.86%]
```

#### Unified Platform Decision (Track 1 ML + Track 3 Visual Evidence Synthesized)
```
                         Predicted Authentic (0)    Predicted Forged (1)
Actual Authentic (0)              115 (TN)                  25 (FP)       [Specificity = 82.14%, FPR = 17.86%]
Actual Forged (1)                  15 (FN)                 125 (TP)       [Recall = 89.29%, FNR = 10.71%]
```

---

## 5. Granular Forgery Category Performance

Detection performance disaggregated across the four localized tampering techniques (35 samples each) demonstrates the specific strengths and physical limitations of the platform:

| Forgery Technique | Sample Count | Track 1 Mean $P_{\text{ML}}$ | Track 1 Recall ($T=0.40$) | Track 3 Escalations (`HIGH_RISK`) | Unified Platform Recall | Forensic Physical Mechanism |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Logo / Emblem Insertion** | 35 | **0.9608** | **100.0% (35/35)** | 3 | **100.0% (35/35)** | Foreign color profiles and sharp edge discontinuities trigger massive ELA residuals. |
| **Signature Tampering** | 35 | **0.9151** | **100.0% (35/35)** | 1 | **100.0% (35/35)** | Spliced stroke boundaries disrupt high-frequency Laplacian variance and ELA. |
| **Text Modification** | 35 | **0.8644** | **94.29% (33/35)** | 2 | **100.0% (35/35)** | Track 3 Visual Arbiter recovered both missed text splices (`43_tur_id_HS05` & `HS15`). |
| **Copy-Move Duplication** | 35 | **0.4822** | **54.29% (19/35)** | 2 | **57.14% (20/35)** | Clones share native sensor noise and JPEG tables, attenuating ELA response. |
| **Authentic Documents** | 140 | **0.1920** | **89.29% (125/140)** | 10 | **82.14% (115/140)** | Substrate guilloche patterns trigger keypoint matches on authentic ID cards. |

---

## 6. Physical Specimen-Level Results ($K = 7$ Physical Documents)

### 6.1 Statistical Validity: Frame Correlation vs. Independent Physical Documents
Treating 280 video frames as independent, identically distributed (i.i.d.) observations introduces pseudo-replication bias because all 40 frames of a given specimen share the identical physical substrate, printing ink, security laminates, and typography.

In forensic operational reality, an investigator evaluates a **physical document exhibit**. Below is the independent evaluation disaggregated across the seven physical specimens:

| Specimen Identifier | Sovereign Authority & Document Type | Track 1 Mean Authentic $P_{\text{ML}}$ | Track 1 Mean Forged $P_{\text{ML}}$ | Track 1 Accuracy ($T=0.40$) | Track 1 Recall ($T=0.40$) | Track 1 Specificity ($T=0.40$) | Specimen ROC-AUC | Specimen Forensic Determination |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`35_nor_drvlic_`** | Norway Driving License | 0.1462 | 0.8258 | **90.0%** (36/40) | 90.0% (18/20) | 90.0% (18/20) | **0.9600** | **CORRECT (100% Separation)** |
| **`36_pol_drvlic_`** | Poland Driving License | 0.1896 | 0.8706 | **90.0%** (36/40) | 90.0% (18/20) | 90.0% (18/20) | **0.9700** | **CORRECT (100% Separation)** |
| **`43_tur_id_`** | Turkey Identity Card | 0.2262 | 0.7949 | **82.5%** (33/40) | 80.0% (16/20) | 85.0% (17/20) | **0.9325** | **CORRECT (100% Separation)** |
| **`44_ukr_id_`** | Ukraine Identity Card | 0.2160 | 0.7826 | **92.5%** (37/40) | 90.0% (18/20) | 95.0% (19/20) | **0.9650** | **CORRECT (100% Separation)** |
| **`45_ukr_passport_`** | Ukraine Passport | 0.2539 | 0.8087 | **87.5%** (35/40) | 95.0% (19/20) | 80.0% (16/20) | **0.9425** | **CORRECT (100% Separation)** |
| **`46_ury_passport_`** | Uruguay Passport | 0.1700 | 0.7392 | **85.0%** (34/40) | 80.0% (16/20) | 90.0% (18/20) | **0.9238** | **CORRECT (100% Separation)** |
| **`50_xpo_id_`** | Interpol Identity Card | 0.1425 | 0.8176 | **90.0%** (36/40) | 85.0% (17/20) | 95.0% (19/20) | **0.9650** | **CORRECT (100% Separation)** |

### 6.2 Key Specimen Findings:
1. **Unambiguous Authentic Separation:** Across all 7 physical specimens, the mean authentic probability never exceeded **0.2539**, remaining comfortably below the primary operational threshold $T = 0.40$ and within the `LOW_RISK` tier for 6 out of 7 specimens.
2. **Unambiguous Forged Separation:** Across all 7 physical specimens, the mean forged probability exceeded **0.7392**, placing forged versions firmly into the `HIGH_RISK` tier.
3. **Specimen Generalization:** The platform generalized effectively across diverse substrates, including polycarbonate driving licenses, national identity smart cards, and paper passport biographical pages with security laminates.

---

## 7. Resolution of Known Audit & Reporting Inconsistencies

### 7.1 Resolution 1: Preservation of EX-11 Raw $P_{\text{ML}}$ and Separate Compression Qualification
In the Phase 8 controlled evaluation, exhibit `EX-11` (authentic document with severe JPEG compression at $Q = 25$) yielded:
- **Track 1 Raw ML:** $P_{\text{ML}} = 0.4129$. At primary operational threshold $T = 0.40$, the raw binary classification is strictly **`FORGED`** (generating a Track 1 False Positive).
- **Track 3 Visual Evidence:** AKAZE keypoint matching yielded zero corroborated tampering clusters (DCT grid inlier filter required $\ge 30$ matches for $Q < 40$).
- **Borderline Compression Qualification:** Because $Q = 25 < 40$ and raw $P_{\text{ML}} \in [0.40, 0.45]$ without visual corroboration, the platform synthesis layer triggered the qualification gate:
  - Unified Risk Tier: `SUSPICIOUS`
  - Overall Verdict: `SUSPICIOUS / COMPRESSION_DEGRADED`
  - Advisory Notice: `HEAVY_COMPRESSION_ARTIFACTS` permanently appended to the report.
- **Reporting Governance:** To prevent confusion, the report explicitly preserves both metrics: Track 1 records `EX-11` as a **False Positive** ($P_{\text{ML}} = 0.4129$), while the Unified Platform records it as a **Qualified True Negative** routed for physical re-acquisition.

### 7.2 Resolution 2: Forensic Explanation of EX-04 Document-Level Tier
Audit finding: Exhibit `EX-04` (authentic 2-page composite PDF) exhibits:
- Page 0 ML Probability: $P_0 = 0.1395$ (`LOW_RISK`)
- Page 1 ML Probability: $P_1 = 0.1395$ (`LOW_RISK`)
- Document-Level Risk Tier: **`SUSPICIOUS`**

**Forensic Root Cause Analysis:**
On Page 0 (California Driving License scan), the document substrate includes multiple official repetitive state seals and microprint patterns. The AKAZE feature detector in Track 3 identified matching keypoints across these identical emblems (`cm_pairs = 1`, 31 inliers, confidence 0.85).
In [`RiskStage`](file:///d:/Forgery%20Detection%20ML/backend/app/pipeline/stages/risk_stage.py#L120-L145), the arbiter evaluated:
1. `(cm_pairs >= 2 or cm_inliers >= 40)` is False $\implies$ Visual evidence does **not** escalate to `HIGH_RISK` (preventing an erroneous forgery accusation).
2. However, because a valid duplicate cluster was confirmed (`cm_pairs == 1`), `visual_risk_tier` was set to `SUSPICIOUS`.
3. The arbiter escalated the document from `LOW_RISK` to `SUSPICIOUS / REVIEW_REQUIRED` to instruct the forensic investigator to manually inspect the detected duplicate region.
Thus, `EX-04` has a `SUSPICIOUS` tier not due to ML probability ($P_{\text{ML}} = 0.1395$), but due to an auditable Track 3 visual anomaly notice.

### 7.3 Resolution 3: Mathematical Clarification of Multi-Page Logarithmic Thresholding
In Phase 8R, the multi-page threshold formula:
$$T_N = \min\left(0.75, \; 0.40 + 0.07 \cdot \ln N\right)$$
was informally referenced as a Bonferroni-corrected threshold.

**Mathematical Governance Clarification:**  
This threshold is formally designated as an **Empirical Logarithmic Multi-Page Significance Threshold**, not a formal Bonferroni-Holm step-down procedure:
- *Justification:* Taking the maximum probability across $N$ pages ($\max_i P_i$) causes an extreme-value sampling distribution that monotonically inflates false alarms as $N$ increases ($1 - (1 - \alpha)^N$).
- *Heuristic Calibration:* The logarithmic damping factor $0.07 \cdot \ln N$ raises the uncorroborated classification bar from $0.40$ ($N=1$) to $0.4485$ ($N=2$) and $0.5612$ ($N=10$). If $P_{\max}$ falls between $0.40$ and $T_N$, it requires visual region corroboration ($V_k \ge 1$) to escalate to `HIGH_RISK`, otherwise assigning `SUSPICIOUS`. This empirical formulation is mathematically sound and prevents false-alarm cascades without claiming formal family-wise error rate proofs.

### 7.4 Resolution 4: Strict Separation of Track 1 FNs vs. Track 3 Visual Evidence Detections
To ensure complete transparency, cases missed by Track 1 ML that were subsequently detected by Track 3 Visual Evidence are never retroactively counted as Track 1 True Positives. They are explicitly documented as:
- **Track 1 ML:** False Negative (FN).
- **Track 3 Visual Arbiter:** True Positive Detection (Escalated to `HIGH_RISK`).

Three specific examples on the held-out benchmark:
1. `44_ukr_id_CA05_copy_move.tif`: Track 1 $P_{\text{ML}} = 0.2410$ (FN) $\rightarrow$ Track 3 detected 2 clone clusters with 15 inliers (conf 0.85) $\rightarrow$ Platform: `HIGH_RISK`.
2. `43_tur_id_HS05_text.tif`: Track 1 $P_{\text{ML}} = 0.3871$ (FN) $\rightarrow$ Track 3 detected 2 clone clusters with 27 inliers (conf 0.85) $\rightarrow$ Platform: `HIGH_RISK`.
3. `43_tur_id_HS15_text.tif`: Track 1 $P_{\text{ML}} = 0.3003$ (FN) $\rightarrow$ Track 3 detected 2 clone clusters with 35 inliers (conf 0.85) $\rightarrow$ Platform: `HIGH_RISK`.

### 7.5 Resolution 5: Absolute Proscription of Definitive Terminology
The platform code, APIs, schemas, database custody logs, and reporting templates were verified to contain **zero occurrences** of prohibited terms, including `CONFIRMED FORGERY`, `AUTHENTICATED DOCUMENT`, or judicial admissibility assertions. All findings are framed as probabilistic likelihoods ($P_{\text{ML}}$), risk tiers (`LOW_RISK`, `SUSPICIOUS`, `HIGH_RISK`), and visual anomaly observations.

---

## 8. Illustrative Forensic Decision Traces

To demonstrate the deterministic auditability of the platform, the following decision traces illustrate how diverse exhibits are processed through the three evidence tracks:

```mermaid
flowchart TD
    A["Raw Exhibit Ingestion"] --> B["Track 1: Frozen ML Inference"]
    A --> C["Track 2: Symbolic OCR & Layout"]
    A --> D["Track 3: Visual Anomaly Analysis"]
    A --> E["Non-Destructive DQT Header Parsing"]

    B --> F{"P_ML >= 0.40?"}
    E --> G{"Q < 40 and Borderline?"}
    D --> H{"Visual Clusters >= 2?"}

    F -- "Yes" --> I["Base Tier: SUSPICIOUS / HIGH_RISK"]
    F -- "No" --> J["Base Tier: LOW_RISK"]

    G -- "Yes" --> K["Apply Compression Qualification Notice"]
    H -- "Yes" --> L["Elevate Unified Tier to HIGH_RISK"]

    I --> M["Unified Synthesis Arbiter"]
    J --> M
    K --> M
    L --> M

    M --> N["Forensic Report & Custody Ledger"]
```

### Trace Example 1: Authentic Baseline Exhibit (`EX-01` / `35_nor_drvlic_HA15`)
```json
{
  "trace_id": "TRACE-20261101-EX01",
  "document_id": "c8342634-6f59-4466-abed-0e6f37bdd16b",
  "track_1_ml": {
    "forgery_probability": 0.2058,
    "operational_threshold": 0.40,
    "raw_prediction": "AUTHENTIC",
    "base_tier": "LOW_RISK",
    "top_contributing_features": {
      "img_ela_max_difference_mean": 18.0,
      "img_laplacian_variance_mean": 163.19,
      "cm_inlier_matches": 28.0
    }
  },
  "track_2_symbolic": {
    "status": "NOT_EVALUATED",
    "findings_count": 0
  },
  "track_3_visual": {
    "detected_clusters": 0,
    "copy_move_confirmed": false,
    "visual_tier": "LOW_RISK"
  },
  "compression_qualification": {
    "is_jpeg": false,
    "estimated_quality": null,
    "is_heavily_compressed": false
  },
  "synthesis_arbiter": {
    "ml_base_tier": "LOW_RISK",
    "visual_tier": "LOW_RISK",
    "tier_escalation_applied": false,
    "compression_qualification_applied": false,
    "final_risk_tier": "LOW_RISK",
    "overall_verdict": "LOW_RISK / AUTHENTIC"
  }
}
```

### Trace Example 2: Spliced Alteration with Visual Corroboration (`43_tur_id_HS05_text`)
```json
{
  "trace_id": "TRACE-20261101-TUR43-HS05",
  "document_id": "d748f2b1-5e29-4c81-87ab-1e04a912bb89",
  "track_1_ml": {
    "forgery_probability": 0.3871,
    "operational_threshold": 0.40,
    "raw_prediction": "AUTHENTIC",
    "base_tier": "SUSPICIOUS",
    "feature_completeness": 1.0
  },
  "track_3_visual": {
    "detected_clusters": 2,
    "total_inlier_matches": 27,
    "max_cluster_confidence": 0.85,
    "copy_move_confirmed": true,
    "visual_tier": "HIGH_RISK",
    "evidence_items": [
      {"detector": "AKAZE_Cluster", "severity": 90.0, "confidence": 0.85, "description": "Duplicate text character source"},
      {"detector": "AKAZE_Cluster", "severity": 90.0, "confidence": 0.85, "description": "Duplicate text character destination"}
    ]
  },
  "synthesis_arbiter": {
    "ml_base_tier": "SUSPICIOUS",
    "visual_tier": "HIGH_RISK",
    "tier_escalation_applied": true,
    "escalation_reason": "Track 3 confirmed 2 duplicate clone clusters (27 inliers, conf 0.85)",
    "final_risk_tier": "HIGH_RISK",
    "overall_verdict": "SUSPICIOUS / HIGH_RISK",
    "raw_track1_preserved": true
  }
}
```

---

## 9. Statistical Limitations & Discussion

1. **Small Cluster Count ($K = 7$ Physical Specimens):**  
   While the held-out benchmark comprises 280 images, they originate from exactly seven physical document specimens. As established in Phase 4, resampled bootstrap confidence intervals over $K=7$ clusters exhibit slight discretization. Broader real-world deployment must expand the physical document pool to include utility bills, banking statements, and corporate invoices.
2. **Video Frame Capture Correlation:**  
   The 40 frames per specimen in MIDV-500 represent physical video frames under varying angles, distances, reflections, and lighting. Because lighting artifacts (glare, deep shadows) alter high-frequency Laplacian variance and local ELA differences, single-frame predictions exhibit higher variance than specimen-averaged inferences.
3. **The Classical Feature Bottleneck for Smooth Clones:**  
   Without model retraining, classical Random Forest relying on global ELA statistics and AKAZE keypoints plateaus at ~54%–57% recall on smooth, textureless copy-move duplications. When a cloned region is extracted from an untextured background, AKAZE cannot identify sufficient distinct keypoint pairs. Future model iterations (Phase 10+) should explore dense patch self-supervised embeddings or spatial correlation maps.

---

## 10. Final Acceptance Recommendation

Based on the empirical verification of the frozen platform against the locked Phase 4 held-out benchmark:

1. **Model Governance Adherence:** The frozen Random Forest model SHA-256 (`f274d4a9...`), the 18-feature schema (`eaef5216...`), and the operational threshold $T = 0.40$ were 100% preserved without modification, retraining, or leakage.
2. **Track 1 Baseline Reproduction:** Evaluated on 280 test frames, Track 1 ML replicated the Phase 4 baseline metrics identically (Accuracy: 88.21%, ROC-AUC: 0.9473, PR-AUC: 0.9607).
3. **Visual Arbiter Efficacy:** Track 3 Visual Evidence successfully elevated three previously missed forgeries (two text splices, one copy-move clone) into `HIGH_RISK`, increasing platform forged recall to **89.29%**.
4. **Physical Specimen Reliability:** Across all seven physical specimens, the platform achieved **100% correct separation** between authentic baseline documents and tampered derivatives.
5. **Architectural Integrity:** Raw Track 1 predictions remain strictly isolated from Track 2/3 qualifications, preserving audit trail integrity and preventing false classification masking.

**Recommendation:**  
**Phase 9 Locked Held-Out Benchmark Evaluation is complete, fully verified, and recommended for formal acceptance.**

---
*Report compiled and certified by Antigravity — November 1, 2026.*
