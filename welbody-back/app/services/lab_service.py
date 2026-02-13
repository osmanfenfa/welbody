"""
Lab service for managing laboratory tests and results
Implements US-07: Request laboratory tests
Implements US-08: Review laboratory results
"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.models.lab import LabRequest, LabResult
from app.schemas.lab import LabRequestCreateRequest, LabRequestUpdateRequest, LabResultCreateRequest

class LabService:
    """Service for laboratory test management"""
    
    @staticmethod
    def create_lab_request(db: Session, patient_id: str, request_data: LabRequestCreateRequest) -> LabRequest:
        """Create a new lab test request (US-07)"""
        try:
            # Generate request ID similar to patient ID format
            request_id = LabService._generate_request_id(db)
            
            db_request = LabRequest(
                request_id=request_id,
                patient_id=patient_id,
                doctor_name=request_data.doctor_name,
                doctor_specialty=request_data.doctor_specialty,
                test_type=request_data.test_type,
                test_description=request_data.test_description,
                test_code=request_data.test_code,
                priority=request_data.priority,
                clinical_indication=request_data.clinical_indication,
                relevant_patient_history=request_data.relevant_patient_history,
                expected_completion_date=request_data.expected_completion_date,
            )
            
            db.add(db_request)
            db.commit()
            db.refresh(db_request)
            
            return db_request
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create lab request: {str(e)}")
    
    @staticmethod
    def get_lab_request(db: Session, request_id: str) -> LabRequest:
        """Get lab request by ID"""
        return db.query(LabRequest).filter(LabRequest.request_id == request_id).first()
    
    @staticmethod
    def get_patient_lab_requests(db: Session, patient_id: str, skip: int = 0, limit: int = 100) -> tuple[int, list[LabRequest]]:
        """Get all lab requests for a patient"""
        total = db.query(LabRequest).filter(LabRequest.patient_id == patient_id).count()
        requests = db.query(LabRequest).filter(
            LabRequest.patient_id == patient_id
        ).order_by(LabRequest.requested_date.desc()).offset(skip).limit(limit).all()
        return total, requests
    
    @staticmethod
    def update_lab_request(db: Session, request_id: str, update_data: LabRequestUpdateRequest) -> LabRequest:
        """Update a lab request"""
        try:
            db_request = db.query(LabRequest).filter(LabRequest.request_id == request_id).first()
            
            if not db_request:
                raise ValueError(f"Lab request {request_id} not found")
            
            update_dict = update_data.model_dump(exclude_unset=True)
            
            for key, value in update_dict.items():
                if value is not None:
                    setattr(db_request, key, value)
            
            db_request.updated_at = datetime.now()
            
            db.commit()
            db.refresh(db_request)
            
            return db_request
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update lab request: {str(e)}")
    
    @staticmethod
    def submit_lab_result(db: Session, patient_id: str, result_data: LabResultCreateRequest) -> LabResult:
        """Submit lab test results (US-08)"""
        try:
            # Get the lab request
            lab_request = db.query(LabRequest).filter(
                LabRequest.request_id == result_data.request_id
            ).first()
            
            if not lab_request:
                raise ValueError(f"Lab request {result_data.request_id} not found")
            
            # Generate result ID
            result_id = LabService._generate_result_id(db)
            
            db_result = LabResult(
                result_id=result_id,
                request_id=result_data.request_id,
                patient_id=patient_id,
                test_type=lab_request.test_type,
                result_data=result_data.result_data,
                result_numeric=result_data.result_numeric,
                result_unit=result_data.result_unit,
                reference_range=result_data.reference_range,
                normal_range=result_data.normal_range,
                interpretation=result_data.interpretation,
                abnormal_flag=result_data.abnormal_flag,
                comments=result_data.comments,
                technician_name=result_data.technician_name,
                lab_name=result_data.lab_name,
                completed_date=datetime.now(),
            )
            
            # Update lab request status to completed
            lab_request.status = "completed"
            
            db.add(db_result)
            db.commit()
            db.refresh(db_result)
            
            return db_result
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to submit lab result: {str(e)}")
    
    @staticmethod
    def get_lab_result(db: Session, result_id: str) -> LabResult:
        """Get lab result by ID"""
        return db.query(LabResult).filter(LabResult.result_id == result_id).first()
    
    @staticmethod
    def get_patient_lab_results(db: Session, patient_id: str, skip: int = 0, limit: int = 100) -> tuple[int, list[LabResult]]:
        """Get all lab results for a patient"""
        total = db.query(LabResult).filter(LabResult.patient_id == patient_id).count()
        results = db.query(LabResult).filter(
            LabResult.patient_id == patient_id
        ).order_by(LabResult.result_date.desc()).offset(skip).limit(limit).all()
        return total, results
    
    @staticmethod
    def _generate_request_id(db: Session) -> str:
        """Generate unique lab request ID"""
        today = datetime.now().date()
        date_str = today.strftime("%Y%m%d")
        
        requests_today = db.query(LabRequest).filter(
            LabRequest.request_id.ilike(f"LAB-{date_str}-%")
        ).count()
        
        sequence = str(requests_today + 1).zfill(4)
        return f"LAB-{date_str}-{sequence}"
    
    @staticmethod
    def _generate_result_id(db: Session) -> str:
        """Generate unique lab result ID"""
        today = datetime.now().date()
        date_str = today.strftime("%Y%m%d")
        
        results_today = db.query(LabResult).filter(
            LabResult.result_id.ilike(f"RES-{date_str}-%")
        ).count()
        
        sequence = str(results_today + 1).zfill(4)
        return f"RES-{date_str}-{sequence}"
    
    # ========== Lab Technician Methods (US-14, US-15, US-16) ==========
    
    @staticmethod
    def get_all_pending_requests(db: Session, skip: int = 0, limit: int = 100) -> tuple[int, list[LabRequest]]:
        """Get all pending lab requests (US-14)"""
        total = db.query(LabRequest).filter(
            LabRequest.status.in_(["requested", "pending"])
        ).count()
        requests = db.query(LabRequest).filter(
            LabRequest.status.in_(["requested", "pending"])
        ).order_by(
            LabRequest.priority.asc(),
            LabRequest.requested_date.asc()
        ).offset(skip).limit(limit).all()
        return total, requests
    
    @staticmethod
    def get_in_progress_requests(db: Session, skip: int = 0, limit: int = 100) -> tuple[int, list[LabRequest]]:
        """Get all in-progress lab requests (US-16)"""
        total = db.query(LabRequest).filter(LabRequest.status == "in_progress").count()
        requests = db.query(LabRequest).filter(
            LabRequest.status == "in_progress"
        ).order_by(LabRequest.requested_date.asc()).offset(skip).limit(limit).all()
        return total, requests
    
    @staticmethod
    def mark_in_progress(db: Session, request_id: str) -> LabRequest:
        """Mark a lab request as in progress (US-16)"""
        try:
            lab_request = db.query(LabRequest).filter(LabRequest.request_id == request_id).first()
            
            if not lab_request:
                raise ValueError(f"Lab request {request_id} not found")
            
            lab_request.status = "in_progress"
            lab_request.updated_at = datetime.now()
            
            db.commit()
            db.refresh(lab_request)
            
            return lab_request
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to mark request as in progress: {str(e)}")
    
    @staticmethod
    def get_request_by_id_and_patient(db: Session, request_id: str, patient_id: str = None) -> LabRequest:
        """Get a lab request by ID (with optional patient verification)"""
        query = db.query(LabRequest).filter(LabRequest.request_id == request_id)
        if patient_id:
            query = query.filter(LabRequest.patient_id == patient_id)
        return query.first()
    
    @staticmethod
    def get_requests_by_test_type(db: Session, test_type: str, skip: int = 0, limit: int = 100) -> tuple[int, list[LabRequest]]:
        """Get requests filtered by test type (US-14)"""
        total = db.query(LabRequest).filter(
            LabRequest.test_type == test_type,
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).count()
        requests = db.query(LabRequest).filter(
            LabRequest.test_type == test_type,
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).order_by(
            LabRequest.priority.asc(),
            LabRequest.requested_date.asc()
        ).offset(skip).limit(limit).all()
        return total, requests
    
    @staticmethod
    def get_requests_by_priority(db: Session, priority: str, skip: int = 0, limit: int = 100) -> tuple[int, list[LabRequest]]:
        """Get requests filtered by priority (US-16)"""
        total = db.query(LabRequest).filter(
            LabRequest.priority == priority,
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).count()
        requests = db.query(LabRequest).filter(
            LabRequest.priority == priority,
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).order_by(LabRequest.requested_date.asc()).offset(skip).limit(limit).all()
        return total, requests
    
    @staticmethod
    def get_workload_summary(db: Session) -> dict:
        """Get lab technician workload summary (US-16)"""
        pending_count = db.query(LabRequest).filter(
            LabRequest.status.in_(["requested", "pending"])
        ).count()
        
        in_progress_count = db.query(LabRequest).filter(
            LabRequest.status == "in_progress"
        ).count()
        
        completed_today = db.query(LabResult).filter(
            LabResult.completed_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Get requests by priority
        emergency = db.query(LabRequest).filter(
            LabRequest.priority == "emergency",
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).count()
        
        urgent = db.query(LabRequest).filter(
            LabRequest.priority == "urgent",
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).count()
        
        routine = db.query(LabRequest).filter(
            LabRequest.priority == "routine",
            LabRequest.status.in_(["requested", "pending", "in_progress"])
        ).count()
        
        return {
            "pending_requests": pending_count,
            "in_progress_requests": in_progress_count,
            "completed_today": completed_today,
            "by_priority": {
                "emergency": emergency,
                "urgent": urgent,
                "routine": routine
            }
        }

    @staticmethod
    def get_completed_requests(db: Session, skip: int = 0, limit: int = 100) -> tuple[int, list[LabRequest]]:
        """Get all completed lab requests (US-16)"""
        total = db.query(LabRequest).filter(LabRequest.status == "completed").count()
        requests = db.query(LabRequest).filter(
            LabRequest.status == "completed"
        ).order_by(LabRequest.updated_at.desc()).offset(skip).limit(limit).all()
        return total, requests
