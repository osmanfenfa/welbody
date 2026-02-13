from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.inventory import (
    SupplyCreate,
    SupplyResponse,
    SupplyStockUpdateRequest,
    SupplyUpdate,
)
from app.schemas.pharmacy import DrugCreate, DrugResponse, DrugUpdate, StockUpdateRequest
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.pharmacy_service import PharmacyService

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _resolve_username(db: Session, user_id: str | None) -> str | None:
    if not user_id:
        return None
    db_user = db.query(User).filter(User.user_id == user_id).first()
    return db_user.username if db_user else None


@router.get("/drugs", response_model=List[DrugResponse])
def list_drugs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return PharmacyService.list_drugs(db, skip=skip, limit=limit)


@router.post("/drugs", response_model=DrugResponse, status_code=status.HTTP_201_CREATED)
def create_drug(
    payload: DrugCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    created = PharmacyService.create_drug(db, payload)
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_DRUG_CREATED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint="/inventory/drugs",
        method="POST",
        details=f"Created drug {created.drug_id}",
    )
    return created


@router.get("/drugs/{drug_id}", response_model=DrugResponse)
def get_drug(
    drug_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    drug = PharmacyService.get_drug(db, drug_id)
    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")
    return drug


@router.put("/drugs/{drug_id}", response_model=DrugResponse)
def update_drug(
    drug_id: str,
    payload: DrugUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    updated = PharmacyService.update_drug(db, drug_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_DRUG_UPDATED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint=f"/inventory/drugs/{drug_id}",
        method="PUT",
        details=f"Updated drug {drug_id}",
    )
    return updated


@router.delete("/drugs/{drug_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drug(
    drug_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    deleted = PharmacyService.delete_drug(db, drug_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_DRUG_DELETED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint=f"/inventory/drugs/{drug_id}",
        method="DELETE",
        details=f"Deleted drug {drug_id}",
    )
    return None


@router.put("/drugs/{drug_id}/stock", response_model=DrugResponse)
def update_drug_stock(
    drug_id: str,
    payload: StockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    updated = PharmacyService.update_stock(db, drug_id, payload.quantity, payload.operation)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_DRUG_STOCK_UPDATED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint=f"/inventory/drugs/{drug_id}/stock",
        method="PUT",
        details=f"Stock {payload.operation} {payload.quantity} for {drug_id}",
    )
    return updated


@router.get("/supplies", response_model=List[SupplyResponse])
def list_supplies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return InventoryService.list_supplies(db, skip=skip, limit=limit)


@router.post("/supplies", response_model=SupplyResponse, status_code=status.HTTP_201_CREATED)
def create_supply(
    payload: SupplyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    created = InventoryService.create_supply(db, payload.model_dump())
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_SUPPLY_CREATED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint="/inventory/supplies",
        method="POST",
        details=f"Created supply {created.supply_id}",
    )
    return created


@router.get("/supplies/{supply_id}", response_model=SupplyResponse)
def get_supply(
    supply_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    supply = InventoryService.get_supply(db, supply_id)
    if not supply:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    return supply


@router.put("/supplies/{supply_id}", response_model=SupplyResponse)
def update_supply(
    supply_id: str,
    payload: SupplyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    updated = InventoryService.update_supply(db, supply_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_SUPPLY_UPDATED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint=f"/inventory/supplies/{supply_id}",
        method="PUT",
        details=f"Updated supply {supply_id}",
    )
    return updated


@router.delete("/supplies/{supply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supply(
    supply_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    deleted = InventoryService.delete_supply(db, supply_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_SUPPLY_DELETED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint=f"/inventory/supplies/{supply_id}",
        method="DELETE",
        details=f"Deleted supply {supply_id}",
    )
    return None


@router.put("/supplies/{supply_id}/stock", response_model=SupplyResponse)
def update_supply_stock(
    supply_id: str,
    payload: SupplyStockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    updated = InventoryService.update_supply_stock(db, supply_id, payload.quantity, payload.operation)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    AuditService.log_event(
        db=db,
        event_type="INVENTORY_SUPPLY_STOCK_UPDATED",
        user_id=current_user.get("user_id"),
        username=_resolve_username(db, current_user.get("user_id")),
        endpoint=f"/inventory/supplies/{supply_id}/stock",
        method="PUT",
        details=f"Stock {payload.operation} {payload.quantity} for {supply_id}",
    )
    return updated
