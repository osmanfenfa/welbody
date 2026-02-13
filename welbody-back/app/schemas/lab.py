"""
Laboratory schemas for Pydantic validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TestStatus(str, Enum):
    REQUESTED = "requested"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class LabRequestCreateRequest(BaseModel):
    """Request schema for creating a lab test request"""
    test_type: str = Field(..., description="Type of test")
    test_description: Optional[str] = Field(None, description="Test description")
    test_code: Optional[str] = Field(None, description="Test code")
    priority: TestPriority = Field(default=TestPriority.ROUTINE)
    clinical_indication: Optional[str] = Field(None, description="Clinical indication")
    relevant_patient_history: Optional[str] = Field(None, description="Relevant patient history")
    doctor_name: Optional[str] = Field(None, description="Requesting doctor's name")
    doctor_specialty: Optional[str] = Field(None, description="Doctor's specialty")
    expected_completion_date: Optional[datetime] = Field(None, description="Expected completion date")

class LabRequestUpdateRequest(BaseModel):
    """Request schema for updating a lab request"""
    priority: Optional[TestPriority] = None
    status: Optional[TestStatus] = None
    clinical_indication: Optional[str] = None
    relevant_patient_history: Optional[str] = None
    expected_completion_date: Optional[datetime] = None

class LabRequestResponse(BaseModel):
    """Response schema for lab request"""
    id: int
    request_id: str
    patient_id: str
    doctor_name: str
    doctor_specialty: Optional[str]
    test_type: str
    test_description: Optional[str]
    test_code: Optional[str]
    priority: TestPriority
    status: TestStatus
    clinical_indication: Optional[str]
    relevant_patient_history: Optional[str]
    requested_date: datetime
    expected_completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LabResultCreateRequest(BaseModel):
    """Request schema for submitting lab results"""
    request_id: str = Field(..., description="Lab request ID")
    result_data: Optional[str] = Field(None, description="Detailed result data")
    result_numeric: Optional[float] = Field(None, description="Numeric result value")
    result_unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Reference range")
    normal_range: Optional[str] = Field(None, description="Normal range")
    interpretation: Optional[str] = Field(None, description="Interpretation of results")
    abnormal_flag: Optional[str] = Field(None, description="Normal/Abnormal/Critical")
    comments: Optional[str] = Field(None, description="Additional comments")
    technician_name: Optional[str] = Field(None, description="Technician's name")
    lab_name: Optional[str] = Field(None, description="Laboratory name")

class LabResultResponse(BaseModel):
    """Response schema for lab result"""
    id: int
    result_id: str
    request_id: str
    patient_id: str
    test_type: str
    result_status: TestStatus
    result_data: Optional[str]
    result_numeric: Optional[float]
    result_unit: Optional[str]
    reference_range: Optional[str]
    normal_range: Optional[str]
    interpretation: Optional[str]
    abnormal_flag: Optional[str]
    comments: Optional[str]
    technician_name: Optional[str]
    lab_name: Optional[str]
    result_date: datetime
    completed_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
