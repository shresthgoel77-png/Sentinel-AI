import uuid
import asyncio
import json
import logging
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import APIKey
from providers.openai import OpenAIProvider
from providers.anthropic import AnthropicProvider
from sanitizer import DocumentSanitizer
from graph import app_graph
from policy_engine import get_tenant_policy
import time
import re
from database.models import AuditLog
from sqlalchemy import func

# Retain all of your structural project domain imports
from schemas import TaskInitializationResponse, SourceFileMetadata, DocumentExtractionPayload
from extractor import SecureDocumentExtractor
from redis_client import RedisManager
from langgraph_engine import LangGraphEngineHandoff

# Set up clean system logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.gateway")

# Setup Lifespan state management for clean resource handling
redis_manager: RedisManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_manager
    logger.info("Initializing Sentinel Gateway State Layers...")
    redis_manager = RedisManager()
    yield
    logger.info("Tearing down Sentinel Gateway State Layers...")
    await redis_manager.close()

app = FastAPI(title="Sentinel AI - Pre-Ingestion Node Gateway", version="1.0.0", lifespan=lifespan)

# =====================================================================
# CORS INITIALIZATION LAYER (Required for React App Connectivity)
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Memory State to feed the rapid 400ms React terminal polling interface
tasks_db = {}


# =====================================================================
# PHASE 4: STRUCTURED MODELS & BACKGROUND PIPELINE WORKERS
# =====================================================================
class ScanVerdict(BaseModel):
    status: str  # "processing" | "safe" | "malicious"
    stage: Optional[str] = None
    message: Optional[str] = None
    isolated_injection_phrases: Optional[List[str]] = None
    risk_score: Optional[int] = None

async def run_phase4_analysis_pipeline(task_id: str, file_name: str, file_bytes: bytes):
    """
    Simulates the progressive structural validation loop.
    Feeds log statements sequentially to perfectly coordinate with the 400ms polling UI.
    """
    # Safe decoding array sample to match threat heuristics
    content_sample = ""
    try:
        content_sample = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # Stage 1: Structure Extraction
    tasks_db[task_id] = {
        "status": "processing",
        "stage": "PARSER",
        "message": f"[PARSER] Extracting structures from {file_name}...",
        "isolated_injection_phrases": [],
        "risk_score": 12
    }
    await asyncio.sleep(1.2)  # Maintain visual processing cadence

    # Stage 2: Deep Heuristics Scanning
    tasks_db[task_id] = {
        "status": "processing",
        "stage": "HEURISTICS",
        "message": "[HEURISTICS] Checking for Unicode Lookalikes & Base64 payloads...",
        "isolated_injection_phrases": [],
        "risk_score": 40
    }
    await asyncio.sleep(1.6)

    # Stage 3: Semantic Verification Agent
    tasks_db[task_id] = {
        "status": "processing",
        "stage": "SEMANTIC_AGENT",
        "message": "[SEMANTIC AGENT] Processing intent validation with Gemini...",
        "isolated_injection_phrases": [],
        "risk_score": 65
    }
    await asyncio.sleep(1.5)

    # Stage 4: Risk Resolution Boundary Determination
    trigger_signatures = ["ignore previous instructions", "bypass system prompt", "sudo access", "base64"]
    found_threats = [word for word in trigger_signatures if word in content_sample.lower()]

    if found_threats or "malicious" in file_name.lower():
        # High-risk verdict matches -> Trigger QUARANTINED interface state
        tasks_db[task_id] = {
            "status": "malicious",
            "stage": "SEMANTIC_AGENT",
            "message": "[CRITICAL] Direct Prompt Injection exploit payload identified.",
            "isolated_injection_phrases": found_threats if found_threats else ["Bypass System Rules Trigger"],
            "risk_score": 98
        }
        logger.warning(f"Phase 4 Pipeline Sandbox [MALICIOUS] Vector Isolated: {task_id}")
    else:
        # Secure execution signature -> Trigger INGESTION_READY auth badge
        tasks_db[task_id] = {
            "status": "safe",
            "stage": "SEMANTIC_AGENT",
            "message": "[SUCCESS] Validation complete. Zero high-risk exploit signals mapped.",
            "isolated_injection_phrases": [],
            "risk_score": 3
        }
        logger.info(f"Phase 4 Pipeline Sandbox [SAFE] Processing Complete: {task_id}")


# =====================================================================
# EXISTING PRODUCTION ROUTES (Phases 1, 2, 3)
# =====================================================================
@app.post(
    "/api/analyze-document", 
    response_model=TaskInitializationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest, unpack, and scan documents for indirect prompt injection vectors before database write."
)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Target payload file stream (PDF, DOCX, HTML, MD, TXT).")
):
    # 1. Capture basic file traits safely
    filename = file.filename
    content_type = file.content_type
    
    try:
        # 2. Stream layout bytes securely in memory
        file_bytes = await file.read()
        file_size = len(file_bytes)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Cannot parse an empty document file stream.")
            
        source_metadata = SourceFileMetadata(
            filename=filename,
            content_type=content_type,
            file_size_bytes=file_size
        )
        
        # 3. Route to extraction matrix for deep deconstruction and anomaly isolation
        plaintext, metadata_payload, security_flags = await SecureDocumentExtractor.extract(
            file_bytes=file_bytes, 
            filename=filename, 
            content_type=content_type
        )
        
    except Exception as parse_error:
        logger.error(f"Parser failure on file parsing step: {str(parse_error)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"Failed to safely extract text from document layer: {str(parse_error)}"
        )
    
    # 4. Generate persistent tracking Identity
    task_id = uuid.uuid4()
    
    # 5. Initialize the state signature inside our Redis cache layer
    await redis_manager.initialize_task(task_id=task_id, initial_status="PARSING_COMPLETE")
    
    # 6. Construct data transfer payload object
    extraction_payload = DocumentExtractionPayload(
        task_id=task_id,
        source_metadata=source_metadata,
        extracted_plaintext=plaintext,
        metadata_payload=metadata_payload,
        security_flags=security_flags
    )
    
    # 7. Asynchronously hand off state control directly to the background processing worker
    background_tasks.add_task(LangGraphEngineHandoff.invoke_security_graph, extraction_payload)
    
    # 8. Instantly yield execution block control back to the SaaS API client
    return TaskInitializationResponse(task_id=task_id)


# =====================================================================
# NEW PHASE 4 INTERACTIVE ROUTES (React Dark Terminal UI Extensions)
# =====================================================================
class PromptAnalysisRequest(BaseModel):
    text: str

@app.post(
    "/api/analyze-prompt",
    response_model=TaskInitializationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Direct ingestion channel for raw text prompt scanning."
)
async def analyze_prompt(
    request: PromptAnalysisRequest,
    background_tasks: BackgroundTasks
):
    try:
        task_id = uuid.uuid4()
        
        source_metadata = SourceFileMetadata(
            filename="raw_prompt.txt",
            content_type="text/plain",
            file_size_bytes=len(request.text)
        )
        
        # Initialize in Redis
        await redis_manager.initialize_task(task_id=task_id, initial_status="PARSING_COMPLETE")
        
        extraction_payload = DocumentExtractionPayload(
            task_id=task_id,
            source_metadata=source_metadata,
            extracted_plaintext=request.text,
            metadata_payload="",
            security_flags={}
        )
        
        # Hand off to LangGraph background worker
        background_tasks.add_task(LangGraphEngineHandoff.invoke_security_graph, extraction_payload)
        
        return TaskInitializationResponse(task_id=task_id)
        
    except Exception as e:
        logger.error(f"Prompt ingestion initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prompt scanning failed: {str(e)}")

@app.post(
    "/api/scan",
    summary="Direct ingestion channel for the real-time dark terminal visualization console."
)
async def initial_file_ingestion(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        filename = file.filename
        content_type = file.content_type
        file_bytes = await file.read()
        file_size = len(file_bytes)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Cannot parse an empty document file stream.")
            
        source_metadata = SourceFileMetadata(
            filename=filename,
            content_type=content_type,
            file_size_bytes=file_size
        )
        
        # Extract content
        plaintext, metadata_payload, security_flags = await SecureDocumentExtractor.extract(
            file_bytes=file_bytes, 
            filename=filename, 
            content_type=content_type
        )
        
        task_id = uuid.uuid4()
        
        # Initialize in Redis
        await redis_manager.initialize_task(task_id=task_id, initial_status="PARSING_COMPLETE")
        
        extraction_payload = DocumentExtractionPayload(
            task_id=task_id,
            source_metadata=source_metadata,
            extracted_plaintext=plaintext,
            metadata_payload=metadata_payload,
            security_flags=security_flags
        )
        
        # Hand off to LangGraph background worker
        background_tasks.add_task(LangGraphEngineHandoff.invoke_security_graph, extraction_payload)
        
        return {"task_id": task_id}
        
    except Exception as e:
        logger.error(f"File ingestion scan initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion framework failed: {str(e)}")

@app.get(
    "/api/status/{task_id}", 
    summary="Real-time terminal polling stream engine endpoint."
)
async def get_pipeline_status(task_id: str):
    # 1. Check Redis first
    if redis_manager and redis_manager.client:
        try:
            redis_data = await redis_manager.client.get(f"status:{task_id}")
            if redis_data:
                data = json.loads(redis_data)
                is_complete = data.get("is_complete", False)
                step = data.get("step", "")
                message = data.get("message", "")
                
                result = data.get("result", {})
                semantic_verdict = result.get("semantic_verdict", {})
                
                # Extract risk_score and other metrics
                risk_score = semantic_verdict.get("risk_score") or result.get("confidence") or 0
                quarantine_status = result.get("quarantine_status", "")
                
                # Determine UI status value
                if is_complete:
                    status_val = "malicious" if quarantine_status == "QUARANTINED" else "safe"
                else:
                    status_val = "processing"
                
                # Determine threat classification
                if risk_score > 75:
                    threat_level = "high"
                    final_action = "block"
                elif risk_score > 30:
                    threat_level = "medium"
                    final_action = "redact"
                else:
                    threat_level = "low"
                    final_action = "allow"
                
                # Retrieve explanation
                explanation = data.get("explanation", {})
                findings = explanation.get("summary") or semantic_verdict.get("justification") or result.get("findings") or message
                
                isolated_injection_phrases = semantic_verdict.get("isolated_injection_phrases", [])
                
                return {
                    "status": status_val,
                    "stage": step.upper() if step else None,
                    "message": message,
                    "is_complete": is_complete,
                    "risk_score": risk_score,
                    "confidence": risk_score,
                    "threat_level": threat_level,
                    "final_action": final_action,
                    "findings": findings,
                    "isolated_injection_phrases": isolated_injection_phrases
                }
        except Exception as e:
            logger.error(f"Failed to fetch status from Redis: {str(e)}")

    # 2. Fall back to local tasks_db (simulated pipeline status)
    if task_id in tasks_db:
        task_data = tasks_db[task_id]
        status_val = task_data.get("status", "processing")
        is_complete = status_val in ["safe", "malicious"]
        risk_score = task_data.get("risk_score", 0)
        
        threat_level = "high" if status_val == "malicious" else "low"
        final_action = "block" if status_val == "malicious" else "allow"
        
        return {
            "status": status_val,
            "stage": task_data.get("stage"),
            "message": task_data.get("message"),
            "is_complete": is_complete,
            "risk_score": risk_score,
            "confidence": risk_score,
            "threat_level": threat_level,
            "final_action": final_action,
            "findings": task_data.get("message"),
            "isolated_injection_phrases": task_data.get("isolated_injection_phrases", [])
        }
        
    raise HTTPException(status_code=404, detail="Task signature lookup failed or expired.")

# =====================================================================
# PHASE 5: GATEWAY INTERCEPTION ROUTES (OpenAI SDK Compatible)
# =====================================================================
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    if not credentials.credentials.startswith("sk_sentinel_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Check DB
    api_key_record = db.query(APIKey).filter(APIKey.hashed_key == credentials.credentials).first()
    if not api_key_record or not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key_record

def redact_sensitive_data(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'(sk|pk)_[a-zA-Z0-9]{20,}', '[REDACTED_KEY]', text)
    text = re.sub(r'AKIA[0-9A-Z]{16}', '[REDACTED_CREDENTIAL]', text)
    return text

def write_audit_log_background(
    tenant_id: int, provider_name: str, model_name: str,
    risk_score: float, threats_json: dict, latency: int, tokens: int
):
    db_session = SessionLocal()
    try:
        log_entry = AuditLog(
            tenant_id=tenant_id,
            provider=provider_name,
            model=model_name,
            risk_score=risk_score,
            threats_triggered=threats_json,
            latency_ms=latency,
            tokens_used=tokens
        )
        db_session.add(log_entry)
        db_session.commit()
    except Exception as e:
        logger.error(f"Audit log insertion failed: {e}")
    finally:
        db_session.close()

class OpenAIMessage(BaseModel):
    role: str
    content: str
    
class OpenAIChatCompletionRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0

@app.post(
    "/v1/chat/completions",
    summary="OpenAI-Compatible Gateway Interception Endpoint",
    tags=["Gateway"]
)
async def chat_completions(
    request: OpenAIChatCompletionRequest,
    background_tasks: BackgroundTasks,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    start_time = time.perf_counter()
    policy = get_tenant_policy(db, api_key.tenant_id)
    
    # 1. Compile prompt text from the incoming messages
    prompt_text = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])
    
    # 2. Extract and Sanitize before LangGraph
    clean_text, sanitizer_flags = DocumentSanitizer.process(prompt_text)
    
    combined_content = (
        f"--- VISIBLE TEXT ---\n{clean_text}\n\n"
        f"--- HIDDEN METADATA/FLAGS ---\n\n"
        f"System Flags: {sanitizer_flags}"
    )   
    
    task_id_str = f"gw-{uuid.uuid4()}"
    
    initial_state = {
        "task_id": task_id_str,
        "prompt": combined_content,
        "document_text": clean_text,
        "heuristic_flags": sanitizer_flags
    }
    
    # 3. Synchronously await the execution of the existing LangGraph pipeline
    import asyncio
    graph_result = await asyncio.to_thread(app_graph.invoke, initial_state)
    
    verdict = graph_result.get("semantic_verdict", {})
    risk_score = verdict.get("risk_score", 0)
    threat_signals = {"high_risk_instructions_found": verdict.get("high_risk_instructions_found", False)}
    
    lat = int((time.perf_counter() - start_time) * 1000)
    
    risk_limit = policy.get("max_risk_score", 80)
    
    # 4. Enforce strict gateway threshold
    if risk_score > risk_limit:
        background_tasks.add_task(
            write_audit_log_background, api_key.tenant_id, "BLOCKED", request.model, risk_score, threat_signals, lat, 0
        )
        return {
            "error": {
                "message": f"Sentinel AI Security Block: Prompt injection or high-risk content detected (Risk Score: {risk_score}).",
                "type": "security_policy_violation",
                "param": "prompt",
                "code": "threat_detected"
            },
            "_sentinel_trace": {
                "langgraph_risk": risk_score,
                "latency_ms": lat,
                "threat_signals": threat_signals
            }
        }
        
    # Route dynamically based on the model provided
    provider_name = ""
    if request.model.startswith("gpt") or request.model.startswith("o1"):
        provider = OpenAIProvider()
        provider_name = "OpenAI"
    elif request.model.startswith("claude"):
        provider = AnthropicProvider()
        provider_name = "Anthropic"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider for model: {request.model}")
        
    try:
        response = await provider.generate_completion(request, api_key.hashed_key)
        
        # 5. Egress Scanning and Redaction
        if policy.get("enable_masking", True):
            for choice in response.get("choices", []):
                if "message" in choice and "content" in choice["message"]:
                    original_text = choice["message"]["content"]
                    redacted_text = redact_sensitive_data(original_text)
                    choice["message"]["content"] = redacted_text
                
        lat = int((time.perf_counter() - start_time) * 1000)
        tokens = response.get("usage", {}).get("total_tokens", 0)
        
        # 6. Dispatch async Audit Logging tracking performance and cost mapping silently
        background_tasks.add_task(
            write_audit_log_background, api_key.tenant_id, provider_name, request.model, risk_score, threat_signals, lat, tokens
        )
        
        if isinstance(response, dict):
            response["_sentinel_trace"] = {
                "langgraph_risk": risk_score,
                "latency_ms": lat,
                "threat_signals": threat_signals,
                "tokens_used": tokens
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider generation failed: {str(e)}")

# =====================================================================
# PHASE 6: OPERATIONAL INTELLIGENCE SUITE
# ==========================================
@app.get(
    "/v1/analytics/dashboard",
    summary="Global Analytics Dashboard Data",
    tags=["Analytics"]
)
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    # 1. Total Scans
    total_scans = db.query(func.count(AuditLog.id)).scalar() or 0
    
    # 2. Blocked vs Safe
    threats_blocked = db.query(func.count(AuditLog.id)).filter(AuditLog.provider == "BLOCKED").scalar() or 0
    safe_requests = total_scans - threats_blocked
    
    # 3. Aggregations
    avg_risk = db.query(func.avg(AuditLog.risk_score)).scalar() or 0.0
    avg_latency = db.query(func.avg(AuditLog.latency_ms)).scalar() or 0.0
    total_tokens = db.query(func.sum(AuditLog.tokens_used)).scalar() or 0
    
    # 4. Provider Splits
    openai_count = db.query(func.count(AuditLog.id)).filter(AuditLog.provider == "OpenAI").scalar() or 0
    anthropic_count = db.query(func.count(AuditLog.id)).filter(AuditLog.provider == "Anthropic").scalar() or 0
    
    return {
        "stats": {
            "totalScans": total_scans,
            "threatsBlocked": threats_blocked,
            "safeRequests": safe_requests,
            "averageRiskScore": round(avg_risk, 1),
            "averageLatencyMs": round(avg_latency, 0),
            "providerSplit": {
                "openai": openai_count,
                "anthropic": anthropic_count
            },
            "totalTokens": total_tokens
        }
    }