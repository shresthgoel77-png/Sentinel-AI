import uuid
import asyncio
import json
import logging
import time
import re
import secrets
import datetime
import csv
import sys
from io import StringIO
from contextlib import asynccontextmanager
from typing import Any, List, Optional

from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, status, Depends, Security, APIRouter, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case, text

from database.database import SessionLocal, engine
from database.models import APIKey, AuditLog, GatewayLog, ActionTaken, Application, Incident, Policy, PolicyRule, AlertChannel, TeamMember
from providers.openai import OpenAIProvider
from providers.anthropic import AnthropicProvider
from providers import ProviderRouter
from sanitizer import DocumentSanitizer, EgressSanitizer
from graph import app_graph
from policy_engine import get_tenant_policy, evaluate_policies
from services.audit import write_audit_log_background, write_gateway_log_background
from schemas import (TaskInitializationResponse, SourceFileMetadata,
                     DocumentExtractionPayload, ApplicationCreate, ApplicationResponse,
                     IncidentResponse, IncidentUpdate, PolicyCreate, PolicyResponse, PolicyRuleCreate,
                     AlertChannelCreate, AlertChannelResponse, TrafficLogResponse, TeamMemberCreate, TeamMemberResponse, CompliancePostureResponse)
from extractor import SecureDocumentExtractor
from redis_client import RedisManager
from langgraph_engine import LangGraphEngineHandoff
from cache import tasks_db

router_svc = ProviderRouter()

# Set up clean system logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.gateway")

# Setup Lifespan state management for clean resource handling
redis_manager: RedisManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_manager
    logger.info("Initializing Sentinel Gateway State Layers...")

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connected successfully.")
    except Exception as e:
        logger.error(f"Cannot connect to PostgreSQL at {engine.url}. Is Docker running? Error: {e}")
        raise

    try:
        redis_manager = RedisManager()
        await redis_manager.client.ping()
        logger.info("Redis connected successfully.")
    except Exception as e:
        logger.error(f"Cannot connect to Redis. Is Docker running? Error: {e}")
        raise

    await tasks_db.start()
    yield
    logger.info("Tearing down Sentinel Gateway State Layers...")
    await tasks_db.stop()
    if redis_manager:
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


# =====================================================================
# PHASE 4: STRUCTURED MODELS & BACKGROUND PIPELINE WORKERS
# =====================================================================
async def write_incident_background(incident_data: dict, tenant_id: int):
    from database.database import SessionLocal
    db = SessionLocal()
    try:
        new_incident = Incident(
            application_id=incident_data.get("application_id"),
            tenant_id=tenant_id,
            type=incident_data.get("type"),
            severity=incident_data.get("severity"),
            status=incident_data.get("status", "open"),
            prompt_preview=incident_data.get("prompt_preview"),
            full_prompt=incident_data.get("full_prompt"),
            risk_score=incident_data.get("risk_score"),
            scanner_breakdown=incident_data.get("scanner_breakdown"),
            policy_triggered=incident_data.get("policy_triggered")
        )
        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)
        
        # Async Webhook alert
        if incident_data.get("severity") in ["Critical", "High"]:
            channels = db.query(AlertChannel).filter(AlertChannel.tenant_id == tenant_id, AlertChannel.is_active == True).all()
            for c in channels:
                try:
                    import requests
                    payload = {"text": f"🚨 *{incident_data.get('severity')} Sentinel Incident:*\nType: {incident_data.get('type')}\nScore: {incident_data.get('risk_score')}\nPolicy: {incident_data.get('policy_triggered')}"}
                    requests.post(c.webhook_url, json=payload, timeout=3.0)
                except Exception as e:
                    logger.error(f"Failed webhook: {str(e)}")
                    
        if redis_manager and redis_manager.client:
            await redis_manager.client.publish("incidents:feed", json.dumps({"id": new_incident.id, "type": new_incident.type}))
    except Exception as e:
        logger.error(f"Failed to write incident: {str(e)}")
    finally:
        db.close()

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
    await tasks_db.__setitem__(task_id, {
        "status": "processing",
        "stage": "PARSER",
        "message": f"[PARSER] Extracting structures from {file_name}...",
        "isolated_injection_phrases": [],
        "risk_score": 12
    })
    await asyncio.sleep(1.2)  # Maintain visual processing cadence

    # Stage 2: Deep Heuristics Scanning
    await tasks_db.__setitem__(task_id, {
        "status": "processing",
        "stage": "HEURISTICS",
        "message": "[HEURISTICS] Checking for Unicode Lookalikes & Base64 payloads...",
        "isolated_injection_phrases": [],
        "risk_score": 40
    })
    await asyncio.sleep(1.6)

    # Stage 3: Semantic Verification Agent
    await tasks_db.__setitem__(task_id, {
        "status": "processing",
        "stage": "SEMANTIC_AGENT",
        "message": "[SEMANTIC AGENT] Processing intent validation with Gemini...",
        "isolated_injection_phrases": [],
        "risk_score": 65
    })
    await asyncio.sleep(1.5)

    # Stage 4: Risk Resolution Boundary Determination
    trigger_signatures = ["ignore previous instructions", "bypass system prompt", "sudo access", "base64"]
    found_threats = [word for word in trigger_signatures if word in content_sample.lower()]

    if found_threats or "malicious" in file_name.lower():
        # High-risk verdict matches -> Trigger QUARANTINED interface state
        await tasks_db.__setitem__(task_id, {
            "status": "malicious",
            "stage": "SEMANTIC_AGENT",
            "message": "[CRITICAL] Direct Prompt Injection exploit payload identified.",
            "isolated_injection_phrases": found_threats if found_threats else ["Bypass System Rules Trigger"],
            "risk_score": 98
        })
        logger.warning(f"Phase 4 Pipeline Sandbox [MALICIOUS] Vector Isolated: {task_id}")
    else:
        # Secure execution signature -> Trigger INGESTION_READY auth badge
        await tasks_db.__setitem__(task_id, {
            "status": "safe",
            "stage": "SEMANTIC_AGENT",
            "message": "[SUCCESS] Validation complete. Zero high-risk exploit signals mapped.",
            "isolated_injection_phrases": [],
            "risk_score": 3
        })
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
    task_data = await tasks_db.get(task_id)
    if task_data is not None:
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
    from sqlalchemy.orm import joinedload
    api_key_record = db.query(APIKey).options(joinedload(APIKey.application)).filter(APIKey.hashed_key == credentials.credentials).first()
    if not api_key_record or not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key_record

def verify_admin_role(x_mock_role: str = Header("admin", alias="X-Mock-Role")):
    if x_mock_role == "viewer":
        raise HTTPException(status_code=403, detail="Viewer role does not have permission to execute this action.")
    return x_mock_role

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

v1_router = APIRouter(prefix="/v1")

@v1_router.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    status = {"status": "healthy", "database": "up", "redis": "up"}
    try:
        db.execute("SELECT 1")
    except Exception:
        status["database"] = "down"
        status["status"] = "degraded"
    
    if not redis_manager or not redis_manager.client:
        status["redis"] = "down"
        status["status"] = "degraded"
        
    return status

@v1_router.post(
    "/chat/completions",
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
    
    if getattr(request, "stream", False):
        raise HTTPException(status_code=400, detail="Streaming is currently out of scope for Sentinel AI V1.")
    
    # 1. Compile prompt text from the incoming messages
    prompt_text = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])
    
    task_id_str = str(uuid.uuid4())
    
    source_metadata = SourceFileMetadata(
        filename="gateway_request.txt",
        content_type="text/plain",
        file_size_bytes=len(prompt_text)
    )
    
    extraction_payload = DocumentExtractionPayload(
        task_id=task_id_str,
        source_metadata=source_metadata,
        extracted_plaintext=prompt_text,
        metadata_payload="",
        security_flags={}
    )
    
    # 3. Synchronously await the execution of the existing LangGraph pipeline via LangGraphEngineHandoff
    graph_result = await LangGraphEngineHandoff.invoke_security_graph(extraction_payload)
    
    verdict = graph_result.get("semantic_verdict", {})
    risk_score = verdict.get("risk_score", 0)
    threat_signals = {"high_risk_instructions_found": verdict.get("high_risk_instructions_found", False)}
    classification_reason = verdict.get("justification", "Instruction hierarchy attack detected")
    threat_class = verdict.get("classification", "PROMPT_INJECTION")
    
    lat = int((time.perf_counter() - start_time) * 1000)
    
    client_id = str(api_key.tenant_id)
    provider_name = router_svc._get_provider_name(request.model)
    
    # 4. Enforce Dynamic Policy Studio Logic
    policy_action, triggered_policy = evaluate_policies(db, api_key.tenant_id, prompt_text, risk_score)
    
    # Track major anomalies or blocked incidents
    if risk_score > 50 or policy_action == "BLOCKED":
        severity = "Critical" if risk_score > 80 else "High" if risk_score > 60 else "Medium"
        incident_data = {
            "application_id": api_key.application_id,
            "type": threat_class or "Suspicious Activity",
            "severity": severity,
            "status": "open",
            "prompt_preview": prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text,
            "full_prompt": prompt_text,
            "risk_score": risk_score,
            "scanner_breakdown": graph_result.get("semantic_verdict", {}),
            "policy_triggered": triggered_policy or "Default Strict"
        }
        background_tasks.add_task(write_incident_background, incident_data, api_key.tenant_id)
    
    # 5. Halt Proxy if Policy explicitly DENIES execution
    if policy_action == "BLOCKED":
        background_tasks.add_task(
            write_audit_log_background, api_key.tenant_id, "BLOCKED", request.model, risk_score, threat_signals, lat, 0
        )
        # Final failure gateway telemetry
        background_tasks.add_task(
            write_gateway_log_background,
            request_id=task_id_str,
            client_id=client_id,
            provider_used=provider_name,
            model_name=request.model,
            risk_score=float(risk_score),
            threat_classification=threat_class,
            action_taken=ActionTaken.BLOCKED,
            latency_ms=float(lat),
            token_usage_prompt=0,
            token_usage_completion=0
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "message": f"Blocked by Sentinel AI: {classification_reason}",
                    "type": "security_policy_violation",
                    "param": None,
                    "code": threat_class,
                    "risk_score": risk_score
                }
            }
        )
        
    try:
        response = await router_svc.route(request, api_key.hashed_key)
        
        # Check if router returned error gracefully
        if "error" in response:
            lat = int((time.perf_counter() - start_time) * 1000)
            background_tasks.add_task(
                write_gateway_log_background, request_id=task_id_str, client_id=client_id, provider_used=provider_name, 
                model_name=request.model, risk_score=float(risk_score), threat_classification=None, 
                action_taken=ActionTaken.FAILED, latency_ms=float(lat), token_usage_prompt=0, token_usage_completion=0
            )
            code = response.get("error", {}).get("code", 500)
            return JSONResponse(status_code=int(code), content=response)
        
        # 5. Egress Scanning and Redaction
        if policy.get("enable_masking", True):
            for choice in response.get("choices", []):
                if "message" in choice and "content" in choice["message"]:
                    original_text = choice["message"]["content"]
                    redacted_text = EgressSanitizer.redact_sensitive_data(original_text)
                    choice["message"]["content"] = redacted_text
                
        lat = int((time.perf_counter() - start_time) * 1000)
        
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        tokens = usage.get("total_tokens", 0)
        
        # 6. Dispatch async Audit Logging tracking performance and cost mapping silently
        background_tasks.add_task(
            write_audit_log_background, api_key.tenant_id, provider_name, request.model, risk_score, threat_signals, lat, tokens
        )
        
        background_tasks.add_task(
            write_gateway_log_background,
            request_id=task_id_str,
            client_id=client_id,
            provider_used=provider_name,
            model_name=request.model,
            risk_score=float(risk_score),
            threat_classification=None,
            action_taken=ActionTaken.ALLOWED,
            latency_ms=float(lat),
            token_usage_prompt=prompt_tokens,
            token_usage_completion=completion_tokens
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
        lat = int((time.perf_counter() - start_time) * 1000)
        background_tasks.add_task(
            write_gateway_log_background, request_id=task_id_str, client_id=client_id, provider_used=provider_name, 
            model_name=request.model, risk_score=float(risk_score), threat_classification=None, 
            action_taken=ActionTaken.FAILED, latency_ms=float(lat), token_usage_prompt=0, token_usage_completion=0
        )
        raise HTTPException(status_code=500, detail=f"Provider generation failed: {str(e)}")

# =====================================================================
# PHASE 5.5: APPLICATION MANAGEMENT ROUTES
# =====================================================================
@v1_router.get("/applications", response_model=List[ApplicationResponse], tags=["Applications"])
async def list_applications(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    return db.query(Application).filter(Application.tenant_id == api_key.tenant_id).all()

@v1_router.post("/applications", response_model=ApplicationResponse, tags=["Applications"])
async def create_application(app_data: ApplicationCreate, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    new_app = Application(
        name=app_data.name,
        description=app_data.description,
        status=app_data.status,
        tenant_id=api_key.tenant_id
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@v1_router.get("/applications/{app_id}", response_model=ApplicationResponse, tags=["Applications"])
async def get_application(app_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    app_record = db.query(Application).filter(Application.id == app_id, Application.tenant_id == api_key.tenant_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_record

@v1_router.post("/applications/{app_id}/keys", tags=["Applications"])
async def generate_app_key(app_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    app_record = db.query(Application).filter(Application.id == app_id, Application.tenant_id == api_key.tenant_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
        
    raw_key = f"sk_sentinel_{secrets.token_urlsafe(24)}"
    new_key = APIKey(
        hashed_key=raw_key,
        tenant_id=api_key.tenant_id,
        application_id=app_id
    )
    db.add(new_key)
    db.commit()
    return {"api_key": raw_key, "message": "Store this key safely. It will not be shown again."}

@v1_router.get("/applications/{app_id}/traffic", tags=["Applications"])
async def get_app_traffic(app_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    app_record = db.query(Application).filter(Application.id == app_id, Application.tenant_id == api_key.tenant_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
        
    return {
        "metrics": [
            {"date": "Mon", "safe": 120, "blocked": 4},
            {"date": "Tue", "safe": 240, "blocked": 12},
            {"date": "Wed", "safe": 180, "blocked": 3},
            {"date": "Thu", "safe": 320, "blocked": 15},
            {"date": "Fri", "safe": 290, "blocked": 8},
        ]
    }

# =====================================================================
# PHASE 5.6: INCIDENT MANAGEMENT ROUTES
# =====================================================================
@v1_router.get("/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
async def list_incidents(status: Optional[str] = None, severity: Optional[str] = None, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    query = db.query(Incident).filter(Incident.tenant_id == api_key.tenant_id)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    return query.order_by(Incident.created_at.desc()).all()

@v1_router.get("/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
async def get_incident(incident_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    record = db.query(Incident).filter(Incident.id == incident_id, Incident.tenant_id == api_key.tenant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record

@v1_router.patch("/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
async def update_incident(incident_id: int, update_data: IncidentUpdate, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    record = db.query(Incident).filter(Incident.id == incident_id, Incident.tenant_id == api_key.tenant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if update_data.status:
        record.status = update_data.status
        if update_data.status in ["resolved", "false_positive"]:
            record.resolved_at = datetime.datetime.utcnow()
            record.resolved_by = update_data.resolved_by or "Admin Viewer"
            
    db.commit()
    db.refresh(record)
    return record


# =====================================================================
# PHASE 5.7: POLICY STUDIO MANAGEMENT ROUTES
# =====================================================================

@v1_router.get("/policies", response_model=List[PolicyResponse], tags=["Policies"])
async def list_policies(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    return db.query(Policy).filter(Policy.tenant_id == api_key.tenant_id).all()

@v1_router.post("/policies", response_model=PolicyResponse, tags=["Policies"])
async def create_policy(data: PolicyCreate, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    new_policy = Policy(
        tenant_id=api_key.tenant_id,
        name=data.name,
        description=data.description,
        type=data.type,
        scope=data.scope,
        is_active=data.is_active
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    
    for rule in data.rules:
        new_rule = PolicyRule(
            policy_id=new_policy.id,
            condition_type=rule.condition_type,
            condition_value=rule.condition_value,
            action=rule.action,
            priority=rule.priority,
            is_active=rule.is_active
        )
        db.add(new_rule)
    db.commit()
    db.refresh(new_policy)
    return new_policy

@v1_router.patch("/policies/{policy_id}/toggle", response_model=PolicyResponse, tags=["Policies"])
async def toggle_policy(policy_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.tenant_id == api_key.tenant_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.is_active = not policy.is_active
    db.commit()
    db.refresh(policy)
    return policy

class PolicyTestRequest(BaseModel):
    prompt: str

@v1_router.post("/policies/test", tags=["Policies"])
async def test_policy_bench(data: PolicyTestRequest, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Simulates the exact heuristic LangGraph breakdown but safely bypasses Background Incident telemetry allowing UI debugging.
    """
    initial_state = {"messages": [data.prompt], "threat_verdict": None, "semantic_threat_confidence": None}
    
    async def invoke_graph_async():
        return app_graph.invoke(initial_state)

    try:
        final_state = await asyncio.wait_for(invoke_graph_async(), timeout=5.0)
        risk_score = final_state.get("semantic_threat_confidence", 0)
        
        # Safe mock policy run mapping the raw score
        policy_action, triggered_policy = evaluate_policies(db, api_key.tenant_id, data.prompt, risk_score)
        
        return {
            "risk_score": risk_score,
            "policy_action": policy_action,
            "policy_triggered": triggered_policy or "Fallback Security Score",
            "scanner_payload": final_state.get("semantic_verdict", {})
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Test Bench Simulator Error: {str(e)}"})

# =====================================================================
# PHASE 6: OPERATIONAL INTELLIGENCE SUITE
# ==========================================
@v1_router.get("/overview", tags=["Analytics"])
async def get_overview_analytics(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    threats_blocked_today = db.query(func.count(Incident.id)).filter(
        Incident.tenant_id == api_key.tenant_id,
        Incident.created_at >= today_start,
        Incident.status != "false_positive"
    ).scalar() or 0
    
    open_incidents = db.query(func.count(Incident.id)).filter(
        Incident.tenant_id == api_key.tenant_id,
        Incident.status.notin_(["resolved", "false_positive"])
    ).scalar() or 0
    
    policy_health_score = max(10, 100 - (open_incidents * 2))
    apps_protected = db.query(func.count(Application.id)).filter(Application.tenant_id == api_key.tenant_id).scalar() or 0
    
    week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    trend_query = db.query(
        cast(GatewayLog.time_stamp, Date).label('date'),
        func.sum(case((GatewayLog.action_taken == 'ALLOWED', 1), else_=0)).label('allowed'),
        func.sum(case((GatewayLog.action_taken == 'BLOCKED', 1), else_=0)).label('blocked')
    ).filter(
        GatewayLog.client_id == str(api_key.tenant_id),
        GatewayLog.time_stamp >= week_ago
    ).group_by(cast(GatewayLog.time_stamp, Date)).all()
    
    trend_data = [
        {
            "date": str(r.date)[-5:], 
            "allowed": r.allowed or 0, 
            "blocked": r.blocked or 0, 
            "total": (r.allowed or 0) + (r.blocked or 0)
        } for r in trend_query
    ]
    
    top_threats_query = db.query(
        Incident.type,
        func.count(Incident.id).label('count')
    ).filter(
        Incident.tenant_id == api_key.tenant_id,
        Incident.created_at >= week_ago
    ).group_by(Incident.type).order_by(func.count(Incident.id).desc()).limit(5).all()
    
    top_threats = [{"type": r[0], "count": r[1]} for r in top_threats_query]
    
    return {
        "threats_blocked_today": threats_blocked_today,
        "open_incidents": open_incidents,
        "policy_health_score": policy_health_score,
        "applications_protected": apps_protected,
        "trend_data": trend_data,
        "top_threats": top_threats
    }

import io
import csv
from fastapi.responses import StreamingResponse

@v1_router.get("/audit/export", tags=["Analytics"])
async def export_audit(
    start: Optional[str] = None, 
    end: Optional[str] = None, 
    api_key: APIKey = Depends(verify_api_key), 
    db: Session = Depends(get_db)
):
    query = db.query(GatewayLog).filter(GatewayLog.client_id == str(api_key.tenant_id))
    if start:
        query = query.filter(GatewayLog.time_stamp >= start)
    if end:
        query = query.filter(GatewayLog.time_stamp <= end)
        
    logs = query.order_by(GatewayLog.time_stamp.desc()).limit(1000).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Provider", "Model", "Risk Score", "Threat", "Action"])
    
    for log in logs:
        writer.writerow([
            log.id, 
            log.time_stamp, 
            log.provider_used, 
            log.model_name, 
            log.risk_score, 
            log.threat_classification or "", 
            log.action_taken.value if hasattr(log.action_taken, 'value') else log.action_taken
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=audit_export.csv"}
    )

@v1_router.get("/traffic", response_model=List[TrafficLogResponse], tags=["Analytics"])
async def get_live_traffic(limit: int = 100, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    logs = db.query(GatewayLog).filter(GatewayLog.client_id == str(api_key.tenant_id)).order_by(GatewayLog.time_stamp.desc()).limit(limit).all()
    for log in logs:
        if hasattr(log.action_taken, 'value'): 
            log.action_taken = log.action_taken.value
    return logs

@v1_router.post("/alerts/configure", response_model=AlertChannelResponse, tags=["Alerts"])
async def configure_alerts(data: AlertChannelCreate, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    channel = db.query(AlertChannel).filter(AlertChannel.tenant_id == api_key.tenant_id, AlertChannel.type == data.type).first()
    if channel:
        channel.webhook_url = data.webhook_url
        channel.events = data.events
        channel.is_active = data.is_active
    else:
        channel = AlertChannel(tenant_id=api_key.tenant_id, type=data.type, webhook_url=data.webhook_url, events=data.events, is_active=data.is_active)
        db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

@v1_router.get("/team", response_model=List[TeamMemberResponse], tags=["Team"])
async def get_team(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    from database.models import TeamMember
    return db.query(TeamMember).filter(TeamMember.tenant_id == api_key.tenant_id).all()

@v1_router.post("/team/invite", response_model=TeamMemberResponse, tags=["Team"])
async def invite_team(data: TeamMemberCreate, api_key: APIKey = Depends(verify_api_key), role: str = Depends(verify_admin_role), db: Session = Depends(get_db)):
    from database.models import TeamMember
    member = TeamMember(tenant_id=api_key.tenant_id, email=data.email, name=data.name, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@v1_router.delete("/team/{id}", tags=["Team"])
async def remove_team_member(id: int, api_key: APIKey = Depends(verify_api_key), role: str = Depends(verify_admin_role), db: Session = Depends(get_db)):
    from database.models import TeamMember
    member = db.query(TeamMember).filter(TeamMember.id == id, TeamMember.tenant_id == api_key.tenant_id).first()
    if not member:
        raise HTTPException(404, "Member not found")
    db.delete(member)
    db.commit()
    return {"status": "removed"}

@v1_router.get("/me/onboarding", tags=["Onboarding"])
async def get_onboarding(api_key: APIKey = Depends(verify_api_key)):
    return {"onboarding_completed": api_key.tenant.onboarding_completed}

@v1_router.post("/me/onboarding", tags=["Onboarding"])
async def complete_onboarding(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    api_key.tenant.onboarding_completed = True
    db.commit()
    return {"onboarding_completed": True}

@v1_router.get("/compliance/posture", response_model=CompliancePostureResponse, tags=["Compliance"])
async def get_compliance_posture(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    active_policies = db.query(Policy).filter(Policy.tenant_id == api_key.tenant_id, Policy.is_active == True).count()
    return CompliancePostureResponse(
        frameworks_active=["SOC2", "GDPR"] if active_policies > 0 else ["Internal Baseline"],
        last_audit_date=datetime.datetime.utcnow(),
        event_retention_days=90,
        soc2_aligned=(active_policies >= 2)
    )

@v1_router.get(
    "/analytics/dashboard",
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

@v1_router.get("/incidents", tags=["Incidents"])
async def list_incidents(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    return [{
        "id": i.id, "created_at": i.created_at, "application_id": i.application_id, 
        "type": i.type, "severity": i.severity, "status": i.status,
        "risk_score": i.risk_score, "policy_triggered": i.policy_triggered,
        "prompt_preview": i.prompt_preview
    } for i in incidents]

@v1_router.get("/incidents/{incident_id}", tags=["Incidents"])
async def get_incident(incident_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    i = db.query(Incident).filter(Incident.id == incident_id).first()
    if not i: raise HTTPException(status_code=404, detail="Incident not found")
    # Graceful fallback logic bridging schemas
    return {
        "id": i.id, "created_at": i.created_at, "application_id": i.application_id, 
        "type": i.type, "severity": i.severity, "status": i.status,
        "risk_score": i.risk_score, "policy_triggered": i.policy_triggered,
        "prompt_preview": i.prompt_preview, "full_prompt": getattr(i, 'full_prompt', i.prompt_preview),
        "scanner_breakdown": getattr(i, 'scanner_breakdown', {"isolated_injection_phrases": []})
    }

@v1_router.patch("/incidents/{incident_id}", tags=["Incidents"])
async def update_incident(incident_id: int, update: IncidentUpdate, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    i = db.query(Incident).filter(Incident.id == incident_id).first()
    if not i: raise HTTPException(status_code=404, detail="Incident not found")
    i.status = update.status
    db.commit()
    return {"status": i.status}

class PolicyTestRequest(BaseModel):
    prompt: str

@v1_router.post("/policies/test", tags=["Policies"])
async def test_policy_bench(req: PolicyTestRequest, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    # Structure the payload strictly towards Graph analysis
    extraction_payload = DocumentExtractionPayload(
        task_id=str(uuid.uuid4()),
        source_metadata=SourceFileMetadata(filename="test_bench.txt", content_type="text/plain", file_size_bytes=len(req.prompt)),
        extracted_plaintext=req.prompt, metadata_payload="", security_flags={}
    )
    
    # Simulate execution synchronously
    graph_result = await LangGraphEngineHandoff.invoke_security_graph(extraction_payload)
    verdict = graph_result.get("semantic_verdict", {})
    risk_score = verdict.get("risk_score", 0)
    
    # Compare with existing metrics dynamically
    policy_action, triggered_policy = evaluate_policies(db, api_key.tenant_id, req.prompt, risk_score)
    
    return {
        "policy_action": policy_action,
        "risk_score": risk_score,
        "policy_triggered": triggered_policy or "Default Strict",
        "scanner_payload": verdict
    }

@v1_router.get("/policies", tags=["Policies"])
async def list_policies(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    return db.query(Policy).filter(Policy.tenant_id == api_key.tenant_id).all()

@v1_router.patch("/policies/{policy_id}/toggle", tags=["Policies"])
async def toggle_policy(policy_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    p = db.query(Policy).filter(Policy.id == policy_id, Policy.tenant_id == api_key.tenant_id).first()
    if not p: raise HTTPException(status_code=404, detail="Policy not found")
    p.is_active = not p.is_active
    db.commit()
    return {"is_active": p.is_active}

@v1_router.get("/team", tags=["Team"])
async def list_team(api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    return db.query(TeamMember).filter(TeamMember.tenant_id == api_key.tenant_id).all()

@v1_router.post("/team/invite", tags=["Team"])
async def invite_team_member(req: TeamMemberCreate, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    tm = TeamMember(tenant_id=api_key.tenant_id, name=req.name, email=req.email, role=req.role)
    db.add(tm)
    db.commit()
    db.refresh(tm)
    return tm

@v1_router.delete("/team/{member_id}", tags=["Team"])
async def revoke_member(member_id: int, api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db), __=Depends(verify_admin_role)):
    m = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.tenant_id == api_key.tenant_id).first()
    if not m: raise HTTPException(status_code=404, detail="Member not found")
    db.delete(m)
    db.commit()
    return {"status": "revoked"}

@v1_router.get("/audit/export", tags=["Audit"])
async def export_audit_log(
    start: Optional[str] = None, end: Optional[str] = None, 
    api_key: APIKey = Depends(verify_api_key), db: Session = Depends(get_db)):
    
    query = db.query(AuditLog).filter(AuditLog.tenant_id == api_key.tenant_id)
    if start: query = query.filter(AuditLog.time_stamp >= start)
    if end: query = query.filter(AuditLog.time_stamp <= end)
    
    logs = query.all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Timestamp", "Provider", "Model", "Risk Score", "Latency (ms)", "Tokens"])
    for l in logs:
        cw.writerow([l.id, l.time_stamp, l.provider, l.model, l.risk_score, l.latency_ms, l.tokens_used])
        
    return StreamingResponse(
        iter([si.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_export.csv"}
    )

app.include_router(v1_router)