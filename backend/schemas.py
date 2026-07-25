from pydantic import BaseModel, Field, UUID4
from typing import Dict, Any, Optional
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

class TaskInitializationResponse(BaseModel):
    task_id: UUID4 = Field(..., description="The unique identity tracking this document's safety analysis.")
    status: str = Field("PARSING_COMPLETE", description="Initial status written to the cache layer.")


class SourceFileMetadata(BaseModel):
    filename: str
    content_type: str
    file_size_bytes: int

class DocumentExtractionPayload(BaseModel):
    task_id: UUID4
    source_metadata: SourceFileMetadata
    extracted_plaintext: str = Field(..., description="Clean, visible body text meant for safe chunking.")
    metadata_payload: str = Field(..., description="Aggregated hidden text, alt tags, metadata, and structural anomalies.")
    security_flags: Dict[str, Any] = Field(default_factory=dict, description="Metadata flags like suspected_hidden_text or anomalous_sizes.")

class FlaggedSection(BaseModel):
    text: str = Field(
        ..., 
        description="The exact, unedited section of the raw document that contributed to the unsafe verdict."
    )
    reason: str = Field(
        ..., 
        description="A brief explanation of why this section was flagged. Maximum 8 words."
    )

class SecurityExplanationOutput(BaseModel):
    summary: str = Field(
        ..., 
        description="A summary describing why the document is unsafe. Maximum 15 words."
    )
    flagged_sections: List[FlaggedSection] = Field(
        default_factory=list,
        description="List of flagged sections. Must be empty if the document is safe."
    )

class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class TenantResponse(TenantBase):
    id: int
    
    class Config:
        from_attributes = True

class APIKeyBase(BaseModel):
    is_active: bool = True

class APIKeyCreate(APIKeyBase):
    hashed_key: str
    tenant_id: int
    application_id: Optional[int] = None

class APIKeyResponse(APIKeyBase):
    id: int
    tenant_id: int
    application_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class ApplicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: int
    tenant_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PolicyBase(BaseModel):
    configuration: Dict[str, Any]

class PolicyCreate(PolicyBase):
    tenant_id: int

class PolicyResponse(PolicyBase):
    id: int
    tenant_id: int
    
    class Config:
        from_attributes = True

class IncidentBase(BaseModel):
    type: str
    severity: str
    status: str = "open"
    prompt_preview: Optional[str] = None
    full_prompt: Optional[str] = None
    full_response: Optional[str] = None
    risk_score: float
    scanner_breakdown: Optional[Dict[str, Any]] = None
    policy_triggered: Optional[str] = None

class IncidentCreate(IncidentBase):
    application_id: Optional[int] = None
    tenant_id: int

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    resolved_by: Optional[str] = None

class PolicyRuleBase(BaseModel):
    condition_type: str
    condition_value: str
    action: str
    priority: int = 10
    is_active: bool = True

class PolicyRuleCreate(PolicyRuleBase):
    pass

class PolicyRuleResponse(PolicyRuleBase):
    id: int
    class Config:
        from_attributes = True

class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "custom"
    scope: str = "global"
    is_active: bool = True

class PolicyCreate(PolicyBase):
    rules: List[PolicyRuleCreate] = []

class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime
    rules: List[PolicyRuleResponse] = []
    
    class Config:
        from_attributes = True

class AlertChannelCreate(BaseModel):
    type: str = "slack"
    webhook_url: str
    events: List[str] = ["incident.critical", "incident.high"]
    is_active: bool = True

class AlertChannelResponse(AlertChannelCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TrafficLogResponse(BaseModel):
    id: int
    time_stamp: datetime
    provider_used: str
    model_name: str
    risk_score: float
    threat_classification: Optional[str] = None
    action_taken: str
    latency_ms: float
    class Config:
        from_attributes = True

class IncidentResponse(IncidentBase):
    id: int
    application_id: Optional[int] = None
    tenant_id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class AuditLogBase(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    risk_score: Optional[float] = None
    threats_triggered: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None

class AuditLogCreate(AuditLogBase):
    tenant_id: int

class AuditLogResponse(AuditLogBase):
    id: int
    tenant_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class TeamMemberBase(BaseModel):
    name: str
    email: str
    role: str

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberResponse(TeamMemberBase):
    id: int
    tenant_id: int
    
    class Config:
        from_attributes = True

class CompliancePostureResponse(BaseModel):
    frameworks_active: List[str]
    last_audit_date: datetime
    event_retention_days: int
    soc2_aligned: bool
