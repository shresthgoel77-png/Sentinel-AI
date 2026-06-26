import uuid
import json
import traceback
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis

# This handles client requests for redis
from graph import app_graph, r 

app = FastAPI(title="AI Shield Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"status": "Backend is online and ready!"}

# --- NEW: Safety Wrapper for the AI ---
def run_ai_safely(state: dict):
    try:
        # Try to run the LangGraph pipeline
        app_graph.invoke(state)
    except Exception as e:
        # If it crashes, print the EXACT error to the terminal
        print(f"\n❌ FATAL AI CRASH: {str(e)}\n")
        traceback.print_exc()
        
        # Tell React to stop spinning by writing the error to Redis
        if r:
            error_payload = {
                "step": "SYSTEM FAILURE",
                "message": f"AI Pipeline Crashed: {str(e)}",
                "is_complete": True,
                "threat_level": "low",
                "confidence": 0,
                "final_action": "error",
                "findings": "Backend AI failed to execute."
            }
            r.setex(f"status:{state['task_id']}", 3600, json.dumps(error_payload))

@app.post("/api/analyze-prompt")
async def analyze_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    user_text = request.text
    task_id = str(uuid.uuid4()) 
    
    initial_state = {
        "task_id": task_id,
        "prompt": user_text,
        "scan_type": "",
        "findings": "",
        "threat_level": "",
        "confidence": 0,
        "final_action": ""
    }
    
    # Hand the job to our new safety wrapper instead of directly to the graph
    background_tasks.add_task(run_ai_safely, initial_state)
    
    return {
        "status": "processing",
        "task_id": task_id,
        "message": "AI pipeline started!"
    }

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if not r:
        return {"error": "Redis database is not connected on the backend."}
        
    data = r.get(f"status:{task_id}")
    
    if data:
        return json.loads(data)
    else:
        return {"step": "Pending", "message": "Waiting for AI to start...", "is_complete": False}