from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DrugCreate(BaseModel):
    drug_id: Optional[str] = Field(default=None, description="Optional custom drug ID")
    name: str
    generic_name: Optional[str] = None
    brand: Optional[str] = None
    strength: Optional[str] = None
    formulation: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: int = 0
    reorder_level: int = 0
    batch_number: Optional[str] = None
    expiration_date: Optional[str] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class DrugUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    brand: Optional[str] = None
    strength: Optional[str] = None
    formulation: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: Optional[int] = None
    reorder_level: Optional[int] = None
    batch_number: Optional[str] = None
    expiration_date: Optional[str] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_available: Optional[bool] = None


class StockUpdateRequest(BaseModel):
    quantity: int
    operation: Literal["set", "increment", "decrement"] = "set"


class AvailabilityUpdateRequest(BaseModel):
    is_available: bool


class DrugResponse(BaseModel):
    drug_id: str
    name: str
    generic_name: Optional[str]
    brand: Optional[str]
    strength: Optional[str]
    formulation: Optional[str]
    unit: Optional[str]
    quantity_in_stock: int
    reorder_level: int
    batch_number: Optional[str]
    expiration_date: Optional[str]
    supplier: Optional[str]
    location: Optional[str]
    notes: Optional[str]
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
