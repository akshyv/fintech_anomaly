from flask import Flask
from flask_cors import CORS
from database import init_db
from routes import init_routes

app = Flask(__name__)
CORS(app)

init_routes(app)

if __name__ == '__main__':
    init_db()
    
    print("Flask server starting on http://localhost:5000")
    app.run(debug=True, port=5000)