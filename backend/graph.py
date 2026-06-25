import json
import redis
from typing import Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# ==========================================
# REDIS SETUP
# ==========================================
# Paste your copied Upstash URL here:
REDIS_URL = "redis://default:gQAAAAAAAhOUAAIgcDE3OWExNmMwM2YwY2Q0MDEyYjhjMDllY2I1ZWJiOTEyYw@normal-dory-136084.upstash.io:6379"

# We use try/except so your server doesn't crash if the URL is wrong
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis successfully!")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    r = None

def update_status(task_id: str, step: str, message: str, is_complete: bool = False, final_data: dict = None):
    """Helper function to write real-time updates to the Redis whiteboard."""
    print(f"[{step}] {message}")
    if r and task_id:
        status_payload = {
            "step": step,
            "message": message,
            "is_complete": is_complete,
            "final_data": final_data or {}
        }
        # Save to Redis for 1 hour (3600 seconds)
        r.setex(f"status:{task_id}", 3600, json.dumps(status_payload))

# ==========================================
# PIPELINE SETUP
# ==========================================
class ThreatState(TypedDict):
    task_id: str         # NEW: We need to know which task we are updating
    prompt: str
    scan_type: str
    findings: str
    threat_level: str
    confidence: int
    final_action: str

def planner_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Planner", "Routing prompt to correct scanner...")
    
    text = state["prompt"]
    scan_type = "deep_scan" if len(text) > 50 else "standard"
    return {"scan_type": scan_type}

def scanner_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Scanner", "Analyzing text for malicious intent...")
    
    text = state["prompt"]
    if "api key" in text.lower() or "password" in text.lower():
        findings = "Potential credential exposure or PII request found."
    elif "ignore previous instructions" in text.lower():
        findings = "Potential jailbreak prompt injection attempt detected."
    else:
        findings = "No immediate anomalies flagged in basic text scan."
    return {"findings": findings}

def classifier_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Classifier", "Calculating threat confidence level...")
    
    findings = state["findings"]
    if "jailbreak" in findings:
        return {"threat_level": "High", "confidence": 95}
    elif "PII" in findings or "credential" in findings:
        return {"threat_level": "Medium", "confidence": 80}
    else:
        return {"threat_level": "Low", "confidence": 99}

def responder_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Responder", "Finalizing security protocol...")
    
    threat = state["threat_level"]
    if threat == "High":
        action = "BLOCK"
    elif threat == "Medium":
        action = "REDACT"
    else:
        action = "ALLOW"
        
    # This is the final step, so we package the final data for the frontend!
    final_data = {
        "threat_level": threat,
        "confidence": state.get("confidence"),
        "final_action": action
    }
    update_status(task_id, "Complete", "Analysis finished.", is_complete=True, final_data=final_data)
        
    return {"final_action": action}

# Compile Graph
workflow = StateGraph(ThreatState)
workflow.add_node("planner", planner_agent)
workflow.add_node("scanner", scanner_agent)
workflow.add_node("classifier", classifier_agent)
workflow.add_node("responder", responder_agent)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "scanner")
workflow.add_edge("scanner", "classifier")
workflow.add_edge("classifier", "responder")
workflow.add_edge("responder", END)
app_graph = workflow.compile()