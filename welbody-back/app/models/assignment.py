"""
Assignment model for staff assignments to patients
Implements US-09: Assign nurses or surgeons to a patient
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base import Base

class StaffRole(str, enum.Enum):
    """Role of assigned staff"""
    NURSE = "nurse"
    SURGEON = "surgeon"
    SPECIALIST = "specialist"
    ANESTHETIST = "anesthetist"
    TECHNICIAN = "technician"

class AssignmentStatus(str, enum.Enum):
    """Status of assignment"""
    ACTIVE = "active"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Assignment(Base):
    """Staff assignment model for assigning staff to patients"""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False, index=True)
    staff_name = Column(String(100), nullable=False)
    staff_id = Column(String(50), nullable=True)
    staff_role = Column(SQLEnum(StaffRole), nullable=False)
    specialty = Column(String(100), nullable=True)
    assigning_doctor = Column(String(100), nullable=False)
    status = Column(SQLEnum(AssignmentStatus), default=AssignmentStatus.ACTIVE)
    task_description = Column(Text, nullable=True)
    care_instructions = Column(Text, nullable=True)
    special_notes = Column(Text, nullable=True)
    assigned_date = Column(DateTime, server_default=func.now(), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Assignment {self.assignment_id}: {self.staff_name} ({self.staff_role}) to {self.patient_id}>"