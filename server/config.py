import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Groq API configuration for LLM explanations
    # Why Groq? 10x faster than OpenAI, free tier is generous
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Database (will add in M5)
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_USER = os.getenv('DB_USER', 'root')
    # DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    # DB_NAME = os.getenv('DB_NAME', 'anomaly_detector')

# Debug: Check if Groq API key is loaded
if Config.GROQ_API_KEY:
    print(f"✅ Groq API key loaded (starts with: {Config.GROQ_API_KEY[:8]}...)")
else:
    print("⚠️  WARNING: GROQ_API_KEY not found in .env - LLM explanations will fail")