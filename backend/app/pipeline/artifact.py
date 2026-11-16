"""
Artifact — represents any file generated during pipeline execution.

Instead of passing raw file paths between stages, every generated file
is registered as an Artifact on AnalysisContext. This gives the Report
Generator and Risk Engine a uniform, typed view of all pipeline outputs
regardless of which stage produced them.

Examples of future artifacts:
  - original upload (upload stage)
  - PDF page images (preprocessing stage)
  - preprocessed images (preprocessing stage, Phase 2)
  - ELA difference images (forgery stage, Phase 3)
  - heatmaps (explainability stage, Phase 5)
  - cropped signature / logo regions (forgery stage, Phase 3)
  - generated forensic report (report stage, Phase 5)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Artifact:
    # ------------------------------------------------------------------ #
    # Identity                                                             #
    # ------------------------------------------------------------------ #
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ------------------------------------------------------------------ #
    # Classification                                                       #
    # ------------------------------------------------------------------ #
    # Semantic type — e.g. "original_upload", "page_image", "heatmap",
    # "ela_image", "report", "cropped_region", "ocr_visualization"
    type: str = ""

    # ------------------------------------------------------------------ #
    # Location                                                             #
    # ------------------------------------------------------------------ #
    path: str = ""
    sha256_hash: Optional[str] = None
    mime_type: str = ""

    # ------------------------------------------------------------------ #
    # Provenance                                                           #
    # ------------------------------------------------------------------ #
    created_by_stage: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------ #
    # Optional context                                                     #
    # ------------------------------------------------------------------ #
    description: str = ""
    # Page index this artifact belongs to (0-based). None = document-level.
    page_index: Optional[int] = None
