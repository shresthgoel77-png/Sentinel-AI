import uuid
import json
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

#This handles client requests for redis
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

# --- NEW: Background Task Implementation ---
@app.post("/api/analyze-prompt")
async def analyze_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    user_text = request.text
    
    # Generate a unique receipt ID for this user's request
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
    
    # Hand the job to LangGraph to process in the BACKGROUND
    background_tasks.add_task(app_graph.invoke, initial_state)
    
    # Instantly return the receipt to the frontend so it can start its loading animation
    return {
        "status": "processing",
        "task_id": task_id,
        "message": "AI pipeline started!"
    }

# --- NEW: Polling Endpoint for React ---
@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    # If Redis isn't connected, throw an error safely
    if not r:
        return {"error": "Redis database is not connected on the backend."}
        
    # Check the Redis whiteboard for this specific task ID
    data = r.get(f"status:{task_id}")
    
    if data:
        # Return the JSON data written by our agents
        return json.loads(data)
    else:
        # If the agents haven't written anything yet
        return {"step": "Pending", "message": "Waiting for AI to start...", "is_complete": False}