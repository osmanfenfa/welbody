from datetime import datetime

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.triage import Triage


def _next_daily_sequence_id(db: Session, prefix: str, field) -> str:
    latest = (
        db.query(field)
        .filter(field.like(f"{prefix}-%"))
        .order_by(field.desc())
        .first()
    )
    next_number = 1
    if latest and latest[0]:
        try:
            next_number = int(str(latest[0]).split("-")[-1]) + 1
        except Exception:
            next_number = 1
    return f"{prefix}-{str(next_number).zfill(4)}"


def generate_patient_id(db: Session) -> str:
    day_prefix = datetime.utcnow().strftime("%Y%m%d")
    return _next_daily_sequence_id(db, f"PAT-{day_prefix}", Patient.patient_id)


def generate_triage_id(db: Session) -> str:
    day_prefix = datetime.utcnow().strftime("%Y%m%d")
    return _next_daily_sequence_id(db, f"TRI-{day_prefix}", Triage.triage_id)
