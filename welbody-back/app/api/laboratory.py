"""
Laboratory Technician API endpoints
Implements US-14: View lab test requests
Implements US-15: Submit test results
Implements US-16: Track test status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.dependencies import get_db, require_roles
from app.models.lab import LabRequest, LabResult
from app.schemas.lab import LabRequestResponse, LabResultCreateRequest, LabResultResponse
from app.services.lab_service import LabService

router = APIRouter(
    prefix="/lab-technician",
    tags=["lab-technician"],
    dependencies=[Depends(require_roles("LAB_TECHNICIAN", "ADMIN"))],
)


# ========== Lab Request Viewing (US-14) ==========

@router.get("/requests/pending")
def get_pending_requests(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    View all pending lab test requests (US-14)
    
    Lab technician can see all requests waiting to be processed.
    Results are ordered by priority and request time.
    """
    try:
        total, requests = LabService.get_all_pending_requests(db, skip, limit)
        return {
            "total_pending": total,
            "requests": requests,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/requests/in-progress")
def get_in_progress_requests(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    View all in-progress lab test requests (US-16)
    
    Lab technician can track tests currently being processed.
    """
    try:
        total, requests = LabService.get_in_progress_requests(db, skip, limit)
        return {
            "total_in_progress": total,
            "requests": requests,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/requests/by-type/{test_type}")
def get_requests_by_type(
    test_type: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    View pending requests filtered by test type (US-14)
    
    Lab technician can filter requests to process specific test types.
    """
    try:
        total, requests = LabService.get_requests_by_test_type(db, test_type, skip, limit)
        return {
            "test_type": test_type,
            "total_pending": total,
            "requests": requests,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/requests/by-priority/{priority}")
def get_requests_by_priority(
    priority: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    View pending requests filtered by priority (US-16)
    
    Lab technician can prioritize work by priority level.
    Valid priorities: emergency, urgent, routine
    """
    if priority not in ["emergency", "urgent", "routine"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority must be one of: emergency, urgent, routine"
        )
    
    try:
        total, requests = LabService.get_requests_by_priority(db, priority, skip, limit)
        return {
            "priority": priority,
            "total_pending": total,
            "requests": requests,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/requests/{request_id}", response_model=LabRequestResponse)
def get_request_details(
    request_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed view of a specific lab request (US-14)
    
    Lab technician can view all details needed to process the test.
    """
    try:
        lab_request = LabService.get_lab_request(db, request_id)
        
        if not lab_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lab request {request_id} not found"
            )
        
        return lab_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Status Tracking (US-16) ==========

@router.put("/requests/{request_id}/start")
def start_processing_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark a lab request as in-progress (US-16)
    
    Lab technician marks a request when starting to process it.
    """
    try:
        lab_request = LabService.mark_in_progress(db, request_id)
        
        return {
            "request_id": lab_request.request_id,
            "patient_id": lab_request.patient_id,
            "test_type": lab_request.test_type,
            "status": lab_request.status,
            "message": "Request marked as in progress"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/workload-summary")
def get_workload_summary(db: Session = Depends(get_db)):
    """
    Get workload summary for lab technician (US-16)
    
    Shows pending requests, in-progress requests, and today's completed tests.
    Helps with workload management and accountability.
    """
    try:
        summary = LabService.get_workload_summary(db)
        return {
            "timestamp": datetime.now(),
            "workload": summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Result Submission (US-15) ==========

@router.post("/results", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED)
def submit_lab_result(
    result_data: LabResultCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Submit lab test results (US-15)
    
    Lab technician enters and submits test results so doctors can access them immediately.
    Results are automatically linked to the patient and doctor is notified.
    """
    try:
        # Verify the lab request exists
        lab_request = LabService.get_lab_request(db, result_data.request_id)
        if not lab_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lab request {result_data.request_id} not found"
            )
        
        # Submit the result
        lab_result = LabService.submit_lab_result(db, lab_request.patient_id, result_data)
        
        return lab_result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/results/{result_id}", response_model=LabResultResponse)
def get_result_details(
    result_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a submitted result (US-15)
    
    Lab technician can verify submitted results.
    """
    try:
        lab_result = LabService.get_lab_result(db, result_id)
        
        if not lab_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lab result {result_id} not found"
            )
        
        return lab_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Dashboard and Reporting ==========

@router.get("/dashboard")
def get_lab_technician_dashboard(db: Session = Depends(get_db)):
    """
    Get lab technician dashboard with all key information (US-14, US-15, US-16)
    
    Provides a comprehensive view of:
    - Pending requests to process
    - Requests currently in progress
    - Recently completed results
    - Workload by priority
    """
    try:
        # Get pending requests
        pending_count, pending_requests = LabService.get_all_pending_requests(db, limit=10)
        
        # Get in-progress requests
        in_progress_count, in_progress_requests = LabService.get_in_progress_requests(db, limit=5)
        
        # Get workload summary
        summary = LabService.get_workload_summary(db)
        
        return {
            "dashboard": {
                "pending_requests": {
                    "total": pending_count,
                    "requests": pending_requests[:10]
                },
                "in_progress_requests": {
                    "total": in_progress_count,
                    "requests": in_progress_requests[:5]
                },
                "workload_summary": summary,
                "timestamp": datetime.now()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics")
def get_lab_statistics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get lab statistics for reporting (US-16)
    
    Shows test completion rates, average turnaround time, and workload trends.
    """
    try:
        from sqlalchemy import func
        
        # Count completed tests in the period
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_completed = db.query(func.count(LabResult.id)).filter(
            LabResult.completed_date >= start_date
        ).scalar()
        
        total_pending = db.query(func.count(LabRequest.id)).filter(
            LabRequest.status.in_(["requested", "pending"])
        ).scalar()
        
        total_in_progress = db.query(func.count(LabRequest.id)).filter(
            LabRequest.status == "in_progress"
        ).scalar()
        
        return {
            "statistics": {
                "completed_today": total_completed,
                "pending": total_pending,
                "in_progress": total_in_progress,
                "total_active": total_pending + total_in_progress,
                "timestamp": datetime.now()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/requests/completed")
def get_completed_requests(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    View completed lab test requests (US-16)
    
    Lab technician can track completed work for accountability.
    """
    try:
        total, requests = LabService.get_completed_requests(db, skip, limit)
        return {
            "total_completed": total,
            "requests": requests,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
