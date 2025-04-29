#!/bin/bash

# Check if venv exists and create if it doesn't
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    
    # After creating venv, install dependencies
    source .venv/bin/activate
    pip install -r requirements.txt
    
    # Check if flask_sqlalchemy is in requirements, add it if not
    if ! grep -q "flask_sqlalchemy" requirements.txt; then
        echo "Adding flask_sqlalchemy to requirements"
        echo "flask_sqlalchemy" >> requirements.txt
        pip install flask_sqlalchemy
    fi
else
    # Just activate if venv already exists
    source .venv/bin/activate
fi

# Run the Flask application
python3 app.py

