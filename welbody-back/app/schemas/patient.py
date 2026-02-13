from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PatientCreate(BaseModel):
    patient_id: str
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PatientResponse(BaseModel):
    patient_id: str
    first_name: str
    last_name: Optional[str]
    date_of_birth: Optional[str]
    gender: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
