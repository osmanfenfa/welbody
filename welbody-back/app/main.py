from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.doctors import router as doctor_router
from app.api.inventory import router as inventory_router
from app.api.laboratory import router as laboratory_router
from app.api.nursing import router as nursing_router
from app.api.pharmacy import router as pharmacy_router
from app.api.triage import router as triage_router
from app.db.base import Base
from app.db.session import engine

# Load models so SQLAlchemy metadata is aware of every table.
import app.models  # noqa: F401

app = FastAPI(title="WELBODY API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified successfully")
    except Exception as exc:
        print(f"Warning: Could not initialize database: {exc}")
        print("Continuing without database connection...")


app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(doctor_router)
app.include_router(inventory_router)
app.include_router(laboratory_router)
app.include_router(nursing_router)
app.include_router(pharmacy_router)
app.include_router(triage_router)


@app.get("/")
def root():
    return {
        "message": "WELBODY API",
        "module": "System Administrator",
        "status": "online",
    }
