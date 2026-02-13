from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=True)
    email = Column(String(200), nullable=True)
    full_name = Column(String(200), nullable=True)
    role = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.user_id} {self.username}>"
