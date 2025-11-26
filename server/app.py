from flask import Flask
from flask_cors import CORS
from routes import api
import traceback
import sys

app = Flask(__name__)
CORS(app)

# Register blueprint
app.register_blueprint(api)

# Add error handler to see full errors
@app.errorhandler(500)
def internal_error(error):
    print("=" * 80, file=sys.stderr)
    print("500 ERROR OCCURRED:", file=sys.stderr)
    traceback.print_exc()
    print("=" * 80, file=sys.stderr)
    return {"error": "Internal server error", "details": str(error)}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)