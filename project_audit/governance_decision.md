# Approved raw-ML/document-assessment separation

The user approved: "Yes?separate raw ML and document assessment (recommended)" in response to the explicit governance question in this session.

Implementation: capture raw model output before existing JPEG/multi-page qualification; retain source page index, selection method and is_document_probability=false. Expose raw_ml separately in analysis responses and versioned snapshots. Existing track_1_ml compatibility fields and unified assessment rules remain unchanged. Primary T=.40, tier boundaries, all weights, frozen schema/model and historical records are preserved. Multi-page selection is labeled as a heuristic, not Bonferroni correction or calibrated document probability. Legacy analyses have raw_ml=null; missing history is never invented.

Regression evidence: test_raw_ml_survives_jpeg_heuristic_without_policy_change and test_raw_max_page_selection_is_explicit_and_unmodified exercise P=.42 while the preserved historical document class can remain AUTHENTIC/SUSPICIOUS. The raw page class remains FORGED at T=.40.
