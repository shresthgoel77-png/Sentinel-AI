from sqlalchemy.orm import Session
from database.models import Policy

def get_tenant_policy(db: Session, tenant_id: int) -> dict:
    """
    Retrieves the custom policy rules assigned to the specific tenant environment. 
    Falls back to a secure default baseline if no customized policy is present.
    """
    policy_record = db.query(Policy).filter(Policy.tenant_id == tenant_id).first()
    
    if policy_record and policy_record.configuration:
        return policy_record.configuration
        
    return {
        "max_risk_score": 80,
        "enable_masking": True
    }
