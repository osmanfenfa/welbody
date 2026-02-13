from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.drug import Drug
from app.models.prescription import Prescription
from app.models.patient import Patient
from app.schemas.pharmacy import DrugCreate, DrugUpdate


class PharmacyService:
    @staticmethod
    def generate_drug_id() -> str:
        return f"DRG-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

    @staticmethod
    def list_drugs(db: Session, skip: int = 0, limit: int = 50) -> List[Drug]:
        return db.query(Drug).order_by(Drug.name).offset(skip).limit(limit).all()

    @staticmethod
    def get_drug(db: Session, drug_id: str) -> Optional[Drug]:
        return db.query(Drug).filter(Drug.drug_id == drug_id).first()

    @staticmethod
    def create_drug(db: Session, drug_data: DrugCreate) -> Drug:
        drug = Drug(
            drug_id=drug_data.drug_id or PharmacyService.generate_drug_id(),
            name=drug_data.name,
            generic_name=drug_data.generic_name,
            brand=drug_data.brand,
            strength=drug_data.strength,
            formulation=drug_data.formulation,
            unit=drug_data.unit,
            quantity_in_stock=drug_data.quantity_in_stock,
            reorder_level=drug_data.reorder_level,
            batch_number=drug_data.batch_number,
            expiration_date=drug_data.expiration_date,
            supplier=drug_data.supplier,
            location=drug_data.location,
            notes=drug_data.notes,
            is_available=(drug_data.quantity_in_stock > 0),
        )
        db.add(drug)
        db.commit()
        db.refresh(drug)
        return drug

    @staticmethod
    def update_drug(db: Session, drug_id: str, data: DrugUpdate) -> Optional[Drug]:
        drug = db.query(Drug).filter(Drug.drug_id == drug_id).first()
        if not drug:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(drug, field, value)
        drug.is_available = (drug.quantity_in_stock or 0) > 0
        drug.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(drug)
        return drug

    @staticmethod
    def delete_drug(db: Session, drug_id: str) -> bool:
        drug = db.query(Drug).filter(Drug.drug_id == drug_id).first()
        if not drug:
            return False
        db.delete(drug)
        db.commit()
        return True

    @staticmethod
    def update_stock(db: Session, drug_id: str, quantity: int, operation: str = "set") -> Optional[Drug]:
        drug = db.query(Drug).filter(Drug.drug_id == drug_id).first()
        if not drug:
            return None
        if operation == "set":
            drug.quantity_in_stock = quantity
        elif operation == "increment":
            drug.quantity_in_stock = (drug.quantity_in_stock or 0) + quantity
        elif operation == "decrement":
            drug.quantity_in_stock = max(0, (drug.quantity_in_stock or 0) - quantity)
        # Update availability flag
        drug.is_available = drug.quantity_in_stock > 0
        drug.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(drug)
        return drug

    @staticmethod
    def update_availability(db: Session, drug_id: str, is_available: bool) -> Optional[Drug]:
        drug = db.query(Drug).filter(Drug.drug_id == drug_id).first()
        if not drug:
            return None
        drug.is_available = is_available
        drug.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(drug)
        return drug

    @staticmethod
    def get_prescriptions_for_patient(db: Session, patient_id: str) -> List[Prescription]:
        return db.query(Prescription).filter(Prescription.patient_id == patient_id).all()

    @staticmethod
    def prepare_medication_list(db: Session, patient_id: str):
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
        meds = []
        for p in prescriptions:
            meds.append({
                "prescription_id": p.prescription_id,
                "medication_name": p.medication_name,
                "dose": p.dose,
                "frequency": p.frequency,
                "duration": p.duration,
                "instructions": p.instructions,
            })
        return {
            "patient_id": patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}" if patient else None,
            "medications": meds,
            "generated_at": datetime.utcnow(),
        }

    @staticmethod
    def dispense_prescription(db: Session, prescription_id: str) -> dict:
        pres = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
        if not pres:
            return {"error": "Prescription not found"}
        # Try to find drug by medication_name
        drug = db.query(Drug).filter(Drug.name.ilike(pres.medication_name)).first()
        if not drug:
            return {"error": "Drug not stocked"}
        # Assume prescription dose represents units to decrement if numeric, else 1
        try:
            qty = int(pres.duration) if pres.duration and pres.duration.isdigit() else 1
        except Exception:
            qty = 1
        if drug.quantity_in_stock < qty:
            return {"error": "Insufficient stock", "available": drug.quantity_in_stock}
        drug.quantity_in_stock -= qty
        drug.is_available = drug.quantity_in_stock > 0
        drug.updated_at = datetime.utcnow()
        # Mark prescription as dispensed if model has status
        try:
            pres.status = "dispensed"
            pres.dispensed_date = datetime.utcnow()
        except Exception:
            pass
        db.commit()
        db.refresh(drug)
        return {"success": True, "drug_id": drug.drug_id, "remaining": drug.quantity_in_stock}
