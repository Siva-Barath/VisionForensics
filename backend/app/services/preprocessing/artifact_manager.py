"""
ArtifactManager — registers processed page images as Artifacts on AnalysisContext.

Does not perform any image processing.
Owns the naming convention and MIME type assignment for preprocessed artifacts.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.pipeline.artifact import Artifact
from app.pipeline.context import AnalysisContext
from app.core.logging import get_logger

logger = get_logger(__name__)

_STAGE = "preprocessing"


class ArtifactManager:
    """
    Saves a processed image to disk and registers it as an Artifact.

    Args:
        output_dir: Directory where processed images are written.
                    Typically StorageService.processed_dir(document_id).
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save_and_register(
        self,
        image: np.ndarray,
        context: AnalysisContext,
        page_index: int,
    ) -> Artifact:
        """
        Write `image` to disk and register it as a `preprocessed_image` Artifact.

        Args:
            image:      Processed image array (H×W×C BGR or H×W gray).
            context:    Shared pipeline context — artifact is registered here.
            page_index: 0-based page index.

        Returns:
            The registered Artifact.
        """
        filename = f"{context.document_id}_preprocessed_page_{page_index}.png"
        dest = self._output_dir / filename

        success = cv2.imwrite(str(dest), image)
        if not success:
            raise OSError(f"ArtifactManager: cv2.imwrite failed for {dest}")

        artifact = Artifact(
            type="preprocessed_image",
            path=str(dest),
            mime_type="image/png",
            created_by_stage=_STAGE,
            page_index=page_index,
            description=f"Preprocessed page {page_index}",
        )
        context.register_artifact(artifact)
        logger.debug(
            "Registered preprocessed artifact | page=%d | path=%s | id=%s",
            page_index, dest, artifact.id,
        )
        return artifact
