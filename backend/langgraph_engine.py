# backend/langgraph_engine.py
import logging
import asyncio
from sanitizer import DocumentSanitizer
from schemas import DocumentExtractionPayload

# Import the status updater and the compiled graph from your existing graph.py
from graph import update_status 
from graph import app_graph  # <-- FIXED: Using your actual compiled graph name!

logger = logging.getLogger("sentinel.gateway")

class LangGraphEngineHandoff:
    @staticmethod
    async def invoke_security_graph(payload: DocumentExtractionPayload) -> None:
        logger.info(f"Initiating LangGraph Evaluation for Task ID: {payload.task_id}")
        task_id_str = str(payload.task_id)
        
        try:
            # 1. Update Upstash using your existing function from graph.py
            update_status(
                task_id=task_id_str, 
                step="scanning", 
                message="LangGraph engine initialized. Scanning document for prompt injection..."
            )
            
            # --- NEW SANITIZATION STEP ---
            # 2a. Run the raw text through the Phase 2 Sanitizer
            clean_text, sanitizer_flags = DocumentSanitizer.process(payload.extracted_plaintext)
            
            # Combine the original flags with our new sanitizer flags
            payload.security_flags.update(sanitizer_flags)
            
            # 2b. Prepare the state EXACTLY how your ThreatState TypedDict expects it.
            combined_content = (
                f"--- VISIBLE TEXT ---\n{clean_text}\n\n"
                f"--- HIDDEN METADATA/FLAGS ---\n{payload.metadata_payload}\n"
                f"System Flags: {payload.security_flags}"
            )   
            
            initial_state = {
                "task_id": task_id_str,
                "prompt": combined_content
            }
            
            # 3. Trigger your graph using the correct variable
            result = await asyncio.to_thread(app_graph.invoke, initial_state) 
            
            # 4. Final success update
            update_status(
                task_id=task_id_str,
                step="complete", 
                message="Scanning complete.",
                is_complete=True,
                extra_data={"result": result}
            )
            
        except Exception as e:
            logger.error(f"Graph failure: {str(e)}")
            update_status(task_id=task_id_str, step="error", message=str(e), is_complete=True)