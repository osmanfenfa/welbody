from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PatientRegistrationRequest(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    complaints: Optional[str] = None
    vital_signs: Optional[dict] = None
    triage_notes: Optional[str] = None
    priority: Optional[str] = None
    officer_name: Optional[str] = None
    patient_notes: Optional[str] = None


class PatientUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    patient_notes: Optional[str] = None
    complaints: Optional[str] = None
    vital_signs: Optional[dict] = None
    triage_notes: Optional[str] = None
    priority: Optional[str] = None
    officer_name: Optional[str] = None


class TriageDataResponse(BaseModel):
    triage_id: str
    nurse_name: Optional[str] = None
    priority: Optional[str] = None
    complaints: Optional[str] = None
    vital_signs: Optional[dict] = None
    triage_notes: Optional[str] = None
    created_at: datetime


class PatientRecordResponse(BaseModel):
    patient_id: str
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    patient_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_triage: Optional[TriageDataResponse] = None


class PatientRegistrationResponse(PatientRecordResponse):
    id_card_url: str = Field(description="GET this URL to print/download patient card")


class PatientListResponse(BaseModel):
    total: int
    patients: list[PatientRecordResponse]
