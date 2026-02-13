from app.db.session import engine
from app.db.base import Base

# Ensure all SQLAlchemy models are imported before creating tables.
import app.models  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)
