from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CareActivityCreate(BaseModel):
    patient_id: str
    staff_name: Optional[str]
    staff_role: Optional[str]
    activity_type: Optional[str]
    description: Optional[str]
    observations: Optional[str]
    is_pre_operative: Optional[bool] = False
    is_post_operative: Optional[bool] = False


class CareActivityResponse(BaseModel):
    care_activity_id: str
    patient_id: str
    staff_name: Optional[str]
    staff_role: Optional[str]
    activity_type: Optional[str]
    description: Optional[str]
    observations: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class CareActivityListResponse(BaseModel):
    activities: List[CareActivityResponse]
