"""
pdf_generator.py — Defense-Grade Forensic PDF Report Builder for VisionForensics AI.

Constructs comprehensive, multi-page, publication-quality forensic investigation reports
using fpdf2. Adheres to strict evidentiary standards, traceability, and defensibility guidelines.
"""

from __future__ import annotations
import os
import io
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PIL import Image

from app.core.logging import get_logger

logger = get_logger(__name__)


def sanitize_text(text: Optional[str]) -> str:
    """Sanitizes text for safe rendering in core PDF Latin-1 fonts."""
    if not text:
        return ""
    # Replace common unicode typographic characters with safe ASCII equivalents
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2014": "--", "\u2013": "-", "\u2022": "*", "\u2026": "...",
        "\u00a0": " ", "\u2265": ">=", "\u2264": "<=", "\u00d7": "x",
        "\u03c3": "sigma", "\u03bc": "mu", "\u00b5": "mu", "\u2260": "!=",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    # Encode to latin-1 with replacement fallback
    return text.encode("latin-1", "replace").decode("latin-1")


class ForensicReportPDF(FPDF):
    """Custom FPDF class providing standardized forensic headers, footers, and styling."""

    def __init__(self, report_number: str, exhibit_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_number = report_number
        self.exhibit_id = exhibit_id
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.page_no() == 1:
            # First page has a custom hero header, skip standard running header
            return

        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(100, 116, 139)  # Slate 500
        self.cell(
            0,
            6,
            sanitize_text(f"VISIONFORENSICS AI  |  REPORT: {self.report_number}  |  EXHIBIT: {self.exhibit_id[:18]}..."),
            border="B",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(148, 163, 184)  # Slate 400
        self.cell(
            0,
            6,
            f"Page {self.page_no()}/{{nb}}  |  Cryptographic Chain of Custody Verified  |  Tamper-Evident Report",
            border="T",
            align="C",
        )


class ForensicPDFBuilder:
    """Builds multi-page forensic reports from analysis and comparison contexts."""

    def __init__(self) -> None:
        pass

    def build_report(
        self,
        report_number: str,
        document_meta: Dict[str, Any],
        analysis_data: Dict[str, Any],
        custody_logs: List[Dict[str, Any]],
        comparison_data: Optional[Dict[str, Any]] = None,
        analyst_notes: Optional[str] = None,
        analyst_name: str = "Forensic Analyst",
        analyst_role: str = "FORENSIC_ANALYST",
    ) -> bytes:
        """
        Compiles the full forensic investigation report into a PDF byte array.
        """
        doc_id = document_meta.get("id", "UNKNOWN-DOC")
        doc_name = document_meta.get("original_filename", "Unknown Document")
        doc_hash = document_meta.get("sha256_hash", "NOT RECORDED")

        pdf = ForensicReportPDF(report_number=report_number, exhibit_id=doc_id, orientation="P", unit="mm", format="A4")
        pdf.alias_nb_pages()

        # ============================================================== #
        # PAGE 1: TITLE BANNER, EXHIBIT PROFILE & EXECUTIVE SUMMARY      #
        # ============================================================== #
        pdf.add_page()

        # Hero Banner
        pdf.set_fill_color(15, 23, 42)  # Slate 900
        pdf.rect(0, 0, 210, 36, "F")

        pdf.set_xy(15, 10)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, "VISIONFORENSICS AI PLATFORM", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 5, "INTELLIGENT DOCUMENT TAMPERING DETECTION & FORENSIC ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(59, 130, 246)  # Blue 500
        pdf.cell(0, 5, sanitize_text("EVIDENTIARY REPORT  *  OFFICIAL RECORD OF FORENSIC EXAMINATION"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_y(42)

        # Report Header Details Box
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(15, 42, 180, 26, "DF")

        pdf.set_xy(18, 45)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "REPORT IDENTIFIER:")
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(50, 5, report_number)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "EXAMINATION DATE:")
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(45, 5, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "EXAMINING ANALYST:")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(50, 5, sanitize_text(f"{analyst_name} ({analyst_role})"))

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "ANALYSIS VERSION:")
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(45, 5, f"v{analysis_data.get('analysis_version', 1)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "CASE IDENTIFIER:")
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(50, 5, sanitize_text(str(document_meta.get("case_id") or "UNASSIGNED")))

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "CLASSIFICATION:")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(180, 83, 9)
        pdf.cell(45, 5, "CONFIDENTIAL / LAW ENFORCEMENT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(5)

        # Section: Exhibit Profile
        self._section_title(pdf, "1. PRIMARY DOCUMENT EXHIBIT PROFILE")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(203, 213, 225)

        exhibit_props = [
            ("Original Filename:", doc_name),
            ("Document UUID:", doc_id),
            ("MIME / Format:", f"{document_meta.get('file_type', 'UNKNOWN').upper()} Exhibit"),
            ("File Size:", f"{document_meta.get('size_bytes', 0):,} bytes ({round(document_meta.get('size_bytes', 0) / 1024, 1)} KB)"),
            ("Page Count:", f"{document_meta.get('page_count', 1)} page(s)"),
            ("Exhibit SHA-256:", doc_hash),
        ]

        for label, val in exhibit_props:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(42, 5, label, border="B")
            pdf.set_font("Courier" if "SHA-256" in label or "UUID" in label else "Helvetica", "", 7.5 if "SHA-256" in label else 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(138, 5, sanitize_text(str(val)), border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(5)

        # Section: Executive Summary & Two-Track Verdict
        self._section_title(pdf, "2. EXECUTIVE SUMMARY & FORENSIC SYNTHESIS")

        risk_tier = analysis_data.get("unified_risk_tier", "UNKNOWN")
        verdict = analysis_data.get("overall_verdict", "INCONCLUSIVE")
        risk_desc = analysis_data.get("risk_description", "")
        composite_score = analysis_data.get("composite_risk_score", 0.0)

        # Risk Banner
        tier_colors = {
            "LOW_RISK": ((209, 250, 229), (5, 150, 105), "LOW RISK - AUTHENTIC TIER"),
            "SUSPICIOUS": ((254, 243, 199), (217, 119, 6), "SUSPICIOUS - ELEVATED ANOMALIES"),
            "HIGH_RISK": ((254, 226, 226), (220, 38, 38), "HIGH RISK - SEVERE ANOMALIES"),
        }
        bg_col, txt_col, tier_label = tier_colors.get(risk_tier, ((241, 245, 249), (100, 116, 139), "UNKNOWN RISK TIER"))

        pdf.set_fill_color(*bg_col)
        pdf.set_draw_color(*txt_col)
        pdf.rect(15, pdf.get_y(), 180, 20, "DF")

        pdf.set_xy(18, pdf.get_y() + 3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*txt_col)
        pdf.cell(120, 6, tier_label)

        pdf.set_font("Courier", "B", 9)
        pdf.cell(50, 6, f"COMPOSITE: {composite_score:.1f}/100", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, sanitize_text(f"Verdict: {verdict}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(7)

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(180, 4.5, sanitize_text(risk_desc or "Automated two-track evaluation completed."))

        # ============================================================== #
        # PAGE 2: DETAILED ML (TRACK 1) & SYMBOLIC (TRACK 2) BREAKDOWN   #
        # ============================================================== #
        pdf.add_page()
        self._section_title(pdf, "3. RANDOM FOREST SCREENING AND DOCUMENT ASSESSMENT")

        t1 = analysis_data.get("raw_ml") or analysis_data.get("track_1_ml") or {}
        ml_prob = t1.get("forgery_probability")
        ml_status = t1.get("status") or "UNAVAILABLE"
        ml_class = t1.get("predicted_class") or "NOT_CLASSIFIED"
        ml_thresh = t1.get("operational_threshold") or 0.40
        completeness = t1.get("feature_completeness") if t1.get("feature_completeness") is not None else 1.0

        pdf.set_fill_color(248, 250, 252)
        pdf.rect(15, pdf.get_y(), 180, 16, "F")

        pdf.set_xy(18, pdf.get_y() + 2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "ML Subsystem Status:")
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(50, 5, sanitize_text(str(ml_status)))

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "Raw Page Class:" if analysis_data.get("raw_ml") else "Legacy ML Summary:")
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(220, 38, 38) if str(ml_class) == "FORGED" else pdf.set_text_color(5, 150, 105)
        pdf.cell(45, 5, sanitize_text(str(ml_class)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "P_ML Probability:")
        pdf.set_font("Courier", "B", 9)
        pdf.set_text_color(15, 23, 42)
        prob_str = f"{ml_prob:.4f} ({ml_prob*100:.1f}%)" if ml_prob is not None else "N/A"
        pdf.cell(50, 5, prob_str)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(40, 5, "Decision Threshold (T):")
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(45, 5, f"{ml_thresh:.2f} (Frozen Phase 4 Benchmark)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(5)

        # Top Features Table
        top_features = t1.get("top_contributing_features", {})
        if top_features:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 5, "Top Contributing Random Forest Features (18-Feature Schema):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_fill_color(226, 232, 240)
            pdf.cell(90, 5, "Feature Name", border=1, fill=True)
            pdf.cell(45, 5, "Importance Weight", border=1, fill=True)
            pdf.cell(45, 5, "Observed Measurement", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Courier", "", 7.5)
            for feat_name, weight in list(top_features.items())[:6]:
                pdf.cell(90, 4.5, sanitize_text(str(feat_name)[:45]), border=1)
                pdf.cell(45, 4.5, f"{float(weight):.4f}", border=1)
                pdf.cell(45, 4.5, "Recorded in Exhibit", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 5, "No feature importance breakdown available for this inference.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(6)

        # Section: Track 2 Symbolic Evidence
        self._section_title(pdf, "4. TRACK 2: DETERMINISTIC SYMBOLIC EVIDENCE")

        t2 = analysis_data.get("track_2_symbolic", {})
        sym_score = t2.get("symbolic_severity_score", 0.0)
        sym_evidence = t2.get("symbolic_evidence", [])

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(60, 5, f"Symbolic Severity Score: {sym_score:.2f} / 1.00", border="B")
        pdf.cell(120, 5, f"Physical Evidence Items Collected: {len(sym_evidence)}", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        if sym_evidence:
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_fill_color(226, 232, 240)
            pdf.cell(35, 5, "Detector Subsystem", border=1, fill=True)
            pdf.cell(30, 5, "Category", border=1, fill=True)
            pdf.cell(25, 5, "Severity", border=1, fill=True)
            pdf.cell(90, 5, "Forensic Finding", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Helvetica", "", 7.5)
            for ev in sym_evidence[:8]:
                pdf.cell(35, 4.5, sanitize_text(str(ev.get("detector", ""))), border=1)
                pdf.cell(30, 4.5, sanitize_text(str(ev.get("category", ""))), border=1)
                pdf.cell(25, 4.5, f"{float(ev.get('severity', 0.0)):.2f}", border=1)
                pdf.cell(90, 4.5, sanitize_text(str(ev.get("description", ""))[:58]), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 5, "No discrete symbolic evidence items triggered threshold alarms.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ============================================================== #
        # PAGE 3: DETECTED REGIONS & PAGE-BY-PAGE FINDINGS               #
        # ============================================================== #
        pdf.add_page()
        self._section_title(pdf, "5. REGION-LEVEL FORENSIC DETECTIONS")

        regions = analysis_data.get("detected_regions", [])
        if regions:
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_fill_color(226, 232, 240)
            pdf.cell(25, 5, "Region ID", border=1, fill=True)
            pdf.cell(18, 5, "Page", border=1, fill=True)
            pdf.cell(35, 5, "Detector", border=1, fill=True)
            pdf.cell(22, 5, "Severity", border=1, fill=True)
            pdf.cell(40, 5, "Bounding Box", border=1, fill=True)
            pdf.cell(40, 5, "Classification", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Courier", "", 7.5)
            for r in regions[:15]:
                bb = r.get("bounding_box", {})
                if isinstance(bb, dict):
                    # Check if bounding_box is in {x, y, width, height} or {points: [...]}
                    if "x" in bb and "width" in bb:
                        bbox_str = f"[{bb['x']},{bb['y']},{bb['width']}x{bb['height']}]"
                    elif "points" in bb:
                        bbox_str = f"Polygon ({len(bb['points'])} pts)"
                    else:
                        bbox_str = "Standard BBox"
                else:
                    bbox_str = "Detected Area"

                pdf.cell(25, 4.5, sanitize_text(str(r.get("id", ""))), border=1)
                pdf.cell(18, 4.5, f"Page {r.get('page_index', 0) + 1}", border=1)
                pdf.cell(35, 4.5, sanitize_text(str(r.get("detector", ""))), border=1)
                pdf.cell(22, 4.5, f"{float(r.get('severity', 0.0)):.2f}", border=1)
                pdf.cell(40, 4.5, bbox_str, border=1)
                pdf.cell(40, 4.5, sanitize_text(str(r.get("category", ""))), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 5, "No localized tampering regions identified on this document exhibit.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(5)

        # Multi-Page Dimension Summary
        dims = analysis_data.get("image_dimensions", {})
        pages = dims.get("pages", [])
        if len(pages) > 1:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 5, f"Multi-Page PDF Geometry Summary ({len(pages)} Total Pages):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Courier", "", 7.5)
            for p in pages:
                pdf.cell(0, 4, f"  * Page {p.get('page_index', 0) + 1}: {p.get('width', 0)} x {p.get('height', 0)} px @ {p.get('dpi', 200)} DPI", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(5)

        # Decision Trace Synthesis
        trace = analysis_data.get("decision_trace", [])
        if trace:
            self._section_title(pdf, "6. FORENSIC SYNTHESIS & DECISION TRACE")
            for item in trace[:6]:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 4.5, sanitize_text(f"[{item.get('track', 'SYNTHESIS')}] {item.get('finding', '')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                if item.get("description"):
                    pdf.set_font("Helvetica", "", 7.5)
                    pdf.set_text_color(71, 85, 105)
                    pdf.multi_cell(180, 4, sanitize_text(f"  {item.get('description')}"))
                pdf.ln(1)

        # ============================================================== #
        # PAGE 4: DOCUMENT COMPARISON FINDINGS (IF AVAILABLE)            #
        # ============================================================== #
        if comparison_data:
            pdf.add_page()
            self._section_title(pdf, "7. DIFFERENTIAL DOCUMENT COMPARISON RESULTS")

            meta_diff = comparison_data.get("metadata_diff", {})
            doc_b_meta = meta_diff.get("document_b", {})
            align_meta = comparison_data.get("alignment", {})
            metrics = comparison_data.get("metrics", {})
            summary = comparison_data.get("summary", {})

            pdf.set_fill_color(248, 250, 252)
            pdf.rect(15, pdf.get_y(), 180, 20, "F")

            pdf.set_xy(18, pdf.get_y() + 2)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(40, 5, "Comparison Exhibit B:")
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(130, 5, sanitize_text(doc_b_meta.get("filename", "Unknown Counterpart")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_x(18)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(40, 5, "Exhibit B SHA-256:")
            pdf.set_font("Courier", "", 7.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(130, 5, str(doc_b_meta.get("sha256_hash", "NOT RECORDED")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_x(18)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(40, 5, "Registration Method:")
            pdf.set_font("Courier", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(50, 5, f"{align_meta.get('status', 'UNALIGNED')} (Conf: {align_meta.get('confidence', 0.0):.2f})")

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(40, 5, "Compared Page Pair:")
            pdf.set_font("Courier", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(45, 5, f"Page {comparison_data.get('page_a', 0) + 1} vs Page {comparison_data.get('page_b', 0) + 1}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.ln(5)

            # Quantitative Metrics Box
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(226, 232, 240)
            pdf.cell(45, 5, "Overall Similarity", border=1, fill=True)
            pdf.cell(45, 5, "Structural SSIM", border=1, fill=True)
            pdf.cell(45, 5, "Differing Pixel %", border=1, fill=True)
            pdf.cell(45, 5, "Comparison Verdict", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Courier", "B", 8)
            pdf.cell(45, 5, f"{metrics.get('similarity_score', 0.0)*100:.1f}%", border=1)
            pdf.cell(45, 5, f"{metrics.get('ssim_score', 0.0):.4f}", border=1)
            pdf.cell(45, 5, f"{metrics.get('difference_percentage', 0.0):.2f}%", border=1)
            pdf.cell(45, 5, sanitize_text(str(summary.get("verdict_category", "LOCALIZED_DIFFERENCES"))), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.ln(5)

            # Differential Regions Table
            diff_regions = comparison_data.get("differential_regions", [])
            if diff_regions:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 5, f"Detected Discrepancy Regions ({len(diff_regions)} Total):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_fill_color(226, 232, 240)
                pdf.cell(25, 5, "Region ID", border=1, fill=True)
                pdf.cell(45, 5, "Discrepancy Category", border=1, fill=True)
                pdf.cell(25, 5, "Severity", border=1, fill=True)
                pdf.cell(35, 5, "Area (px)", border=1, fill=True)
                pdf.cell(50, 5, "Bounding Coordinates", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font("Courier", "", 7.5)
                for dr in diff_regions[:10]:
                    dbb = dr.get("bounding_box", {})
                    pdf.cell(25, 4.5, sanitize_text(str(dr.get("region_id", ""))), border=1)
                    pdf.cell(45, 4.5, sanitize_text(str(dr.get("category", ""))), border=1)
                    pdf.cell(25, 4.5, f"{float(dr.get('severity', 0.0)):.2f}", border=1)
                    pdf.cell(35, 4.5, f"{int(dr.get('area', 0)):,}", border=1)
                    pdf.cell(50, 4.5, f"[{dbb.get('x',0)},{dbb.get('y',0)},{dbb.get('width',0)}x{dbb.get('height',0)}]", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ============================================================== #
        # FINAL PAGE: CHAIN OF CUSTODY, ANALYST NOTES & DISCLAIMER       #
        # ============================================================== #
        pdf.add_page()
        self._section_title(pdf, "8. CHAIN OF CUSTODY & EVIDENTIARY AUDIT LOG")

        if custody_logs:
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(226, 232, 240)
            pdf.cell(42, 5, "Timestamp (UTC)", border=1, fill=True)
            pdf.cell(45, 5, "Custody Event", border=1, fill=True)
            pdf.cell(22, 5, "Integrity Status", border=1, fill=True)
            pdf.cell(71, 5, "Recorded SHA-256 Hash", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Courier", "", 6.5)
            for ev in custody_logs[:12]:
                ts = str(ev.get("timestamp", ""))[:19]
                pdf.cell(42, 4, ts, border=1)
                pdf.cell(45, 4, sanitize_text(str(ev.get("event_type", ""))), border=1)
                pdf.cell(22, 4, sanitize_text(str(ev.get("status", "VERIFIED"))), border=1)
                pdf.cell(71, 4, str(ev.get("sha256_hash", ""))[:32] + "...", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 5, "No chain of custody logs recorded for this exhibit.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(5)

        # Analyst Notes Section
        self._section_title(pdf, "9. ANALYST OBSERVATIONS & OPINION")
        pdf.set_font("Helvetica", "I" if not analyst_notes else "", 8)
        pdf.set_text_color(30, 41, 59)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(15, pdf.get_y(), 180, 24, "DF")

        pdf.set_xy(18, pdf.get_y() + 2)
        notes_text = analyst_notes or "No supplementary manual analyst notes entered at time of report generation."
        pdf.multi_cell(174, 4, sanitize_text(notes_text))

        pdf.set_y(pdf.get_y() + 18)

        # Analyst Signature Block
        pdf.set_draw_color(148, 163, 184)
        pdf.line(15, pdf.get_y() + 10, 85, pdf.get_y() + 10)
        pdf.line(110, pdf.get_y() + 10, 180, pdf.get_y() + 10)

        pdf.set_xy(15, pdf.get_y() + 12)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(70, 4, sanitize_text(f"EXAMINER: {analyst_name}"), new_x=XPos.RIGHT)
        pdf.set_x(110)
        pdf.cell(70, 4, "SUPERVISORY AUDIT SIGN-OFF", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(12)

        # Evidentiary Disclaimer Box (Mandatory Forensic Caveat)
        pdf.set_fill_color(254, 242, 242)  # Red 50
        pdf.set_draw_color(248, 113, 113)  # Red 400
        pdf.rect(15, pdf.get_y(), 180, 24, "DF")

        pdf.set_xy(18, pdf.get_y() + 2)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 4, "MANDATORY FORENSIC METHODOLOGY & EVIDENTIARY DISCLAIMER:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(18)
        pdf.set_font("Helvetica", "", 6.8)
        pdf.set_text_color(127, 29, 29)
        disclaimer = (
            "VisionForensics AI provides probabilistic anomaly detections and statistical risk estimates. "
            "Under no circumstances do automated outputs constitute definitive legal claims of 'CONFIRMED FORGERY' "
            "or self-authenticating judicial warrants. Detected discrepancies, feature importances, and structural "
            "similarity metrics reflect digital artifacts that may arise from optical scanning variances, legitimate "
            "revisions, compression transcodings, or fraudulent manipulation. Findings must be evaluated in "
            "conjunction with independent corroborating forensic evidence."
        )
        pdf.multi_cell(174, 3.2, sanitize_text(disclaimer))

        return bytes(pdf.output())

    def _section_title(self, pdf: FPDF, title: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(0, 6, sanitize_text(title), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1.5)
