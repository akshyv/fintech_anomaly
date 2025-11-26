from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from database import SessionLocal, get_user_profile, get_all_profiles, Transaction
from data_generator import generate_transaction
from risk_ml import RiskMLService
import traceback

api = Blueprint('api', __name__)
risk_service = RiskMLService()

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
            'transaction_id': t.transaction_id,
            'user_id': t.user_id,
            'amount': float(t.amount),
            'merchant': t.merchant,
            'merchant_category': t.merchant_category,
            'location': t.location,
            'timestamp': t.timestamp.isoformat() + 'Z',
            'is_anomaly': t.is_anomaly
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
def calculate_risk():
    db = SessionLocal()
    try:
        print("=== CALCULATE RISK START ===")
        data = request.get_json()
        transaction = data.get('transaction')
        user_profile = data.get('user_profile')
        ml_score = data.get('ml_score')
        
        if not transaction or not user_profile or ml_score is None:
            return jsonify({'error': 'transaction, user_profile, and ml_score are required'}), 400
        
        # Get recent transactions (last hour) for velocity calculation
        user_id = transaction['user_id']
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.timestamp >= one_hour_ago
        ).all()
        
        # Convert to list for velocity calculation
        recent_txns_list = [{
            'transaction_id': t.transaction_id,
            'amount': float(t.amount),
            'timestamp': t.timestamp.isoformat()
        } for t in recent_transactions]
        
        result = risk_service.calculate_risk_score(
            transaction, 
            user_profile, 
            ml_score, 
            recent_txns_list
        )
        
        print("=== CALCULATE RISK SUCCESS ===")
        return jsonify(result)
    except Exception as e:
        print("=== CALCULATE RISK ERROR ===")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()