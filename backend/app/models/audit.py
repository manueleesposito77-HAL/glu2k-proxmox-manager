from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False, index=True)  # login, create_vm, delete_firewall_rule, ecc.
    resource_type = Column(String, nullable=True)  # cluster, vm, user, firewall_rule, ecc.
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON string con details extra
    ip = Column(String, nullable=True)
    status = Column(String, default="success")  # success | failed
