"""
Audit logging service for compliance tracking.
Logs every risk decision with full context for regulatory requirements.
"""

from database import SessionLocal, AuditLog
import json
from datetime import datetime

def log_decision(transaction_id, user_id, risk_score, decision, risk_components=None, explanation=None):
    """
    Log a risk decision to the audit trail.
    
    Args:
        transaction_id (int): ID of the transaction being assessed
        user_id (str): User who made the transaction
        risk_score (float): Calculated risk score (0.0 - 1.0)
        decision (str): Final decision (APPROVE/MANUAL REVIEW/DECLINE)
        risk_components (dict): Breakdown of risk factors
        explanation (str): LLM-generated explanation
    
    Returns:
        AuditLog: The created audit log entry
    
    Raises:
        Exception: If database write fails
    """
    print("=== AUDIT LOG START ===")
    print(f"Logging decision for txn_id: {transaction_id}, user: {user_id}")
    print(f"Risk score: {risk_score:.3f}, Decision: {decision}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Convert risk_components dict to JSON string for storage
        components_json = json.dumps(risk_components) if risk_components else None
        
        # Create audit log entry
        audit_entry = AuditLog(
            transaction_id=transaction_id,
            user_id=user_id,
            risk_score=risk_score,
            decision=decision,
            risk_components=components_json,
            explanation=explanation,
            timestamp=datetime.utcnow()
        )
        
        # Persist to database
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)  # Get the auto-generated ID
        
        print(f"✅ Audit log saved with ID: {audit_entry.id}")
        print("=== AUDIT LOG SUCCESS ===")
        
        return audit_entry
        
    except Exception as e:
        print(f"❌ AUDIT LOG ERROR: {str(e)}")
        db.rollback()
        raise Exception(f"Failed to log decision: {str(e)}")
    finally:
        db.close()


def get_audit_logs(limit=10, user_id=None):
    """
    Retrieve recent audit log entries.
    
    Args:
        limit (int): Maximum number of entries to return (default 10)
        user_id (str): Optional filter by user_id
    
    Returns:
        list: List of audit log dictionaries
    """
    print(f"=== FETCHING AUDIT LOGS (limit={limit}, user_id={user_id}) ===")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Build query
        query = db.query(AuditLog)
        
        # Filter by user if specified
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        # Order by most recent first, limit results
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        print(f"✅ Found {len(logs)} audit entries")
        
        # Convert to dictionaries
        return [log.to_dict() for log in logs]
        
    except Exception as e:
        print(f"❌ AUDIT FETCH ERROR: {str(e)}")
        raise Exception(f"Failed to fetch audit logs: {str(e)}")
    finally:
        db.close()