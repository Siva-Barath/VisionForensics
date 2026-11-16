"""Create case entities without committing outside the caller's transaction."""
from datetime import datetime, timezone
import uuid
from app.models.case import Case


def new_case(title, notes, priority, user_id):
    return Case(id=str(uuid.uuid4()), case_number=f"VF-{datetime.now(timezone.utc):%Y}-{uuid.uuid4().hex[:10].upper()}",
                title=title.strip(), description=notes, priority=priority.upper(), lead_investigator_id=user_id)
