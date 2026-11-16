# Final ML validation

13 November 2026. Integration validation, not a new accuracy benchmark or model certification.

| Invariant | Verified result |
|---|---|
| Frozen Random Forest SHA-256 | `f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280` |
| Frozen schema SHA-256 | `eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc` |
| Input count | 18, exact model/schema name and order equality |
| Class order | `[0, 1]`, forgery probability from class 1 |
| Binary operational threshold | T = 0.40, unchanged |
| Risk definitions and existing qualification rules | Preserved |
| Training / replacement / tuning | None performed |
| Protected files | All 21 model/schema/evaluation/Phase 4 and Phase 9 files match the read-only baseline |

Model and schema bytes are checked before executable joblib deserialization. The verified model bytes are loaded through a byte stream to avoid a second unchecked file read. Loading fails closed for changed digests, wrong names/order/count or wrong classes. This does not make arbitrary joblib files safe; only the pinned trusted artifact is accepted.

The active input order is:

1. img_width
2. img_height
3. img_aspect_ratio
4. img_laplacian_variance_mean
5. img_blur_severity_mean
6. img_noise_sigma_mean
7. img_edge_density_mean
8. img_illumination_std_mean
9. img_ela_region_count_mean
10. img_ela_max_difference_mean
11. img_entropy_score_mean
12. cm_keypoint_count_akaze
13. cm_descriptor_matches
14. cm_inlier_matches
15. cm_average_region_size
16. cm_duplicate_pair_count
17. cm_confidence
18. cm_inlier_ratio

The existing feature-preparation policy handles missing/nonfinite inputs with frozen training medians where permitted, marks degraded results and aborts excessive missing critical inputs. Imputed fields remain separately identified. UI reference medians are never substituted for unavailable observations. Supplemental fusion/outcome fields are separated from the canonical feature export; the frozen 18 numerical inputs and their contract are unchanged.

With the user's explicit governance approval, `raw_ml` preserves the result before JPEG or multi-page qualification. The selected page index and selection method are retained. Maximum-page selection is explicitly a heuristic; it is not a calibrated document probability or formal multiplicity correction. `pages_ml` retains each page's result. Existing document policy, historical analyses and threshold values are preserved. A raw class can therefore differ from the document assessment, and both are shown.

The display composite is a 0–100 assessment score, not a probability. UNKNOWN is presented as unavailable without a green verification indicator. Existing raw risk bands and binary T=.40 answer different questions. Top contributing feature values are not SHAP explanations or causal attribution.

Evidence: complete backend suite 339 passed; isolated workflow checks include genuine 18-input vectors and snapshot readback; 57 live HTTPS checks include frozen inference and after-restart raw snapshots. Final protected-file results are in `final_verification.json`. Local sandbox denial of scikit-learn worker resources caused an intermediate failed test run; the same suite passed with required resources allowed. No model setting was changed to force a pass.

Read-only impurity importance inspection found approximately 65.58% combined weight on ELA max/count, Laplacian variance and blur. This indicates sensitivity to compression and capture quality; it does not establish per-document causality. No new accuracy, calibration, demographic robustness or legal admissibility claim is made. Historical benchmark records remain the historical record, not a new evaluation result.
