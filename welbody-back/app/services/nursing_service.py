from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.care_activity import CareActivity, ActivityStatus


class NursingService:
    @staticmethod
    def generate_care_activity_id():
        return f"CAT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

    @staticmethod
    def create_care_activity(db: Session, data: dict) -> CareActivity:
        ca = CareActivity(
            care_activity_id=NursingService.generate_care_activity_id(),
            patient_id=data.get('patient_id'),
            assignment_id=data.get('assignment_id'),
            staff_name=data.get('staff_name'),
            staff_role=data.get('staff_role'),
            activity_type=data.get('activity_type'),
            description=data.get('description'),
            observations=data.get('observations'),
            is_pre_operative=data.get('is_pre_operative', False),
            is_post_operative=data.get('is_post_operative', False),
            status=ActivityStatus.PLANNED,
        )
        db.add(ca)
        db.commit()
        db.refresh(ca)
        return ca

    @staticmethod
    def get_activities_for_patient(db: Session, patient_id: str) -> List[CareActivity]:
        return db.query(CareActivity).filter(CareActivity.patient_id == patient_id).order_by(CareActivity.created_at.desc()).all()

    @staticmethod
    def update_activity(db: Session, care_activity_id: str, updates: dict) -> Optional[CareActivity]:
        ca = db.query(CareActivity).filter(CareActivity.care_activity_id == care_activity_id).first()
        if not ca:
            return None
        for k, v in updates.items():
            if hasattr(ca, k):
                setattr(ca, k, v)
        ca.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ca)
        return ca
