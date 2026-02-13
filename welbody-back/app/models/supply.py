from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db.base import Base


class Supply(Base):
    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, index=True)
    supply_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=True)
    quantity_in_stock = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=0, nullable=False)
    batch_number = Column(String(80), nullable=True)
    expiration_date = Column(String(50), nullable=True)
    supplier = Column(String(150), nullable=True)
    location = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Supply {self.supply_id}: {self.name}>"
