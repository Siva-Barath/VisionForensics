# VisionForensics AI — Release Manifest
## Final Codebase Freeze & Deployment Environment Manifest

**Release Version:** `v1.0.0-pilot.accepted`  
**Freeze Status:** **FROZEN & VERIFIED**  
**Freeze Date:** November 1, 2026  
**Platform Reference:** VisionForensics AI (Intelligent Document Tampering Detection & Forensic Analysis Platform)

---

## 1. Cryptographic Model & Schema Hashes

| Artifact Identifier | Filesystem Location | Cryptographic SHA-256 Checksum | Audit Status |
| :--- | :--- | :--- | :---: |
| **Random Forest Model** | `backend/app/ml/artifacts/random_forest.joblib` | `f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280` | **VERIFIED (LOCKED)** |
| **Active Feature Schema** | `backend/app/ml/artifacts/active_feature_schema.json` | `eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc` | **VERIFIED (LOCKED)** |
| **Logistic Regression (Ref)**| `backend/app/ml/artifacts/logistic_regression.joblib` | `9b3fe1fa02ba30bf2ec09c30bfdafe3108c5c56783df8298dc9688439ea861a7` | **VERIFIED (LOCKED)** |
| **Feature Scaler** | `backend/app/ml/artifacts/scaler.joblib` | `0229fa17cfb235ee41fa3d207f23a67d01859c629fbbe9557bf8e05cb6b38c20` | **VERIFIED (LOCKED)** |

---

## 2. Core Source Code Snapshot Hashes

The following SHA-256 checksums uniquely define the exact state of the accepted platform codebase:

| Component / Subsystem | Source File Path | SHA-256 Checksum |
| :--- | :--- | :--- |
| **Pipeline Coordinator** | `backend/app/pipeline/pipeline.py` | `cfe3f3c3d3cdceb08f45e35c3d36e3806fd3327edbed15fdb68913f72d53ec56` |
| **Analysis Context** | `backend/app/pipeline/context.py` | `80ba048d9b761797d53c9a2af92e62be22f4c6c5058e77e64918ef8d99155999` |
| **ML Inference Stage** | `backend/app/pipeline/stages/ml_inference_stage.py` | `5ec67de3108317fa7a8c8c0815eadafc19b045b23cfb7c15f334650003e6c0a7` |
| **Risk Synthesis Stage** | `backend/app/pipeline/stages/risk_stage.py` | `ca0910e4677d224e6e48176647b446f74009790de80e8fba7648259343e06d4a` |
| **Feature Extractor** | `backend/app/ml/feature_extractor.py` | `9c902b36c6e1b0daa2983956c8de4aec2e09ef12aebfc47311fc7f72ae85ad3c` |
| **Inference Service** | `backend/app/services/ml_inference/inference_service.py` | `4b4e5ecb3d16a7597db0877ba48345edf4b7632fa98bdeaf406ac78c84e089e3` |
| **JPEG Quality Estimator** | `backend/app/services/forensics/jpeg_quality_estimator.py` | `5be2cca559544d4d945f888d38c8bba9c75c1c919883e7478a7322794d0edebb` |
| **Copy-Move Analyzer** | `backend/app/services/forensics/copy_move_region_analyzer.py` | `f02bbeb5734fb3980b99493f10394cdef6528f48536e648cde982c981788be31` |
| **PDF Conversion** | `backend/app/services/preprocessing/pdf_converter.py` | `a392276a339d1080155b4d666cef15030e0d99a91260affe9306db1756e4ed48` |
| **Document API** | `backend/app/api/documents.py` | `de70972c02dd28576352e308a6a3034e099955bb8a902f93fdc5843c5a6e23be` |
| **Auth & Security API** | `backend/app/api/auth.py` | `a7ca4c66a9d5fb3a4db06817fbbacf76429539278d3a3d1014f8df8b0f674476` |
| **Comparison API** | `backend/app/api/comparison.py` | `c68ada55d41587eb00b181436ebb8b5940f670fb897ec243a0c2024a0bb2d039` |
| **Report API** | `backend/app/api/reports.py` | `a91038efde4d100b0116acb3b7c381d00c2f83403ba5e9b33238d8f51d921aae` |
| **Database Session** | `backend/app/database/session.py` | `eda18a7a2a0dd6d27b0dcc5ff8fdd9e9f058a7922b5d7635bbf520fc09a9f72f` |
| **ORM Data Models** | `backend/app/models/__init__.py` | `0cdf4b74845b5181cf3bcc8cee0168c89446dac3793d6fd516ecf338e451b8ec` |
| **Backend Main Entry** | `backend/main.py` | `295a6ecae429f4bb120df0f10c6d3df39df3ca945d7d4c8273dcbe15e18e38f9` |
| **Docker Compose Config** | `docker-compose.pilot.yml` | `09367fd97ca58fe1de3cf443681e08eaa74ee93a13f1f2c68130f8119e40c56f` |
| **Nginx Pilot Config** | `frontend/nginx.pilot.conf` | `f22ba3d2fcdd1958c85dc19dd7e554b5c61f39fe5e8f735b0b3c3f1186f6e62f` |
| **Backend Dependencies** | `backend/requirements.txt` | `4cff1c667b8f4239226f69971e99191cbe4351d0a861cd4d2be6b3bcd8abfcd1` |
| **Frontend Dependencies** | `frontend/package.json` | `4a0fd117fb45474c27472128b74ce3385f8840fee7f1ea1f20ef72d0c21f5b8a` |

---

## 3. Database Schema & Migration Identifier

- **ORM Framework:** SQLAlchemy 2.0.30
- **Database Engine:** PostgreSQL 16.3
- **Migration Framework:** Alembic 1.13.1
- **Current Head Revision:** `146af5c0448f (head)`
- **Core Persisted Tables:**
  - `users` (Argon2id password hashes, role-based access attributes)
  - `documents` (Exhibit metadata, original SHA-256 hash, physical file path)
  - `document_analyses` (Per-document and per-page ML probabilities, features JSON, risk tiers)
  - `document_comparisons` (SSIM scores, alignment matrices, differential masks)
  - `forensic_reports` (Serialized investigation summaries, PDF download hashes)
  - `exhibit_custody_logs` (Cryptographic append-only chain of custody events)
  - `security_audit_logs` (Authentication events, authorization failures, IDOR blocks)

---

## 4. Operational Thresholds & Pipeline Configurations

- **Primary Binary Classification Threshold:** $T = 0.40$ (Hardcoded in `MLInferenceStage`).
- **Default Reference Threshold:** $T = 0.50$ (Balanced baseline reference).
- **Multi-Page Logarithmic Significance Threshold:**
  $$T_N = \min\left(0.75, \; 0.40 + 0.07 \cdot \ln N\right)$$
  - For $N = 1$: $T_1 = 0.4000$
  - For $N = 2$: $T_2 = 0.4485$
  - For $N = 5$: $T_5 = 0.5127$
  - For $N = 10$: $T_{10} = 0.5612$
- **Track 3 Keypoint Matching Gate:**
  - Detector: AKAZE (Accelerated-KAZE) keypoints + descriptors.
  - Inlier Threshold: Minimum $\ge 15$ inliers.
  - Confidence Threshold: Minimum $\ge 0.80$ cluster confidence.
  - Multi-Cluster Escalation: `cm_pairs >= 2` or `cm_inliers >= 40` $\implies$ `HIGH_RISK`.
  - Single-Cluster Alert: `cm_pairs == 1` $\implies$ `SUSPICIOUS`.
- **JPEG Quality Factor Qualification:**
  - Parsing Method: Direct 64-element luminance DQT extraction from `0xFFDB` markers.
  - Severe Compression Cutoff: $Q < 40$.
  - DCT Grid Keypoint Inlier Filter: Threshold raised from 15 to 30 when $Q < 40$.
  - Borderline Qualification Gate: If $Q < 40$ and $P_{\text{ML}} \in [0.40, 0.45]$ without visual confirmation, qualify verdict to `SUSPICIOUS / COMPRESSION_DEGRADED` and Track 1 class to `AUTHENTIC`.

---

## 5. Runtime Environment & Pilot Parameters

- **Environment Setting:** `APP_ENV=pilot`
- **Debug Mode:** `DEBUG=false`
- **Host Binding Restrictions:**
  - HTTPS: `127.0.0.1:8443`
  - HTTP Redirect: `127.0.0.1:8080` (Redirects with 301 to `https://127.0.0.1:8443/`)
  - Backend API: `http://172.28.0.3:8000` (Internal Docker network only; NOT bound to host)
  - PostgreSQL: `5432` (Internal Docker network only; NOT bound to host)
- **Uvicorn Worker Count:** Exactly **1 worker** (`--workers 1`), preserving in-memory sliding window rate limiter consistency.
- **Trusted Proxy:** Narrowly scoped Docker bridge subnet (`172.28.0.0/16`), trusting exclusively the internal Nginx reverse proxy.
- **TLS Security:** Dedicated Internal Certificate Authority (`ca/pilot_ca.crt`), terminating TLS 1.3/1.2 on Nginx with private key permissions restricted to service identity (`0o600`).
