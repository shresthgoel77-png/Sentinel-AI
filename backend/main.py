from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- NEW: Import the compiled graph we built in graph.py ---
from backend.graph import app_graph 

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

@app.post("/api/analyze-prompt")
async def analyze_prompt(request: PromptRequest):
    user_text = request.text
    
    print(f"\n--- NEW REQUEST RECEIVED ---")
    print(f"Text to analyze: '{user_text}'")
    
    # 1. Prepare the blank "clipboard" for LangGraph
    initial_state = {
        "prompt": user_text,
        "scan_type": "",
        "findings": "",
        "threat_level": "",
        "confidence": 0,
        "final_action": ""
    }
    
#This is the main backend 

    # 2. Hand the clipboard to LangGraph and let the 4 agents run!
    print("Starting LangGraph pipeline...")
    final_state = app_graph.invoke(initial_state)
    print("Pipeline finished!\n")

    # 3. Return the fully filled-out clipboard to the frontend
    return {
        "status": "success",
        "analysis": final_state
    }