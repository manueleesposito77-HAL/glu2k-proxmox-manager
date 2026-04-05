from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.core.security import require_admin
from datetime import datetime, timedelta
from typing import Optional
import json

router = APIRouter()


@router.get("")
def list_audit(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    limit: int = Query(200, le=1000),
    offset: int = Query(0, ge=0),
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    since_hours: Optional[int] = None,
):
    q = db.query(AuditLog)
    if username:
        q = q.filter(AuditLog.username == username)
    if action:
        q = q.filter(AuditLog.action.like(f"%{action}%"))
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if status:
        q = q.filter(AuditLog.status == status)
    if since_hours:
        since = datetime.utcnow() - timedelta(hours=since_hours)
        q = q.filter(AuditLog.timestamp >= since)
    total = q.count()
    rows = q.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "user_id": r.user_id,
            "username": r.username,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "details": json.loads(r.details) if r.details else None,
            "ip": r.ip,
            "status": r.status,
        })
    return {"total": total, "items": items}


@router.get("/actions")
def list_actions(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Lista distinti di azioni presenti nei log (per dropdown filtro)."""
    rows = db.query(AuditLog.action).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


@router.get("/usernames")
def list_usernames(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(AuditLog.username).distinct().all()
    return sorted([r[0] for r in rows if r[0]])
