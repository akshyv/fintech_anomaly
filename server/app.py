from flask import Flask
from flask_cors import CORS
from routes import register_routes
from database import init_db

app = Flask(__name__)

# Allow frontend on port 3000 to call backend on port 5000
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize database
init_db()

# Register all API routes
register_routes(app)

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 BACKEND SERVER STARTING")
    print("=" * 50)
    print("📍 Backend running on: http://localhost:5000")
    print("🔗 Frontend should run on: http://localhost:3000")
    print("🧪 Health check: http://localhost:5000/health")
    print("💾 Database: SQLite (transactions.db)")
    print("=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')