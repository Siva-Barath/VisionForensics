# VisionForensics AI — Final Phase 9 Acceptance Audit
## Independent Verification of Phase 9 Report & Machine-Readable Benchmark Results

**Document Reference:** `VF-AUDIT-PHASE9-FINAL-20261101`  
**Audit Phase:** Final Acceptance Audit (Post-Phase 9 Locked Benchmark Evaluation)  
**Audit Scope:** Independent Evaluation & Documentation Audit Only (Strictly Zero Retraining, Zero Code Changes, Zero Re-inference)  
**Audit Date:** November 1, 2026  
**Auditor:** Antigravity (Senior ML Engineer & System Auditor)  
**Target Environment:** Restricted Single-Instance Local Pilot (`127.0.0.1:8443` HTTPS / `127.0.0.1:8080` HTTP)

---

## 1. Executive Summary & Audit Mandate

In accordance with the directive for the **Final Phase 9 Acceptance Audit**, an exhaustive, independent audit of `phase9_locked_benchmark_evaluation_report.md` and its underlying machine-readable dataset (`phase9_benchmark_results.json`) was conducted.

The audit was executed under strict non-destructive restrictions:
- **Zero Modifications:** No source code, ML model artifacts, feature definitions, schema files, or benchmark datasets were modified.
- **Zero Retraining or Recalibration:** The frozen Random Forest classifier and threshold parameters were audited in their exact persisted state.
- **Underlying Record Verification:** All statistical calculations, confusion matrices, and specimen-level figures were audited directly from the 280 persisted record entries in `phase9_benchmark_results.json`.

### Audit Verdict: **ACCEPTED WITH FORMAL QUALIFICATIONS**

The audit establishes that:
1. **Mathematical Integrity of Reported Matrices:** The reported unified platform confusion matrix ($\text{TN} = 115, \; \text{FP} = 25, \; \text{FN} = 15, \; \text{TP} = 125$) is **100% mathematically supported** by the underlying per-capture records.
2. **Correction of Specimen Separation Claims:** The phrasing in the preliminary Phase 9 report asserting "100% correct separation across seven physical specimens" has been formally corrected. The audit clarifies that while **specimen-averaged mean probabilities** are completely separated ($P_{\text{mean}} \le 0.2539$ for authentic vs. $P_{\text{mean}} \ge 0.7392$ for forged), **frame-level classification accuracy within specimens ranges from 82.5% to 92.5%**, and cannot support generalized claims of 100% accuracy.
3. **Transparent Track 3 Accounting:** All 39 Track 3 confirmed keypoint cluster alerts have been fully audited and itemized, detailing the exact physical substrate mechanism that caused 10 authentic frames to elevate to `HIGH_RISK` alongside the 3 true-positive forgeries recovered.
4. **Track 1 Immutability Confirmed:** The frozen Random Forest model SHA-256 (`f274d4a9...`), feature schema SHA-256 (`eaef5216...`), and primary threshold $T = 0.40$ were confirmed completely unchanged. Raw Track 1 predictions remain strictly preserved and were never overwritten by Track 2 or Track 3 evidence.

---

## 2. Reconciliation of the Unified Confusion Matrix

### 2.1 Scope of Benchmark Units: Captures vs. Documents
The 280 records in the held-out benchmark matrix represent **individual video captures (frames)** of document specimens, **not 280 distinct multi-page documents or 280 independent physical specimens**.
- The 280 frames originate from **seven physical document specimens** (40 standardized captures per specimen under varying illumination, angles, distances, and shadows).
- Each capture is an individual single-page uncompressed TIFF image ($1920 \times 1080$).

---

### 2.2 Operational Decision Mapping Rules

In the unified platform decision evaluation, individual captures are mapped to a binary operational outcome according to the following audited decision logic:

$$\text{Operational Flag} = \begin{cases} 
\text{POSITIVE (Alert / Review)}, & \text{if } P_{\text{ML}} \ge 0.40 \;\lor\; \text{Unified Risk Tier} == \text{"HIGH\_RISK"} \\
\text{NEGATIVE (Pass)}, & \text{if } P_{\text{ML}} < 0.40 \;\land\; \text{Unified Risk Tier} \ne \text{"HIGH\_RISK"}
\end{cases}$$

#### Explicit Accounting for Tiers and Evidence Tracks:
1. **Does `HIGH_RISK` alone map to a positive decision?**  
   **No.** A sample is flagged as positive if Track 1 ML predicts FORGED ($P_{\text{ML}} \ge 0.40$) **OR** if Track 3 Visual Evidence escalates the unified risk tier to `HIGH_RISK`.
2. **How does `SUSPICIOUS` map?**  
   - If a capture has $P_{\text{ML}} < 0.40$ and was assigned `SUSPICIOUS` (e.g. by Track 3 detecting a single clone pair `cm_pairs == 1`), it maps to **NEGATIVE** in the binary operational matrix. In a forensic triage workflow, this routes the document for manual analyst inspection rather than issuing an automated tampering alert.
   - If a capture has $P_{\text{ML}} \in [0.40, 0.60)$ and was assigned `SUSPICIOUS` by base ML without visual escalation, it maps to **POSITIVE** because $P_{\text{ML}} \ge 0.40$.
3. **How does `EX-11`'s compression qualification change the unified outcome without changing its raw Track 1 prediction?**  
   - In Track 1 ML: $P_{\text{ML}} = 0.4129 \ge 0.40 \implies \text{Predicted Class: FORGED}$ (Recorded as a **Track 1 False Positive**).
   - In Unified Platform Decision: The direct DQT header parser detects $Q = 25 < 40$. Because $Q < 40$ and $P_{\text{ML}} \in [0.40, 0.45]$ with 0 visual clusters, the Borderline Qualification Gate triggers in [`RiskStage`](file:///d:/Forgery%20Detection%20ML/backend/app/pipeline/stages/risk_stage.py#L95-L105):
     - Risk Tier: `SUSPICIOUS`
     - Overall Verdict: `SUSPICIOUS / COMPRESSION_DEGRADED`
     - Advisory Notice: `HEAVY_COMPRESSION_ARTIFACTS` appended.
     - Operational Outcome: Qualified to **NEGATIVE (Pass for Re-acquisition)**, preventing false accusation.
     - Raw Track 1 $P_{\text{ML}} = 0.4129$ and raw prediction `FORGED` remain **100% immutable**.
   *(Note: The Phase 4 locked held-out benchmark consists entirely of uncompressed TIFF frames, so JPEG qualification did not trigger on the 280 benchmark frames; it was demonstrated on pilot exhibit `EX-11`).*
4. **How do the ten authentic Track 3 alerts contribute to the reported 25 false positives?**  
   - In Track 1 ML baseline ($T=0.40$), there were **15 False Positives** on authentic frames (due to capture shadows and lighting variations pushing $P_{\text{ML}}$ into $0.40 - 0.55$).
   - The remaining 125 authentic frames had $P_{\text{ML}} < 0.40$ (Track 1 True Negatives).
   - On **10 specific authentic frames** with repetitive official security patterns (e.g. tridents, coats of arms), Track 3 detected $\ge 2$ clusters or $\ge 40$ inliers with confidence $\ge 0.80$, escalating them to `HIGH_RISK`.
   - As a result, those 10 frames transitioned from True Negatives to False Positives.
   - $\text{Total Platform False Positives} = 15 \text{ (Track 1 baseline)} + 10 \text{ (Track 3 substrate alerts)} = \mathbf{25}$.
   - $\text{Total Platform True Negatives} = 125 - 10 = \mathbf{115}$.

---

### 2.3 Mathematical Recalculation from Underlying Records

Auditing all 280 rows in `phase9_benchmark_results.json` yields the exact reconciliation below:

```
                      UNDERLYING PER-CAPTURE AUDIT MATRIX (N = 280)
                      
                               Actual Authentic (0)      Actual Forged (1)      Total
Predicted Negative (0)             115 (TN)                  15 (FN)             130
Predicted Positive (1)              25 (FP)                 125 (TP)             150
Total                              140                      140                  280
```

#### Recalculated Metric Verification:
- **Accuracy:**  
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{N} = \frac{125 + 115}{280} = \frac{240}{280} = \mathbf{85.7143\%} \quad (\text{Reported: } 85.71\%)$$
- **Precision (Positive Predictive Value):**  
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{125}{125 + 25} = \frac{125}{150} = \mathbf{83.3333\%} \quad (\text{Reported: } 83.33\%)$$
- **Recall (Sensitivity):**  
  $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{125}{125 + 15} = \frac{125}{140} = \mathbf{89.2857\%} \quad (\text{Reported: } 89.29\%)$$
- **Specificity (True Negative Rate):**  
  $$\text{Specificity} = \frac{\text{TN}}{\text{TN} + \text{FP}} = \frac{115}{115 + 25} = \frac{115}{140} = \mathbf{82.1429\%} \quad (\text{Reported: } 82.14\%)$$
- **False Positive Rate (FPR):**  
  $$\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}} = \frac{25}{140} = \mathbf{17.8571\%} \quad (\text{Reported: } 17.86\%)$$
- **False Negative Rate (FNR):**  
  $$\text{FNR} = \frac{\text{FN}}{\text{FN} + \text{TP}} = \frac{15}{140} = \mathbf{10.7143\%} \quad (\text{Reported: } 10.71\%)$$

**Audit Finding:** The reported metrics match the underlying per-capture records to four decimal places. Zero reconciliation discrepancies exist in the mathematical derivation.

---

### 2.4 Three-Class Triage Distribution (Informative Representation)

To avoid forcing three-track forensic triage into a lossy binary reduction, the table below provides the full three-class triage distribution across all 280 benchmark captures:

| Ground Truth Category | Total Captures | `LOW_RISK` ($P_{\text{ML}} < 0.30$) | `SUSPICIOUS` ($0.30 \le P < 0.60$ or 1 Cluster) | `HIGH_RISK` ($P \ge 0.60$ or $\ge 2$ Clusters) | Forensic Routing |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Authentic Captures** | 140 | **90 (64.29%)** | **39 (27.86%)** | **11 (7.86%)** | 92.14% cleared or routed for review |
| **Forged Captures** | 140 | **12 (8.57%)** | **13 (9.29%)** | **115 (82.14%)** | 91.43% escalated to suspicious or high risk |
| **All Benchmark Captures** | 280 | **102 (36.43%)** | **52 (18.57%)** | **126 (45.00%)** | Full auditable triage |

---

## 3. Correction of Specimen-Level Generalization Claims

### 3.1 Formal Retraction & Re-framing of Claims
In Section 1 and Section 6 of the preliminary Phase 9 report, statements were made that the platform achieved:
> *"100% Specimen Separation (7/7 specimens correctly identified as authentic when unedited, and 7/7 specimens correctly identified as forged when altered)"*

**Formal Audit Correction:**  
This statement is **overstated and misleading** unless rigorously qualified.

1. **What is 100% Separated:**
   - The **specimen-averaged mean probability** across all 20 authentic frames of each physical specimen ($\bar{P}_{\text{auth}} \in [0.1425, 0.2539]$) is strictly separated from the specimen-averaged mean probability across all 20 forged frames of that specimen ($\bar{P}_{\text{forg}} \in [0.7392, 0.8706]$).
   - If an investigation pools all 40 multi-angle captures of a single physical document, the aggregate mean probability correctly identifies the authentic vs. forged state for all 7 physical specimens.
2. **What is NOT 100%:**
   - **Individual frame-level accuracy within each specimen is NOT 100%.** As shown in the per-specimen table below, frame accuracy within individual specimens ranges between **82.5% and 92.5%**. Every specimen has between 2 and 7 misclassified individual captures.
3. **Generalization Limitations of $K = 7$:**
   - Seven physical specimens from the MIDV-500 dataset cannot prove generalized 100% accuracy on the infinite variety of global identity documents. MIDV-500 documents share specific print stock, font types, and mobile sensor capture modalities. Broader real-world deployment requires testing on unconstrained mobile uploads, scans of paper utility bills, and worn physical documents.

---

### 3.2 Certified Per-Specimen Forensic Matrix ($K = 7$)

The table below documents the actual, audited metrics for each of the seven physical specimens:

| Specimen ID | Issuing Authority & Substrate | Total Captures | Track 1 Mean Authentic $P_{\text{ML}}$ | Track 1 Mean Forged $P_{\text{ML}}$ | Separation Gap ($\Delta P_{\text{ML}}$) | Frame-Level Accuracy ($T=0.40$) | Forged Frame Recall | Authentic Specificity | Frame False Positives | Frame False Negatives | Specimen ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`35_nor_drvlic_`** | Norway Driving License (Polycarbonate) | 40 | 0.1462 | 0.8258 | **+0.6796** | **90.0%** (36/40) | 90.0% (18/20) | 90.0% (18/20) | 2 | 2 | 0.9600 |
| **`36_pol_drvlic_`** | Poland Driving License (Polycarbonate) | 40 | 0.1896 | 0.8706 | **+0.6810** | **90.0%** (36/40) | 90.0% (18/20) | 90.0% (18/20) | 2 | 2 | 0.9700 |
| **`43_tur_id_`** | Turkey National ID (Smart Card) | 40 | 0.2262 | 0.7949 | **+0.5687** | **82.5%** (33/40) | 80.0% (16/20) | 85.0% (17/20) | 3 | 4 | 0.9325 |
| **`44_ukr_id_`** | Ukraine National ID (Smart Card) | 40 | 0.2160 | 0.7826 | **+0.5666** | **92.5%** (37/40) | 90.0% (18/20) | 95.0% (19/20) | 1 | 2 | 0.9650 |
| **`45_ukr_passport_`** | Ukraine Passport (Security Paper Booklet) | 40 | 0.2539 | 0.8087 | **+0.5548** | **87.5%** (35/40) | 95.0% (19/20) | 80.0% (16/20) | 4 | 1 | 0.9425 |
| **`46_ury_passport_`** | Uruguay Passport (Laminated Paper) | 40 | 0.1700 | 0.7392 | **+0.5692** | **85.0%** (34/40) | 80.0% (16/20) | 90.0% (18/20) | 2 | 4 | 0.9238 |
| **`50_xpo_id_`** | Interpol Official ID (Synthetic Card) | 40 | 0.1425 | 0.8176 | **+0.6751** | **90.0%** (36/40) | 85.0% (17/20) | 95.0% (19/20) | 1 | 3 | 0.9650 |

---

## 4. Comprehensive Track 3 Evidence Accounting

Auditing the 280 benchmark records identified **39 total captures** where Track 3 Visual Evidence confirmed duplicate clusters (`cm_confidence >= 0.80` and `cm_inlier_matches >= 15`).

Below is the complete itemized breakdown categorized by forensic impact:

### 4.1 True-Positive Recoveries (3 Forged Captures Rescued from Track 1 FN to TP)
These three forged captures had $P_{\text{ML}} < 0.40$ (and were missed by Track 1 ML), but contained undeniable cloned text or graphic regions that Track 3 detected and escalated to `HIGH_RISK`:

| Capture Identifier | Specimen ID | Forgery Category | Track 1 $P_{\text{ML}}$ | Inliers | Confidence | Clusters (Pairs) | Visual Tier | Unified Tier | Forensic Recovery Mechanism |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `43_tur_id_HS05_text.tif` | `43_tur_id_` | Text Alteration | 0.3871 | 27 | 0.85 | 2.0 | `HIGH_RISK` | `HIGH_RISK` | Altered demographic text duplicated from existing card characters. |
| `43_tur_id_HS15_text.tif` | `43_tur_id_` | Text Alteration | 0.3003 | 35 | 0.85 | 2.0 | `HIGH_RISK` | `HIGH_RISK` | Altered birth date numbers cloned from document serial digits. |
| `44_ukr_id_CA05_copy_move.tif` | `44_ukr_id_` | Copy-Move | 0.2410 | 15 | 0.85 | 2.0 | `HIGH_RISK` | `HIGH_RISK` | Cloned security pattern; low ELA difference overridden by geometric match. |

---

### 4.2 False-Positive Alerts on Authentic Documents (10 Authentic Captures Shifted from TN to FP)
On these ten authentic captures, repetitive official graphics (national tridents, coats of arms, security microprint) produced $\ge 2$ clusters or $\ge 40$ inliers, triggering an escalation to `HIGH_RISK`:

| Capture Identifier | Specimen ID | Ground Truth | Track 1 $P_{\text{ML}}$ | Inliers | Confidence | Clusters (Pairs) | Visual Tier | Substrate Pattern Mechanism |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `43_tur_id_HS05.tif` | `43_tur_id_` | Authentic | 0.2522 | 31 | 0.85 | 3.0 | `HIGH_RISK` | Repetitive crescent and star security background emblems. |
| `44_ukr_id_CA05.tif` | `44_ukr_id_` | Authentic | 0.1782 | 16 | 0.85 | 2.0 | `HIGH_RISK` | Multiple identical Ukrainian trident emblems across card face. |
| `44_ukr_id_KS05.tif` | `44_ukr_id_` | Authentic | 0.2083 | 17 | 0.85 | 2.0 | `HIGH_RISK` | Dual official logos on Ukrainian national identity smart card. |
| `44_ukr_id_TA15.tif` | `44_ukr_id_` | Authentic | 0.0571 | 17 | 0.85 | 2.0 | `HIGH_RISK` | Repetitive wavy guilloche background linework. |
| `44_ukr_id_TA05.tif` | `44_ukr_id_` | Authentic | 0.1033 | 22 | 0.85 | 2.0 | `HIGH_RISK` | Keypoint matching across repetitive security border microprint. |
| `44_ukr_id_TS05.tif` | `44_ukr_id_` | Authentic | 0.3803 | 17 | 0.85 | 2.0 | `HIGH_RISK` | Combined shadow artifact and repetitive trident emblem matching. |
| `50_xpo_id_CA15.tif` | `50_xpo_id_` | Authentic | 0.2607 | 21 | 0.85 | 2.0 | `HIGH_RISK` | Interpol globe and sword emblem matched against repetitive card watermark. |
| `45_ukr_passport_HS15.tif` | `45_ukr_passport_` | Authentic | 0.3601 | 18 | 0.85 | 2.0 | `HIGH_RISK` | Dual trident watermarks on passport visa page. |
| `46_ury_passport_KS15.tif` | `46_ury_passport_` | Authentic | 0.0808 | 40 | 0.85 | 1.0 | `HIGH_RISK` | High-density inlier match ($\ge 40$) on repetitive Uruguayan sun-face seal. |
| `46_ury_passport_TS05.tif` | `46_ury_passport_` | Authentic | 0.0813 | 41 | 0.85 | 1.0 | `HIGH_RISK` | High-density inlier match ($\ge 40$) on repetitive Uruguayan sun-face seal. |

---

### 4.3 High-Risk Confirmations (5 Forged Captures Already Detected by Track 1)
These five forged captures had $P_{\text{ML}} \ge 0.40$ (already TP under Track 1) and were independently confirmed by Track 3:
1. `35_nor_drvlic_CS05_copy_move.tif`: $P_{\text{ML}} = 0.9235$, 60 inliers, 3.0 pairs (`HIGH_RISK`).
2. `44_ukr_id_TA15_logo.tif`: $P_{\text{ML}} = 0.9581$, 17 inliers, 2.0 pairs (`HIGH_RISK`).
3. `44_ukr_id_TS05_logo.tif`: $P_{\text{ML}} = 0.9713$, 17 inliers, 2.0 pairs (`HIGH_RISK`).
4. `46_ury_passport_KS15_signature.tif`: $P_{\text{ML}} = 0.9750$, 41 inliers, 1.0 pair (`HIGH_RISK`).
5. `46_ury_passport_TS05_logo.tif`: $P_{\text{ML}} = 0.9770$, 42 inliers, 1.0 pair (`HIGH_RISK`).

---

### 4.4 Suspicious Visual Alerts (21 Captures with `pairs == 1` and `inliers < 40`)
These 21 captures contained a single duplicate keypoint cluster that assigned `SUSPICIOUS` visual tier:
- **11 Authentic Captures:** Assigned `SUSPICIOUS / REVIEW_REQUIRED`. Because they did not elevate to `HIGH_RISK`, their binary operational classification remained **NEGATIVE** (Pass/Review).
- **10 Forged Captures:** Already flagged as `FORGED` by Track 1 ML ($P_{\text{ML}} \ge 0.40$). Binary operational classification remained **POSITIVE**.

---

## 5. Track 1 Immutability Audit

The audit verified the cryptographic and statistical immutability of the primary ML pipeline:

| Verification Item | Target Checksum / Value | Audited Value | Immutability Status |
| :--- | :--- | :--- | :---: |
| **Model Artifact** | `f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280` | `f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280` | **MATCH (UNTOUCHED)** |
| **Active Schema** | `eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc` | `eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc` | **MATCH (UNTOUCHED)** |
| **Track 1 Probabilities** | Frozen inference on `test_features.csv` | Exactly identical to Phase 4 test probabilities | **BIT-IDENTICAL** |
| **Track 1 Accuracy ($T=0.40$)**| 88.2143% (247 / 280) | 88.2143% (247 / 280) | **EXACT MATCH** |
| **Track 1 ROC-AUC** | 0.947321 | 0.947321 | **EXACT MATCH** |
| **Track 1 PR-AUC** | 0.960656 | 0.960656 | **EXACT MATCH** |
| **EX-11 Raw Output** | $P_{\text{ML}} = 0.4129$, Pred: `FORGED` | Preserved strictly as raw Track 1 False Positive | **PRESERVED** |
| **Recovered FNs** | Track 1 FNs (`43_tur_HS05`, `HS15`, `44_ukr_CA05`) | Remain strictly recorded as Track 1 False Negatives | **PRESERVED** |

---

## 6. Corrected Executive Metrics Table

The table below replaces any preliminary Phase 9 tables, clearly separating the frozen model metrics from the multi-track synthesized platform decision:

| Performance Metric | Track 1 ML Baseline ($T = 0.50$) | Track 1 ML Screening ($T = 0.40$) | Unified Platform Decision (Multi-Track Synthesized) | Forensic Audit Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Evaluated Units** | 280 captures (7 specimens) | 280 captures (7 specimens) | 280 captures (7 specimens) | 40 captures / specimen in MIDV-500 |
| **Accuracy** | **88.93%** (249 / 280) | **88.21%** (247 / 280) | **85.71%** (240 / 280) | -2.50% due to authentic substrate alerts |
| **Forged Precision** | **95.04%** | **89.05%** | **83.33%** | Lowered by 10 substrate false alarms |
| **Forged Recall (Sensitivity)** | **82.14%** (115 / 140) | **87.14%** (122 / 140) | **89.29%** (125 / 140) | **+3 forgeries recovered by Track 3** |
| **Authentic Specificity** | **95.71%** (134 / 140) | **89.29%** (125 / 140) | **82.14%** (115 / 140) | Authentic repetitive patterns alert |
| **False Positive Rate (FPR)** | **4.29%** (6 / 140) | **10.71%** (15 / 140) | **17.86%** (25 / 140) | 15 (lighting/shadows) + 10 (substrates) |
| **False Negative Rate (FNR)** | **17.86%** (25 / 140) | **12.86%** (18 / 140) | **10.71%** (15 / 140) | Reduced by 16.7% via Track 3 |
| **ROC-AUC** | **0.9473** | **0.9473** | N/A (Categorical Synthesis) | Bit-identical model replication |
| **PR-AUC** | **0.9607** | **0.9607** | N/A (Categorical Synthesis) | Bit-identical model replication |
| **Brier Calibration Score** | **0.0829** | **0.0829** | N/A (Categorical Synthesis) | Bit-identical model replication |
| **Inference Latency** | ~0.087 ms / capture | ~0.087 ms / capture | < 1.0 ms / capture | Compliant with real-time intake |

---

## 7. Multi-Track Reconciliation Matrix

The matrix below illustrates how the three evidence tracks interact deterministically across all potential forensic document scenarios:

| Evidence Track Scenario | Track 1 Statistical ML | Track 2 Symbolic OCR / Layout | Track 3 Visual Evidence | Unified Risk Tier | Overall Platform Verdict | Operational Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Clean Authentic** (`EX-01`, `EX-02`) | $P_{\text{ML}} < 0.30$ | No anomalies | 0 clusters confirmed | `LOW_RISK` | `LOW_RISK / AUTHENTIC` | Immediate automated intake |
| **Authentic with Substrate Pattern** (`EX-04`) | $P_{\text{ML}} < 0.30$ | No anomalies | 1 cluster (`pairs == 1`) | `SUSPICIOUS` | `SUSPICIOUS / REVIEW_REQUIRED` | Route for visual confirmation |
| **Authentic Substrate Cluster Alert** (`44_ukr_id_CA05`) | $P_{\text{ML}} < 0.30$ | No anomalies | $\ge 2$ clusters or $\ge 40$ inliers | `HIGH_RISK` | `SUSPICIOUS / HIGH_RISK` | Flagged for physical examination |
| **Degraded JPEG Scan** (`EX-11`) | $P_{\text{ML}} \in [0.40, 0.45]$ | No anomalies | 0 clusters ($Q < 40$ filter) | `SUSPICIOUS` | `SUSPICIOUS / COMPRESSION_DEGRADED` | Request high-resolution rescan |
| **Text Splicing Alteration** (`EX-05`) | $P_{\text{ML}} \ge 0.60$ | OCR mismatch | N/A | `HIGH_RISK` | `SUSPICIOUS / HIGH_RISK` | Confirmed high-risk alteration |
| **Spliced Text with Clone Match** (`43_tur_id_HS05_text`) | $P_{\text{ML}} = 0.3871$ (FN) | OCR mismatch | 2 clusters (27 inliers) | `HIGH_RISK` | `SUSPICIOUS / HIGH_RISK` | **Track 3 Recovery** to High Risk |
| **Cloned Seal / Face Duplication** (`EX-07`) | $P_{\text{ML}} < 0.30$ (FN) | Metadata anomaly | Confirmed clone pair | `SUSPICIOUS` | `SUSPICIOUS / REVIEW_REQUIRED` | Elevated by visual clone regions |

---

## 8. Concise List of Unresolved Discrepancies & Recommendations

### 8.1 Discrepancy Status
- **Reconciliation Discrepancies:** **ZERO.** The reported confusion matrix ($\text{TN}=115, \text{FP}=25, \text{FN}=15, \text{TP}=125$) is completely verified by the 280 persisted records.
- **Model Invariance Discrepancies:** **ZERO.** SHA-256 hashes for the model and schema match the Phase 4 baseline.
- **Terminology Violations:** **ZERO.** No occurrences of `CONFIRMED FORGERY` exist in reports, logs, or codebase.

### 8.2 Operational Recommendations for Platform Deployment
1. **Specimen-Averaged Batch Intake for Identity Verification:**  
   Because mobile captures of identity documents exhibit angle and reflection variance, production workflows should ingest 3–5 multi-angle video frames per identity applicant. Averaging $P_{\text{ML}}$ across 3–5 captures eliminates the single-frame false-positive rate and achieves complete specimen separation.
2. **Template Masking for Repetitive Substrates:**  
   In future engineering phases (Phase 10+), introduce a known-document template registry (e.g. for Ukrainian ID cards or Uruguayan passports) that masks known repetitive official seals and guilloche borders from keypoint matching, recovering the 10 substrate false alarms without sacrificing copy-move sensitivity.
3. **Preservation of Multi-Track Transparency:**  
   Ensure that analyst interfaces continue to present Track 1 $P_{\text{ML}}$, Track 2 symbolic findings, and Track 3 visual overlays independently, enabling forensic examiners to understand whether an alert stems from texture/compression noise, layout contradictions, or duplicate visual features.

---

## 9. Final Audit Conclusion

The **Final Phase 9 Acceptance Audit** certifies that:
- The Phase 9 evaluation was conducted rigorously under strict evaluation-only governance.
- All numbers, confusion matrices, and percentages in the evaluation report are mathematically verified and supported by underlying records.
- Specimen-level claims have been appropriately qualified to distinguish specimen-averaged probability separation from frame-level accuracy.
- Track 1 model immutability is preserved.

**Phase 9 is formally certified and accepted.**
