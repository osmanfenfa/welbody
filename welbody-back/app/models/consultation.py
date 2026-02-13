"""
Consultation model for doctor's clinical findings and care notes
Implements US-06: Document clinical findings, observations, and care notes
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base import Base

class ConsultationType(str, enum.Enum):
    """Type of consultation"""
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    SPECIALIST = "specialist"

class ConsultationStatus(str, enum.Enum):
    """Consultation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"

class Consultation(Base):
    """Consultation model for storing clinical findings and care notes"""
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False, index=True)
    doctor_name = Column(String(100), nullable=False)
    doctor_specialty = Column(String(100), nullable=True)
    consultation_type = Column(SQLEnum(ConsultationType), default=ConsultationType.INITIAL)
    status = Column(SQLEnum(ConsultationStatus), default=ConsultationStatus.PENDING)
    chief_complaint = Column(Text, nullable=True)
    history_of_present_illness = Column(Text, nullable=True)
    physical_examination = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    differential_diagnosis = Column(Text, nullable=True)
    treatment_plan = Column(Text, nullable=True)
    care_notes = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    
    # Timestamps
    consultation_date = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Consultation {self.id}: {self.patient_id} - {self.consultation_type}>"