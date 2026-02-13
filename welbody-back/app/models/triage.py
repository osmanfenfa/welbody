from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime
from app.db.base import Base


class Triage(Base):
    __tablename__ = "triage"

    id = Column(Integer, primary_key=True, index=True)
    triage_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), nullable=False, index=True)
    nurse_name = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    vital_signs = Column(Text, nullable=True)
    assessment_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Triage {self.triage_id} for {self.patient_id} priority={self.priority}>"
