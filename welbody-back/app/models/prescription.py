"""
Prescription model for medication prescriptions
Implements US-10: Prescribe medications electronically
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base import Base

class PrescriptionStatus(str, enum.Enum):
    """Status of prescription"""
    DRAFT = "draft"
    ISSUED = "issued"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Frequency(str, enum.Enum):
    """Medication frequency"""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_4_HOURS = "every_4_hours"
    EVERY_6_HOURS = "every_6_hours"
    EVERY_8_HOURS = "every_8_hours"
    EVERY_12_HOURS = "every_12_hours"
    AS_NEEDED = "as_needed"
    ONCE_WEEKLY = "once_weekly"
    CUSTOM = "custom"

class Route(str, enum.Enum):
    """Route of administration"""
    ORAL = "oral"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBCUTANEOUS = "subcutaneous"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    SUBLINGUAL = "sublingual"
    RECTAL = "rectal"

class Prescription(Base):
    """Medication prescription model"""
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False, index=True)
    doctor_name = Column(String(100), nullable=False)
    doctor_id = Column(String(50), nullable=True)
    doctor_specialty = Column(String(100), nullable=True)
    medication_name = Column(String(100), nullable=False)
    medication_code = Column(String(50), nullable=True)
    drug_generic_name = Column(String(100), nullable=True)
    dose = Column(String(100), nullable=False)  
    dose_value = Column(String(50), nullable=True)
    dose_unit = Column(String(50), nullable=True)
    route = Column(SQLEnum(Route), default=Route.ORAL)
    frequency = Column(SQLEnum(Frequency), default=Frequency.THREE_TIMES_DAILY)
    custom_frequency = Column(String(200), nullable=True)
    duration = Column(String(100), nullable=True)  
    total_quantity = Column(String(100), nullable=True)
    refills_allowed = Column(Integer, default=0)
    instructions = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    clinical_indication = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    side_effects = Column(Text, nullable=True)
    precautions = Column(Text, nullable=True)
    status = Column(SQLEnum(PrescriptionStatus), default=PrescriptionStatus.ISSUED)
    prescribed_date = Column(DateTime, server_default=func.now(), nullable=False)
    dispensed_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Prescription {self.prescription_id}: {self.medication_name} for {self.patient_id}>"
