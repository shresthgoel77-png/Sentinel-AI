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

class APIKeyResponse(APIKeyBase):
    id: int
    tenant_id: int
    
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