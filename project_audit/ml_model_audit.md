# Frozen ML audit

13 November 2026. Read-only model/schema inspection; no training, feature modification, threshold tuning or historical reevaluation.

Actual frozen artifact SHA-256: `f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280`, matching the directive. Schema SHA-256: `eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc`. Hash-verified artifact inspection found an sklearn Pipeline with `classifier` step, classes `[0,1]`, 18 inputs and `feature_names_in_` exactly matching schema order.

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

Actual path: FeatureExtractor -> FeaturePreparer -> ordered named DataFrame -> frozen predict_proba -> column 1 -> class at T=.40 -> raw risk band -> per-page/document heuristic -> RiskStage -> API. FeaturePreparer handles None/NaN/infinity/non-numeric with fixed authentic-training medians; two missing critical ELA/Laplacian/blur features abort, lesser missingness degrades. It only checks schema length, not exact identity/order/digest. Loader checks predict_proba existence but not model digest/names/classes. Probabilities are rounded to four decimals. Top contributors are manually selected feature values, not full feature vectors or SHAP attribution.

Raw risk bands in inference_service.py: P<.30 LOW_RISK, P<.55 SUSPICIOUS, else HIGH_RISK. Primary binary threshold is .40. RiskStage can rewrite class to AUTHENTIC for JPEG Q<40 and P=.40-.45. MLInferenceStage selects max-page candidate and uses T_N=min(.75,.40+.07*log(N)); it can also rewrite above-.40 class to AUTHENTIC. The comment calling this Bonferroni-corrected is unsupported. It is a heuristic document gate, not a formal statistical correction or calibrated document probability. Altering approved gates/risk definitions needs governance approval/versioning; preserve raw per-page outputs and frozen T=.40 separately.

Measured impurity feature importance: ELA max 38.20%, ELA region count 9.60%, Laplacian 10.66%, blur 7.12% (combined 65.58%); ELA pair 47.79%; copy-move confidence ~0.17%; width/height/aspect zero. These are model internals, not new accuracy or causal evidence. Capture blur/recompression/lighting/resolution/perspective shifts can affect dominant substrate features; low-texture clones and text/signature/logo alterations remain limitations. No claim of generalization on arbitrary documents follows.

Persistence loses pages_ml, raw feature vector, ML-specific tier and media/visual qualifications. get_context substitutes unified tier for raw ML tier. UI/API/report cannot consistently distinguish raw probability, raw class, display score and unified assessment across restart.

Training/evaluation sources: `ml/train_baseline.py` writes directly to artifacts if executed; do not run. `tools/evaluate_phase4_test.py` and `evaluate_phase9_locked_benchmark.py` are historical evaluators; locked samples are not tuning data. Dataset root exists. Historical Phase4/Phase9 metrics remain historical; the baseline manifest hashes local artifacts and Phase4/Phase9-named records/scripts.

Required validation: wrong digest before deserialization; equal-length reordered/duplicate schema; unexpected feature names/classes; finite/range/error handling; missing critical features; deterministic frozen predictions; per-page invariants; restart equality; separate raw and heuristic semantics. Impurity importance inspection required read-only escalation because local thread-pool pipe creation was sandbox-blocked; artifacts were not altered.
