from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    api_keys = relationship("APIKey", back_populates="tenant")
    policies = relationship("Policy", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    hashed_key = Column(String, unique=True, index=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    is_active = Column(Boolean, default=True)
    tenant = relationship("Tenant", back_populates="api_keys")

class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    configuration = Column(JSON, nullable=False)
    tenant = relationship("Tenant", back_populates="policies")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    provider = Column(String)
    model = Column(String)
    risk_score = Column(Float)
    threats_triggered = Column(JSON)
    latency_ms = Column(Integer)
    tokens_used = Column(Integer)
    tenant = relationship("Tenant", back_populates="audit_logs")
