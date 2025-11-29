import pickle
import numpy as np
from groq import Groq
from config import Config
import json
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
        
# FIND the generate_explanation function (around line 160-245)
# REPLACE THE ENTIRE FUNCTION WITH THIS CORRECTED VERSION:

def generate_explanation(transaction: dict, risk_components: dict, decision: str) -> str:
    """
    Generate human-readable explanation using Groq LLM.
    
    Why Groq + llama-3.3-70b-versatile?
    - 500+ tokens/sec (10x faster than GPT-4)
    - Free tier: 14,400 requests/day
    - Excellent at concise financial reasoning
    - Low latency critical for real-time risk decisions
    
    Args:
        transaction: Full transaction dict
        risk_components: Dict with model_anomaly, amount_ratio, user_trust, velocity (each containing value/weight/contribution)
        decision: "APPROVE" | "MANUAL REVIEW" | "DECLINE"
    
    Returns:
        <100 token plain English explanation
    """
    try:
        print(f"=== GROQ LLM EXPLANATION START ===")
        print(f"Decision: {decision}")
        print(f"Risk components structure: {risk_components.keys()}")
        
        # Extract values from nested structure
        model_anomaly = risk_components.get('model_anomaly', {}).get('value', 0)
        amount_ratio_raw = risk_components.get('amount_ratio', {}).get('raw_ratio', 1)
        user_trust = risk_components.get('user_trust', {}).get('value', 0)
        velocity = risk_components.get('velocity', {}).get('value', 0)
        account_age = risk_components.get('user_trust', {}).get('account_age_days', 0)
        
        print(f"Extracted values - ML: {model_anomaly:.2f}, Amount Ratio: {amount_ratio_raw:.2f}x")
        
        # Check if API key exists
        if not Config.GROQ_API_KEY:
            print("❌ GROQ_API_KEY not configured")
            raise ValueError("Groq API key not found in environment")
        
        # Initialize Groq client
        client = Groq(api_key=Config.GROQ_API_KEY)
        
        # Build context-rich prompt
        prompt = f"""You are a financial risk analyst. Explain this transaction decision in <100 tokens.

TRANSACTION:
- Amount: ${transaction['amount']:.2f}
- Merchant: {transaction['merchant']} ({transaction['merchant_category']})
- User: {transaction.get('user_id', 'Unknown')} (account age: {account_age} days)
- Time: {transaction['timestamp']}

RISK ANALYSIS:
- ML Anomaly Score: {model_anomaly:.2f}/1.0 (weight: 40%)
- Amount Ratio: {amount_ratio_raw:.2f}x avg (weight: 30%)
- User Trust Score: {user_trust:.2f}/1.0 (weight: 20%)
- Velocity Score: {velocity:.2f}/1.0 (weight: 10%)

DECISION: {decision}

Explain why this decision was made. Focus on the top 2 risk factors. Be concise and actionable."""

        # Call Groq API
        print(f"Calling Groq API with model: llama-3.3-70b-versatile")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Best speed/quality balance
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise financial risk analyst. Respond in <100 tokens."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=150,  # Hard limit to prevent verbose responses
            temperature=0.3,  # Low temp = more deterministic/factual
            timeout=10  # Fail fast if Groq is slow
        )
        
        explanation = response.choices[0].message.content.strip()
        token_count = len(explanation.split())
        
        print(f"✅ LLM explanation generated ({token_count} tokens)")
        print(f"Explanation preview: {explanation[:100]}...")
        print(f"=== GROQ LLM EXPLANATION SUCCESS ===")
        
        return explanation
        
    except Exception as e:
        print(f"❌ GROQ LLM ERROR: {str(e)}")
        print(f"=== GROQ LLM EXPLANATION FAILED ===")
        
        # Fallback explanation if LLM fails - FIXED to handle nested dict
        try:
            model_score = risk_components.get('model_anomaly', {}).get('value', 0)
            amount_ratio = risk_components.get('amount_ratio', {}).get('raw_ratio', 1)
            return f"Decision: {decision}. Primary risk factors: ML anomaly score ({model_score:.2f}) and amount ratio ({amount_ratio:.2f}x average)."
        except:
            # Ultimate fallback if even that fails
            return f"Decision: {decision}. Unable to generate detailed explanation due to technical error."