from flask import jsonify, request
from database import Transaction, get_user_profile, get_all_profiles, SessionLocal
from data_generator import generate_transaction
from risk_ml import risk_ml_service
from datetime import datetime

def init_routes(app):
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
    
    @app.route('/users', methods=['GET'])
    def get_users():
        profiles = get_all_profiles()
        return jsonify({
            "users": [
                {
                    "user_id": uid,
                    "name": profile["name"],
                    "account_age_days": profile["account_age_days"],
                    "avg_transaction": profile["avg_transaction"],
                    "location": "N/A"
                }
                for uid, profile in profiles.items()
            ]
        })
    
    @app.route('/generate-transaction', methods=['POST'])
    def generate_transaction_route():
        db = SessionLocal()
        try:
            data = request.json
            user_id = data.get('user_id')
            is_anomaly = data.get('is_anomaly', False)
            
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400
            
            user_profile = get_user_profile(user_id)
            if not user_profile:
                return jsonify({"error": f"User {user_id} not found"}), 404
            
            transaction_data = generate_transaction(user_profile, is_anomaly)
            
            transaction = Transaction(
                transaction_id=transaction_data['transaction_id'],
                user_id=transaction_data['user_id'],
                user_name=transaction_data['user_name'],
                amount=transaction_data['amount'],
                amount_ratio=transaction_data['amount_ratio'],
                merchant=transaction_data['merchant'],
                merchant_category=transaction_data['merchant_category'],
                category_risk=transaction_data['category_risk'],
                location=transaction_data['location'],
                timestamp=datetime.fromisoformat(transaction_data['timestamp'].replace('Z', '+00:00')),
                device_id=transaction_data['device_id'],
                ip_address=transaction_data['ip_address'],
                is_anomaly_label=transaction_data['is_anomaly_label'],
                account_age_days=transaction_data['account_age_days'],
                user_avg_transaction=transaction_data['user_avg_transaction']
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            return jsonify(transaction_data), 201
            
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    @app.route('/transactions', methods=['GET'])
    def get_transactions():
        db = SessionLocal()
        try:
            user_id = request.args.get('user_id')
            is_anomaly = request.args.get('is_anomaly')
            limit = request.args.get('limit', 50, type=int)
            
            query = db.query(Transaction)
            
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            if is_anomaly is not None:
                is_anomaly_bool = is_anomaly.lower() == 'true'
                query = query.filter(Transaction.is_anomaly_label == is_anomaly_bool)
            
            transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
            
            return jsonify({
                "transactions": [t.to_dict() for t in transactions],
                "count": len(transactions)
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    @app.route('/transactions/stats', methods=['GET'])
    def get_transaction_stats():
        db = SessionLocal()
        try:
            total_count = db.query(Transaction).count()
            anomaly_count = db.query(Transaction).filter(Transaction.is_anomaly_label == True).count()
            normal_count = total_count - anomaly_count
            
            return jsonify({
                "total": total_count,
                "normal": normal_count,
                "anomalous": anomaly_count
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    @app.route('/score-transaction', methods=['POST'])
    def score_transaction():
        """Score a transaction using ML model and return anomaly score with SHAP features"""
        try:
            transaction = request.json
            
            if not transaction:
                return jsonify({"error": "Transaction data is required"}), 400
            
            required_fields = ['amount_ratio', 'timestamp', 'category_risk', 'account_age_days']
            missing_fields = [field for field in required_fields if field not in transaction]
            
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            result = risk_ml_service.score_transaction(transaction)
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500