"""
comparison_service.py — Forensic Document Comparison & Differential Analysis Service.

Performs:
1. Cryptographic exhibit verification and page extraction for Document A and Document B.
2. Geometric alignment and feature-based image registration (ORB + RANSAC homography)
   with resilient fallback to aspect-preserving resizing.
3. High-precision Structural Similarity Index (SSIM) and pixel difference computation.
4. Difference heatmap generation and thresholded differential mask extraction.
5. Differential region extraction with contour polygon simplification and classification.
6. Isolated storage of derived comparison artifacts without modifying original exhibits.
7. Immutable chain-of-custody recording for both documents.
"""

from __future__ import annotations
import os
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

import cv2
import numpy as np
from PIL import Image
import pypdfium2 as pdfium
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.page import DocumentPage
from app.repositories.comparison_repository import ComparisonRepository
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import AuditService
from app.core.security import verify_file_integrity
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_ssim(img1_gray: np.ndarray, img2_gray: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Computes Structural Similarity Index (SSIM) between two single-channel grayscale images.
    Returns (mean_ssim, ssim_error_map).
    """
    C1 = 6.5025   # (0.01 * 255) ** 2
    C2 = 58.5225  # (0.03 * 255) ** 2

    im1 = img1_gray.astype(np.float64)
    im2 = img2_gray.astype(np.float64)

    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(im1, -1, window)
    mu2 = cv2.filter2D(im2, -1, window)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.filter2D(im1 ** 2, -1, window) - mu1_sq
    sigma2_sq = cv2.filter2D(im2 ** 2, -1, window) - mu2_sq
    sigma12 = cv2.filter2D(im1 * im2, -1, window) - mu1_mu2

    numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
    ssim_map = numerator / (denominator + 1e-10)

    # Avoid boundary artifacts in mean calculation
    valid_ssim = ssim_map[5:-5, 5:-5] if ssim_map.shape[0] > 10 and ssim_map.shape[1] > 10 else ssim_map
    mean_ssim = float(np.clip(valid_ssim.mean(), 0.0, 1.0))
    error_map = np.clip((1.0 - ssim_map) * 255.0, 0, 255).astype(np.uint8)

    return mean_ssim, error_map


class ComparisonService:
    """Service orchestrating forensic document comparison and differential analysis."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _resolve_page_image(
        self, doc: Document, page_index: int, db: Session
    ) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Loads the specified page image for a document exhibit into an RGB numpy array.
        Returns (image_bgr, (width, height)).
        """
        if page_index < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page index {page_index} must be non-negative.",
            )

        doc_path = Path(doc.file_path)
        if not doc_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file for '{doc.id}' not found on storage.",
            )

        # 1. Handle PDF Documents
        if doc.file_type.lower() == "pdf":
            doc_repo = DocumentRepository(db)
            pages = doc_repo.get_document_pages(doc.id)
            page_record: Optional[DocumentPage] = None
            for p in pages:
                if p.page_index == page_index:
                    page_record = p
                    break

            # If page image exists on disk from previous processing, load it
            if page_record and page_record.image_path and Path(page_record.image_path).exists():
                img = cv2.imread(page_record.image_path)
                if img is not None:
                    h, w = img.shape[:2]
                    return img, (w, h)

            # Fallback: render directly from PDF using pypdfium2
            try:
                pdf_doc = pdfium.PdfDocument(str(doc_path))
                if page_index >= len(pdf_doc):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Requested page {page_index} exceeds document page count of {len(pdf_doc)}.",
                    )
                page = pdf_doc[page_index]
                pil_image = page.render(scale=2.0).to_pil()
                img_rgb = np.array(pil_image)
                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                h, w = img_bgr.shape[:2]
                return img_bgr, (w, h)
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Failed to render PDF page %d for doc %s: %s", page_index, doc.id, exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to render PDF page {page_index}: {exc}",
                )

        # 2. Handle Single-Page Images (PNG, JPG, JPEG)
        if page_index > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Single-image exhibit '{doc.original_filename}' does not contain page {page_index}.",
            )

        img = cv2.imread(str(doc_path))
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unable to decode image exhibit '{doc.original_filename}'.",
            )
        h, w = img.shape[:2]
        return img, (w, h)

    def _align_images(
        self, img_ref: np.ndarray, img_tgt: np.ndarray
    ) -> Tuple[np.ndarray, str, float, int, int, int]:
        """
        Geometrically aligns target image (B) to reference image (A) coordinate system.
        Returns:
            aligned_b, status, confidence, keypoints_a, keypoints_b, matches_count
        """
        h_ref, w_ref = img_ref.shape[:2]
        h_tgt, w_tgt = img_tgt.shape[:2]

        gray_ref = cv2.cvtColor(img_ref, cv2.COLOR_BGR2GRAY)
        gray_tgt = cv2.cvtColor(img_tgt, cv2.COLOR_BGR2GRAY)

        # Initialize ORB detector
        orb = cv2.ORB_create(nfeatures=2500, scaleFactor=1.2, nlevels=8)
        kp_ref, des_ref = orb.detectAndCompute(gray_ref, None)
        kp_tgt, des_tgt = orb.detectAndCompute(gray_tgt, None)

        num_kp_a = len(kp_ref) if kp_ref else 0
        num_kp_b = len(kp_tgt) if kp_tgt else 0

        if des_ref is None or des_tgt is None or num_kp_a < 10 or num_kp_b < 10:
            # Insufficient keypoints for homography — fallback to direct resize
            resized_tgt = cv2.resize(img_tgt, (w_ref, h_ref), interpolation=cv2.INTER_AREA if (w_tgt > w_ref) else cv2.INTER_CUBIC)
            return resized_tgt, "FALLBACK_DIRECT_RESIZE", 0.40, num_kp_a, num_kp_b, 0

        # Match features with BFMatcher and Lowe's ratio test
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        raw_matches = matcher.knnMatch(des_tgt, des_ref, k=2)

        good_matches = []
        for m in raw_matches:
            if len(m) == 2 and m[0].distance < 0.75 * m[1].distance:
                good_matches.append(m[0])

        num_matches = len(good_matches)

        if num_matches >= 15:
            pts_tgt = np.float32([kp_tgt[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            pts_ref = np.float32([kp_ref[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(pts_tgt, pts_ref, cv2.RANSAC, 5.0)

            if H is not None:
                det = float(np.linalg.det(H[:2, :2]))
                # Check determinant to ensure homography is non-singular and not excessively stretched
                if 0.15 < det < 6.5:
                    aligned_b = cv2.warpPerspective(
                        img_tgt, H, (w_ref, h_ref),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    confidence = float(min(1.0, round(num_matches / 60.0, 3)))
                    return aligned_b, "FEATURE_ALIGNED", confidence, num_kp_a, num_kp_b, num_matches

        # Fallback to direct resize if homography was rejected or matches < 15
        resized_tgt = cv2.resize(img_tgt, (w_ref, h_ref), interpolation=cv2.INTER_AREA if (w_tgt > w_ref) else cv2.INTER_CUBIC)
        return resized_tgt, "FALLBACK_DIRECT_RESIZE", 0.50, num_kp_a, num_kp_b, num_matches

    def perform_comparison(
        self,
        db: Session,
        document_a: Document,
        document_b: Document,
        page_a: int = 0,
        page_b: int = 0,
        align_images: bool = True,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes full forensic comparison between Document A (page_a) and Document B (page_b).
        """
        comparison_id = str(uuid.uuid4())
        client_ip = ip_address or "127.0.0.1"

        # 1. Cryptographic Exhibit Verification
        if document_a.file_path and document_a.sha256_hash:
            if not verify_file_integrity(Path(document_a.file_path), document_a.sha256_hash):
                AuditService.record_custody_event(
                    db,
                    document_id=document_a.id,
                    event_type="TAMPERING_ALARM",
                    sha256_hash=document_a.sha256_hash,
                    user_id=user_id,
                    status="TAMPERED",
                    ip_address=client_ip,
                    details={"action": "comparison_aborted", "corrupted_exhibit": document_a.id},
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"TAMPERING_ALARM: Document A ({document_a.original_filename}) hash mismatch.",
                )

        if document_b.file_path and document_b.sha256_hash:
            if not verify_file_integrity(Path(document_b.file_path), document_b.sha256_hash):
                AuditService.record_custody_event(
                    db,
                    document_id=document_b.id,
                    event_type="TAMPERING_ALARM",
                    sha256_hash=document_b.sha256_hash,
                    user_id=user_id,
                    status="TAMPERED",
                    ip_address=client_ip,
                    details={"action": "comparison_aborted", "corrupted_exhibit": document_b.id},
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"TAMPERING_ALARM: Document B ({document_b.original_filename}) hash mismatch.",
                )

        # 2. Page Image Resolution
        img_a, dims_a = self._resolve_page_image(document_a, page_a, db)
        img_b, dims_b = self._resolve_page_image(document_b, page_b, db)

        w_a, h_a = dims_a
        w_b, h_b = dims_b

        # 3. Geometric Alignment & Registration
        if align_images:
            aligned_b, align_status, align_conf, kp_a, kp_b, matches = self._align_images(img_a, img_b)
        else:
            aligned_b = cv2.resize(img_b, (w_a, h_a))
            align_status, align_conf, kp_a, kp_b, matches = "DIRECT_RESIZE_UNALIGNED", 0.50, 0, 0, 0

        # 4. Grayscale & SSIM Analysis
        gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(aligned_b, cv2.COLOR_BGR2GRAY)

        ssim_score, ssim_err_map = compute_ssim(gray_a, gray_b)

        # 5. Differential Pixel Computation & Masking
        abs_diff = cv2.absdiff(img_a, aligned_b)
        gray_diff = cv2.cvtColor(abs_diff, cv2.COLOR_BGR2GRAY)

        # Gaussian blur to filter minor digitizer sensor noise
        blurred_diff = cv2.GaussianBlur(gray_diff, (3, 3), 0)
        _, raw_mask = cv2.threshold(blurred_diff, 28, 255, cv2.THRESH_BINARY)

        # Morphological closing to bridge contiguous alteration strokes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        clean_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, kernel)

        total_pixels = w_a * h_a
        differing_pixels = int(cv2.countNonZero(clean_mask))
        diff_ratio = differing_pixels / max(total_pixels, 1)
        diff_percentage = round(diff_ratio * 100.0, 2)

        # Calculate calibrated similarity score
        similarity_score = float(np.clip(round(ssim_score * (1.0 - (diff_ratio * 0.45)), 4), 0.0, 1.0))

        # 6. Differential Region Extraction
        contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        differential_regions: List[Dict[str, Any]] = []

        # Sort contours by area descending
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        region_idx = 1
        for cnt in contours:
            area = int(cv2.contourArea(cnt))
            if area < 40:  # Ignore microscopic scan noise
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            # Compute mean difference intensity within this contour
            mask_roi = clean_mask[y:y+h, x:x+w]
            diff_roi = gray_diff[y:y+h, x:x+w]
            mean_intensity = float(np.mean(diff_roi[mask_roi > 0])) if np.any(mask_roi > 0) else 0.0
            severity = float(np.clip(round(mean_intensity / 255.0, 3), 0.1, 1.0))

            # Approximate polygon contour
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            poly_points = [[int(pt[0][0]), int(pt[0][1])] for pt in approx]
            if len(poly_points) < 3:
                poly_points = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

            # Category heuristic
            aspect = float(w) / max(h, 1)
            if h <= 45 and w <= 350 and aspect > 1.2:
                category = "TEXT_MODIFICATION"
            elif area > 12000:
                category = "MACRO_CONTENT_DIFFERENCE"
            else:
                category = "CONTENT_INSERTION_OR_DELETION"

            differential_regions.append({
                "region_id": f"diff-{region_idx:03d}",
                "category": category,
                "bounding_box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                "polygon": poly_points,
                "severity": severity,
                "area": area,
                "page_a": page_a,
                "page_b": page_b,
            })
            region_idx += 1

        # 7. Generate Visual Diff Heatmap & Overlay Artifacts
        heatmap = cv2.applyColorMap(gray_diff, cv2.COLORMAP_JET)
        # Composite: retain Document A where diff is 0, blend heatmap where diff > 0
        diff_mask_norm = (gray_diff.astype(np.float32) / 255.0)[:, :, np.newaxis]
        alpha = np.clip(diff_mask_norm * 1.5, 0.0, 0.75)
        blended_heatmap = ((1.0 - alpha) * img_a.astype(np.float32) + alpha * heatmap.astype(np.float32)).astype(np.uint8)

        # 8. Isolated Derived Artifact Storage
        comp_storage_dir = Path(self.settings.processed_dir) / "comparisons" / comparison_id
        comp_storage_dir.mkdir(parents=True, exist_ok=True)

        heatmap_path = comp_storage_dir / "diff_heatmap.png"
        mask_path = comp_storage_dir / "diff_mask.png"
        aligned_b_path = comp_storage_dir / "aligned_b.png"

        cv2.imwrite(str(heatmap_path), blended_heatmap)
        cv2.imwrite(str(mask_path), clean_mask)
        cv2.imwrite(str(aligned_b_path), aligned_b)

        # Compute SHA-256 hashes of derived artifacts for reproducibility
        def _get_hash(p: Path) -> str:
            h = hashlib.sha256()
            h.update(p.read_bytes())
            return h.hexdigest()

        artifacts_meta = {
            "diff_heatmap": {"path": str(heatmap_path), "sha256": _get_hash(heatmap_path)},
            "diff_mask": {"path": str(mask_path), "sha256": _get_hash(mask_path)},
            "aligned_b": {"path": str(aligned_b_path), "sha256": _get_hash(aligned_b_path)},
        }

        # 9. Verdict Classification & Forensic Caveat
        if similarity_score >= 0.995 and len(differential_regions) == 0:
            verdict_category = "IDENTICAL"
        elif similarity_score >= 0.85:
            verdict_category = "LOCALIZED_DIFFERENCES"
        elif similarity_score >= 0.50:
            verdict_category = "SIGNIFICANT_DIFFERENCES"
        else:
            verdict_category = "DIFFERENT_DOCUMENTS"

        if align_status == "FALLBACK_DIRECT_RESIZE" and ssim_score < 0.40:
            verdict_category = "INCONCLUSIVE_ALIGNMENT"

        forensic_caveat = (
            "Visual differences indicate document variations, revisions, or digitizer variances between exhibits. "
            "In strict accordance with forensic methodology, detected visual differences do not constitute definitive "
            "proof of fraudulent intent or unlawful forgery."
        )

        metadata_diff = {
            "document_a": {
                "document_id": document_a.id,
                "filename": document_a.original_filename,
                "file_type": document_a.file_type,
                "size_bytes": document_a.size_bytes,
                "page_count": document_a.page_count or 1,
                "current_page": page_a,
                "sha256_hash": document_a.sha256_hash or "",
                "dimensions": [w_a, h_a],
            },
            "document_b": {
                "document_id": document_b.id,
                "filename": document_b.original_filename,
                "file_type": document_b.file_type,
                "size_bytes": document_b.size_bytes,
                "page_count": document_b.page_count or 1,
                "current_page": page_b,
                "sha256_hash": document_b.sha256_hash or "",
                "dimensions": [w_b, h_b],
            },
            "dimension_match": (w_a == w_b and h_a == h_b),
            "page_count_match": ((document_a.page_count or 1) == (document_b.page_count or 1)),
            "format_match": (document_a.file_type.lower() == document_b.file_type.lower()),
            "hash_match": (document_a.sha256_hash == document_b.sha256_hash and bool(document_a.sha256_hash)),
        }

        alignment_meta = {
            "status": align_status,
            "confidence": align_conf,
            "keypoints_detected_a": kp_a,
            "keypoints_detected_b": kp_b,
            "matches_found": matches,
        }

        metrics_meta = {
            "similarity_score": similarity_score,
            "ssim_score": round(ssim_score, 4),
            "difference_percentage": diff_percentage,
            "differing_pixels": differing_pixels,
            "total_pixels": total_pixels,
        }

        summary_meta = {
            "verdict_category": verdict_category,
            "differential_regions_count": len(differential_regions),
            "forensic_caveat": forensic_caveat,
        }

        # 10. Record Chain of Custody Events
        AuditService.record_custody_event(
            db,
            document_id=document_a.id,
            event_type="DOCUMENT_COMPARISON_PERFORMED",
            sha256_hash=document_a.sha256_hash or "",
            user_id=user_id,
            status="VERIFIED",
            ip_address=client_ip,
            details={
                "comparison_id": comparison_id,
                "counterpart_document_id": document_b.id,
                "page_a": page_a,
                "page_b": page_b,
                "similarity": similarity_score,
            },
        )

        AuditService.record_custody_event(
            db,
            document_id=document_b.id,
            event_type="DOCUMENT_COMPARISON_PERFORMED",
            sha256_hash=document_b.sha256_hash or "",
            user_id=user_id,
            status="VERIFIED",
            ip_address=client_ip,
            details={
                "comparison_id": comparison_id,
                "counterpart_document_id": document_a.id,
                "page_a": page_a,
                "page_b": page_b,
                "similarity": similarity_score,
            },
        )

        # 11. Persist in Database
        repo = ComparisonRepository(db)
        repo.create_comparison(
            comparison_id=comparison_id,
            document_a_id=document_a.id,
            document_b_id=document_b.id,
            page_a=page_a,
            page_b=page_b,
            similarity_score=similarity_score,
            ssim_score=ssim_score,
            difference_percentage=diff_percentage,
            alignment_status=align_status,
            alignment_confidence=align_conf,
            verdict_category=verdict_category,
            differential_regions=differential_regions,
            metadata_diff=metadata_diff,
            summary=summary_meta,
            artifacts=artifacts_meta,
            user_id=user_id,
        )

        artifact_urls = {
            "diff_heatmap": f"/api/v1/comparison/{comparison_id}/artifacts/diff_heatmap",
            "diff_mask": f"/api/v1/comparison/{comparison_id}/artifacts/diff_mask",
            "aligned_b": f"/api/v1/comparison/{comparison_id}/artifacts/aligned_b",
        }

        return {
            "comparison_id": comparison_id,
            "document_a_id": document_a.id,
            "document_b_id": document_b.id,
            "page_a": page_a,
            "page_b": page_b,
            "alignment": alignment_meta,
            "metrics": metrics_meta,
            "differential_regions": differential_regions,
            "metadata_diff": metadata_diff,
            "summary": summary_meta,
            "artifact_urls": artifact_urls,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
