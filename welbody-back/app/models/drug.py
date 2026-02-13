from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db.base import Base


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False, index=True)
    generic_name = Column(String(120), nullable=True)
    brand = Column(String(120), nullable=True)
    strength = Column(String(50), nullable=True)
    formulation = Column(String(80), nullable=True)
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
        return f"<Drug {self.drug_id}: {self.name}>"
