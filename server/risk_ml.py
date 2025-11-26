"""
ML-based risk scoring and SHAP explanations
"""
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import os

class RiskMLService:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'amount_ratio',
            'hour',
            'day_of_week',
            'category_risk',
            'account_age_days'
        ]
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """Load existing model or train a new one"""
        model_path = 'models/model.pkl'
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            print("Loaded existing Isolation Forest model")
        else:
            print("Training new Isolation Forest model...")
            self.model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            # Generate synthetic training data
            np.random.seed(42)
            n_samples = 1000
            
            # Normal transactions
            normal_data = np.column_stack([
                np.random.uniform(0.5, 1.5, n_samples),
                np.random.randint(8, 20, n_samples),
                np.random.randint(0, 7, n_samples),
                np.random.uniform(0.1, 0.4, n_samples),
                np.random.uniform(100, 1000, n_samples)
            ])
            
            # Anomalous transactions
            n_anomalies = 100
            anomaly_data = np.column_stack([
                np.random.uniform(2.5, 5.0, n_anomalies),
                np.random.randint(0, 24, n_anomalies),
                np.random.randint(0, 7, n_anomalies),
                np.random.uniform(0.6, 1.0, n_anomalies),
                np.random.uniform(1, 30, n_anomalies)
            ])
            
            training_data = np.vstack([normal_data, anomaly_data])
            self.model.fit(training_data)
            
            # Save model
            os.makedirs('models', exist_ok=True)
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            print(f"Model trained and saved to {model_path}")
    
    def extract_features(self, transaction):
        """Extract ML features from transaction dictionary"""
        timestamp = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00'))
        
        features = {
            'amount_ratio': transaction['amount_ratio'],
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'category_risk': transaction['category_risk'],
            'account_age_days': transaction['account_age_days']
        }
        
        feature_vector = np.array([
            features[name] for name in self.feature_names
        ]).reshape(1, -1)
        
        return features, feature_vector
    
    def calculate_shap_approximation(self, features, feature_vector, anomaly_score):
        """Simplified SHAP-like attribution"""
        baseline = np.array([[1.0, 14, 3, 0.3, 365]])
        baseline_score = -self.model.score_samples(baseline)[0]
        
        contributions = {}
        for i, feature_name in enumerate(self.feature_names):
            perturbed = feature_vector.copy()
            perturbed[0, i] = baseline[0, i]
            perturbed_score = -self.model.score_samples(perturbed)[0]
            contribution = anomaly_score - perturbed_score
            contributions[feature_name] = float(contribution)
        
        sorted_features = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]
        
        return dict(sorted_features)
    
    def score_transaction(self, transaction):
        """Score a transaction and return anomaly score with SHAP features"""
        try:
            features, feature_vector = self.extract_features(transaction)
            raw_score = -self.model.score_samples(feature_vector)[0]
            anomaly_score = min(max(raw_score, 0), 1)
            
            shap_features = self.calculate_shap_approximation(
                features, 
                feature_vector, 
                raw_score
            )
            
            return {
                'anomaly_score': float(anomaly_score),
                'shap_features': shap_features,
                'raw_features': features
            }
            
        except Exception as e:
            raise Exception(f"Error scoring transaction: {str(e)}")


risk_ml_service = RiskMLService()