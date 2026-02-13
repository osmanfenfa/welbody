from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import require_roles
from app.schemas.pharmacy import (
    AvailabilityUpdateRequest,
    DrugCreate,
    DrugResponse,
    DrugUpdate,
    StockUpdateRequest,
)
from app.services.pharmacy_service import PharmacyService
from app.db.session import get_db
from app.utils.pdf_generator import generate_medication_list_pdf

router = APIRouter(
    prefix="/pharmacy",
    tags=["pharmacy"],
    dependencies=[Depends(require_roles("PHARMACIST", "ADMIN"))],
)


@router.get("/drugs", response_model=List[DrugResponse])
def list_drugs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    drugs = PharmacyService.list_drugs(db, skip=skip, limit=limit)
    return drugs


@router.post("/drugs", response_model=DrugResponse)
def create_drug(drug: DrugCreate, db: Session = Depends(get_db)):
    created = PharmacyService.create_drug(db, drug)
    return created


@router.get("/drugs/{drug_id}", response_model=DrugResponse)
def get_drug(drug_id: str, db: Session = Depends(get_db)):
    d = PharmacyService.get_drug(db, drug_id)
    if not d:
        raise HTTPException(status_code=404, detail="Drug not found")
    return d


@router.put("/drugs/{drug_id}", response_model=DrugResponse)
def update_drug(drug_id: str, data: DrugUpdate, db: Session = Depends(get_db)):
    updated = PharmacyService.update_drug(db, drug_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Drug not found")
    return updated


@router.put("/drugs/{drug_id}/stock", response_model=DrugResponse)
def update_stock(drug_id: str, req: StockUpdateRequest, db: Session = Depends(get_db)):
    result = PharmacyService.update_stock(db, drug_id, req.quantity, operation=req.operation)
    if not result:
        raise HTTPException(status_code=404, detail="Drug not found")
    return result


@router.put("/drugs/{drug_id}/availability", response_model=DrugResponse)
def update_availability(drug_id: str, req: AvailabilityUpdateRequest, db: Session = Depends(get_db)):
    result = PharmacyService.update_availability(db, drug_id, req.is_available)
    if not result:
        raise HTTPException(status_code=404, detail="Drug not found")
    return result


@router.get("/patients/{patient_id}/medications")
def get_patient_medications(patient_id: str, db: Session = Depends(get_db)):
    meds = PharmacyService.get_prescriptions_for_patient(db, patient_id)
    return {
        "patient_id": patient_id,
        "total": len(meds),
        "medications": [
            {
                "prescription_id": med.prescription_id,
                "medication_name": med.medication_name,
                "dose": med.dose,
                "frequency": med.frequency,
                "duration": med.duration,
                "instructions": med.instructions,
                "status": med.status,
                "prescribed_date": med.prescribed_date,
                "dispensed_date": med.dispensed_date,
            }
            for med in meds
        ],
    }


@router.get("/patients/{patient_id}/medication-list")
def medication_list(
    patient_id: str,
    format: str = Query("json", pattern="^(json|pdf)$"),
    db: Session = Depends(get_db),
):
    data = PharmacyService.prepare_medication_list(db, patient_id)
    if format == "pdf":
        pdf = generate_medication_list_pdf(
            patient_id=data["patient_id"],
            patient_name=data["patient_name"],
            medications=data["medications"],
        )
        from fastapi import Response

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{patient_id}-medication-list.pdf"'},
        )
    return data


@router.post("/prescriptions/{prescription_id}/dispense")
def dispense_prescription(prescription_id: str, db: Session = Depends(get_db)):
    res = PharmacyService.dispense_prescription(db, prescription_id)
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
