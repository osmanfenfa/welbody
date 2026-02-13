from typing import Dict, List, Set


SYSTEM_ROLES: Set[str] = {
    "ADMIN",
    "DOCTOR",
    "NURSE",
    "SURGEON",
    "TRIAGE",
    "LAB_TECHNICIAN",
    "PHARMACIST",
}

STAFF_ROLES: Set[str] = {
    "DOCTOR",
    "NURSE",
    "SURGEON",
    "TRIAGE",
    "LAB_TECHNICIAN",
    "PHARMACIST",
}

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "ADMIN": [
        "admin.auth",
        "admin.user.create",
        "admin.user.read",
        "admin.user.update",
        "admin.user.delete",
        "admin.role.manage",
        "admin.audit.read",
        "inventory.drug.manage",
        "inventory.supply.manage",
    ],
    "DOCTOR": [
        "patient.read",
        "consultation.create",
        "consultation.read",
        "consultation.update",
        "lab.request.create",
        "lab.result.read",
        "assignment.create",
        "prescription.create",
    ],
    "NURSE": [
        "patient.read.assigned",
        "care_activity.create",
        "care_activity.read",
        "care_activity.update",
    ],
    "SURGEON": [
        "patient.read.assigned",
        "lab.result.read",
        "care_activity.read",
        "care_activity.update",
    ],
    "TRIAGE": [
        "patient.create",
        "patient.read",
        "patient.update",
        "triage.create",
        "triage.update",
        "patient.card.print",
    ],
    "LAB_TECHNICIAN": [
        "lab.request.read",
        "lab.request.update.status",
        "lab.result.create",
        "lab.result.read",
    ],
    "PHARMACIST": [
        "prescription.read",
        "prescription.dispense",
        "inventory.drug.read",
        "inventory.drug.update_stock",
        "medication.list.print",
    ],
}


def normalize_role(role: str | None) -> str:
    return (role or "").strip().upper().replace("-", "_")


def is_valid_role(role: str | None) -> bool:
    return normalize_role(role) in SYSTEM_ROLES
