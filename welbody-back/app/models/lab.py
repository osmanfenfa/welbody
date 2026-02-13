"""
Laboratory models for test requests and results
Implements US-07: Electronically request laboratory tests
Implements US-08: Review laboratory results
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base import Base

class TestStatus(str, enum.Enum):
    """Status of laboratory test"""
    REQUESTED = "requested"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestPriority(str, enum.Enum):
    """Priority level of test"""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class LabRequest(Base):
    """Laboratory test request model"""
    __tablename__ = "lab_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False, index=True)
    doctor_name = Column(String(100), nullable=False)
    doctor_specialty = Column(String(100), nullable=True)
    test_type = Column(String(100), nullable=False)  
    test_description = Column(Text, nullable=True)
    test_code = Column(String(50), nullable=True)
    priority = Column(SQLEnum(TestPriority), default=TestPriority.ROUTINE)
    status = Column(SQLEnum(TestStatus), default=TestStatus.REQUESTED)
    clinical_indication = Column(Text, nullable=True)
    relevant_patient_history = Column(Text, nullable=True)
    
    # Timestamps
    requested_date = Column(DateTime, server_default=func.now(), nullable=False)
    expected_completion_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<LabRequest {self.request_id}: {self.test_type}>"

class LabResult(Base):
    """Laboratory test result model"""
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(String(50), unique=True, index=True, nullable=False)
    request_id = Column(String(50), ForeignKey("lab_requests.request_id"), nullable=False, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False, index=True)
    technician_name = Column(String(100), nullable=True)
    lab_name = Column(String(100), nullable=True)
    test_type = Column(String(100), nullable=False)
    result_status = Column(SQLEnum(TestStatus), default=TestStatus.COMPLETED)
    result_data = Column(Text, nullable=True) 
    result_numeric = Column(Float, nullable=True)  # Single numeric result if applicable
    result_unit = Column(String(50), nullable=True)  
    reference_range = Column(String(100), nullable=True)
    normal_range = Column(String(100), nullable=True)
    interpretation = Column(Text, nullable=True)
    abnormal_flag = Column(String(20), nullable=True)  # Normal, Abnormal, Critical
    comments = Column(Text, nullable=True)
    
    # Timestamps
    result_date = Column(DateTime, server_default=func.now(), nullable=False)
    completed_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<LabResult {self.result_id}: {self.test_type}>"
