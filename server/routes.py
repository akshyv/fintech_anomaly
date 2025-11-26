from flask import jsonify, request
from database import get_all_profiles, get_user_profile, Transaction
from data_generator import generate_transaction
from database import SessionLocal
from datetime import datetime

def register_routes(app):
    """Register all API endpoints"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        return jsonify({
            "status": "ok",
            "message": "Transaction Anomaly Detector API is running",
            "version": "1.0.0"
        })
    
    @app.route('/users', methods=['GET'])
    def get_users():
        """Get all available user profiles"""
        try:
            profiles = get_all_profiles()
            return jsonify({
                "status": "success",
                "users": profiles
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/generate-transaction', methods=['POST'])
    def generate_txn():
        """
        Generate a synthetic transaction and save to database
        
        Body params:
            user_id: string (alice, bob, charlie)
            is_anomaly: boolean (default: false)
        """
        db = SessionLocal()
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Request body required"}), 400
            
            user_id = data.get('user_id')
            is_anomaly = data.get('is_anomaly', False)
            
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400
            
            # Validate user exists
            profile = get_user_profile(user_id)
            if not profile:
                return jsonify({
                    "error": f"Invalid user_id: {user_id}",
                    "valid_users": ["alice", "bob", "charlie"]
                }), 400
            
            # Generate transaction
            transaction_data = generate_transaction(user_id, is_anomaly)
            
            # Save to database
            db_transaction = Transaction(
                transaction_id=transaction_data['transaction_id'],
                user_id=transaction_data['user_id'],
                user_name=transaction_data['user_name'],
                amount=transaction_data['amount'],
                amount_ratio=transaction_data['amount_ratio'],
                merchant=transaction_data['merchant'],
                merchant_category=transaction_data['merchant_category'],
                category_risk=transaction_data['category_risk'],
                location=transaction_data['location'],
                timestamp=datetime.fromisoformat(transaction_data['timestamp']),
                device_id=transaction_data['device_id'],
                ip_address=transaction_data['ip_address'],
                is_anomaly_label=transaction_data['is_anomaly_label'],
                account_age_days=transaction_data['account_age_days'],
                user_avg_transaction=transaction_data['user_avg_transaction']
            )
            
            db.add(db_transaction)
            db.commit()
            db.refresh(db_transaction)
            
            print(f"✅ Saved transaction: {db_transaction.transaction_id} (ID: {db_transaction.id})")
            
            return jsonify({
                "status": "success",
                "message": "Transaction generated and saved to database",
                "transaction": transaction_data,
                "db_id": db_transaction.id
            })
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    @app.route('/transactions', methods=['GET'])
    def get_transactions():
        """
        Get all transactions from database
        
        Query params:
            limit: int (default: 50)
            user_id: string (optional filter)
            is_anomaly: boolean (optional filter)
        """
        db = SessionLocal()
        try:
            # Get query parameters
            limit = request.args.get('limit', 50, type=int)
            user_id = request.args.get('user_id', None, type=str)
            is_anomaly = request.args.get('is_anomaly', None, type=str)
            
            # Build query
            query = db.query(Transaction)
            
            # Apply filters
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            if is_anomaly is not None:
                is_anomaly_bool = is_anomaly.lower() == 'true'
                query = query.filter(Transaction.is_anomaly_label == is_anomaly_bool)
            
            # Order by most recent first
            query = query.order_by(Transaction.created_at.desc())
            
            # Apply limit
            transactions = query.limit(limit).all()
            
            # Convert to dict
            transactions_data = [txn.to_dict() for txn in transactions]
            
            return jsonify({
                "status": "success",
                "count": len(transactions_data),
                "transactions": transactions_data
            })
            
        except Exception as e:
            print(f"❌ Error fetching transactions: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    @app.route('/transactions/stats', methods=['GET'])
    def get_stats():
        """Get transaction statistics"""
        db = SessionLocal()
        try:
            total_count = db.query(Transaction).count()
            normal_count = db.query(Transaction).filter(Transaction.is_anomaly_label == False).count()
            anomaly_count = db.query(Transaction).filter(Transaction.is_anomaly_label == True).count()
            
            # Count by user
            alice_count = db.query(Transaction).filter(Transaction.user_id == 'alice').count()
            bob_count = db.query(Transaction).filter(Transaction.user_id == 'bob').count()
            charlie_count = db.query(Transaction).filter(Transaction.user_id == 'charlie').count()
            
            return jsonify({
                "status": "success",
                "stats": {
                    "total": total_count,
                    "normal": normal_count,
                    "anomalous": anomaly_count,
                    "by_user": {
                        "alice": alice_count,
                        "bob": bob_count,
                        "charlie": charlie_count
                    }
                }
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()