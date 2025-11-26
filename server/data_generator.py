"""
Generate synthetic transaction data using Faker
"""

from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# Merchant categories with risk scores
MERCHANT_CATEGORIES = {
    'grocery': 0.1,
    'gas': 0.15,
    'restaurant': 0.2,
    'retail': 0.3,
    'online': 0.4,
    'electronics': 0.5,
    'travel': 0.6,
    'jewelry': 0.8,
    'luxury': 0.9
}


def generate_transaction(user_profile, is_anomaly=False):
    """
    Generate a synthetic transaction for a user profile
    
    Args:
        user_profile: Dictionary with user profile data
        is_anomaly: Boolean, whether to generate an anomalous transaction
    
    Returns:
        Dictionary with transaction data
    """
    # Extract user profile data (handle both dict and object)
    if isinstance(user_profile, dict):
        user_id = user_profile['user_id']
        name = user_profile['name']
        avg_transaction = user_profile['avg_transaction']
        location = user_profile['location']
        preferred_categories = user_profile['preferred_categories']
    else:
        user_id = user_profile.user_id
        name = user_profile.name
        avg_transaction = user_profile.avg_transaction
        location = user_profile.location
        preferred_categories = user_profile.preferred_categories
    
    if is_anomaly:
        # Anomalous transaction: high amount, unusual category, odd time
        amount = avg_transaction * random.uniform(3.0, 8.0)
        category = random.choice(['luxury', 'jewelry', 'electronics', 'travel'])
        
        # Unusual time (late night or early morning)
        hour = random.choice(list(range(0, 5)) + list(range(22, 24)))
        timestamp = datetime.now().replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        # Different location
        location = fake.city() + ', ' + fake.state_abbr()
    else:
        # Normal transaction: typical amount, preferred category, normal time
        amount = avg_transaction * random.uniform(0.5, 2.0)
        category = random.choice(preferred_categories)
        
        # Normal business hours
        hour = random.randint(8, 22)
        timestamp = datetime.now().replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
    
    # Generate merchant name based on category
    merchant_names = {
        'grocery': ['Whole Foods', 'Safeway', 'Trader Joe\'s', 'Kroger'],
        'gas': ['Shell', 'Chevron', 'BP', 'Exxon'],
        'restaurant': ['McDonald\'s', 'Chipotle', 'Starbucks', 'Olive Garden'],
        'retail': ['Target', 'Walmart', 'Costco', 'Best Buy'],
        'online': ['Amazon', 'eBay', 'Etsy', 'Wayfair'],
        'electronics': ['Apple Store', 'Best Buy', 'Microsoft Store', 'Newegg'],
        'travel': ['Expedia', 'Booking.com', 'Airbnb', 'United Airlines'],
        'jewelry': ['Tiffany & Co', 'Kay Jewelers', 'Zales', 'Blue Nile'],
        'luxury': ['Gucci', 'Louis Vuitton', 'Rolex', 'Hermès']
    }
    
    merchant = random.choice(merchant_names.get(category, ['Generic Store']))
    
    return {
        'user_id': user_id,
        'amount': round(amount, 2),
        'merchant': merchant,
        'merchant_category': category,
        'location': location,
        'timestamp': timestamp.isoformat() + 'Z'
    }