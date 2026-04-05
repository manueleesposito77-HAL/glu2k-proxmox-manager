"""Helper per audit logging"""
import json
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.audit import AuditLog
from app.models.user import User
from typing import Optional, Any


def log_action(
    db: Session,
    request: Optional[Request],
    user: Optional[User],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[Any] = None,
    details: Optional[dict] = None,
    status: str = "success",
):
    """Registra un'azione nell'audit log."""
    try:
        ip = None
        if request:
            ip = request.client.host if request.client else None
            # Gestisci X-Forwarded-For per reverse proxy
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                ip = fwd.split(",")[0].strip()
        entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=json.dumps(details) if details else None,
            ip=ip,
            status=status,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        # Non fallire mai la richiesta per problemi di audit
        print(f"[audit] Failed to log action '{action}': {e}")
        try: db.rollback()
        except: pass
