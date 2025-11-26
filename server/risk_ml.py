import pickle
import numpy as np
import shap
from datetime import datetime, timedelta

class RiskMLService:
    def __init__(self, model_path='models/model.pkl'):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        self.explainer = shap.TreeExplainer(self.model)
    
    def extract_features(self, transaction, user_profile):
        """Extract features from transaction for ML model"""
        amount_ratio = transaction['amount'] / user_profile['avg_transaction']
        hour = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00')).hour
        day = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00')).weekday()
        
        # Simple merchant category encoding
        merchant_categories = ['retail', 'restaurant', 'online', 'gas', 'grocery', 'travel', 'entertainment']
        merchant_category_encoded = merchant_categories.index(transaction['merchant_category']) if transaction['merchant_category'] in merchant_categories else 0
        
        account_age_days = user_profile['account_age_days']
        features = np.array([[amount_ratio, hour, day, merchant_category_encoded, account_age_days]])
        
        return {
            'features': features,
            'amount_ratio': amount_ratio,
            'hour': hour,
            'day': day,
            'merchant_category_encoded': merchant_category_encoded,
            'account_age_days': account_age_days
        }
    
    def score_transaction(self, transaction, user_profile):
        """Score transaction with ML model and return SHAP explanations"""
        try:
            print("AKSHY_transaction:", transaction)
            feature_data = self.extract_features(transaction, user_profile)
            print("="*15)
            print(f"Extracted features shape: {feature_data['features'].shape}")
            features = feature_data['features']
            print(f"Features array: {features}")
            
            # Get anomaly score (Isolation Forest returns -1 to 1, convert to 0 to 1)
            anomaly_score_raw = self.model.decision_function(features)[0]
            print(f"Raw anomaly score: {anomaly_score_raw}")
            # Normalize to 0-1 range (higher = more anomalous)
            anomaly_score = 1 / (1 + np.exp(anomaly_score_raw))
            print(f"Normalized anomaly score: {anomaly_score}")
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(features)
            feature_names = ['amount_ratio', 'hour', 'day', 'merchant_category']
            
            # Get top 3 features by absolute SHAP value
            shap_dict = {name: float(value) for name, value in zip(feature_names, shap_values[0])}
            sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
            
            return {
                'anomaly_score': float(anomaly_score),
                'shap_features': dict(sorted_shap),
                'raw_features': {
                    'amount_ratio': float(feature_data['amount_ratio']),
                    'hour': int(feature_data['hour']),
                    'day': int(feature_data['day']),
                    'merchant_category_encoded': int(feature_data['merchant_category_encoded'])
                }
            }
        except Exception as e:
            raise Exception(f"Error scoring transaction: {str(e)}")
    
    def calculate_risk_score(self, transaction, user_profile, ml_score, recent_transactions):
        """
        Calculate multi-factor risk score combining ML + business rules
        
        Components:
        - model_anomaly (0.4): ML model's assessment
        - amount_ratio (0.3): Transaction size vs user's average
        - user_trust (0.2): Account age (newer accounts = higher risk)
        - velocity (0.1): Recent transaction count
        """
        try:
            # Component 1: Model Anomaly (weight 0.4)
            model_anomaly_value = ml_score
            model_anomaly_weight = 0.4
            model_anomaly_contribution = model_anomaly_value * model_anomaly_weight
            
            # Component 2: Amount Ratio (weight 0.3)
            # High ratio = high risk, cap at 3x for scoring
            amount_ratio = transaction['amount'] / user_profile['avg_transaction']
            amount_ratio_normalized = min(amount_ratio / 3.0, 1.0)  # Normalize to 0-1
            amount_ratio_weight = 0.3
            amount_ratio_contribution = amount_ratio_normalized * amount_ratio_weight
            
            # Component 3: User Trust (weight 0.2)
            # Newer accounts = less trust = higher risk
            # 0 days = 1.0 risk, 365+ days = 0.0 risk
            account_age_days = user_profile['account_age_days']
            user_trust_value = max(0, 1.0 - (account_age_days / 365.0))
            user_trust_weight = 0.2
            user_trust_contribution = user_trust_value * user_trust_weight
            
            # Component 4: Velocity (weight 0.1)
            # More transactions in last hour = higher risk
            # 0 txns = 0.0 risk, 5+ txns = 1.0 risk
            velocity_count = len(recent_transactions)
            velocity_value = min(velocity_count / 5.0, 1.0)
            velocity_weight = 0.1
            velocity_contribution = velocity_value * velocity_weight
            
            # Calculate final risk score
            risk_score = (
                model_anomaly_contribution +
                amount_ratio_contribution +
                user_trust_contribution +
                velocity_contribution
            )
            
            # Determine decision
            if risk_score > 0.7:
                decision = "DECLINE"
            elif risk_score >= 0.4:
                decision = "MANUAL REVIEW"
            else:
                decision = "APPROVE"
            
            return {
                'risk_score': float(risk_score),
                'decision': decision,
                'components': {
                    'model_anomaly': {
                        'value': float(model_anomaly_value),
                        'weight': model_anomaly_weight,
                        'contribution': float(model_anomaly_contribution)
                    },
                    'amount_ratio': {
                        'value': float(amount_ratio_normalized),
                        'weight': amount_ratio_weight,
                        'contribution': float(amount_ratio_contribution),
                        'raw_ratio': float(amount_ratio)
                    },
                    'user_trust': {
                        'value': float(user_trust_value),
                        'weight': user_trust_weight,
                        'contribution': float(user_trust_contribution),
                        'account_age_days': account_age_days
                    },
                    'velocity': {
                        'value': float(velocity_value),
                        'weight': velocity_weight,
                        'contribution': float(velocity_contribution),
                        'recent_count': velocity_count
                    }
                }
            }
        except Exception as e:
            raise Exception(f"Error calculating risk score: {str(e)}")