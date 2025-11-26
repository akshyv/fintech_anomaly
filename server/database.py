"""
User profiles and database models
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
# from database import Base


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite database file location
DB_PATH = os.path.join(os.path.dirname(__file__), 'transactions.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL debug logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


class Transaction(Base):
    """SQLAlchemy model for transactions"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    user_name = Column(String)
    amount = Column(Float)
    amount_ratio = Column(Float)
    merchant = Column(String)
    merchant_category = Column(String)
    category_risk = Column(Float)
    location = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    device_id = Column(String)
    ip_address = Column(String)
    is_anomaly_label = Column(Boolean)
    account_age_days = Column(Integer)
    user_avg_transaction = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "amount": self.amount,
            "amount_ratio": self.amount_ratio,
            "merchant": self.merchant,
            "merchant_category": self.merchant_category,
            "category_risk": self.category_risk,
            "location": self.location,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "is_anomaly_label": self.is_anomaly_label,
            "account_age_days": self.account_age_days,
            "user_avg_transaction": self.user_avg_transaction,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserProfile:
    """Represents a customer profile with transaction patterns"""
    
    def __init__(self, user_id, name, account_age_days, avg_transaction, 
                 trust_score, preferred_categories):
        self.user_id = user_id
        self.name = name
        self.account_age_days = account_age_days
        self.avg_transaction = avg_transaction
        self.trust_score = trust_score  # 0.0 to 1.0
        self.preferred_categories = preferred_categories
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "account_age_days": self.account_age_days,
            "avg_transaction": self.avg_transaction,
            "trust_score": self.trust_score,
            "preferred_categories": self.preferred_categories
        }


# Hardcoded user profiles for demo
USER_PROFILES = {
    "alice": UserProfile(
        user_id="alice",
        name="Alice Johnson",
        account_age_days=730,  # 2 years old account
        avg_transaction=150.0,
        trust_score=0.95,
        preferred_categories=["grocery", "gas", "restaurant"]
    ),
    "bob": UserProfile(
        user_id="bob",
        name="Bob Smith",
        account_age_days=365,  # 1 year old account
        avg_transaction=300.0,
        trust_score=0.75,
        preferred_categories=["electronics", "online", "travel"]
    ),
    "charlie": UserProfile(
        user_id="charlie",
        name="Charlie Williams",
        account_age_days=30,  # New account (30 days)
        avg_transaction=500.0,
        trust_score=0.40,
        preferred_categories=["luxury", "jewelry", "online"]
    )
}


def get_user_profile(user_id):
    """Retrieve user profile by ID"""
    return USER_PROFILES.get(user_id)


def get_all_profiles():
    """Get all available user profiles"""
    return {uid: profile.to_dict() for uid, profile in USER_PROFILES.items()}