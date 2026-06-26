import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, status

from schemas import TaskInitializationResponse, SourceFileMetadata, DocumentExtractionPayload
from extractor import SecureDocumentExtractor
from redis_client import RedisStateManager
from langgraph_engine import LangGraphEngineHandoff

# Set up clean system logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.gateway")

# Setup Lifespan state management for clean resource handling
redis_manager: RedisStateManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_manager
    logger.info("Initializing Sentinel Gateway State Layers...")
    redis_manager = RedisStateManager()
    yield
    logger.info("Tearing down Sentinel Gateway State Layers...")
    await redis_manager.close()

app = FastAPI(title="Sentinel AI - Pre-Ingestion Node Gateway", version="1.0.0", lifespan=lifespan)

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