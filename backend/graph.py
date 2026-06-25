import json
import redis
import time
from typing import Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# ==========================================
# REDIS SETUP
# ==========================================
# Upstash Cloud Redis connection URI
REDIS_URL = "rediss://default:gQAAAAAAAhOUAAIgcDE3OWExNmMwM2YwY2Q0MDEyYjhjMDllY2I1ZWJiOTEyYw@normal-dory-136084.upstash.io:6379"


try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Connected to Upstash Redis successfully!")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    r = None

def update_status(task_id: str, step: str, message: str, is_complete: bool = False, extra_data: dict = None):
    """
    Helper function to write real-time, flattened updates to the Redis whiteboard.
    Ensures that metadata keys sit at the top level for rapid React JSON extraction.
    """
    print(f"[{step}] {message}")
    if r and task_id:
        status_payload = {
            "step": step,
            "message": message,
            "is_complete": is_complete
        }
        
        # If there's evaluation metrics available, flatten them directly into the root level
        if extra_data:
            status_payload.update(extra_data)
            
        # Save to Redis for 1 hour (3600 seconds)
        r.setex(f"status:{task_id}", 3600, json.dumps(status_payload))

# ==========================================
# PIPELINE SETUP
# ==========================================
class ThreatState(TypedDict):
    task_id: str         
    prompt: str
    scan_type: str
    findings: str
    threat_level: str
    confidence: int
    final_action: str

def planner_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Planner", "[SYSTEM] Extracting packet metadata & routing payload...")
    time.sleep(1) # Artificial delay to allow UI log streaming visibility
    
    text = state["prompt"]
    scan_type = "deep_scan" if len(text) > 50 else "standard"
    return {"scan_type": scan_type}

def scanner_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Scanner", "[AGENT] Running lexical security analysis on vector inputs...")
    time.sleep(1.2)
    
    text = state["prompt"]
    if "api key" in text.lower() or "password" in text.lower():
        findings = "Potential credential exposure or high-risk PII request detected."
    elif "ignore previous instructions" in text.lower() or "system prompt" in text.lower():
        findings = "Malicious prompt injection attempt matching known jailbreak signatures."
    else:
        findings = "No immediate structural anomalies flagged in token validation sequence."
    return {"findings": findings}

def classifier_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Classifier", "[AGENT] Evaluating pattern classification and risk weights...")
    time.sleep(1.2)
    
    findings = state["findings"]
    if "jailbreak" in findings:
        return {"threat_level": "high", "confidence": 95}
    elif "PII" in findings or "credential" in findings:
        return {"threat_level": "medium", "confidence": 80}
    else:
        return {"threat_level": "low", "confidence": 12}

def responder_agent(state: ThreatState) -> Dict[str, Any]:
    task_id = state.get("task_id", "")
    update_status(task_id, "Responder", "[SYSTEM] Compiling core firewall response protocol...")
    time.sleep(1)
    
    threat = state["threat_level"]
    if threat == "high":
        action = "block"
    elif threat == "medium":
        action = "redact"
    else:
        action = "allow"
        
    # Gather everything into a single layout dictionary matching React interface parsing hooks
    final_payload = {
        "threat_level": threat,
        "confidence": state.get("confidence", 0),
        "final_action": action,
        "findings": state.get("findings", "")
    }
    
    update_status(task_id, "Complete", "[SYSTEM] Pipeline executed. Connection finalized.", is_complete=True, extra_data=final_payload)
        
    return {"final_action": action}

# ==========================================
# COMPILING THE LANGGRAPH
# ==========================================
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