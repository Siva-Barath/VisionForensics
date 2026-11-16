"""
comparison_repository.py — Data access repository for Document Comparison exhibits.
Persists and retrieves forensic differential analysis records.
"""

from __future__ import annotations
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_

from app.models.comparison import DocumentComparison
from app.core.logging import get_logger

logger = get_logger(__name__)


class ComparisonRepository:
    """Repository handling database operations for forensic document comparisons."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def create_comparison(
        self,
        document_a_id: str,
        document_b_id: str,
        page_a: int,
        page_b: int,
        similarity_score: float,
        ssim_score: float,
        difference_percentage: float,
        alignment_status: str,
        alignment_confidence: float,
        verdict_category: str,
        differential_regions: List[Dict[str, Any]],
        metadata_diff: Dict[str, Any],
        summary: Dict[str, Any],
        artifacts: Dict[str, Any],
        user_id: Optional[str] = None,
        comparison_id: Optional[str] = None,
    ) -> DocumentComparison:
        """Persists a new forensic document comparison record."""
        comp = DocumentComparison(
            id=comparison_id or str(uuid.uuid4()),
            document_a_id=document_a_id,
            document_b_id=document_b_id,
            page_a=page_a,
            page_b=page_b,
            user_id=user_id,
            similarity_score=similarity_score,
            ssim_score=ssim_score,
            difference_percentage=difference_percentage,
            alignment_status=alignment_status,
            alignment_confidence=alignment_confidence,
            verdict_category=verdict_category,
            differential_regions=differential_regions,
            metadata_diff=metadata_diff,
            summary=summary,
            artifacts=artifacts,
        )
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        logger.info(
            "Created DocumentComparison %s (doc_a=%s, doc_b=%s, similarity=%.4f)",
            comp.id,
            document_a_id,
            document_b_id,
            similarity_score,
        )
        return comp

    def get_comparison(self, comparison_id: str) -> Optional[DocumentComparison]:
        """Fetches a comparison record by its unique ID with document relationships."""
        stmt = (
            select(DocumentComparison)
            .options(
                joinedload(DocumentComparison.document_a),
                joinedload(DocumentComparison.document_b),
            )
            .where(DocumentComparison.id == comparison_id)
        )
        return self.db.scalars(stmt).first()

    def get_comparisons_for_documents(
        self, document_id: str
    ) -> List[DocumentComparison]:
        """Finds all comparisons involving a given document ID."""
        stmt = (
            select(DocumentComparison)
            .where(
                or_(
                    DocumentComparison.document_a_id == document_id,
                    DocumentComparison.document_b_id == document_id,
                )
            )
            .order_by(DocumentComparison.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
