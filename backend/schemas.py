from pydantic import BaseModel, Field, UUID4
from typing import Dict, Any, Optional

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