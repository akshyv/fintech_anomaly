import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database (will add in M5)
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_USER = os.getenv('DB_USER', 'root')
    # DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    # DB_NAME = os.getenv('DB_NAME', 'anomaly_detector')