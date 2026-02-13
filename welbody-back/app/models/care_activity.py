from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Enum as SQLEnum
from datetime import datetime
import enum
from app.db.base import Base


class ActivityType(str, enum.Enum):
    MEDICATION = "medication"
    VITALS = "vitals"
    PROCEDURE = "procedure"
    NOTE = "note"


class ActivityStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CareActivity(Base):
    __tablename__ = "care_activities"

    id = Column(Integer, primary_key=True, index=True)
    care_activity_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), nullable=False, index=True)
    assignment_id = Column(String(50), nullable=True)
    staff_name = Column(String(200), nullable=True)
    staff_role = Column(String(100), nullable=True)
    activity_type = Column(SQLEnum(ActivityType), default=ActivityType.NOTE)
    description = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    vital_signs_recorded = Column(Text, nullable=True)
    is_pre_operative = Column(Boolean, default=False)
    is_post_operative = Column(Boolean, default=False)
    procedure_type = Column(String(200), nullable=True)
    notes_for_next_shift = Column(Text, nullable=True)
    intervention_required = Column(Boolean, default=False)
    status = Column(SQLEnum(ActivityStatus), default=ActivityStatus.PLANNED)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CareActivity {self.care_activity_id} for {self.patient_id} status={self.status}>"
