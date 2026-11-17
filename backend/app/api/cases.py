"""Investigation cases and exact, authorization-scoped workspace totals."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.database.session import get_db
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.case_service import new_case

router = APIRouter(tags=['Cases'])


class CaseInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: Optional[str] = Field(None, max_length=10000)
    priority: str = 'ROUTINE'
    status: Optional[str] = 'ACTIVE'


def case_query(user):
    statement = select(Case)
    if user.role not in ('SYSTEM_ADMINISTRATOR', 'SENIOR_INVESTIGATOR'):
        statement = statement.where(Case.lead_investigator_id == user.id)
    return statement


def serialize_case(case, db):
    docs = db.scalars(select(Document).where(Document.case_id == case.id)).all()
    doc_ids = [d.id for d in docs]

    final_assessment = "PENDING"
    primary_doc_id = doc_ids[0] if doc_ids else None

    if doc_ids:
        analyses = db.scalars(
            select(Analysis)
            .where(Analysis.document_id.in_(doc_ids), Analysis.is_latest.is_(True))
        ).all()
        tiers = [a.unified_risk_tier for a in analyses]
        if "HIGH_RISK" in tiers:
            final_assessment = "HIGH_RISK"
        elif "SUSPICIOUS" in tiers:
            final_assessment = "SUSPICIOUS"
        elif "LOW_RISK" in tiers:
            final_assessment = "LOW_RISK"
        else:
            final_assessment = "PENDING"

    return {
        'id': case.id,
        'case_number': case.case_number,
        'title': case.title,
        'notes': case.description,
        'priority': case.priority,
        'status': case.status,
        'created_at': case.created_at.isoformat() if case.created_at else None,
        'updated_at': (case.updated_at or case.created_at).isoformat() if (case.updated_at or case.created_at) else None,
        'document_count': len(docs),
        'final_assessment': final_assessment,
        'primary_document_id': primary_doc_id,
        'exhibit_filenames': [d.original_filename for d in docs],
    }


@router.post('/cases', status_code=201)
def create_case(payload: CaseInput, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not payload.title.strip():
        raise HTTPException(422, 'Case title must contain text')
    case = new_case(payload.title, payload.notes, payload.priority, current_user.id)
    if payload.status:
        case.status = payload.status.upper()
    db.add(case)
    db.commit()
    db.refresh(case)
    return serialize_case(case, db)


@router.get('/cases/stats')
def get_case_stats(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    all_cases = db.scalars(case_query(current_user)).all()
    total = len(all_cases)
    active = sum(1 for c in all_cases if str(c.status).upper() in ('ACTIVE', 'OPEN'))
    under_review = sum(1 for c in all_cases if str(c.status).upper() in ('IN_REVIEW', 'UNDER_REVIEW', 'REVIEW'))
    completed = sum(1 for c in all_cases if str(c.status).upper() in ('COMPLETED', 'CLOSED'))
    escalated = sum(1 for c in all_cases if str(c.status).upper() in ('ESCALATED', 'FLAGGED'))
    return {
        'total_cases': total,
        'active': active,
        'under_review': under_review,
        'completed': completed,
        'escalated': escalated,
    }


@router.get('/cases')
def list_cases(limit: int = Query(100, ge=1, le=200), skip: int = Query(0, ge=0),
               status: Optional[str] = Query(None),
               search: Optional[str] = Query(None),
               current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    stmt = case_query(current_user)
    if status and status.upper() != 'ALL':
        if status.upper() == 'UNDER_REVIEW' or status.upper() == 'REVIEW':
            stmt = stmt.where(Case.status.in_(['IN_REVIEW', 'UNDER_REVIEW', 'REVIEW']))
        else:
            stmt = stmt.where(func.upper(Case.status) == status.upper())
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (Case.case_number.ilike(pattern)) |
            (Case.title.ilike(pattern)) |
            (Case.description.ilike(pattern))
        )
    cases = db.scalars(stmt.order_by(Case.created_at.desc()).offset(skip).limit(limit)).all()
    return [serialize_case(case, db) for case in cases]


@router.get('/cases/{case_id}')
def get_case(case_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    case = db.scalars(case_query(current_user).where(Case.id == case_id)).first()
    if case is None:
        raise HTTPException(404, 'Case not found or access denied')
    return serialize_case(case, db)


@router.get('/workspace/stats')
def workspace_stats(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    visible = DocumentRepository(db).visible_documents_query(current_user).subquery()
    docs = db.scalar(select(func.count()).select_from(visible))
    cases = db.scalar(select(func.count()).select_from(case_query(current_user).subquery()))
    joined = select(Analysis.unified_risk_tier, func.count()).join(visible, Analysis.document_id == visible.c.id).where(Analysis.is_latest.is_(True)).group_by(Analysis.unified_risk_tier)
    tiers = dict(db.execute(joined).all())
    examined = db.scalar(select(func.count()).select_from(visible).where(visible.c.status == 'processed'))
    return {'total_cases': cases, 'total_documents': docs, 'examined_documents': examined,
            'requires_review': tiers.get('SUSPICIOUS', 0), 'high_risk': tiers.get('HIGH_RISK', 0),
            'low_risk': tiers.get('LOW_RISK', 0), 'unknown': tiers.get('UNKNOWN', 0)}
