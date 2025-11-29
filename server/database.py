"""
User profiles and database models
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# SQLite database file location
DB_PATH = os.path.join(os.path.dirname(__file__), 'transactions.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
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
    print("Database initialized successfully")


class Transaction(Base):
    """SQLAlchemy model for transactions"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    merchant_category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": float(self.amount),
            "merchant": self.merchant,
            "merchant_category": self.merchant_category,
            "location": self.location,
            "timestamp": self.timestamp.isoformat() + 'Z' if self.timestamp else None,
            "is_anomaly": self.is_anomaly
        }
class AuditLog(Base):
    """
    Audit log for compliance tracking.
    Records every risk decision with full context.
    """
    __tablename__ = 'audit_log'
    
    # Primary key - auto-incrementing ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction reference
    transaction_id = Column(Integer, nullable=False)
    user_id = Column(String(50), nullable=False)
    
    # Risk assessment results
    risk_score = Column(Float, nullable=False)  # 0.0 - 1.0
    decision = Column(String(20), nullable=False)  # APPROVE/MANUAL REVIEW/DECLINE
    
    # Risk components breakdown (stored as JSON string)
    risk_components = Column(String, nullable=True)  # JSON: {ml_score, amount_ratio, etc.}
    
    # AI explanation
    explanation = Column(String, nullable=True)
    
    # Audit metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.decision} for txn {self.transaction_id}>"
    
    def to_dict(self):
        """Convert audit log entry to dictionary for JSON response"""
        import json
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'risk_score': round(self.risk_score, 3),
            'decision': self.decision,
            'risk_components': json.loads(self.risk_components) if self.risk_components else {},
            'explanation': self.explanation,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
class UserProfile:
    """Represents a customer profile with transaction patterns"""
    
    def __init__(self, user_id, name, account_age_days, avg_transaction, 
                 location, trust_score, preferred_categories):
        self.user_id = user_id
        self.name = name
        self.account_age_days = account_age_days
        self.avg_transaction = avg_transaction
        self.location = location
        self.trust_score = trust_score
        self.preferred_categories = preferred_categories
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "account_age_days": self.account_age_days,
            "avg_transaction": self.avg_transaction,
            "location": self.location,
            "trust_score": self.trust_score,
            "preferred_categories": self.preferred_categories
        }


# Hardcoded user profiles for demo
USER_PROFILES = {
    "alice": UserProfile(
        user_id="alice",
        name="Alice Johnson",
        account_age_days=730,
        avg_transaction=150.0,
        location="New York, NY",
        trust_score=0.95,
        preferred_categories=["grocery", "gas", "restaurant"]
    ),
    "bob": UserProfile(
        user_id="bob",
        name="Bob Smith",
        account_age_days=365,
        avg_transaction=300.0,
        location="Los Angeles, CA",
        trust_score=0.75,
        preferred_categories=["electronics", "online", "travel"]
    ),
    "charlie": UserProfile(
        user_id="charlie",
        name="Charlie Williams",
        account_age_days=30,
        avg_transaction=500.0,
        location="Miami, FL",
        trust_score=0.40,
        preferred_categories=["luxury", "jewelry", "online"]
    )
}


def get_user_profile(user_id):
    """Retrieve user profile by ID"""
    profile = USER_PROFILES.get(user_id)
    return profile.to_dict() if profile else None


def get_all_profiles():
    """Get all available user profiles as a list"""
    return [profile.to_dict() for profile in USER_PROFILES.values()]


# Create tables on import
Base.metadata.create_all(engine)