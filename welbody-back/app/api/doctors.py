import json
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.assignment import Assignment, AssignmentStatus, StaffRole
from app.models.consultation import Consultation, ConsultationStatus
from app.models.lab import LabRequest, LabResult, TestStatus
from app.models.patient import Patient
from app.models.prescription import Prescription, PrescriptionStatus
from app.models.triage import Triage
from app.models.user import User
from app.schemas.consultation import ConsultationCreateRequest, ConsultationResponse
from app.schemas.lab import LabRequestCreateRequest, LabRequestResponse, LabResultResponse
from app.schemas.prescription import PrescriptionCreateRequest, PrescriptionResponse

router = APIRouter(prefix="/doctor", tags=["doctor"])


class AssignmentCreateRequest(BaseModel):
    staff_name: str
    staff_role: Literal["nurse", "surgeon"]
    staff_id: Optional[str] = None
    specialty: Optional[str] = None
    task_description: Optional[str] = None
    care_instructions: Optional[str] = None
    special_notes: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    assignment_id: str
    patient_id: str
    staff_name: str
    staff_id: Optional[str] = None
    staff_role: str
    specialty: Optional[str] = None
    assigning_doctor: str
    status: str
    task_description: Optional[str] = None
    care_instructions: Optional[str] = None
    special_notes: Optional[str] = None
    assigned_date: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True


def _generate_id(db: Session, field, prefix: str) -> str:
    day_prefix = datetime.utcnow().strftime("%Y%m%d")
    latest = (
        db.query(field)
        .filter(field.like(f"{prefix}-{day_prefix}-%"))
        .order_by(field.desc())
        .first()
    )
    next_number = 1
    if latest and latest[0]:
        try:
            next_number = int(str(latest[0]).split("-")[-1]) + 1
        except Exception:
            next_number = 1
    return f"{prefix}-{day_prefix}-{str(next_number).zfill(4)}"


def _doctor_profile(db: Session, current_user: dict) -> tuple[str, Optional[str], Optional[str]]:
    db_user = db.query(User).filter(User.user_id == current_user.get("user_id")).first()
    if not db_user:
        return current_user.get("user_id") or "Unknown Doctor", None, None
    return db_user.full_name or db_user.username, None, db_user.user_id


def _parse_triage(record: Optional[Triage]) -> Optional[dict]:
    if not record:
        return None
    complaints = None
    notes = None
    if record.assessment_notes:
        try:
            parsed = json.loads(record.assessment_notes)
            if isinstance(parsed, dict):
                complaints = parsed.get("complaints")
                notes = parsed.get("triage_notes")
        except Exception:
            notes = record.assessment_notes
    vital_signs = None
    if record.vital_signs:
        try:
            vital_signs = json.loads(record.vital_signs)
        except Exception:
            vital_signs = {"value": record.vital_signs}
    return {
        "triage_id": record.triage_id,
        "officer_name": record.nurse_name,
        "priority": record.priority,
        "complaints": complaints,
        "vital_signs": vital_signs,
        "triage_notes": notes,
        "created_at": record.created_at,
    }


def _latest_triage(db: Session, patient_id: str) -> Optional[Triage]:
    return (
        db.query(Triage)
        .filter(Triage.patient_id == patient_id)
        .order_by(Triage.created_at.desc())
        .first()
    )


def _get_patient_or_404(db: Session, patient_id: str) -> Patient:
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/patients")
def list_registered_patients(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    query = db.query(Patient)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Patient.patient_id.ilike(pattern),
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.phone.ilike(pattern),
            )
        )
    total = query.count()
    patients = query.order_by(Patient.updated_at.desc()).offset(skip).limit(limit).all()
    rows = []
    for patient in patients:
        rows.append(
            {
                "patient_id": patient.patient_id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth,
                "gender": patient.gender,
                "phone": patient.phone,
                "address": patient.address,
                "notes": patient.notes,
                "latest_triage": _parse_triage(_latest_triage(db, patient.patient_id)),
                "updated_at": patient.updated_at,
            }
        )
    return {"total": total, "patients": rows}


@router.get("/patients/{patient_id}")
def get_patient_record(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    patient = _get_patient_or_404(db, patient_id)
    return {
        "patient_id": patient.patient_id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "phone": patient.phone,
        "address": patient.address,
        "notes": patient.notes,
        "latest_triage": _parse_triage(_latest_triage(db, patient.patient_id)),
    }


@router.post("/patients/{patient_id}/consultations", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
def create_consultation(
    patient_id: str,
    payload: ConsultationCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    doctor_name, doctor_specialty, _ = _doctor_profile(db, current_user)
    consultation = Consultation(
        patient_id=patient_id,
        doctor_name=doctor_name,
        doctor_specialty=payload.doctor_specialty or doctor_specialty,
        consultation_type=payload.consultation_type,
        status=ConsultationStatus.COMPLETED,
        chief_complaint=payload.chief_complaint,
        history_of_present_illness=payload.history_of_present_illness,
        physical_examination=payload.physical_examination,
        assessment=payload.assessment,
        diagnosis=payload.diagnosis,
        differential_diagnosis=payload.differential_diagnosis,
        treatment_plan=payload.treatment_plan,
        care_notes=payload.care_notes,
        findings=payload.findings,
        observations=payload.observations,
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation


@router.get("/patients/{patient_id}/consultations", response_model=List[ConsultationResponse])
def list_consultations(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    return (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient_id)
        .order_by(Consultation.consultation_date.desc())
        .all()
    )


@router.post("/patients/{patient_id}/lab-requests", response_model=LabRequestResponse, status_code=status.HTTP_201_CREATED)
def request_lab_test(
    patient_id: str,
    payload: LabRequestCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    doctor_name, doctor_specialty, _ = _doctor_profile(db, current_user)
    lab_request = LabRequest(
        request_id=_generate_id(db, LabRequest.request_id, "LAB"),
        patient_id=patient_id,
        doctor_name=doctor_name,
        doctor_specialty=payload.doctor_specialty or doctor_specialty,
        test_type=payload.test_type,
        test_description=payload.test_description,
        test_code=payload.test_code,
        priority=payload.priority,
        status=TestStatus.REQUESTED,
        clinical_indication=payload.clinical_indication,
        relevant_patient_history=payload.relevant_patient_history,
        expected_completion_date=payload.expected_completion_date,
    )
    db.add(lab_request)
    db.commit()
    db.refresh(lab_request)
    return lab_request


@router.get("/patients/{patient_id}/lab-requests", response_model=List[LabRequestResponse])
def list_patient_lab_requests(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    return (
        db.query(LabRequest)
        .filter(LabRequest.patient_id == patient_id)
        .order_by(LabRequest.requested_date.desc())
        .all()
    )


@router.get("/patients/{patient_id}/lab-results", response_model=List[LabResultResponse])
def list_lab_results(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    return (
        db.query(LabResult)
        .filter(LabResult.patient_id == patient_id)
        .order_by(LabResult.result_date.desc())
        .all()
    )


@router.post("/patients/{patient_id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_staff_to_patient(
    patient_id: str,
    payload: AssignmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    doctor_name, _, _ = _doctor_profile(db, current_user)
    assignment = Assignment(
        assignment_id=_generate_id(db, Assignment.assignment_id, "ASN"),
        patient_id=patient_id,
        staff_name=payload.staff_name,
        staff_id=payload.staff_id,
        staff_role=StaffRole(payload.staff_role),
        specialty=payload.specialty,
        assigning_doctor=doctor_name,
        status=AssignmentStatus.ACTIVE,
        task_description=payload.task_description,
        care_instructions=payload.care_instructions,
        special_notes=payload.special_notes,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/patients/{patient_id}/assignments", response_model=List[AssignmentResponse])
def list_assignments(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    return (
        db.query(Assignment)
        .filter(Assignment.patient_id == patient_id)
        .order_by(Assignment.assigned_date.desc())
        .all()
    )


@router.post("/patients/{patient_id}/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
    patient_id: str,
    payload: PrescriptionCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    doctor_name, doctor_specialty, doctor_id = _doctor_profile(db, current_user)
    prescription = Prescription(
        prescription_id=_generate_id(db, Prescription.prescription_id, "PRX"),
        patient_id=patient_id,
        doctor_name=doctor_name,
        doctor_id=doctor_id,
        doctor_specialty=payload.doctor_specialty or doctor_specialty,
        medication_name=payload.medication_name,
        medication_code=payload.medication_code,
        drug_generic_name=payload.drug_generic_name,
        dose=payload.dose,
        dose_value=payload.dose_value,
        dose_unit=payload.dose_unit,
        route=payload.route,
        frequency=payload.frequency,
        custom_frequency=payload.custom_frequency,
        duration=payload.duration,
        total_quantity=payload.total_quantity,
        refills_allowed=payload.refills_allowed,
        instructions=payload.instructions,
        special_instructions=payload.special_instructions,
        clinical_indication=payload.clinical_indication,
        contraindications=payload.contraindications,
        side_effects=payload.side_effects,
        precautions=payload.precautions,
        status=PrescriptionStatus.ISSUED,
        expiry_date=payload.expiry_date,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


@router.get("/patients/{patient_id}/prescriptions", response_model=List[PrescriptionResponse])
def list_prescriptions(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("DOCTOR", "ADMIN")),
):
    _get_patient_or_404(db, patient_id)
    return (
        db.query(Prescription)
        .filter(Prescription.patient_id == patient_id)
        .order_by(Prescription.prescribed_date.desc())
        .all()
    )
