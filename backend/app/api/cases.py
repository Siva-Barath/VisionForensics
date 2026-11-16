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
    priority: Literal['routine', 'urgent'] = 'routine'


def case_query(user):
    statement = select(Case)
    if user.role not in ('SYSTEM_ADMINISTRATOR', 'SENIOR_INVESTIGATOR'):
        statement = statement.where(Case.lead_investigator_id == user.id)
    return statement


def serialize_case(case, db):
    return {'id': case.id, 'case_number': case.case_number, 'title': case.title,
            'notes': case.description, 'priority': case.priority, 'status': case.status,
            'created_at': case.created_at.isoformat(),
            'document_count': db.scalar(select(func.count()).select_from(Document).where(Document.case_id == case.id))}


@router.post('/cases', status_code=201)
def create_case(payload: CaseInput, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not payload.title.strip():
        raise HTTPException(422, 'Case title must contain text')
    case = new_case(payload.title, payload.notes, payload.priority, current_user.id)
    db.add(case)
    db.commit()
    db.refresh(case)
    return serialize_case(case, db)


@router.get('/cases')
def list_cases(limit: int = Query(50, ge=1, le=100), skip: int = Query(0, ge=0),
               current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cases = db.scalars(case_query(current_user).order_by(Case.created_at.desc()).offset(skip).limit(limit)).all()
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
