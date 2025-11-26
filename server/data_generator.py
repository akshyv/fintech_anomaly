"""
Synthetic transaction data generation using Faker
"""

from faker import Faker
import random
from datetime import datetime


fake = Faker()

# Merchant categories with risk weights
MERCHANT_CATEGORIES = {
    "grocery": {"risk": 0.1, "avg_amount": 80},
    "gas": {"risk": 0.1, "avg_amount": 50},
    "restaurant": {"risk": 0.2, "avg_amount": 60},
    "electronics": {"risk": 0.4, "avg_amount": 400},
    "online": {"risk": 0.5, "avg_amount": 150},
    "travel": {"risk": 0.3, "avg_amount": 800},
    "luxury": {"risk": 0.7, "avg_amount": 1200},
    "jewelry": {"risk": 0.8, "avg_amount": 2000},
    "crypto": {"risk": 0.9, "avg_amount": 5000}
}


def generate_transaction(user_profile, is_anomaly=False):
    """
    Generate a synthetic transaction for a given user profile
    
    Args:
        user_profile: UserProfile object (not user_id string)
        is_anomaly: If True, generate suspicious transaction
    
    Returns:
        dict: Transaction data
    """
    # Generate transaction ID
    transaction_id = f"txn_{fake.uuid4()[:8]}"
    
    # Select merchant category
    if is_anomaly:
        # For anomalies, pick high-risk categories
        category = random.choice(["luxury", "jewelry", "crypto", "online"])
    else:
        # For normal, use user's preferred categories
        category = random.choice(user_profile.preferred_categories)
    
    category_info = MERCHANT_CATEGORIES[category]
    
    # Generate amount
    if is_anomaly:
        # Anomalous: 3-10x user's average
        amount = round(user_profile.avg_transaction * random.uniform(3.0, 10.0), 2)
    else:
        # Normal: 0.5-2x user's average with some variation
        base = category_info["avg_amount"]
        amount = round(base * random.uniform(0.7, 1.5), 2)
    
    # Generate merchant name
    merchant = fake.company()
    
    # Generate location
    if is_anomaly and random.random() > 0.5:
        # 50% chance of foreign location for anomalies
        location = fake.country()
    else:
        location = f"{fake.city()}, {fake.state_abbr()}"
    
    # Generate timestamp (current time with some variance)
    timestamp = datetime.now().isoformat()
    
    # Generate device info
    device_id = f"device_{fake.uuid4()[:8]}"
    ip_address = fake.ipv4()
    
    # Calculate amount ratio (transaction amount / user average)
    amount_ratio = round(amount / user_profile.avg_transaction, 2)
    
    transaction = {
        "transaction_id": transaction_id,
        "user_id": user_profile.user_id,
        "user_name": user_profile.name,
        "amount": amount,
        "amount_ratio": amount_ratio,
        "merchant": merchant,
        "merchant_category": category,
        "category_risk": category_info["risk"],
        "location": location,
        "timestamp": timestamp,
        "device_id": device_id,
        "ip_address": ip_address,
        "is_anomaly_label": is_anomaly,
        "account_age_days": user_profile.account_age_days,
        "user_avg_transaction": user_profile.avg_transaction
    }
    
    return transaction


def generate_batch_transactions(user_profile, count=10, anomaly_ratio=0.2):
    """
    Generate a batch of transactions for testing
    
    Args:
        user_profile: UserProfile object
        count: Number of transactions to generate
        anomaly_ratio: Proportion of anomalous transactions (0.0 to 1.0)
    
    Returns:
        list: List of transactions
    """
    transactions = []
    num_anomalies = int(count * anomaly_ratio)
    
    for i in range(count):
        is_anomaly = i < num_anomalies
        txn = generate_transaction(user_profile, is_anomaly)
        transactions.append(txn)
    
    # Shuffle to mix normal and anomalous
    random.shuffle(transactions)
    return transactions