# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Run backend :5000
python .\server\app.py

# Run frontend using python
cd .\client\ 
python -m http.server 3000