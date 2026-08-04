from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
import enum
from .database import Base

class ActionTaken(enum.Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    onboarding_completed = Column(Boolean, default=False)
    api_keys = relationship("APIKey", back_populates="tenant")
    policies = relationship("Policy", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")
    applications = relationship("Application", back_populates="tenant")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="applications")
    api_keys = relationship("APIKey", back_populates="application")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, default="open", nullable=False)
    prompt_preview = Column(String, nullable=True)
    full_prompt = Column(String, nullable=True)
    full_response = Column(String, nullable=True)
    risk_score = Column(Float, nullable=False)
    scanner_breakdown = Column(JSON, nullable=True)
    policy_triggered = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)

    tenant = relationship("Tenant", backref="incidents")
    application = relationship("Application", backref="incidents")

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    hashed_key = Column(String, unique=True, index=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    tenant = relationship("Tenant", back_populates="api_keys")
    application = relationship("Application", back_populates="api_keys")

class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Legacy Default")
    description = Column(String, nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    type = Column(String, default="custom")
    is_active = Column(Boolean, default=True)
    config = Column(JSON, nullable=True)
    scope = Column(String, default="global")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="policies")
    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")

class PolicyRule(Base):
    __tablename__ = "policy_rules"
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    condition_type = Column(String, nullable=False)
    condition_value = Column(String, nullable=False)
    action = Column(String, nullable=False)
    priority = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)

    policy = relationship("Policy", back_populates="rules")

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

class GatewayLog(Base):
    __tablename__ = "gateway_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), index=True, nullable=False)
    client_id = Column(String, index=True, nullable=False)
    provider_used = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    threat_classification = Column(String, nullable=True)
    action_taken = Column(Enum(ActionTaken), nullable=False)
    latency_ms = Column(Float, nullable=False)
    token_usage_prompt = Column(Integer, default=0)
    token_usage_completion = Column(Integer, default=0)
    time_stamp = Column(DateTime, default=datetime.datetime.utcnow)


class AlertChannel(Base):
    __tablename__ = "alert_channels"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    type = Column(String, default="slack")
    webhook_url = Column(String, nullable=False)
    events = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant")

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="viewer") 
    invited_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    tenant = relationship("Tenant")
