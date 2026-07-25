from sqlalchemy.orm import Session
from database.models import Policy, PolicyRule
import re

def get_tenant_policy(db: Session, tenant_id: int) -> dict:
    """Legacy backward compatibility wrapper."""
    return {
        "max_risk_score": 80,
        "enable_masking": True
    }

def evaluate_policies(db: Session, tenant_id: int, prompt_text: str, risk_score: float) -> tuple:
    """
    Evaluates dynamic rules.
    Returns (action, triggered_policy_name).
    actions: 'ALLOWED', 'BLOCKED'
    """
    policies = db.query(Policy).filter(Policy.tenant_id == tenant_id, Policy.is_active == True).all()
    if not policies:
        return ("BLOCKED" if risk_score > 80 else "ALLOWED"), ("Default Legacy Threshold" if risk_score > 80 else None)
        
    for policy in policies:
        rules = sorted([r for r in policy.rules if r.is_active], key=lambda x: x.priority)
        for rule in rules:
            matched = False
            if rule.condition_type == "semantic":
                try:
                    threshold = float(rule.condition_value.replace(">", "").strip())
                    if risk_score >= threshold:
                        matched = True
                except:
                    pass
            elif rule.condition_type == "regex":
                try:
                    if re.search(rule.condition_value, prompt_text, re.IGNORECASE):
                        matched = True
                except:
                    pass
            elif rule.condition_type == "heuristic":
                if rule.condition_value.lower() in prompt_text.lower():
                    matched = True
            
            if matched:
                action_str = rule.action.lower()
                final_action = "BLOCKED" if action_str == "block" else "ALLOWED"
                return final_action, policy.name
                
    return "ALLOWED", None
