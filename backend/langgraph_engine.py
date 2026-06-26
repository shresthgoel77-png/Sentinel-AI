# backend/langgraph_engine.py
import logging
import asyncio
from schemas import DocumentExtractionPayload

# Import the status updater and the compiled graph from YOUR existing graph.py
from graph import update_status 
# NOTE: Assuming you have a compiled graph named `sentinel_graph` in graph.py. 
# e.g., sentinel_graph = builder.compile()
from graph import sentinel_graph 

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
                message="LangGraph engine initialized. Scanning for prompt injection..."
            )
            
            # 2. Prepare the state for your LangGraph
            initial_state = {
                "document_text": payload.extracted_plaintext,
                "metadata_payload": payload.metadata_payload,
                "security_flags": payload.security_flags,
            }
            
            # 3. Trigger your graph (run in an executor if your graph is synchronous)
            # If your graph.py uses async nodes, use sentinel_graph.ainvoke()
            result = await asyncio.to_thread(sentinel_graph.invoke, initial_state)
            
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