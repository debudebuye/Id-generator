#!/usr/bin/env python3
"""
WSGI entry point for PythonAnywhere deployment
"""
import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Import the Flask app
from app import app

# For PythonAnywhere, we need to expose the app variable
application = app

if __name__ == "__main__":
    app.run()
