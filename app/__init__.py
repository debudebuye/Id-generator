from flask import Flask
from .config.settings import Config
from .config.production import ProductionConfig
import os

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Configure app based on environment
    if config_name == 'production' or os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
        print("Using production configuration")
    else:
        app.config.from_object(Config)
        print("Using development configuration")
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)
    
    # Initialize Swagger
    from flasgger import Swagger
    Swagger(app)
    
    # Import routes after app initialization
    from .routes import bp
    app.register_blueprint(bp)
    
    return app

# Create the Flask application instance
app = create_app()

# Export the app instance
__all__ = ['app', 'create_app'] 