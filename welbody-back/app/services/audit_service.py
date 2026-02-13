from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        details: Optional[str] = None,
    ) -> Optional[AuditLog]:
        try:
            log = AuditLog(
                event_type=event_type,
                user_id=user_id,
                username=username,
                endpoint=endpoint,
                method=method,
                details=details,
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        except Exception:
            db.rollback()
            return None

    @staticmethod
    def list_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[int, List[AuditLog]]:
        query = db.query(AuditLog)
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        return total, logs
