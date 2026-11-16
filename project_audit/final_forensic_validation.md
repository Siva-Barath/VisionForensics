# Final forensic validation

13 November 2026. Functional and negative-case verification. PASS means the stated implementation works under tested conditions, not universal forgery detection accuracy.

| Module | Actual implementation / validation | Interpretation and remaining limits |
|---|---|---|
| ELA | Genuine JPEG recompression differences; scalar and regional findings; stored Inferno normalized error image with SHA-256; authenticated original and map checks | High error is not proof of editing. Compression, texture and capture can produce high response. The UI no longer invents heatmap blobs from bounding boxes. |
| Image quality | Laplacian variance, blur, noise, edges, illumination and entropy; grayscale/channel handling corrected; actual metrics retained | Quality is separate from authenticity. Extreme/skewed input remains challenging; perspective/glare support is heuristic and not comprehensively validated. |
| Copy-move | AKAZE matching, spatial/geometric checks and regions; real summaries and pipeline execution statuses | Repetitive patterns can cause false matches. No universal confidence calibration. No regions flagged is not evidence of authenticity. |
| OCR | Availability and failure handling tested; mock EasyOCR/Tesseract adapters marked unavailable; Paddle initialization/extraction failures surface | OCR is unavailable in the deployed container. Native PaddleX/Faiss dependency incompatibility also prevents reliable runtime use. Field/character/semantic verification is not claimed. |
| Metadata | Actual Pillow EXIF and pypdf properties retained and displayed | Missing properties are normal. Comprehensive timestamp consistency and semantic validation remain partial. Editing-tool metadata alone is not proof of forgery. |
| Signature/visual | Bounding-box normalization, genuine contour/ink/shape analysis, region checks; background polarity correction in logo geometry | Region appearance is a heuristic. No validated reference-backed signature authenticity or signer identity verification. |
| JPEG | Source DQT quality estimate, compression qualification, explicit non-JPEG applicability | Estimate can differ from original encoder quality. PNG/PDF are not source JPEGs. Existing qualification policy is unchanged. |
| Multi-page PDF | Genuine bounded rasters; explicit render failure; native resources closed; page dimensions correspond to actual derived rasters; per-page inference and readback | No generated error image enters inference. Maximum-page synthesis remains a labeled historical heuristic. Original-to-derived full transformation provenance is incomplete. |
| Comparison | Actual ORB/RANSAC alignment, SSIM/difference artifacts and regions; both-parent authorization; live HTTPS comparison succeeded | Lighting, registration and resize fallback affect results. Similarity does not establish document authenticity. |
| Reports | Actual PDFs, correct score/version/page count, raw result separation, analyst notes, exhibit/case ID, limitations, hashes and genuine custody | A report is examiner support. Full case narrative/notes are not comprehensively incorporated in the existing PDF template. |

Completed checks are supported by the 339-test backend suite, 70 isolated workflow checks, 57 deployed HTTPS checks, and the test artifacts named in [final test report](final_test_report.md). Browser DOM tests exercise zoom, page switching, page-filtered polygon selection and genuine ELA-map/error behavior. No screenshot review or human interpretation study was available.

Test fixture corrections were made where the previous fixtures did not represent the asserted condition: aliased checkerboards, a large dark block mislabeled as an unshadowed page, ideal continuous-circle expectations for raster geometry, and an ambiguous 50-degree deskew case. Production thresholds or risk weights were not tuned to those fixtures. The deskew maximum-angle guard is tested independently; extreme-angle estimation remains a limitation.

No historical benchmark data was relabeled or rerun to manufacture acceptance. Controlled synthetic files have explicit provenance under `controlled_provenance.json`; they test processing and integrity, not real-world authenticity classification.
