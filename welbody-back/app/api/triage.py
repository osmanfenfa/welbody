import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.patient import Patient
from app.models.triage import Triage
from app.models.user import User
from app.schemas.triage import (
    PatientListResponse,
    PatientRecordResponse,
    PatientRegistrationRequest,
    PatientRegistrationResponse,
    PatientUpdateRequest,
    TriageDataResponse,
)
from app.utils.id_generator import generate_patient_id, generate_triage_id
from app.utils.pdf_generator import generate_patient_id_card_pdf

router = APIRouter(prefix="/triage", tags=["triage"])


def _serialize_vital_signs(vital_signs: Optional[dict]) -> Optional[str]:
    if vital_signs is None:
        return None
    return json.dumps(vital_signs)


def _parse_vital_signs(raw: Optional[str]) -> Optional[dict]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        return {"value": raw}


def _serialize_assessment(complaints: Optional[str], triage_notes: Optional[str]) -> Optional[str]:
    payload = {}
    if complaints is not None:
        payload["complaints"] = complaints
    if triage_notes is not None:
        payload["triage_notes"] = triage_notes
    if not payload:
        return None
    return json.dumps(payload)


def _parse_assessment(raw: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not raw:
        return None, None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed.get("complaints"), parsed.get("triage_notes")
    except Exception:
        pass
    return None, raw


def _resolve_officer_name(db: Session, current_user: dict, requested_name: Optional[str]) -> Optional[str]:
    if requested_name:
        return requested_name
    user_id = current_user.get("user_id")
    if not user_id:
        return None
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        return None
    return db_user.full_name or db_user.username


def _latest_triage(db: Session, patient_id: str) -> Optional[Triage]:
    return (
        db.query(Triage)
        .filter(Triage.patient_id == patient_id)
        .order_by(Triage.created_at.desc())
        .first()
    )


def _triage_to_response(record: Optional[Triage]) -> Optional[TriageDataResponse]:
    if not record:
        return None
    complaints, triage_notes = _parse_assessment(record.assessment_notes)
    return TriageDataResponse(
        triage_id=record.triage_id,
        nurse_name=record.nurse_name,
        priority=record.priority,
        complaints=complaints,
        vital_signs=_parse_vital_signs(record.vital_signs),
        triage_notes=triage_notes,
        created_at=record.created_at,
    )


def _patient_to_response(patient: Patient, latest: Optional[Triage]) -> PatientRecordResponse:
    return PatientRecordResponse(
        patient_id=patient.patient_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        phone=patient.phone,
        address=patient.address,
        patient_notes=patient.notes,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        latest_triage=_triage_to_response(latest),
    )


@router.post("/patients/register", response_model=PatientRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_patient(
    payload: PatientRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("TRIAGE", "ADMIN")),
):
    patient = Patient(
        patient_id=generate_patient_id(db),
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
        notes=payload.patient_notes,
    )
    triage_record = Triage(
        triage_id=generate_triage_id(db),
        patient_id=patient.patient_id,
        nurse_name=_resolve_officer_name(db, current_user, payload.officer_name),
        priority=payload.priority,
        vital_signs=_serialize_vital_signs(payload.vital_signs),
        assessment_notes=_serialize_assessment(payload.complaints, payload.triage_notes),
    )
    try:
        db.add(patient)
        db.add(triage_record)
        db.commit()
        db.refresh(patient)
        db.refresh(triage_record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register patient: {exc}")

    response = _patient_to_response(patient, triage_record).model_dump()
    response["id_card_url"] = f"/triage/patients/{patient.patient_id}/id-card"
    return response


@router.get("/patients", response_model=PatientListResponse)
def list_patients(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("TRIAGE", "ADMIN")),
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
    records = query.order_by(Patient.updated_at.desc()).offset(skip).limit(limit).all()
    patients = [_patient_to_response(record, _latest_triage(db, record.patient_id)) for record in records]
    return {"total": total, "patients": patients}


@router.get("/patients/{patient_id}", response_model=PatientRecordResponse)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("TRIAGE", "ADMIN")),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return _patient_to_response(patient, _latest_triage(db, patient_id))


@router.put("/patients/{patient_id}", response_model=PatientRecordResponse)
def update_patient(
    patient_id: str,
    payload: PatientUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("TRIAGE", "ADMIN")),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    data = payload.model_dump(exclude_unset=True)
    for field_name, value in data.items():
        if field_name in {"patient_notes"}:
            patient.notes = value
        elif hasattr(patient, field_name) and field_name not in {"complaints", "vital_signs", "triage_notes", "priority", "officer_name"}:
            setattr(patient, field_name, value)

    should_add_triage = any(
        data.get(field) is not None for field in ["complaints", "vital_signs", "triage_notes", "priority", "officer_name"]
    )
    new_triage_record = None
    if should_add_triage:
        new_triage_record = Triage(
            triage_id=generate_triage_id(db),
            patient_id=patient.patient_id,
            nurse_name=_resolve_officer_name(db, current_user, data.get("officer_name")),
            priority=data.get("priority"),
            vital_signs=_serialize_vital_signs(data.get("vital_signs")),
            assessment_notes=_serialize_assessment(data.get("complaints"), data.get("triage_notes")),
        )
        db.add(new_triage_record)

    try:
        db.commit()
        db.refresh(patient)
        if new_triage_record is not None:
            db.refresh(new_triage_record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update patient record: {exc}")

    latest = new_triage_record or _latest_triage(db, patient.patient_id)
    return _patient_to_response(patient, latest)


@router.get("/patients/{patient_id}/id-card")
def print_patient_card(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("TRIAGE", "ADMIN")),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    latest = _latest_triage(db, patient_id)
    full_name = f"{patient.first_name} {patient.last_name or ''}".strip()
    pdf_data = generate_patient_id_card_pdf(
        patient_id=patient.patient_id,
        full_name=full_name,
        gender=patient.gender,
        date_of_birth=patient.date_of_birth,
        priority=latest.priority if latest else None,
    )
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{patient.patient_id}-id-card.pdf"'},
    )
