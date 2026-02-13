from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.supply import Supply


class InventoryService:
    @staticmethod
    def generate_supply_id() -> str:
        return f"SUP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

    @staticmethod
    def list_supplies(db: Session, skip: int = 0, limit: int = 100) -> List[Supply]:
        return db.query(Supply).order_by(Supply.name).offset(skip).limit(limit).all()

    @staticmethod
    def get_supply(db: Session, supply_id: str) -> Optional[Supply]:
        return db.query(Supply).filter(Supply.supply_id == supply_id).first()

    @staticmethod
    def create_supply(db: Session, data: dict) -> Supply:
        s = Supply(
            supply_id=data.get("supply_id") or InventoryService.generate_supply_id(),
            name=data.get("name"),
            description=data.get("description"),
            unit=data.get("unit"),
            quantity_in_stock=data.get("quantity_in_stock", 0),
            reorder_level=data.get("reorder_level", 0),
            location=data.get("location"),
            supplier=data.get("supplier"),
            batch_number=data.get("batch_number"),
            expiration_date=data.get("expiration_date"),
            notes=data.get("notes"),
            is_available=(data.get("quantity_in_stock", 0) > 0),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def update_supply(db: Session, supply_id: str, updates: dict) -> Optional[Supply]:
        s = db.query(Supply).filter(Supply.supply_id == supply_id).first()
        if not s:
            return None
        for field, value in updates.items():
            if value is not None and hasattr(s, field):
                setattr(s, field, value)
        s.is_available = (s.quantity_in_stock or 0) > 0
        s.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def delete_supply(db: Session, supply_id: str) -> bool:
        s = db.query(Supply).filter(Supply.supply_id == supply_id).first()
        if not s:
            return False
        db.delete(s)
        db.commit()
        return True

    @staticmethod
    def update_supply_stock(db: Session, supply_id: str, quantity: int, operation: str = "set") -> Optional[Supply]:
        s = db.query(Supply).filter(Supply.supply_id == supply_id).first()
        if not s:
            return None
        if operation == "set":
            s.quantity_in_stock = quantity
        elif operation == "increment":
            s.quantity_in_stock = (s.quantity_in_stock or 0) + quantity
        elif operation == "decrement":
            s.quantity_in_stock = max(0, (s.quantity_in_stock or 0) - quantity)
        s.is_available = s.quantity_in_stock > 0
        s.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(s)
        return s
