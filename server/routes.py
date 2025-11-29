from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from database import SessionLocal, get_user_profile, get_all_profiles, Transaction, AuditLog
from data_generator import generate_transaction
from risk_ml import RiskMLService, generate_explanation
from audit import log_decision, get_audit_logs
import traceback

api = Blueprint('api', __name__)
risk_service = RiskMLService()
USER_PROFILES = get_all_profiles()

@api.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@api.route('/users', methods=['GET'])
def get_users():
    try:
        profiles = get_all_profiles()
        # Convert dict to list if needed
        if isinstance(profiles, dict):
            profiles_list = list(profiles.values())
        else:
            profiles_list = profiles
        return jsonify({'users': profiles_list})
    except Exception as e:
        print("ERROR in /users:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/generate-transaction', methods=['POST'])
def create_transaction():
    db = SessionLocal()
    try:
        print("=== GENERATE TRANSACTION START ===")
        data = request.get_json()
        print(f"Request data: {data}")
        
        user_id = data.get('user_id')
        is_anomaly = data.get('is_anomaly', False)
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        print(f"Getting user profile for: {user_id}")
        user_profile = get_user_profile(user_id)
        if not user_profile:
            return jsonify({'error': 'User not found'}), 404
        
        print(f"User profile: {user_profile}")
        
        # Generate transaction
        print("Generating transaction...")
        transaction_data = generate_transaction(user_profile, is_anomaly)
        print(f"Generated transaction: {transaction_data}")
        
        # Save to database
        print("Saving to database...")
        transaction = Transaction(
            user_id=transaction_data['user_id'],
            amount=transaction_data['amount'],
            merchant=transaction_data['merchant'],
            merchant_category=transaction_data['merchant_category'],
            location=transaction_data['location'],
            timestamp=datetime.fromisoformat(transaction_data['timestamp'].replace('Z', '+00:00')),
            is_anomaly=is_anomaly
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        print(f"Saved transaction with ID: {transaction.transaction_id}")
        
        # Convert to dict for response
        result = {
            'transaction_id': transaction.transaction_id,
            'user_id': transaction.user_id,
            'amount': float(transaction.amount),
            'merchant': transaction.merchant,
            'merchant_category': transaction.merchant_category,
            'location': transaction.location,
            'timestamp': transaction.timestamp.isoformat() + 'Z',
            'is_anomaly': transaction.is_anomaly
        }
        
        print("\n\t=== GENERATE TRANSACTION SUCCESS ===")
        return jsonify(result)
    except Exception as e:
        print("=== GENERATE TRANSACTION ERROR ===")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/transactions', methods=['GET'])
def get_transactions():
    db = SessionLocal()
    try:
        print("=== GET TRANSACTIONS START ===")
        user_id = request.args.get('user_id')
        is_anomaly = request.args.get('is_anomaly')
        limit = int(request.args.get('limit', 50))
        
        print(f"Query params - user_id: {user_id}, is_anomaly: {is_anomaly}, limit: {limit}")
        
        query = db.query(Transaction)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if is_anomaly is not None:
            is_anomaly_bool = is_anomaly.lower() == 'true'
            query = query.filter(Transaction.is_anomaly == is_anomaly_bool)
        
        transactions = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        print(f"Found {len(transactions)} transactions")
        
        result = [{
        'transaction_id': str(t.transaction_id),  # Convert to string
        'user_id': t.user_id,
        'user_name': next((u['name'] for u in USER_PROFILES if u['user_id'] == t.user_id), 'Unknown'),  # Add user name
        'amount': float(t.amount),
        'merchant': t.merchant,
        'merchant_category': t.merchant_category,
        'location': t.location,
        'timestamp': t.timestamp.isoformat() + 'Z',
        'is_anomaly': t.is_anomaly,
        'is_anomaly_label': t.is_anomaly,  # For frontend badge
        'amount_ratio': float(t.amount) / next((u['avg_transaction'] for u in USER_PROFILES if u['user_id'] == t.user_id), 100)  # Calculate ratio
    } for t in transactions]
        
        print("=== GET TRANSACTIONS SUCCESS ===")
        return jsonify({
            'transactions': result,
            'count': len(result)
        })
    except Exception as e:
        print("=== GET TRANSACTIONS ERROR ===")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/transactions/stats', methods=['GET'])
def get_stats():
    db = SessionLocal()
    try:
        print("=== GET STATS START ===")
        total = db.query(Transaction).count()
        normal = db.query(Transaction).filter(Transaction.is_anomaly == False).count()
        anomalous = db.query(Transaction).filter(Transaction.is_anomaly == True).count()
        
        print(f"Stats - total: {total}, normal: {normal}, anomalous: {anomalous}")
        print("=== GET STATS SUCCESS ===")
        
        return jsonify({
            'total': total,
            'normal': normal,
            'anomalous': anomalous
        })
    except Exception as e:
        print("=== GET STATS ERROR ===")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/score-transaction', methods=['POST'])
def score_transaction():
    try:
        print("=== SCORE TRANSACTION START ===")
        data = request.get_json()
        print(f"\n\tRequest data: {data}")
        transaction = data.get('transaction')
        user_profile = data.get('user_profile')
        
        if not transaction or not user_profile:
            return jsonify({'error': 'transaction and user_profile are required'}), 400
        print("====="*10,181)
        result = risk_service.score_transaction(transaction, user_profile)
        print(f"\n\tScoring result: {result}")
        print("=== SCORE TRANSACTION SUCCESS ===")
        return jsonify(result)
    except Exception as e:
        print("=== SCORE TRANSACTION ERROR ===")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/calculate-risk', methods=['POST'])
@api.route('/calculate-risk', methods=['POST'])
def calculate_risk():
    """Calculate comprehensive risk score with business rules + ML"""
    print("\n=== CALCULATE RISK START ===")
    
    try:
        data = request.json
        print(f"Received data: {data}")
        
        # Extract transaction and profile data
        transaction = data.get('transaction')
        user_profile = data.get('user_profile')
        ml_score = data.get('ml_score')
        
        # Validation
        if not transaction or not user_profile or ml_score is None:
            print("❌ Missing required fields")
            return jsonify({'error': 'Missing required fields: transaction, user_profile, or ml_score'}), 400
        
        # Extract specific fields
        transaction_id = transaction.get('transaction_id')
        user_id = transaction.get('user_id')
        amount = transaction.get('amount')
        
        if not all([transaction_id, user_id, amount]):
            print("❌ Missing transaction fields")
            return jsonify({'error': 'Missing transaction_id, user_id, or amount'}), 400
        
        print(f"User profile: {user_profile['user_id']}, trust: {user_profile['trust_score']}")
        print(f"Transaction ID: {transaction_id}, Amount: ${amount}, ML Score: {ml_score:.3f}")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Calculate velocity (transactions in last hour)
            # For demo, use simplified logic - in production, query DB for time window
            recent_txns = db.query(Transaction).filter(Transaction.user_id == user_id).count()
            velocity_score = min(recent_txns / 10.0, 1.0)  # Normalize: 10+ txns = max risk
            
            # Calculate amount ratio
            avg_transaction = user_profile['avg_transaction']
            amount_ratio = amount / avg_transaction
            amount_ratio_score = min(amount_ratio / 3.0, 1.0)  # 3x avg = max risk
            
            # Calculate trust score (inverse of account age risk)
            trust_score = user_profile['trust_score']
            trust_risk = 1.0 - trust_score  # Higher trust = lower risk
            
            # === WEIGHTED RISK CALCULATION ===
            risk_components = {
                'ml_anomaly': {
                    'value': ml_score,
                    'weight': 0.4,
                    'contribution': ml_score * 0.4
                },
                'amount_ratio': {
                    'value': amount_ratio_score,
                    'weight': 0.3,
                    'contribution': amount_ratio_score * 0.3
                },
                'user_trust': {
                    'value': trust_risk,
                    'weight': 0.2,
                    'contribution': trust_risk * 0.2
                },
                'velocity': {
                    'value': velocity_score,
                    'weight': 0.1,
                    'contribution': velocity_score * 0.1
                }
            }
            
            # Calculate final weighted score
            final_risk = sum(comp['contribution'] for comp in risk_components.values())
            
            # === DECISION LOGIC ===
            if final_risk > 0.7:
                decision = "DECLINE"
            elif final_risk > 0.4:
                decision = "MANUAL REVIEW"
            else:
                decision = "APPROVE"
            
            print(f"Final risk: {final_risk:.3f} → {decision}")
            
            # === LOG TO AUDIT TRAIL ===
            print("=== CALLING AUDIT LOGGER ===")
            audit_entry = log_decision(
                transaction_id=transaction_id,
                user_id=user_id,
                risk_score=final_risk,
                decision=decision,
                risk_components=risk_components,
                explanation=None  # Will be added by /explain-decision endpoint
            )
            
            response = {
                'risk_score': round(final_risk, 3),
                'decision': decision,
                'components': risk_components,
                'audit_id': audit_entry.id  # Return audit log ID for reference
            }
            
            print("=== CALCULATE RISK SUCCESS ===")
            return jsonify(response)
            
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@api.route('/audit-log', methods=['GET'])
def get_audit_log():
    """
    Retrieve audit log entries for compliance review.
    Query params:
        - limit: Max entries to return (default 10, max 100)
        - user_id: Filter by specific user (optional)
    """
    print("\n=== GET AUDIT LOG START ===")
    
    try:
        # Parse query parameters
        limit = request.args.get('limit', default=10, type=int)
        user_id = request.args.get('user_id', default=None, type=str)
        
        # Enforce max limit
        limit = min(limit, 100)
        
        print(f"Fetching audit logs: limit={limit}, user_id={user_id}")
        
        # Fetch logs using audit service
        logs = get_audit_logs(limit=limit, user_id=user_id)
        
        print(f"✅ Returning {len(logs)} audit entries")
        print("=== GET AUDIT LOG SUCCESS ===")
        
        return jsonify({
            'count': len(logs),
            'logs': logs
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
        
@api.route('/explain-decision', methods=['POST'])
def explain_decision():
    """Generate LLM explanation for risk decision"""
    print("\n=== EXPLAIN DECISION START ===")
    
    try:
        data = request.json
        transaction = data.get('transaction')
        risk_components = data.get('risk_components')
        decision = data.get('decision')
        
        if not all([transaction, risk_components, decision]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Import the standalone function (not from class)
        from risk_ml import generate_explanation
        
        # Call the standalone function directly
        explanation = generate_explanation(
            transaction=transaction,
            risk_components=risk_components,
            decision=decision
        )
        
        print(f"✅ Generated explanation: {explanation[:100]}...")
        
        # === UPDATE AUDIT LOG WITH EXPLANATION ===
        transaction_id = transaction.get('transaction_id')
        if transaction_id:
            print(f"=== UPDATING AUDIT LOG {transaction_id} WITH EXPLANATION ===")
            db = SessionLocal()
            try:
                # Find the most recent audit entry for this transaction
                audit_entry = db.query(AuditLog).filter(
                    AuditLog.transaction_id == transaction_id
                ).order_by(AuditLog.timestamp.desc()).first()
                
                if audit_entry:
                    audit_entry.explanation = explanation
                    db.commit()
                    print(f"✅ Audit log {audit_entry.id} updated with explanation")
                else:
                    print(f"⚠️ No audit entry found for transaction {transaction_id}")
            finally:
                db.close()
        
        response = {
            'explanation': explanation,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print("=== EXPLAIN DECISION SUCCESS ===")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500