import logging
from database.database import SessionLocal
from database.models import AuditLog, GatewayLog, ActionTaken

logger = logging.getLogger("sentinel.gateway")

def write_audit_log_background(
    tenant_id: int, provider_name: str, model_name: str,
    risk_score: float, threats_json: dict, latency: int, tokens: int
):
    
    db_session = SessionLocal()
    try:
        log_entry = AuditLog(
            tenant_id=tenant_id,
            provider=provider_name,
            model=model_name,
            risk_score=risk_score,
            threats_triggered=threats_json,
            latency_ms=latency,
            tokens_used=tokens
        )
        db_session.add(log_entry)
        db_session.commit()
    except Exception as e:
        logger.error(f"Audit log insertion failed: {e}")
    finally:
        db_session.close()

def write_gateway_log_background(
    request_id: str,
    client_id: str,
    provider_used: str,
    model_name: str,
    risk_score: float,
    threat_classification: str,
    action_taken: ActionTaken,
    latency_ms: float,
    token_usage_prompt: int,
    token_usage_completion: int
):
    db_session = SessionLocal()
    try:
        log_entry = GatewayLog(
            request_id=request_id,
            client_id=client_id,
            provider_used=provider_used,
            model_name=model_name,
            risk_score=risk_score,
            threat_classification=threat_classification,
            action_taken=action_taken,
            latency_ms=latency_ms,
            token_usage_prompt=token_usage_prompt,
            token_usage_completion=token_usage_completion
        )
        db_session.add(log_entry)
        db_session.commit()
    except Exception as e:
        logger.error(f"Gateway log insertion failed: {e}")
    finally:
        db_session.close()
