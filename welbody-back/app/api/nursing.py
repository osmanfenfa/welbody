import json
from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, require_roles
from app.core.security import normalize_role
from app.models.assignment import Assignment, AssignmentStatus, StaffRole
from app.models.care_activity import ActivityStatus, ActivityType, CareActivity
from app.models.consultation import Consultation
from app.models.lab import LabResult
from app.models.patient import Patient
from app.models.triage import Triage
from app.models.user import User

router = APIRouter(prefix="/nursing", tags=["nursing"])

class CareActivityCreateRequest(BaseModel):
    assignment_id: Optional[str] = None
    activity_type: Literal["medication", "vitals", "procedure", "note"] = "note"
    description: Optional[str] = None
    observations: Optional[str] = None
    findings: Optional[str] = None
    vital_signs_recorded: Optional[str] = None
    is_pre_operative: bool = False
    is_post_operative: bool = False
    procedure_type: Optional[str] = None
    notes_for_next_shift: Optional[str] = None
    intervention_required: bool = False
    status: Literal["planned", "in_progress", "completed"] = "completed"

def _current_staff_user(db: Session, current_user: dict) -> Optional[User]:
    user_id = current_user.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.user_id == user_id).first()

def _staff_scope_query(db: Session, current_user: dict):
    role = normalize_role(current_user.get("role"))
    query = db.query(Assignment)
    if role == "ADMIN":
        return query
    if role not in {"NURSE", "SURGEON"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db_user = _current_staff_user(db, current_user)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User profile not found")

    staff_role = StaffRole.NURSE if role == "NURSE" else StaffRole.SURGEON
    names = [value for value in [db_user.full_name, db_user.username] if value]
    matchers = [Assignment.staff_id == db_user.user_id]
    if names:
        matchers.append(Assignment.staff_name.in_(names))
    return query.filter(Assignment.staff_role == staff_role).filter(or_(*matchers))

def _patient_or_404(db: Session, patient_id: str) -> Patient:
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient

def _assert_assigned_access(db: Session, current_user: dict, patient_id: str):
    role = normalize_role(current_user.get("role"))
    if role == "ADMIN":
        return
    exists = _staff_scope_query(db, current_user).filter(Assignment.patient_id == patient_id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient not assigned to you")

def _parse_triage(raw: Optional[str]) -> dict:
    if not raw:
        return {"complaints": None, "triage_notes": None}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {
                "complaints": parsed.get("complaints"),
                "triage_notes": parsed.get("triage_notes"),
            }
    except Exception:
        pass
    return {"complaints": None, "triage_notes": raw}

@router.get("/my-assignments")
def my_assignments(
    status_filter: Optional[Literal["active", "pending", "completed", "cancelled"]] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("NURSE", "SURGEON", "ADMIN")),
):
    query = _staff_scope_query(db, current_user)
    if status_filter is not None:
        query = query.filter(Assignment.status == AssignmentStatus(status_filter))
    total = query.count()
    assignments = query.order_by(Assignment.assigned_date.desc()).offset(skip).limit(limit).all()

    rows = []
    for assignment in assignments:
        patient = db.query(Patient).filter(Patient.patient_id == assignment.patient_id).first()
        latest_consultation = (
            db.query(Consultation)
            .filter(Consultation.patient_id == assignment.patient_id)
            .order_by(Consultation.consultation_date.desc())
            .first()
        )
        latest_lab = (
            db.query(LabResult)
            .filter(LabResult.patient_id == assignment.patient_id)
            .order_by(LabResult.result_date.desc())
            .first()
        )
        rows.append(
            {
                "assignment_id": assignment.assignment_id,
                "patient_id": assignment.patient_id,
                "patient_name": f"{patient.first_name} {patient.last_name or ''}".strip() if patient else None,
                "staff_role": assignment.staff_role,
                "assigning_doctor": assignment.assigning_doctor,
                "care_instructions": assignment.care_instructions,
                "task_description": assignment.task_description,
                "special_notes": assignment.special_notes,
                "status": assignment.status,
                "latest_diagnosis": latest_consultation.diagnosis if latest_consultation else None,
                "latest_lab_result": {
                    "result_id": latest_lab.result_id,
                    "test_type": latest_lab.test_type,
                    "interpretation": latest_lab.interpretation,
                    "abnormal_flag": latest_lab.abnormal_flag,
                    "result_date": latest_lab.result_date,
                }
                if latest_lab
                else None,
            }
        )
    return {"total": total, "assignments": rows}

@router.get("/assigned-patients/{patient_id}")
def assigned_patient_record(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("NURSE", "SURGEON", "ADMIN")),
):
    patient = _patient_or_404(db, patient_id)
    _assert_assigned_access(db, current_user, patient_id)

    triage = (
        db.query(Triage)
        .filter(Triage.patient_id == patient_id)
        .order_by(Triage.created_at.desc())
        .first()
    )
    triage_data = _parse_triage(triage.assessment_notes) if triage else {"complaints": None, "triage_notes": None}
    consultations = (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient_id)
        .order_by(Consultation.consultation_date.desc())
        .all()
    )
    labs = (
        db.query(LabResult)
        .filter(LabResult.patient_id == patient_id)
        .order_by(LabResult.result_date.desc())
        .all()
    )
    my_assignments = (
        _staff_scope_query(db, current_user)
        .filter(Assignment.patient_id == patient_id)
        .order_by(Assignment.assigned_date.desc())
        .all()
    )

    return {
        "patient": {
            "patient_id": patient.patient_id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "phone": patient.phone,
            "address": patient.address,
            "notes": patient.notes,
        },
        "triage": {
            "priority": triage.priority if triage else None,
            "officer_name": triage.nurse_name if triage else None,
            "vital_signs": triage.vital_signs if triage else None,
            "complaints": triage_data["complaints"],
            "triage_notes": triage_data["triage_notes"],
            "created_at": triage.created_at if triage else None,
        },
        "consultations": [
            {
                "consultation_date": item.consultation_date,
                "doctor_name": item.doctor_name,
                "diagnosis": item.diagnosis,
                "findings": item.findings,
                "observations": item.observations,
                "treatment_plan": item.treatment_plan,
                "care_notes": item.care_notes,
            }
            for item in consultations
        ],
        "lab_results": [
            {
                "result_id": item.result_id,
                "test_type": item.test_type,
                "result_data": item.result_data,
                "interpretation": item.interpretation,
                "abnormal_flag": item.abnormal_flag,
                "completed_date": item.completed_date,
            }
            for item in labs
        ],
        "assignments": [
            {
                "assignment_id": item.assignment_id,
                "staff_name": item.staff_name,
                "staff_role": item.staff_role,
                "care_instructions": item.care_instructions,
                "task_description": item.task_description,
                "special_notes": item.special_notes,
                "status": item.status,
            }
            for item in my_assignments
        ],
    }

@router.post("/assigned-patients/{patient_id}/care-activities", status_code=status.HTTP_201_CREATED)
def create_care_activity(
    patient_id: str,
    payload: CareActivityCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("NURSE", "ADMIN")),
):
    patient = _patient_or_404(db, patient_id)
    _assert_assigned_access(db, current_user, patient_id)
    db_user = _current_staff_user(db, current_user)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User profile not found")

    assignment_id = payload.assignment_id
    if assignment_id is None:
        latest_assignment = (
            _staff_scope_query(db, current_user)
            .filter(Assignment.patient_id == patient_id)
            .order_by(Assignment.assigned_date.desc())
            .first()
        )
        assignment_id = latest_assignment.assignment_id if latest_assignment else None

    activity = CareActivity(
        care_activity_id=f"CAT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}",
        patient_id=patient.patient_id,
        assignment_id=assignment_id,
        staff_name=db_user.full_name or db_user.username,
        staff_role=normalize_role(current_user.get("role")).lower(),
        activity_type=ActivityType(payload.activity_type),
        description=payload.description,
        observations=payload.observations,
        findings=payload.findings,
        vital_signs_recorded=payload.vital_signs_recorded,
        is_pre_operative=payload.is_pre_operative,
        is_post_operative=payload.is_post_operative,
        procedure_type=payload.procedure_type,
        notes_for_next_shift=payload.notes_for_next_shift,
        intervention_required=payload.intervention_required,
        status=ActivityStatus(payload.status),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return {
        "care_activity_id": activity.care_activity_id,
        "patient_id": activity.patient_id,
        "assignment_id": activity.assignment_id,
        "staff_name": activity.staff_name,
        "staff_role": activity.staff_role,
        "activity_type": activity.activity_type,
        "description": activity.description,
        "observations": activity.observations,
        "status": activity.status,
        "created_at": activity.created_at,
    }

@router.get("/assigned-patients/{patient_id}/care-activities")
def list_care_activities(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("NURSE", "SURGEON", "ADMIN")),
):
    _patient_or_404(db, patient_id)
    _assert_assigned_access(db, current_user, patient_id)
    activities = (
        db.query(CareActivity)
        .filter(CareActivity.patient_id == patient_id)
        .order_by(CareActivity.created_at.desc())
        .all()
    )
    return {
        "total": len(activities),
        "activities": [
            {
                "care_activity_id": item.care_activity_id,
                "assignment_id": item.assignment_id,
                "staff_name": item.staff_name,
                "staff_role": item.staff_role,
                "activity_type": item.activity_type,
                "description": item.description,
                "observations": item.observations,
                "findings": item.findings,
                "vital_signs_recorded": item.vital_signs_recorded,
                "is_pre_operative": item.is_pre_operative,
                "is_post_operative": item.is_post_operative,
                "procedure_type": item.procedure_type,
                "notes_for_next_shift": item.notes_for_next_shift,
                "intervention_required": item.intervention_required,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in activities
        ],
    }