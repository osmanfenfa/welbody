"""
Prescription schemas for Pydantic validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Frequency(str, Enum):
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

class Route(str, Enum):
    ORAL = "oral"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBCUTANEOUS = "subcutaneous"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    SUBLINGUAL = "sublingual"
    RECTAL = "rectal"

class PrescriptionCreateRequest(BaseModel):
    """Request schema for creating a prescription"""
    medication_name: str = Field(..., description="Medication name")
    medication_code: Optional[str] = Field(None, description="Medication code")
    drug_generic_name: Optional[str] = Field(None, description="Generic drug name")
    dose: str = Field(..., description="Dose (e.g., 500mg)")
    dose_value: Optional[str] = Field(None, description="Dose value")
    dose_unit: Optional[str] = Field(None, description="Dose unit")
    route: Route = Field(default=Route.ORAL, description="Route of administration")
    frequency: Frequency = Field(default=Frequency.THREE_TIMES_DAILY, description="Frequency")
    custom_frequency: Optional[str] = Field(None, description="Custom frequency")
    duration: Optional[str] = Field(None, description="Duration (e.g., 7 days)")
    total_quantity: Optional[str] = Field(None, description="Total quantity")
    refills_allowed: int = Field(default=0, description="Number of refills allowed")
    instructions: Optional[str] = Field(None, description="Instructions")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    clinical_indication: Optional[str] = Field(None, description="Clinical indication")
    contraindications: Optional[str] = Field(None, description="Contraindications")
    side_effects: Optional[str] = Field(None, description="Possible side effects")
    precautions: Optional[str] = Field(None, description="Precautions")
    doctor_name: Optional[str] = Field(None, description="Prescribing doctor's name")
    doctor_id: Optional[str] = Field(None, description="Doctor's ID")
    doctor_specialty: Optional[str] = Field(None, description="Doctor's specialty")
    expiry_date: Optional[datetime] = Field(None, description="Prescription expiry date")

class PrescriptionUpdateRequest(BaseModel):
    """Request schema for updating a prescription"""
    status: Optional[PrescriptionStatus] = None
    frequency: Optional[Frequency] = None
    custom_frequency: Optional[str] = None
    instructions: Optional[str] = None
    special_instructions: Optional[str] = None
    refills_allowed: Optional[int] = None
    expiry_date: Optional[datetime] = None

class PrescriptionResponse(BaseModel):
    """Response schema for prescription"""
    id: int
    prescription_id: str
    patient_id: str
    medication_name: str
    medication_code: Optional[str]
    drug_generic_name: Optional[str]
    dose: str
    dose_value: Optional[str]
    dose_unit: Optional[str]
    route: Route
    frequency: Frequency
    custom_frequency: Optional[str]
    duration: Optional[str]
    total_quantity: Optional[str]
    refills_allowed: int
    instructions: Optional[str]
    special_instructions: Optional[str]
    clinical_indication: Optional[str]
    contraindications: Optional[str]
    side_effects: Optional[str]
    precautions: Optional[str]
    doctor_name: str
    doctor_id: Optional[str]
    doctor_specialty: Optional[str]
    status: PrescriptionStatus
    prescribed_date: datetime
    dispensed_date: Optional[datetime]
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
