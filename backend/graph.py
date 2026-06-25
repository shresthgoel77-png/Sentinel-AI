from typing import Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# ==========================================
# STEP 2a: Define the State (The Clipboard)
# ==========================================
# This structure defines exactly what data our agents can read and write.
class ThreatState(TypedDict):
    prompt: str          # The original text from the user
    scan_type: str       # Determined by Planner: "deep_scan" or "standard"
    findings: str        # Written by Scanner: Details of what was found
    threat_level: str    # Written by Classifier: "Low", "Medium", or "High"
    confidence: int      # Written by Classifier: 0 to 100 percentage
    final_action: str    # Written by Responder: "ALLOW", "REDACT", or "BLOCK"

# ==========================================
# STEP 2b: Define the 4 Agents (The Nodes)
# ==========================================

def planner_agent(state: ThreatState) -> Dict[str, Any]:
    print("--- PLANNER AGENT RUNNING ---")
    text = state["prompt"]
    
    # Simple logic for now: if the prompt is long, do a deep scan
    scan_type = "deep_scan" if len(text) > 50 else "standard"
    
    # We return the updates we want to make to the clipboard
    return {"scan_type": scan_type}


def scanner_agent(state: ThreatState) -> Dict[str, Any]:
    print("--- SCANNER AGENT RUNNING ---")
    text = state["prompt"]
    scan_mode = state["scan_type"]
    
    # Simple logic looking for typical malicious keywords
    if "api key" in text.lower() or "password" in text.lower():
        findings = "Potential credential exposure or PII request found."
    elif "ignore previous instructions" in text.lower():
        findings = "Potential jailbreak prompt injection attempt detected."
    else:
        findings = "No immediate anomalies flagged in basic text scan."
        
    return {"findings": findings}


def classifier_agent(state: ThreatState) -> Dict[str, Any]:
    print("--- CLASSIFIER AGENT RUNNING ---")
    findings = state["findings"]
    
    # Assign threat levels based on the scanner's findings
    if "jailbreak" in findings:
        return {"threat_level": "High", "confidence": 95}
    elif "PII" in findings or "credential" in findings:
        return {"threat_level": "Medium", "confidence": 80}
    else:
        return {"threat_level": "Low", "confidence": 99}


def responder_agent(state: ThreatState) -> Dict[str, Any]:
    print("--- RESPONDER AGENT RUNNING ---")
    threat = state["threat_level"]
    
    # Make the final security decision
    if threat == "High":
        action = "BLOCK"
    elif threat == "Medium":
        action = "REDACT"
    else:
        action = "ALLOW"
        
    return {"final_action": action}

# ==========================================
# STEP 2c: Connect the Pipeline (The Graph)
# ==========================================

# 1. Initialize the graph with our custom State structure
workflow = StateGraph(ThreatState)

# 2. Add our 4 agents as nodes in the graph
workflow.add_node("planner", planner_agent)
workflow.add_node("scanner", scanner_agent)
workflow.add_node("classifier", classifier_agent)
workflow.add_node("responder", responder_agent)

# 3. Define the sequential flow (Edges)
workflow.set_entry_point("planner")       # Start here
workflow.add_edge("planner", "scanner")     # Then go here
workflow.add_edge("scanner", "classifier")  # Then go here
workflow.add_edge("classifier", "responder")# Then go here
workflow.add_edge("responder", END)         # Finish!

# 4. Compile the graph so it's ready to execute
app_graph = workflow.compile()