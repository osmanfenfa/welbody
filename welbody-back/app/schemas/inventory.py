from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SupplyCreate(BaseModel):
    supply_id: Optional[str] = Field(default=None, description="Optional custom supply ID")
    name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: int = 0
    reorder_level: int = 0
    batch_number: Optional[str] = None
    expiration_date: Optional[str] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class SupplyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: Optional[int] = None
    reorder_level: Optional[int] = None
    batch_number: Optional[str] = None
    expiration_date: Optional[str] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_available: Optional[bool] = None


class SupplyStockUpdateRequest(BaseModel):
    quantity: int
    operation: Literal["set", "increment", "decrement"] = "set"


class SupplyResponse(BaseModel):
    supply_id: str
    name: str
    description: Optional[str]
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
