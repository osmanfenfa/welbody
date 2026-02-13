"""
Consultation schemas for Pydantic validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ConsultationType(str, Enum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    SPECIALIST = "specialist"

class ConsultationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"

class ConsultationCreateRequest(BaseModel):
    """Request schema for creating a consultation"""
    chief_complaint: Optional[str] = Field(None, description="Chief complaint")
    history_of_present_illness: Optional[str] = Field(None, description="History of present illness")
    physical_examination: Optional[str] = Field(None, description="Physical examination findings")
    assessment: Optional[str] = Field(None, description="Doctor's assessment")
    diagnosis: Optional[str] = Field(None, description="Diagnosis")
    differential_diagnosis: Optional[str] = Field(None, description="Differential diagnosis")
    treatment_plan: Optional[str] = Field(None, description="Treatment plan")
    care_notes: Optional[str] = Field(None, description="Care notes")
    findings: Optional[str] = Field(None, description="Clinical findings")
    observations: Optional[str] = Field(None, description="Observations")
    consultation_type: ConsultationType = Field(default=ConsultationType.INITIAL)
    doctor_name: Optional[str] = Field(None, description="Doctor's name")
    doctor_specialty: Optional[str] = Field(None, description="Doctor's specialty")

class ConsultationUpdateRequest(BaseModel):
    """Request schema for updating a consultation"""
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    diagnosis: Optional[str] = None
    differential_diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    care_notes: Optional[str] = None
    findings: Optional[str] = None
    observations: Optional[str] = None
    status: Optional[ConsultationStatus] = None

class ConsultationResponse(BaseModel):
    """Response schema for consultation data"""
    id: int
    patient_id: str
    doctor_name: str
    doctor_specialty: Optional[str]
    consultation_type: ConsultationType
    status: ConsultationStatus
    chief_complaint: Optional[str]
    history_of_present_illness: Optional[str]
    physical_examination: Optional[str]
    assessment: Optional[str]
    diagnosis: Optional[str]
    differential_diagnosis: Optional[str]
    treatment_plan: Optional[str]
    care_notes: Optional[str]
    findings: Optional[str]
    observations: Optional[str]
    consultation_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
