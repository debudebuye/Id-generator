from flask import Flask
from .config.settings import Config
import os

# Create the Flask application instance
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Configure app
app.config.from_object(Config)

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

# Import routes after app initialization
from .routes import bp
app.register_blueprint(bp)

# Export the app instance
__all__ = ['app'] 